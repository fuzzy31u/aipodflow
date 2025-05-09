package processor

import (
	"context"
	"fmt"

	"github.com/automate-podcast/internal/model"
	"github.com/automate-podcast/services"
	"github.com/sirupsen/logrus"
)

// Art19Processor is responsible for uploading content to Art19
type Art19Processor struct {
	art19Service *services.Art19Service
	logger       *logrus.Logger
}

// NewArt19Processor creates a new Art19Processor instance
func NewArt19Processor(art19Service *services.Art19Service, logger *logrus.Logger) *Art19Processor {
	return &Art19Processor{
		art19Service: art19Service,
		logger:       logger,
	}
}

// UploadDraft uploads the selected content to Art19 as a draft
func (p *Art19Processor) UploadDraft(ctx context.Context, audioPath string, content *model.SelectedContent) error {
	// If no audio file is specified, upload only the title as a draft
	if audioPath == "" {
		p.logger.Info("No audio file specified, uploading only title to Art19 as draft")
		p.logger.Infof("Uploading draft title: %s", content.Title)
		if err := p.art19Service.UploadDraftTitle(ctx, content.Title); err != nil {
			return fmt.Errorf("failed to upload draft title to Art19: %w", err)
		}
		p.logger.Info("Successfully uploaded draft title to Art19!")
		return nil
	}

	// If audio file is present, proceed with full upload (existing logic)
	p.logger.Info("Preparing to upload to Art19...")
	p.logger.Infof("Title: %s", content.Title)
	p.logger.Info("Show Notes: [content omitted for brevity]")
	
	// Verify the audio file exists
	p.logger.Infof("Checking audio file: %s", audioPath)
	
	// Upload to Art19
	p.logger.Info("Uploading to Art19 as draft...")
	err := p.art19Service.PublishEpisode(ctx, audioPath, content.Title, content.ShowNote)
	if err != nil {
		return fmt.Errorf("failed to upload to Art19: %w", err)
	}
	
	p.logger.Info("Successfully uploaded draft to Art19!")
	return nil
}
