package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/automate-podcast/config"
	"github.com/automate-podcast/internal/processor"
	"github.com/automate-podcast/internal/ui"
	"github.com/automate-podcast/services"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

// NewProcessCmd はprocess-transcriptコマンドを作成する
func NewProcessCmd() *cobra.Command {
	var transcriptPath string
	var audioPath string
	var outputDir string
	var verbose bool

	processCmd := &cobra.Command{
		Use:   "process-transcript",
		Short: "Process podcast transcript",
		Long:  `Process podcast transcript to generate show notes and upload to Art19.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			// ロガーの初期化
			logger := logrus.New()
			if verbose {
				logger.SetLevel(logrus.DebugLevel)
			} else {
				logger.SetLevel(logrus.InfoLevel)
			}
			logger.SetFormatter(&logrus.TextFormatter{
				FullTimestamp: true,
			})

			// 設定の読み込み
			cfg, err := config.LoadConfig()
			if err != nil {
				return fmt.Errorf("failed to load configuration: %w", err)
			}

			// 出力ディレクトリの作成
			if outputDir != "" {
				if err := os.MkdirAll(outputDir, 0755); err != nil {
					return fmt.Errorf("failed to create output directory: %w", err)
				}
			}

			// 1. トランスクリプト読み込み
			logger.Infof("Loading transcript from %s", transcriptPath)
			transcript, err := processor.LoadTranscript(transcriptPath)
			if err != nil {
				return fmt.Errorf("failed to load transcript: %w", err)
			}
			logger.Info("Transcript loaded successfully")

			// 2. サービスの初期化
			aiService := services.NewAIService(cfg.OpenAIAPIKey, logger)
			art19Service := services.NewArt19Service(cfg.Art19Username, cfg.Art19Password, logger)

			// 3. プロセッサーの初期化
			contentProcessor := processor.NewContentProcessor(aiService, logger)

			// 4. AI生成処理
			logger.Info("Starting content generation...")
			candidates, err := contentProcessor.GenerateCandidates(transcript)
			if err != nil {
				return fmt.Errorf("content generation failed: %w", err)
			}
			logger.Info("Content generation completed")

			// 5. インタラクティブ選択
			interactiveUI := ui.NewInteractiveUI(logger)
			logger.Info("Starting interactive selection...")
			selectedContent, err := interactiveUI.SelectContent(candidates)
			if err != nil {
				return fmt.Errorf("interactive selection failed: %w", err)
			}
			logger.Info("Selection completed")

			// 6. 選択内容の保存（オプション）
			if outputDir != "" {
				// タイトルをファイル名として使用
				sanitizedTitle := sanitizeFilename(selectedContent.Title)
				outputPath := filepath.Join(outputDir, sanitizedTitle+".txt")
				
				// 内容を保存
				content := fmt.Sprintf("Title: %s\n\nShow Notes:\n%s\n\nAd Timecodes: %v\n",
					selectedContent.Title, selectedContent.ShowNote, selectedContent.AdTimecodes)
				
				if err := os.WriteFile(outputPath, []byte(content), 0644); err != nil {
					logger.Warnf("Failed to save selection to file: %v", err)
				} else {
					logger.Infof("Selection saved to %s", outputPath)
				}
			}

			// 7. Art19アップロード
			art19Processor := processor.NewArt19Processor(art19Service, logger)
			logger.Info("Starting Art19 upload process...")
			if err := art19Processor.UploadDraft(cmd.Context(), audioPath, selectedContent); err != nil {
				return fmt.Errorf("Art19 upload failed: %w", err)
			}

			logger.Info("Process completed successfully!")
			return nil
		},
	}

	// フラグの設定
	processCmd.Flags().StringVarP(&transcriptPath, "input-transcript", "t", "", "Path to transcript file (required)")
	processCmd.Flags().StringVarP(&audioPath, "input-audio", "a", "", "Path to audio file (required)")
	processCmd.Flags().StringVarP(&outputDir, "output-dir", "o", "", "Output directory for generated files")
	processCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose logging")

	// 必須フラグの設定
	processCmd.MarkFlagRequired("input-transcript")
	processCmd.MarkFlagRequired("input-audio")

	return processCmd
}

// sanitizeFilename はファイル名に使えない文字を置き換える
func sanitizeFilename(filename string) string {
	// ファイル名に使えない文字を置き換え
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
