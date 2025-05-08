package ui

import (
	"fmt"
	"strings"

	"github.com/AlecAivazis/survey/v2"
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

	ui.logger.Info("Starting interactive selection process...")

	// 1. Title proposal
	if len(candidates.Titles) > 0 {
		selected.Title = candidates.Titles[0]
		ui.logger.Infof("Proposed title: %s", selected.Title)
	} else {
		ui.logger.Warn("No title proposal available")
		selected.Title = ""
	}

	// 2. Title editing option
	editTitle := false
	editPrompt := &survey.Confirm{
		Message: "Would you like to edit the selected title?",
	}
	if err := survey.AskOne(editPrompt, &editTitle); err != nil {
		return nil, fmt.Errorf("title edit confirmation failed: %w", err)
	}

	if editTitle {
		editedTitle := ""
		editTitlePrompt := &survey.Input{
			Message: "Edit title:",
			Default: selected.Title,
		}
		if err := survey.AskOne(editTitlePrompt, &editedTitle); err != nil {
			return nil, fmt.Errorf("title editing failed: %w", err)
		}
		selected.Title = editedTitle
		ui.logger.Infof("Edited title: %s", selected.Title)
	}

	// 3. Show note proposal
	if len(candidates.ShowNotes) > 0 {
		selected.ShowNote = candidates.ShowNotes[0]
		ui.logger.Info("Proposed show note")
	} else {
		ui.logger.Warn("No show note proposal available")
		selected.ShowNote = ""
	}

	// 4. ShowNote editing option
	editShowNote := false
	editShowNotePrompt := &survey.Confirm{
		Message: "Would you like to edit the selected show notes?",
	}
	if err := survey.AskOne(editShowNotePrompt, &editShowNote); err != nil {
		return nil, fmt.Errorf("show note edit confirmation failed: %w", err)
	}

	if editShowNote {
		editedShowNote := ""
		editShowNoteTextPrompt := &survey.Editor{
			Message:       "Edit show notes:",
			Default:       selected.ShowNote,
			HideDefault:   false,
			AppendDefault: true,
		}
		if err := survey.AskOne(editShowNoteTextPrompt, &editedShowNote); err != nil {
			return nil, fmt.Errorf("show note editing failed: %w", err)
		}
		selected.ShowNote = editedShowNote
		ui.logger.Info("Edited show notes")
	}

	// 5. Ad timecode selection
	adIndex := 0
	adPrompt := &survey.Select{
		Message: "Select ad placement timecodes:",
		Options: formatAdOptions(candidates.AdTimecodes),
	}
	if err := survey.AskOne(adPrompt, &adIndex); err != nil {
		return nil, fmt.Errorf("ad timecode selection failed: %w", err)
	}
	selected.AdTimecodes = candidates.AdTimecodes[adIndex]
	ui.logger.Infof("Selected ad timecodes: %v", selected.AdTimecodes)

	// 6. Final confirmation
	confirm := false
	confirmPrompt := &survey.Confirm{
		Message: "Do you want to proceed with these selections?",
		Default: true,
	}
	if err := survey.AskOne(confirmPrompt, &confirm); err != nil {
		return nil, fmt.Errorf("final confirmation failed: %w", err)
	}

	if !confirm {
		return nil, fmt.Errorf("user cancelled the operation")
	}

	ui.logger.Info("Selection process completed successfully")
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

// formatAdOptions formats ad timecode candidates for display
func formatAdOptions(adTimecodes [][]string) []string {
	options := make([]string, len(adTimecodes))
	for i, timecodes := range adTimecodes {
		options[i] = fmt.Sprintf("%d: %s", i+1, strings.Join(timecodes, ", "))
	}
	return options
}
