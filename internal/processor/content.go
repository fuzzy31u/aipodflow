package processor

import (
	"context"
	"fmt"
	"time"

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
func (p *ContentProcessor) GenerateCandidates(transcript string, generateShowNotes bool) (*model.ContentCandidates, error) {
	ctx := context.Background()
	result := &model.ContentCandidates{}

	p.logger.Info("Starting content generation process...")

	// 1. Generate title candidates
	p.logger.Info("Generating title candidates...")
	titles, err := p.aiService.GenerateTitles(ctx, transcript)
	if err != nil {
		return nil, fmt.Errorf("failed to generate titles: %w", err)
	}
	p.logger.Infof("Generated %d title candidates", len(titles))
	result.Titles = titles

	// If we only need titles, return early
	if !generateShowNotes {
		return result, nil
	}

	// Add a delay to avoid hitting rate limits
	p.logger.Info("Waiting 5 seconds before generating show notes to avoid rate limits...")
	time.Sleep(5 * time.Second)

	// 2. Generate show note candidates
	p.logger.Info("Generating show note candidates...")
	showNotes, err := p.aiService.GenerateShowNotes(ctx, transcript)
	if err != nil {
		p.logger.Warnf("Failed to generate show notes: %v", err)
		// Continue with empty show notes instead of failing
		result.ShowNotes = []string{}
	} else {
		p.logger.Infof("Generated %d show note candidates", len(showNotes))
		result.ShowNotes = showNotes
	}

	return result, nil
}
