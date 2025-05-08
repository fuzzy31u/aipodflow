package services

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"

	"github.com/sirupsen/logrus"
)

// Art19Service handles interactions with the Art19 platform
type Art19Service struct {
	username string
	password string
	logger   *logrus.Logger
}

// UploadDraftTitle uploads only the title to Art19 as a draft (placeholder implementation)
func (s *Art19Service) UploadDraftTitle(ctx context.Context, title string) error {
	s.logger.Infof("Uploading draft title to Art19: %s", title)

	// 必要なURL等は設定や引数で受け取る想定
	art19EpisodeNewURL := os.Getenv("ART19_EPISODE_NEW_URL")
	if art19EpisodeNewURL == "" {
		return fmt.Errorf("ART19_EPISODE_NEW_URL is not set")
	}

	// Playwright MCPサーバーにPOST
	payload := map[string]interface{}{
		"script": "scripts/art19_upload_title.js",
		"env": map[string]string{
			"ART19_USERNAME": s.username,
			"ART19_PASSWORD": s.password,
			"ART19_EPISODE_NEW_URL": art19EpisodeNewURL,
			"EPISODE_TITLE":  title,
		},
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal Playwright payload: %w", err)
	}

	resp, err := http.Post("http://localhost:3001/run-script", "application/json", bytes.NewBuffer(data)) // 例: MCPサーバーは3001番
	if err != nil {
		return fmt.Errorf("failed to call Playwright MCP server: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("Playwright MCP server error: %s", string(body))
	}

	s.logger.Info("Draft title upload requested via Playwright MCP server")
	return nil
}

// NewArt19Service creates a new Art19Service instance
func NewArt19Service(username, password string, logger *logrus.Logger) *Art19Service {
	return &Art19Service{
		username: username,
		password: password,
		logger:   logger,
	}
}

// PublishEpisode handles the process of publishing an episode to Art19
func (s *Art19Service) PublishEpisode(ctx context.Context, audioPath string, title string, description string) error {
	s.logger.Infof("Starting Art19 publishing process for: %s", title)

	// TODO: Implement Art19 publishing logic
	// Since Art19 doesn't have a public write API, we'll need to:
	// 1. Use a headless browser (like Playwright or Puppeteer)
	// 2. Log in to Art19
	// 3. Navigate to the episode creation page
	// 4. Upload the audio file
	// 5. Fill in the episode details
	// 6. Set ad markers
	// 7. Publish the episode

	// For now, this is a placeholder implementation
	s.logger.Warn("Art19 publishing not yet implemented")
	return fmt.Errorf("Art19 publishing not yet implemented")
}

// UploadAudio handles the audio file upload to Art19
func (s *Art19Service) UploadAudio(ctx context.Context, audioPath string) (string, error) {
	s.logger.Infof("Uploading audio file: %s", audioPath)

	// Open the audio file
	file, err := os.Open(audioPath)
	if err != nil {
		return "", fmt.Errorf("failed to open audio file: %w", err)
	}
	defer file.Close()

	// TODO: Implement actual Art19 upload logic
	// This would involve:
	// 1. Getting an upload URL from Art19
	// 2. Uploading the file
	// 3. Getting the file ID

	s.logger.Warn("Art19 audio upload not yet implemented")
	return "", fmt.Errorf("Art19 audio upload not yet implemented")
}

// SetAdMarkers sets the ad insertion points for an episode
func (s *Art19Service) SetAdMarkers(ctx context.Context, episodeID string, markers []float64) error {
	s.logger.Infof("Setting ad markers for episode: %s", episodeID)

	// TODO: Implement ad marker setting logic
	// This would involve:
	// 1. Navigating to the episode's ad settings
	// 2. Adding markers at the specified timestamps
	// 3. Saving the changes

	s.logger.Warn("Art19 ad marker setting not yet implemented")
	return fmt.Errorf("Art19 ad marker setting not yet implemented")
}
