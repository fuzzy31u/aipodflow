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
	"github.com/joho/godotenv"
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
					title := strings.TrimSpace(contentStr[titleStart+len("Title: ") : showNotesStart])
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
	var dryRun bool

	cmd := &cobra.Command{
		Use:   "step3",
		Short: "Redeploy on Vercel",
		Long:  `Call Redeploy button in the Vercel via API to trigger a website redeployment.`,
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

			// Load .env file if it exists
			if err := godotenv.Load(); err != nil {
				logger.Debugf("No .env file found or error loading it: %v", err)
			} else {
				logger.Debug("Loaded environment variables from .env file")
			}

			// Initialize Vercel service directly from environment variables
			vercelService := services.NewVercelServiceFromEnv(logger)

			// Check if Vercel deploy hook is configured
			deployHookURL := os.Getenv("VERCEL_DEPLOY_HOOK")
			if deployHookURL == "" {
				return fmt.Errorf("Vercel deploy hook URL is not configured. Please set the VERCEL_DEPLOY_HOOK environment variable")
			}

			// If dry run, just log the action without actually triggering the deployment
			if dryRun {
				logger.Info("Dry run mode: Would trigger Vercel redeployment using hook URL")
				logger.Info("Vercel hook URL is configured correctly")
			} else {
				// Trigger the redeployment
				logger.Info("Triggering Vercel redeployment...")
				if err := vercelService.TriggerRedeploy(cmd.Context()); err != nil {
					return fmt.Errorf("failed to trigger Vercel redeployment: %w", err)
				}
				logger.Info("Vercel redeployment triggered successfully")
			}

			logger.Info("Step 3 completed successfully!")
			return nil
		},
	}

	// Set flags
	cmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose logging")
	cmd.Flags().BoolVar(&dryRun, "dry-run", false, "Validate configuration without triggering actual redeployment")

	return cmd
}

// Step4Cmd creates a command for generating social media post text
func Step4Cmd() *cobra.Command {
	var verbose bool
	var dryRun bool
	var rssURL string
	var spotifyShowURL string
	var applePodcastShowURL string
	var outputFile string

	cmd := &cobra.Command{
		Use:   "step4",
		Short: "Generate SNS post",
		Long:  `Generate text to post to social media platforms from podcast RSS feed.`,
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

			// Load .env file if it exists
			if err := godotenv.Load(); err != nil {
				logger.Debugf("No .env file found or error loading it: %v", err)
			} else {
				logger.Debug("Loaded environment variables from .env file")
			}

			// Set values from environment variables or command-line flags
			if rssURL == "" {
				rssURL = os.Getenv("RSS_FEED_URL")
				if rssURL == "" {
					logger.Error("RSS_FEED_URL not set in environment or command-line flag")
					return fmt.Errorf("RSS feed URL is required. Set it with --rss-url flag or RSS_FEED_URL environment variable")
				} else {
					logger.Infof("Using RSS feed URL from environment: %s", rssURL)
				}
			}
			logger.Infof("RSS feed URL: %s", rssURL)

			if spotifyShowURL == "" {
				spotifyShowURL = os.Getenv("SPOTIFY_SHOW_URL")
				if spotifyShowURL == "" {
					logger.Error("SPOTIFY_SHOW_URL not set in environment or command-line flag")
					return fmt.Errorf("Spotify show URL is required. Set it with --spotify-url flag or SPOTIFY_SHOW_URL environment variable")
				} else {
					logger.Infof("Using Spotify show URL from environment: %s", spotifyShowURL)
				}
			}
			logger.Infof("Spotify show URL: %s", spotifyShowURL)

			if applePodcastShowURL == "" {
				applePodcastShowURL = os.Getenv("APPLE_PODCAST_URL")
				if applePodcastShowURL == "" {
					logger.Error("APPLE_PODCAST_URL not set in environment or command-line flag")
					return fmt.Errorf("Apple Podcast URL is required. Set it with --apple-url flag or APPLE_PODCAST_URL environment variable")
				} else {
					logger.Infof("Using Apple Podcast URL from environment: %s", applePodcastShowURL)
				}
			}
			logger.Infof("Apple Podcast URL: %s", applePodcastShowURL)

			// Initialize SNS service
			snsService := services.NewSNSService(logger)

			// Fetch latest episode title from RSS feed
			logger.Info("Fetching latest episode title from RSS feed...")
			title, err := snsService.GetLatestEpisodeTitle(cmd.Context(), rssURL)
			if err != nil {
				return fmt.Errorf("failed to fetch latest episode title: %w", err)
			}
			logger.Infof("Latest episode title: %s", title)

			// Fetch latest Spotify episode URL
			logger.Info("Fetching latest Spotify episode URL...")
			spotifyURL, err := snsService.GetLatestSpotifyURL(cmd.Context(), spotifyShowURL)
			if err != nil {
				logger.Warnf("Failed to fetch latest Spotify episode URL: %v", err)
				logger.Warn("Using Spotify show URL as fallback")
				spotifyURL = spotifyShowURL
			}
			logger.Infof("Spotify URL: %s", spotifyURL)

			// Fetch latest Apple Podcast episode URL
			logger.Info("Fetching latest Apple Podcast episode URL...")
			appleURL, err := snsService.GetLatestApplePodcastURL(cmd.Context(), applePodcastShowURL)
			if err != nil {
				logger.Warnf("Failed to fetch latest Apple Podcast episode URL: %v", err)
				logger.Warn("Using Apple Podcast show URL as fallback")
				appleURL = applePodcastShowURL
			}
			logger.Infof("Apple Podcast URL: %s", appleURL)

			// Generate post text
			postText := snsService.CreateSNSPostText(title, spotifyURL, appleURL)

			// Display the post text
			logger.Info("Generated social media post text:")
			fmt.Println("\n" + postText + "\n")
			logger.Infof("Character count: %d", len(postText))

			// Save to file if output file is specified
			if outputFile != "" {
				logger.Infof("Saving post text to file: %s", outputFile)
				if err := os.WriteFile(outputFile, []byte(postText), 0644); err != nil {
					return fmt.Errorf("failed to save post text to file: %w", err)
				}
				logger.Info("Post text saved to file successfully")
			}

			logger.Info("Step 4 completed successfully!")
			return nil
		},
	}

	// Set flags
	cmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose logging")
	cmd.Flags().BoolVar(&dryRun, "dry-run", false, "Validate configuration without making external requests")
	cmd.Flags().StringVar(&rssURL, "rss-url", "", "URL of the podcast RSS feed (required, can also be set via RSS_FEED_URL environment variable)")
	cmd.Flags().StringVar(&spotifyShowURL, "spotify-url", "", "URL of the Spotify show (required, can also be set via SPOTIFY_SHOW_URL environment variable)")
	cmd.Flags().StringVar(&applePodcastShowURL, "apple-url", "", "URL of the Apple Podcast show (required, can also be set via APPLE_PODCAST_URL environment variable)")
	cmd.Flags().StringVar(&outputFile, "output", "", "File to save the generated post text (optional)")

	return cmd
}
