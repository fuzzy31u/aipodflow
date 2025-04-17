package processor

import (
	"context"
	"fmt"

	"github.com/automate-podcast/internal/model"
	"github.com/automate-podcast/services"
	"github.com/sirupsen/logrus"
)

// ContentProcessor はコンテンツ生成処理を担当する
type ContentProcessor struct {
	aiService *services.AIService
	logger    *logrus.Logger
}

// NewContentProcessor は新しいContentProcessorインスタンスを作成する
func NewContentProcessor(aiService *services.AIService, logger *logrus.Logger) *ContentProcessor {
	return &ContentProcessor{
		aiService: aiService,
		logger:    logger,
	}
}

// GenerateCandidates はトランスクリプトからコンテンツ候補を生成する
func (p *ContentProcessor) GenerateCandidates(transcript string) (*model.ContentCandidates, error) {
	ctx := context.Background()

	p.logger.Info("Starting content generation process...")

	// 1. タイトル候補生成
	p.logger.Info("Generating title candidates...")
	titles, err := p.aiService.GenerateTitles(ctx, transcript)
	if err != nil {
		return nil, fmt.Errorf("failed to generate titles: %w", err)
	}
	p.logger.Infof("Generated %d title candidates", len(titles))

	// 2. ShowNote候補生成
	p.logger.Info("Generating show note candidates...")
	showNotes, err := p.aiService.GenerateShowNotes(ctx, transcript)
	if err != nil {
		return nil, fmt.Errorf("failed to generate show notes: %w", err)
	}
	p.logger.Infof("Generated %d show note candidates", len(showNotes))

	// 3. 広告タイムコード候補生成
	p.logger.Info("Generating ad timecode candidates...")
	adTimecodes, err := p.aiService.GenerateAdTimecodes(ctx, transcript)
	if err != nil {
		return nil, fmt.Errorf("failed to generate ad timecodes: %w", err)
	}
	p.logger.Infof("Generated %d ad timecode candidates", len(adTimecodes))

	return &model.ContentCandidates{
		Titles:      titles,
		ShowNotes:   showNotes,
		AdTimecodes: adTimecodes,
	}, nil
}
