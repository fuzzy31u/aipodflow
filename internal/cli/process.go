package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/automate-podcast/config"
	"github.com/automate-podcast/internal/model"
	"github.com/automate-podcast/internal/processor"
	"github.com/automate-podcast/internal/ui"
	"github.com/automate-podcast/services"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

// NewProcessCmd creates a command for transcript processing
func NewProcessCmd() *cobra.Command {
	var inputTranscript string
	var inputAudio string
	var outputDir string
	var verbose bool
	var nonInteractive bool

	processCmd := &cobra.Command{
		Use:   "process-transcript",
		Short: "Process podcast transcript",
		Long:  `Process podcast transcript to generate show notes and upload to Art19.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			// Initialize logger
			logger := logrus.New()
			if verbose {
				logger.SetLevel(logrus.DebugLevel)
			} else {
				logger.SetLevel(logrus.InfoLevel)
			}
			logger.SetFormatter(&logrus.TextFormatter{
				FullTimestamp: true,
			})

			// Load configuration
			cfg, err := config.LoadConfig()
			if err != nil {
				return fmt.Errorf("failed to load configuration: %w", err)
			}

			// Create output directory
			if outputDir != "" {
				if err := os.MkdirAll(outputDir, 0755); err != nil {
					return fmt.Errorf("failed to create output directory: %w", err)
				}
			}

			// 1. Load transcript
			logger.Infof("Loading transcript from %s", inputTranscript)
			transcript, err := processor.LoadTranscript(inputTranscript)
			if err != nil {
				return fmt.Errorf("failed to load transcript: %w", err)
			}
			logger.Info("Transcript loaded successfully")

			// 2. Initialize services
			aiService := services.NewAIService(cfg.OpenAIAPIKey, logger)
			art19Service := services.NewArt19Service(cfg.Art19Username, cfg.Art19Password, logger)

			// 3. Initialize processor
			contentProcessor := processor.NewContentProcessor(aiService, logger)

			// 4. AI generation process
			logger.Info("Starting content generation...")
			// Changed to include instructions directly in the prompt instead of using sample references
			candidates, err := contentProcessor.GenerateCandidates(transcript)
			if err != nil {
				return fmt.Errorf("content generation failed: %w", err)
			}
			logger.Info("Content generation completed")

			// 5. Selection process (interactive or automatic)
			var selectedContent *model.SelectedContent

			if nonInteractive {
				// Non-interactive mode: automatically select the first candidates
				logger.Info("Running in non-interactive mode, automatically selecting first candidates...")
				selectedContent = &model.SelectedContent{
					Title:       candidates.Titles[0],
					ShowNote:    candidates.ShowNotes[0],
					AdTimecodes: candidates.AdTimecodes[0],
				}

				// Output all candidates to file
				if outputDir != "" {
					allCandidatesPath := filepath.Join(outputDir, "all_candidates.txt")
					content := "=== Title Candidates ===\n"
					for i, title := range candidates.Titles {
						content += fmt.Sprintf("%d: %s\n", i+1, title)
					}

					content += "\n=== Show Note Candidates ===\n"
					for i, note := range candidates.ShowNotes {
						content += fmt.Sprintf("%d:\n%s\n\n", i+1, note)
					}

					content += "\n=== Ad Timecode Candidates ===\n"
					for i, timecodes := range candidates.AdTimecodes {
						content += fmt.Sprintf("%d: %v\n", i+1, timecodes)
					}

					if err := os.WriteFile(allCandidatesPath, []byte(content), 0644); err != nil {
						logger.Warnf("Failed to save all candidates to file: %v", err)
					} else {
						logger.Infof("All candidates saved to %s", allCandidatesPath)
					}
				}
			} else {
				// Interactive mode
				interactiveUI := ui.NewInteractiveUI(logger)
				logger.Info("Starting interactive selection...")
				var err error
				selectedContent, err = interactiveUI.SelectContent(candidates)
				if err != nil {
					return fmt.Errorf("interactive selection failed: %w", err)
				}
			}
			logger.Info("Selection completed")

			// 6. Save selection (optional)
			if outputDir != "" {
				// Use title as filename
				sanitizedTitle := sanitizeFilename(selectedContent.Title)
				outputPath := filepath.Join(outputDir, sanitizedTitle+".txt")

				// Save content
				content := fmt.Sprintf("Title: %s\n\nShow Notes:\n%s\n\nAd Timecodes: %v\n",
					selectedContent.Title, selectedContent.ShowNote, selectedContent.AdTimecodes)

				if err := os.WriteFile(outputPath, []byte(content), 0644); err != nil {
					logger.Warnf("Failed to save selection to file: %v", err)
				} else {
					logger.Infof("Selection saved to %s", outputPath)
				}
			}

			// 7. Art19 upload
			art19Processor := processor.NewArt19Processor(art19Service, logger)
			logger.Info("Starting Art19 upload process...")
			if err := art19Processor.UploadDraft(cmd.Context(), inputAudio, selectedContent); err != nil {
				return fmt.Errorf("Art19 upload failed: %w", err)
			}

			logger.Info("Process completed successfully!")
			return nil
		},
	}

	// Set flags
	processCmd.Flags().StringVarP(&inputTranscript, "input-transcript", "t", "", "Path to transcript file (required)")
	processCmd.Flags().StringVarP(&inputAudio, "input-audio", "a", "", "Path to audio file (required)")
	processCmd.Flags().StringVarP(&outputDir, "output-dir", "o", "", "Output directory for generated files")
	processCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose logging")
	processCmd.Flags().BoolVarP(&nonInteractive, "non-interactive", "n", false, "Run in non-interactive mode (auto-select first candidates)")

	// Set required flags
	processCmd.MarkFlagRequired("input-transcript")
	// Audio file is optional (only required for Art19 upload)

	return processCmd
}

// sanitizeFilename replaces characters that cannot be used in filenames
func sanitizeFilename(filename string) string {
	// Replace characters that cannot be used in filenames
	replacer := strings.NewReplacer(
		"/", "_",
		"\\", "_",
		":", "_",
		"*", "_",
		"?", "_",
		"\"", "_",
		"<", "_",
		">", "_",
		"|", "_",
	)
	return replacer.Replace(filename)
}
