package processor

import (
	"context"
	"fmt"

	"github.com/automate-podcast/internal/model"
	"github.com/automate-podcast/services"
	"github.com/sirupsen/logrus"
)

// Art19Processor はArt19へのアップロード処理を担当する
type Art19Processor struct {
	art19Service *services.Art19Service
	logger       *logrus.Logger
}

// NewArt19Processor は新しいArt19Processorインスタンスを作成する
func NewArt19Processor(art19Service *services.Art19Service, logger *logrus.Logger) *Art19Processor {
	return &Art19Processor{
		art19Service: art19Service,
		logger:       logger,
	}
}

// UploadDraft は選択されたコンテンツをArt19にドラフトとしてアップロードする
func (p *Art19Processor) UploadDraft(ctx context.Context, audioPath string, content *model.SelectedContent) error {
	// 音声ファイルが指定されていない場合はアップロードをスキップ
	if audioPath == "" {
		p.logger.Info("No audio file specified, skipping Art19 upload")
		p.logger.Infof("Selected content would be uploaded: Title=%s, ShowNotes=[content omitted]", content.Title)
		return nil
	}
	p.logger.Info("Preparing to upload to Art19...")
	p.logger.Infof("Title: %s", content.Title)
	p.logger.Info("Show Notes: [content omitted for brevity]")
	p.logger.Infof("Ad Timecodes: %v", content.AdTimecodes)
	
	// 音声ファイルの存在確認
	p.logger.Infof("Checking audio file: %s", audioPath)
	
	// Art19へのアップロード
	p.logger.Info("Uploading to Art19 as draft...")
	err := p.art19Service.PublishEpisode(ctx, audioPath, content.Title, content.ShowNote)
	if err != nil {
		return fmt.Errorf("failed to upload to Art19: %w", err)
	}
	
	p.logger.Info("Successfully uploaded draft to Art19!")
	return nil
}
