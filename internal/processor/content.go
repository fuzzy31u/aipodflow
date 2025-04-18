package processor

import (
	"context"
	"fmt"

	"github.com/automate-podcast/internal/model"
	"github.com/automate-podcast/services"
	"github.com/sirupsen/logrus"
)

// ContentProcessor is responsible for content generation processing
type ContentProcessor struct {
	aiService *services.AIService
	logger    *logrus.Logger
}

// NewContentProcessor creates a new ContentProcessor instance
func NewContentProcessor(aiService *services.AIService, logger *logrus.Logger) *ContentProcessor {
	return &ContentProcessor{
		aiService: aiService,
		logger:    logger,
	}
}

// GenerateCandidates generates content candidates from a transcript
func (p *ContentProcessor) GenerateCandidates(transcript string) (*model.ContentCandidates, error) {
	ctx := context.Background()

	p.logger.Info("Starting content generation process...")

	// 1. Generate title candidates
	p.logger.Info("Generating title candidates...")
	titles, err := p.aiService.GenerateTitles(ctx, transcript)
	if err != nil {
		return nil, fmt.Errorf("failed to generate titles: %w", err)
	}
	p.logger.Infof("Generated %d title candidates", len(titles))

	// 2. Generate show note candidates
	p.logger.Info("Generating show note candidates...")
	showNotes, err := p.aiService.GenerateShowNotes(ctx, transcript)
	if err != nil {
		return nil, fmt.Errorf("failed to generate show notes: %w", err)
	}
	p.logger.Infof("Generated %d show note candidates", len(showNotes))

	// 3. Generate ad timecode candidates
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
