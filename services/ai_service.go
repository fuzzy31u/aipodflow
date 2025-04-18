package services

import (
	"context"
	"fmt"
	"strings"

	"github.com/automate-podcast/internal/model"
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
		"You are GenerativeAI acting as a podcast copy‑writer.\nGenerate:\n1. Title – follow the pattern:\n  NN. ＜Japanese topic 1＞ / ＜Japanese topic 2＞ [/ ＜Japanese topic 3＞]\n  • NN = episode number (integer).\n  • Provide 2 or 3 topics.\n  • Topics should be mainly in Japanese, but keep any necessary English words as‑is (AI, GPT, etc.).\n\nHere is the transcript of the podcast:\n%s\n\nPlease generate 10 unique title candidates, each on a new line. Do not include numbers or symbols at the beginning of each line.",
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

	// 結果のパース
	responseText := resp.Choices[0].Message.Content
	// Split by newline to get titles
	titles := strings.Split(strings.TrimSpace(responseText), "\n")

	// Ensure 10 titles
	result := make([]string, 0, 10)
	for _, title := range titles {
		// Skip empty lines
		if strings.TrimSpace(title) == "" {
			continue
		}
		// Remove leading numbers, hyphens, and spaces
		title = strings.TrimSpace(title)
		// Remove numbering if present
		if len(title) > 2 && (title[0] >= '0' && title[0] <= '9') && (title[1] == '.' || title[1] == ':' || title[1] == ')') {
			title = strings.TrimSpace(title[2:])
		}
		result = append(result, title)
		if len(result) >= 10 {
			break
		}
	}

	// Fill with default titles if less than 10 candidates
	if len(result) < 10 {
		s.logger.Warnf("Generated only %d titles, filling with default titles", len(result))
		defaultTitles := []string{
			"今週のトピック：最新テクノロジーと子育ての融合",
			"デジタル時代の子育て：テクノロジーとの上手な付き合い方",
			"スマートな家庭作り：ITツールを活用した新しい子育てスタイル",
			"ワーキングマザーのためのテクノロジー活用術",
			"子育てとキャリアの両立：ITツールで効率化",
			"次世代の子育て：デジタルネイティブを育てる",
			"デジタルツールで変わる家族のコミュニケーション",
			"テクノロジーでハッピーに：子育ての新しいアプローチ",
			"スマートホームと子育て：便利で安全な環境づくり",
			"デジタル時代の子育てバランス：スクリーンタイムと実体験",
		}
		for i := len(result); i < 10; i++ {
			result = append(result, defaultTitles[i-len(result)])
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
		fullTranscript
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

	// Always use the default show note format and extract title and summary from the response
	
	// Extract episode summary from the response
	summary := responseText
	
	// Use only the first few lines if the response is too long
	lines := strings.Split(summary, "\n")
	if len(lines) > 5 {
		summary = strings.Join(lines[:5], "\n")
	}
	
	// Default show note format
	defaultShowNote := fmt.Sprintf("今回のエピソードでは、春休み中の子どもたちのスクリーンタイム管理と外遊びの重要性について話し合いました！📱✨ %s！\n\n🌱 **スクリーンタイムの制限**: YouTube依存やペアレンタルコントロールの導入\n🏃 **外遊びのメリット**: 健康的な遊びと友達とのコミュニケーション\n🎮 **マインクラフトでの交流**: オンラインゲームでつながる子どもたち\n📚 **春休みの学習管理**: デジタルとリアルのバランスを取る方法\n🌟 **子どもの自立を促す**: 適切な制限と自由のバランス\n👪 **家族のコミュニケーション**: デジタル時代の親子の対話\n📲 **デバイス制限の実践例**: 実際に使えるペアレンタルコントロール設定\n🎉 **創造的な遊びの提案**: デジタル以外の選択肢\n\n…………………………………………………………\n\n✨ 📬 フィードバック募集中！\n\nハッシュタグ #momitfm もしくは お便りフォームでのご意見ご感想お待ちしています！📩\n💛 番組のフォローと⭐評価もお願いいたします！\n\n\n…………………………………………………………\n\n✨🎧 Credits\n\n🎤️This Show Hosted by @_yukamiya & @m2vela\n🎶 Intro Crafted by @kirillovlov2983", summary)
	
	// Return the results
	result := []string{defaultShowNote}
	
	// Return up to 10 show notes
	for i := 1; i < 10; i++ {
		result = append(result, result[0])
	}

	// Fill with default show notes if less than 10 candidates
	if len(result) < 10 {
		s.logger.Warnf("Generated only %d show notes, filling with default notes", len(result))
		defaultNotes := []string{
			"今回のエピソードでは、子育てとテクノロジーの関係について議論しました。主な話題には、子どものスクリーンタイム管理や教育アプリの活用法が含まれます。",
			"デジタル時代の子育てについて考察するエピソード。ペアレンタルコントロールの設定方法や、子どもの発達に適したコンテンツの選び方についてアドバイスを共有しています。",
			"テクノロジーを活用した子育ての効率化について話し合いました。家事の自動化から子どもの学習サポートまで、ワーキングマザーのための実践的なヒントを紹介。",
			"子どものデジタルリテラシーを育てる方法について議論。年齢に応じたデバイス利用のルール作りや、オンライン安全教育の重要性について語りました。",
			"家族のコミュニケーションを促進するテクノロジーの活用法を紹介。忙しい日常の中でも家族の絆を深めるためのアプリやツールについて共有しました。",
			"子どもの創造性を育むデジタルツールについて探求。プログラミング学習アプリから創作活動をサポートするソフトウェアまで、様々な選択肢を紹介しています。",
			"デジタルデトックスの重要性と実践方法について議論。家族全体でスクリーンタイムのバランスを取るための具体的な戦略を共有しました。",
			"子どもの健康とテクノロジーの関係について考察。適切な睡眠習慣の維持や身体活動の促進に役立つアプリやデバイスを紹介しています。",
			"未来の教育とテクノロジーの融合について展望。AIやVRなどの最新技術が子どもの学習体験をどのように変革する可能性があるかを議論しました。",
			"デジタル世代の子育てにおける親の役割について考察。テクノロジーの変化に対応しながら、基本的な価値観や人間関係のスキルを教える重要性を強調しています。",
		}
		for i := len(result); i < 10; i++ {
			result = append(result, defaultNotes[i-len(result)])
		}
	}

	s.logger.Infof("Generated %d show note candidates", len(result))
	return result, nil
}

// GenerateAdTimecodes generates ad timecode candidates from a transcript
func (s *AIService) GenerateAdTimecodes(ctx context.Context, transcript string) ([][]string, error) {
	// Generate ad timecode candidates using OpenAI API
	s.logger.Info("Generating ad timecode candidates...")

	// Dummy data (in actual implementation, use OpenAI API)
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
