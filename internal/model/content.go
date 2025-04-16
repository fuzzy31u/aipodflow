package model

// ContentCandidates はAIによって生成されたコンテンツ候補を保持する構造体
type ContentCandidates struct {
	Titles      []string   // タイトル候補（10パターン）
	ShowNotes   []string   // ShowNote候補（10パターン）
	AdTimecodes [][]string // 広告タイムコード候補（10パターン）
}

// SelectedContent はユーザーによって選択されたコンテンツを保持する構造体
type SelectedContent struct {
	Title       string   // 選択されたタイトル
	ShowNote    string   // 選択されたShowNote
	AdTimecodes []string // 選択された広告タイムコード
}
