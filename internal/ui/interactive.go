package ui

import (
	"fmt"
	"strings"

	"github.com/AlecAivazis/survey/v2"
	"github.com/automate-podcast/internal/model"
	"github.com/sirupsen/logrus"
)

// InteractiveUI はインタラクティブなユーザーインターフェースを提供する
type InteractiveUI struct {
	logger *logrus.Logger
}

// NewInteractiveUI は新しいInteractiveUIインスタンスを作成する
func NewInteractiveUI(logger *logrus.Logger) *InteractiveUI {
	return &InteractiveUI{
		logger: logger,
	}
}

// SelectContent はユーザーにコンテンツ候補から選択させる
func (ui *InteractiveUI) SelectContent(candidates *model.ContentCandidates) (*model.SelectedContent, error) {
	selected := &model.SelectedContent{}

	ui.logger.Info("Starting interactive selection process...")

	// 1. タイトル選択
	titleIndex := 0
	titlePrompt := &survey.Select{
		Message: "Select a title:",
		Options: formatTitleOptions(candidates.Titles),
	}
	if err := survey.AskOne(titlePrompt, &titleIndex); err != nil {
		return nil, fmt.Errorf("title selection failed: %w", err)
	}
	selected.Title = candidates.Titles[titleIndex]
	ui.logger.Infof("Selected title: %s", selected.Title)

	// 2. タイトル編集オプション
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

	// 3. ShowNote選択
	showNoteIndex := 0
	showNotePrompt := &survey.Select{
		Message: "Select show notes:",
		Options: formatShowNoteOptions(candidates.ShowNotes),
	}
	if err := survey.AskOne(showNotePrompt, &showNoteIndex); err != nil {
		return nil, fmt.Errorf("show note selection failed: %w", err)
	}
	selected.ShowNote = candidates.ShowNotes[showNoteIndex]
	ui.logger.Info("Selected show notes")

	// 4. ShowNote編集オプション
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

	// 5. 広告タイムコード選択
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

	// 6. 最終確認
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

// formatTitleOptions はタイトル候補を表示用にフォーマットする
func formatTitleOptions(titles []string) []string {
	options := make([]string, len(titles))
	for i, title := range titles {
		options[i] = fmt.Sprintf("%d: %s", i+1, title)
	}
	return options
}

// formatShowNoteOptions はShowNote候補を表示用にフォーマットする
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

// formatAdOptions は広告タイムコード候補を表示用にフォーマットする
func formatAdOptions(adTimecodes [][]string) []string {
	options := make([]string, len(adTimecodes))
	for i, timecodes := range adTimecodes {
		options[i] = fmt.Sprintf("%d: %s", i+1, strings.Join(timecodes, ", "))
	}
	return options
}
