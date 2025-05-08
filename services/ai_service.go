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

// GenerateTitles generates title candidates from a transcript
func (s *AIService) GenerateTitles(ctx context.Context, transcript string) ([]string, error) {
	s.logger.Info("Generating title candidates...")

	// 全文を使用するように変更
	fullTranscript := transcript

	// プロンプトの作成
	prompt := fmt.Sprintf(
		"You are GenerativeAI acting as a podcast copy‑writer.\nGenerate:\n1. Title – follow the pattern:\n  NN. ＜Japanese topic 1＞ / ＜Japanese topic 2＞ [/ ＜Japanese topic 3＞]\n  • NN = episode number (integer).\n  • Provide 2 or 3 topics.\n  • Topics should be mainly in Japanese, but keep any necessary English words as‑is (AI, GPT, etc.).\n\nHere is the transcript of the podcast:\n%s\n\nPlease generate just ONE optimal title following the pattern. Do not include numbers or symbols at the beginning of the line.",
		fullTranscript,
	)

	// OpenAI APIリクエストの作成
	req := openai.ChatCompletionRequest{
		Model: openai.GPT4o,
		Messages: []openai.ChatCompletionMessage{
			{
				Role:    openai.ChatMessageRoleSystem,
				Content: "You are GenerativeAI acting as a podcast copy‑writer. Generate titles following the specified pattern based on the transcript content.",
			},
			{
				Role:    openai.ChatMessageRoleUser,
				Content: prompt,
			},
		},
		Temperature: 0.7,
		MaxTokens:   2000,
	}

	// API呼び出し
	resp, err := s.client.CreateChatCompletion(ctx, req)
	if err != nil {
		s.logger.Errorf("OpenAI API error: %v", err)
		return nil, fmt.Errorf("failed to generate titles: %w", err)
	}

	// Use the complete LLM response and parse it into individual titles
	responseText := resp.Choices[0].Message.Content
	// Split by newline to get titles
	titles := strings.Split(strings.TrimSpace(responseText), "\n")

	// Process titles but preserve their original content
	result := make([]string, 0, 10)
	for _, title := range titles {
		// Skip empty lines
		if strings.TrimSpace(title) == "" {
			continue
		}
		// Add the complete title as provided by the LLM
		result = append(result, strings.TrimSpace(title))
		if len(result) >= 10 {
			break
		}
	}

	// 結果が空の場合は再度生成を試みる
	if len(result) < 1 {
		s.logger.Info("Failed to generate a title, trying again")
		// Create a new prompt requesting more titles
		systemPrompt := fmt.Sprintf(
			"You are GenerativeAI acting as a podcast copy‑writer.\nGenerate:\n1. Title – follow the pattern:\n  NN. ＜Japanese topic 1＞ / ＜Japanese topic 2＞ [/ ＜Japanese topic 3＞]\n  • NN = episode number (integer).\n  • Provide 2 or 3 topics.\n  • Topics should be mainly in Japanese, but keep any necessary English words as‑is (AI, GPT, etc.).\n\nHere is the transcript of the podcast:\n%s\n\nPlease generate just ONE optimal title following the pattern. Do not include numbers or symbols at the beginning of the line.",
			fullTranscript,
		)

		// Create a new request for additional titles
		additionalReq := openai.ChatCompletionRequest{
			Model: openai.GPT4o,
			Messages: []openai.ChatCompletionMessage{
				{
					Role:    openai.ChatMessageRoleSystem,
					Content: "You are GenerativeAI acting as a podcast copy‑writer. Generate titles following the specified pattern based on the transcript content.",
				},
				{
					Role:    openai.ChatMessageRoleUser,
					Content: systemPrompt,
				},
			},
			Temperature: 0.8, // Slightly higher temperature for more variation
			MaxTokens:   2000,
		}

		// Make the API call for additional titles
		additionalResp, err := s.client.CreateChatCompletion(ctx, additionalReq)
		if err != nil {
			s.logger.Warnf("Failed to generate additional title: %v", err)
		} else {
			// Process additional titles
			additionalText := additionalResp.Choices[0].Message.Content
			additionalTitles := strings.Split(strings.TrimSpace(additionalText), "\n")

			for _, title := range additionalTitles {
				if strings.TrimSpace(title) == "" {
					continue
				}
				result = append(result, strings.TrimSpace(title))
				if len(result) >= 1 {
					break
				}
			}
		}
	}

	s.logger.Infof("Generated %d title candidates", len(result))
	return result, nil
}

// GenerateShowNotes generates show note candidates from a transcript
func (s *AIService) GenerateShowNotes(ctx context.Context, transcript string) ([]string, error) {
	// Generate show note candidates using OpenAI API
	s.logger.Info("Generating show note candidates...")

	// 全文を使用するように変更
	fullTranscript := transcript

	// プロンプトの作成
	prompt := fmt.Sprintf(
		"You are GenerativeAI acting as a podcast copy‑writer for a Japanese podcast about parenting and technology.\n\nGenerate ONE complete show note with EXACTLY this format:\n\n1. Opening summary: 2-3 lines in friendly Japanese with many relevant emojis. EVERY sentence MUST end with an exclamation mark (!).\n\n2. Bullet points: 8-12 points, each formatted as:\n   [emoji] [Bold headline in Japanese]: [Short description, maximum 1 line]\n\n3. CTA block: Wrapped in dotted lines (\"\u2026\u2026\u2026\"), asking for feedback via hashtag #momitfm and encouraging follows/ratings\n\n4. Credits section: Must be titled exactly \"✨🎧 Credits\" and list hosts (@_yukamiya & @m2vela) and intro creator (@kirillovlov2983)\n\nThe show note MUST maintain an energetic, conversational tone balancing parenting and tech themes.\n\nHere is the transcript of the podcast:\n%s\n\nGenerate EXACTLY ONE complete show note following ALL formatting requirements above. Do not number your response or include any text like 'Show Note 1:' at the beginning.",
		fullTranscript,
	)

	// OpenAI APIリクエストの作成
	req := openai.ChatCompletionRequest{
		Model: openai.GPT4o,
		Messages: []openai.ChatCompletionMessage{
			{
				Role:    openai.ChatMessageRoleSystem,
				Content: "You are GenerativeAI acting as a podcast copy‑writer for a Japanese podcast about parenting and technology. Follow the formatting instructions EXACTLY. Include emojis, proper bullet points, and all required sections.",
			},
			{
				Role:    openai.ChatMessageRoleUser,
				Content: prompt,
			},
		},
		Temperature: 0.7,
	}

	// API呼び出し
	resp, err := s.client.CreateChatCompletion(ctx, req)
	if err != nil {
		s.logger.Errorf("OpenAI API error: %v", err)
		return nil, fmt.Errorf("failed to generate show notes: %w", err)
	}

	// 結果のパース
	responseText := resp.Choices[0].Message.Content

	// Use the complete LLM-generated show note without modifications
	result := []string{responseText}

	// Log the generated show note
	s.logger.Info("Generated show note proposal")

	s.logger.Infof("Generated %d show note candidates", len(result))
	return result, nil
}

// GenerateAdTimecodes generates ad timecode candidates from a transcript
func (s *AIService) GenerateAdTimecodes(ctx context.Context, transcript string) ([][]string, error) {
	// Generate ad timecode candidates using OpenAI API
	s.logger.Info("Generating ad timecode candidates...")

	// TODO: In the future, this will use the OpenAI API to generate timecodes
	// For now, using dummy data to avoid confusion
	adTimecodes := [][]string{
		{"00:05:30", "00:15:45", "00:25:20"},
		{"00:07:15", "00:18:30", "00:28:10"},
		{"00:04:50", "00:14:25", "00:24:00"},
		{"00:06:40", "00:16:55", "00:26:30"},
		{"00:08:20", "00:19:10", "00:29:45"},
		{"00:05:10", "00:15:25", "00:25:50"},
		{"00:07:35", "00:17:40", "00:27:15"},
		{"00:06:05", "00:16:20", "00:26:00"},
		{"00:08:50", "00:19:30", "00:30:15"},
		{"00:04:30", "00:14:00", "00:23:45"},
	}

	return adTimecodes, nil
}
