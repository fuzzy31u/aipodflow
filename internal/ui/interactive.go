package ui

import (
	"fmt"

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

// formatTitleOptions formats title candidates for display
func formatTitleOptions(titles []string) []string {
	options := make([]string, len(titles))
	for i, title := range titles {
		options[i] = fmt.Sprintf("%d: %s", i+1, title)
	}
	return options
}

// formatShowNoteOptions formats ShowNote candidates for display
func formatShowNoteOptions(showNotes []string) []string {
	options := make([]string, len(showNotes))
	for i, note := range showNotes {
		preview := note
		if len(note) > 100 {
			preview = note[:97] + "..."
		}
		options[i] = fmt.Sprintf("%d: %s", i+1, preview)
	}
	return options
}

// Ad timecode formatting removed
