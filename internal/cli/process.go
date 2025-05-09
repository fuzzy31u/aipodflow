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
	var titlesOnly bool
	var generateShowNotes bool
	var skipUpload bool
	var apiOnly bool

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
			// Determine what to generate based on flags
			genShownotes := generateShowNotes
	
			// If titles-only is set, override other flags
			if titlesOnly {
				genShownotes = false
			}
	
			// Generate content
			candidates, err := contentProcessor.GenerateCandidates(transcript, genShownotes)
			if err != nil {
				return fmt.Errorf("content generation failed: %w", err)
			}
			logger.Info("Content generation completed")

			// 5. Selection process (always use our display-only UI)
			var selectedContent *model.SelectedContent

			// Use the interactive UI which now just displays the content without prompts
			interactiveUI := ui.NewInteractiveUI(logger)
			logger.Info("Displaying content...")
			selectedContent, err = interactiveUI.SelectContent(candidates)
			if err != nil {
				return fmt.Errorf("content display failed: %w", err)
			}

			// Save all candidates to file if output directory is specified
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

				if err := os.WriteFile(allCandidatesPath, []byte(content), 0644); err != nil {
					logger.Warnf("Failed to save all candidates to file: %v", err)
				} else {
					logger.Infof("All candidates saved to %s", allCandidatesPath)
				}
			}
			logger.Info("Content display completed")

			// Exit early if api-only flag is set
			if apiOnly {
				logger.Info("API-only mode: stopping after API call as requested")
				return nil
			}

			// 6. Save selection (optional)
			if outputDir != "" {
				// Use title as filename
				sanitizedTitle := sanitizeFilename(selectedContent.Title)
				outputPath := filepath.Join(outputDir, sanitizedTitle+".txt")

				// Save content
				content := fmt.Sprintf("=== Selected Content ===\nTitle: %s\n\nShow Notes:\n%s",
					selectedContent.Title, selectedContent.ShowNote)

				if err := os.WriteFile(outputPath, []byte(content), 0644); err != nil {
					logger.Warnf("Failed to save selection to file: %v", err)
				} else {
					logger.Infof("Selection saved to %s", outputPath)
				}
			}

			// 7. Art19 upload (optional)
			if !skipUpload {
				art19Processor := processor.NewArt19Processor(art19Service, logger)
				logger.Info("Starting Art19 upload process...")
				if err := art19Processor.UploadDraft(cmd.Context(), inputAudio, selectedContent); err != nil {
					return fmt.Errorf("Art19 upload failed: %w", err)
				}
			} else {
				logger.Info("Skipping Art19 upload as requested")
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
	processCmd.Flags().BoolVar(&titlesOnly, "titles-only", false, "Generate only titles, skip show notes")
	processCmd.Flags().BoolVar(&generateShowNotes, "gen-shownotes", true, "Generate show notes (default: true)")
	processCmd.Flags().BoolVar(&skipUpload, "skip-upload", false, "Skip uploading to Art19")
	processCmd.Flags().BoolVar(&apiOnly, "api-only", false, "Stop after API call and display response")

	// Set required flags
	if err := processCmd.MarkFlagRequired("input-transcript"); err != nil {
		fmt.Fprintf(os.Stderr, "Error marking flag as required: %v\n", err)
	}
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
