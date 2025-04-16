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

// TranscriptionService handles audio transcription using OpenAI's Whisper API
type TranscriptionService struct {
	apiKey string
	logger *logrus.Logger
}

// NewTranscriptionService creates a new TranscriptionService instance
func NewTranscriptionService(apiKey string, logger *logrus.Logger) *TranscriptionService {
	return &TranscriptionService{
		apiKey: apiKey,
		logger: logger,
	}
}

// Transcribe processes an audio file and returns the transcription
func (s *TranscriptionService) Transcribe(ctx context.Context, audioPath string) (string, error) {
	s.logger.Infof("Starting transcription for: %s", audioPath)

	// Open the audio file
	file, err := os.Open(audioPath)
	if err != nil {
		return "", fmt.Errorf("failed to open audio file: %w", err)
	}
	defer file.Close()

	// Create a buffer to store the file
	var buf bytes.Buffer
	if _, err := io.Copy(&buf, file); err != nil {
		return "", fmt.Errorf("failed to read audio file: %w", err)
	}

	// Create the request
	req, err := http.NewRequestWithContext(
		ctx,
		"POST",
		"https://api.openai.com/v1/audio/transcriptions",
		&buf,
	)
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	req.Header.Set("Authorization", "Bearer "+s.apiKey)
	req.Header.Set("Content-Type", "multipart/form-data")

	// Send the request
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	// Read the response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response: %w", err)
	}

	// Parse the response
	var result struct {
		Text string `json:"text"`
	}
	if err := json.Unmarshal(body, &result); err != nil {
		return "", fmt.Errorf("failed to parse response: %w", err)
	}

	s.logger.Infof("Transcription completed successfully")
	return result.Text, nil
}
