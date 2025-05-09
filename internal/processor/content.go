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
func (p *ContentProcessor) GenerateCandidates(transcript string, generateShowNotes bool) (*model.ContentCandidates, error) {
	ctx := context.Background()
	result := &model.ContentCandidates{}

	p.logger.Info("Starting content generation process...")

	// Generate all content in a single API call
	p.logger.Info("Generating all content in a single API call...")
	titles, showNotes, err := p.aiService.GenerateAllContent(ctx, transcript)
	if err != nil {
		return nil, fmt.Errorf("failed to generate content: %w", err)
	}

	// Store the titles
	p.logger.Infof("Generated %d title candidates", len(titles))
	result.Titles = titles

	// If we only need titles, return early
	if !generateShowNotes {
		return result, nil
	}

	// Store the show notes
	p.logger.Infof("Generated %d show note candidates", len(showNotes))
	result.ShowNotes = showNotes

	return result, nil
}
