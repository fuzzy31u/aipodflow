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

// Step1Cmd creates a command for transcript processing and OpenAI API call
func Step1Cmd() *cobra.Command {
	var inputTranscript string
	var outputDir string
	var verbose bool
	var titlesOnly bool
	var generateShowNotes bool
	var openAIKey string

	cmd := &cobra.Command{
		Use:   "step1",
		Short: "Process transcript and call OpenAI API",
		Long:  `Import the transcript file, call OpenAI API, and show the output in console.`,
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

			// Get OpenAI API key from flag or environment
			if openAIKey == "" {
				openAIKey = os.Getenv("OPENAI_API_KEY")
				if openAIKey == "" {
					return fmt.Errorf("OpenAI API key is required. Set it with --openai-key flag or OPENAI_API_KEY environment variable")
				}
			}

			// Create output directory if specified
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

			// 2. Initialize AI service
			aiService := services.NewAIService(openAIKey, logger)

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

			// 5. Display the generated content
			interactiveUI := ui.NewInteractiveUI(logger)
			logger.Info("Displaying content...")
			selectedContent, err := interactiveUI.SelectContent(candidates)
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
				
				// Also save the selected content
				selectedPath := filepath.Join(outputDir, "selected_content.txt")
				selectedContent := fmt.Sprintf("=== Selected Content ===\nTitle: %s\n\nShow Notes:\n%s",
					selectedContent.Title, selectedContent.ShowNote)
				
				if err := os.WriteFile(selectedPath, []byte(selectedContent), 0644); err != nil {
					logger.Warnf("Failed to save selected content to file: %v", err)
				} else {
					logger.Infof("Selected content saved to %s", selectedPath)
				}
			}

			logger.Info("Step 1 completed successfully!")
			return nil
		},
	}

	// Set flags
	cmd.Flags().StringVarP(&inputTranscript, "input-transcript", "t", "", "Path to transcript file (required)")
	cmd.Flags().StringVarP(&outputDir, "output-dir", "o", "", "Output directory for generated files")
	cmd.Flags().StringVar(&openAIKey, "openai-key", "", "OpenAI API key (can also be set via OPENAI_API_KEY environment variable)")
	cmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose logging")
	cmd.Flags().BoolVar(&titlesOnly, "titles-only", false, "Generate only titles, skip show notes")
	cmd.Flags().BoolVar(&generateShowNotes, "gen-shownotes", true, "Generate show notes (default: true)")

	// Set required flags
	if err := cmd.MarkFlagRequired("input-transcript"); err != nil {
		fmt.Fprintf(os.Stderr, "Error marking flag as required: %v\n", err)
	}

	return cmd
}

// Step2Cmd creates a command for uploading to Art19
func Step2Cmd() *cobra.Command {
	var inputAudio string
	var contentFile string
	var verbose bool

	cmd := &cobra.Command{
		Use:   "step2",
		Short: "Upload to Art19",
		Long:  `Upload title, shownote and audio to the Art19 platform.`,
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

			// Load selected content from file
			var selectedContent *model.SelectedContent
			if contentFile != "" {
				// Read content from file
				logger.Infof("Loading content from %s", contentFile)
				content, err := os.ReadFile(contentFile)
				if err != nil {
					return fmt.Errorf("failed to read content file: %w", err)
				}
				
				// Parse content
				contentStr := string(content)
				titleStart := strings.Index(contentStr, "Title: ")
				showNotesStart := strings.Index(contentStr, "Show Notes:")
				
				if titleStart >= 0 && showNotesStart > titleStart {
					title := strings.TrimSpace(contentStr[titleStart+len("Title: "):showNotesStart])
					showNote := strings.TrimSpace(contentStr[showNotesStart+len("Show Notes:"):])
					
					selectedContent = &model.SelectedContent{
						Title:    title,
						ShowNote: showNote,
					}
				} else {
					return fmt.Errorf("failed to parse content file, expected format not found")
				}
			} else {
				return fmt.Errorf("content file is required")
			}

			// Initialize Art19 service
			art19Service := services.NewArt19Service(cfg.Art19Username, cfg.Art19Password, logger)
			art19Processor := processor.NewArt19Processor(art19Service, logger)
			
			// Upload to Art19
			logger.Info("Starting Art19 upload process...")
			if err := art19Processor.UploadDraft(cmd.Context(), inputAudio, selectedContent); err != nil {
				return fmt.Errorf("Art19 upload failed: %w", err)
			}

			logger.Info("Step 2 completed successfully!")
			return nil
		},
	}

	// Set flags
	cmd.Flags().StringVarP(&inputAudio, "input-audio", "a", "", "Path to audio file (required)")
	cmd.Flags().StringVarP(&contentFile, "content-file", "c", "", "Path to content file (required)")
	cmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose logging")

	// Set required flags
	if err := cmd.MarkFlagRequired("input-audio"); err != nil {
		fmt.Fprintf(os.Stderr, "Error marking flag as required: %v\n", err)
	}
	if err := cmd.MarkFlagRequired("content-file"); err != nil {
		fmt.Fprintf(os.Stderr, "Error marking flag as required: %v\n", err)
	}

	return cmd
}

// Step3Cmd creates a command for redeploying on Vercel
func Step3Cmd() *cobra.Command {
	var verbose bool

	cmd := &cobra.Command{
		Use:   "step3",
		Short: "Redeploy on Vercel",
		Long:  `Call Redeploy button in the Vercel via API.`,
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

			// This feature is not implemented yet
			logger.Info("Vercel redeployment feature is not implemented yet")
			logger.Info("This will be implemented in a future update")

			logger.Info("Step 3 completed successfully!")
			return nil
		},
	}

	// Set flags
	cmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose logging")

	return cmd
}

// Step4Cmd creates a command for posting to X
func Step4Cmd() *cobra.Command {
	var verbose bool

	cmd := &cobra.Command{
		Use:   "step4",
		Short: "Post to X",
		Long:  `Create the text to post to X.`,
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

			// This feature is not implemented yet
			logger.Info("X posting feature is not implemented yet")
			logger.Info("This will be implemented in a future update")

			logger.Info("Step 4 completed successfully!")
			return nil
		},
	}

	// Set flags
	cmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose logging")

	return cmd
}
