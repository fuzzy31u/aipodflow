package processor

import (
	"os"
	"path/filepath"
)

// LoadTranscript はトランスクリプトファイルを読み込む
func LoadTranscript(path string) (string, error) {
	// ファイルパスが絶対パスでない場合は絶対パスに変換
	if !filepath.IsAbs(path) {
		absPath, err := filepath.Abs(path)
		if err != nil {
			return "", err
		}
		path = absPath
	}

	// ファイルを読み込む
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	
	return string(data), nil
}
