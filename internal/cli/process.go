package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
)

// NewProcessCmd creates a parent command for podcast processing with step subcommands
func NewProcessCmd() *cobra.Command {
	processCmd := &cobra.Command{
		Use:   "process",
		Short: "Process podcast content",
		Long:  `Process podcast content with separate steps for transcript processing, Art19 upload, Vercel redeployment, and X posting.`,
	}

	// Add step subcommands
	processCmd.AddCommand(Step1Cmd())
	processCmd.AddCommand(Step2Cmd())
	processCmd.AddCommand(Step3Cmd())
	processCmd.AddCommand(Step4Cmd())
	
	// Add the legacy command for backward compatibility
	processCmd.AddCommand(NewLegacyProcessCmd())

	return processCmd
}

// NewLegacyProcessCmd creates the original process command for backward compatibility
func NewLegacyProcessCmd() *cobra.Command {
	var inputTranscript string
	var inputAudio string
	var outputDir string
	var verbose bool
	var titlesOnly bool
	var generateShowNotes bool
	var skipUpload bool
	var apiOnly bool

	processCmd := &cobra.Command{
		Use:   "all",
		Short: "Process podcast transcript (legacy mode)",
		Long:  `Process podcast transcript to generate show notes and upload to Art19 in a single command.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			// Run step 1
			step1Cmd := Step1Cmd()
			step1Args := []string{
				"--input-transcript", inputTranscript,
				"--output-dir", outputDir,
			}
			if verbose {
				step1Args = append(step1Args, "--verbose")
			}
			if titlesOnly {
				step1Args = append(step1Args, "--titles-only")
			}
			if !generateShowNotes {
				step1Args = append(step1Args, "--gen-shownotes=false")
			}
			
			step1Cmd.SetArgs(step1Args)
			if err := step1Cmd.Execute(); err != nil {
				return err
			}
			
			// Exit early if api-only flag is set
			if apiOnly {
				return nil
			}
			
			// Skip Art19 upload if requested
			if !skipUpload && inputAudio != "" {
				// Run step 2
				selectedPath := filepath.Join(outputDir, "selected_content.txt")
				step2Cmd := Step2Cmd()
				step2Args := []string{
					"--input-audio", inputAudio,
					"--content-file", selectedPath,
				}
				if verbose {
					step2Args = append(step2Args, "--verbose")
				}
				
				step2Cmd.SetArgs(step2Args)
				if err := step2Cmd.Execute(); err != nil {
					return err
				}
			}
			
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
