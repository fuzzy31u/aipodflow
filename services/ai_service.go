package services

import (
	"context"
	"fmt"
	"strings"

	"github.com/sashabaranov/go-openai"
	"github.com/sirupsen/logrus"
)

// AIService is a service responsible for AI-related processing
type AIService struct {
	openAIAPIKey string
	client       *openai.Client
	logger       *logrus.Logger
}

// NewAIService creates a new AIService instance
func NewAIService(openAIAPIKey string, logger *logrus.Logger) *AIService {
	// Initialize OpenAI client
	client := openai.NewClient(openAIAPIKey)

	return &AIService{
		openAIAPIKey: openAIAPIKey,
		client:       client,
		logger:       logger,
	}
}

// GenerateAllContent generates both title and show note in a single API call
func (s *AIService) GenerateAllContent(ctx context.Context, transcript string) ([]string, []string, error) {
	s.logger.Info("Generating all content in a single API call...")

	// Use the full transcript
	fullTranscript := transcript

	// Create a combined prompt that requests both title and show note
	prompt := fmt.Sprintf(
		"You are GenerativeAI acting as a podcast copy‑writer for a Japanese podcast about parenting and technology.\n\nPlease generate the following content for this podcast episode:\n\n1. TITLE: Follow this pattern exactly:\n   NN. ＜Japanese topic 1＞ / ＜Japanese topic 2＞ [/ ＜Japanese topic 3＞]\n   * NN = episode number (integer)\n   * Provide 2 or 3 topics\n   * Topics should be mainly in Japanese, but keep any necessary English words as‑is (AI, GPT, etc.)\n\n2. SHOW NOTE: Create exactly this format:\n   * Opening summary: 2-3 lines in friendly Japanese with relevant emojis. Each sentence MUST end with an exclamation mark (!)\n   * Bullet points: 8-12 points, each formatted as: [emoji] [Bold headline in Japanese]: [Short description, maximum 1 line]\n   * CTA block: Wrapped in dotted lines (\"………\"), asking for feedback via hashtag #momitfm\n   * Credits section: Must be titled exactly \"✨🎧 Credits\" and list hosts (@_yukamiya & @m2vela) and intro creator (@kirillovlov2983)\n\nHere is the transcript of the podcast:\n%s\n\nFormat your response with clear section headers [TITLE] and [SHOW NOTE] to separate the content.",
		fullTranscript,
	)

	// Create the OpenAI API request
	req := openai.ChatCompletionRequest{
		Model: openai.GPT4o,
		Messages: []openai.ChatCompletionMessage{
			{
				Role:    openai.ChatMessageRoleSystem,
				Content: "You are GenerativeAI acting as a podcast copy‑writer for a Japanese podcast about parenting and technology. Follow the formatting instructions EXACTLY.",
			},
			{
				Role:    openai.ChatMessageRoleUser,
				Content: prompt,
			},
		},
		Temperature: 0.7,
		MaxTokens:   3000,
	}

	// Make the API call
	resp, err := s.client.CreateChatCompletion(ctx, req)
	if err != nil {
		s.logger.Errorf("OpenAI API error: %v", err)
		return nil, nil, fmt.Errorf("failed to generate content: %w", err)
	}

	// Parse the response
	responseText := resp.Choices[0].Message.Content

	// Split the response into title and show note sections
	titleSection := ""
	showNoteSection := ""

	// Extract title section
	titleStart := strings.Index(responseText, "[TITLE]")
	showNoteStart := strings.Index(responseText, "[SHOW NOTE]")

	if titleStart >= 0 && showNoteStart > titleStart {
		titleSection = strings.TrimSpace(responseText[titleStart+len("[TITLE]"):showNoteStart])
	}

	// Extract show note section
	if showNoteStart >= 0 {
		showNoteSection = strings.TrimSpace(responseText[showNoteStart+len("[SHOW NOTE]"):])
	}

	// If we couldn't find the sections, try to parse the whole response
	if titleSection == "" && showNoteStart < 0 {
		// Try to extract the first line as title
		lines := strings.Split(responseText, "\n")
		if len(lines) > 0 {
			titleSection = lines[0]
			showNoteSection = strings.Join(lines[1:], "\n")
		}
	}

	// Return the results
	titles := []string{titleSection}
	showNotes := []string{showNoteSection}

	s.logger.Info("Generated content successfully")
	return titles, showNotes, nil
}

// GenerateTitles generates title candidates from a transcript
// This is kept for backward compatibility, but now uses GenerateAllContent internally
func (s *AIService) GenerateTitles(ctx context.Context, transcript string) ([]string, error) {
	s.logger.Info("Generating title candidates using combined API call...")

	// Use the combined function but only return titles
	titles, _, err := s.GenerateAllContent(ctx, transcript)
	if err != nil {
		return nil, fmt.Errorf("failed to generate titles: %w", err)
	}

	s.logger.Infof("Generated %d title candidates", len(titles))
	return titles, nil
}

// GenerateShowNotes generates show note candidates from a transcript
// This is kept for backward compatibility, but now uses GenerateAllContent internally
func (s *AIService) GenerateShowNotes(ctx context.Context, transcript string) ([]string, error) {
	s.logger.Info("Generating show note candidates using combined API call...")

	// Use the combined function but only return show notes
	_, showNotes, err := s.GenerateAllContent(ctx, transcript)
	if err != nil {
		return nil, fmt.Errorf("failed to generate show notes: %w", err)
	}

	s.logger.Infof("Generated %d show note candidates", len(showNotes))
	return showNotes, nil
}

// GenerateAdTimecodes generates ad timecode candidates from a transcript
// This function is no longer used but kept for backward compatibility
func (s *AIService) GenerateAdTimecodes(ctx context.Context, transcript string) ([][]string, error) {
	s.logger.Info("Ad timecode generation is deprecated")
	return [][]string{}, nil
}
