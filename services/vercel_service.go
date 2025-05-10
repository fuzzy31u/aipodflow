package services

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"github.com/sirupsen/logrus"
)

// VercelService is a service responsible for Vercel-related operations
type VercelService struct {
	deployHookURL string
	client        *http.Client
	logger        *logrus.Logger
}

// NewVercelService creates a new VercelService instance
func NewVercelService(deployHookURL string, logger *logrus.Logger) *VercelService {
	// Initialize HTTP client with timeout
	client := &http.Client{
		Timeout: time.Second * 30,
	}

	return &VercelService{
		deployHookURL: deployHookURL,
		client:        client,
		logger:        logger,
	}
}

// NewVercelServiceFromEnv creates a new VercelService instance using environment variables
func NewVercelServiceFromEnv(logger *logrus.Logger) *VercelService {
	// Get deploy hook URL from environment variable
	deployHookURL := os.Getenv("VERCEL_DEPLOY_HOOK")

	// Initialize HTTP client with timeout
	client := &http.Client{
		Timeout: time.Second * 30,
	}

	return &VercelService{
		deployHookURL: deployHookURL,
		client:        client,
		logger:        logger,
	}
}

// TriggerRedeploy triggers a redeployment of the website on Vercel
func (s *VercelService) TriggerRedeploy(ctx context.Context) error {
	if s.deployHookURL == "" {
		return fmt.Errorf("Vercel deploy hook URL is not configured")
	}

	s.logger.Info("Triggering Vercel redeployment...")

	// Create a POST request to the deploy hook URL
	// Vercel deploy hooks expect an empty POST request with no body
	req, err := http.NewRequestWithContext(ctx, "POST", s.deployHookURL, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	// Set the Content-Type header to application/json
	req.Header.Set("Content-Type", "application/json")

	// Send the request
	resp, err := s.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	// Log the response status for debugging
	s.logger.Debugf("Vercel API response status: %s", resp.Status)

	// Check the response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		// Read the response body for error details
		body, _ := io.ReadAll(resp.Body)
		s.logger.Debugf("Response body: %s", string(body))
		return fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	s.logger.Info("Vercel redeployment triggered successfully")
	return nil
}
