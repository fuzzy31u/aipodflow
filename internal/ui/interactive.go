package ui

import (
	"github.com/automate-podcast/internal/model"
	"github.com/sirupsen/logrus"
)

// InteractiveUI provides an interactive user interface
type InteractiveUI struct {
	logger *logrus.Logger
}

// NewInteractiveUI creates a new InteractiveUI instance
func NewInteractiveUI(logger *logrus.Logger) *InteractiveUI {
	return &InteractiveUI{
		logger: logger,
	}
}

// SelectContent allows users to select from content candidates
func (ui *InteractiveUI) SelectContent(candidates *model.ContentCandidates) (*model.SelectedContent, error) {
	selected := &model.SelectedContent{}

	ui.logger.Info("Starting content display process...")

	// Display all title candidates
	ui.logger.Info("=== TITLE CANDIDATES ===")
	for i, title := range candidates.Titles {
		ui.logger.Infof("[%d] %s", i+1, title)
	}

	// Display all show note candidates
	ui.logger.Info("\n=== SHOW NOTE CANDIDATES ===")
	for i, note := range candidates.ShowNotes {
		ui.logger.Infof("[%d]\n%s\n", i+1, note)
	}

	// Automatically select the first candidates without prompting
	if len(candidates.Titles) > 0 {
		selected.Title = candidates.Titles[0]
	} else {
		ui.logger.Warn("No title proposal available")
		selected.Title = ""
	}

	if len(candidates.ShowNotes) > 0 {
		selected.ShowNote = candidates.ShowNotes[0]
	} else {
		ui.logger.Warn("No show note proposal available")
		selected.ShowNote = ""
	}

	ui.logger.Info("Content display completed successfully")
	return selected, nil
}

// Note: These formatting functions have been removed as they are no longer used
// in the current implementation of the interactive UI.

// Ad timecode formatting removed
