package config

import (
	"fmt"
	"os"

	"github.com/joho/godotenv"
	"github.com/sirupsen/logrus"
)

// Config holds all configuration values
type Config struct {
	OpenAIAPIKey        string
	Art19Username       string
	Art19Password       string
	TwitterAPIKey       string
	TwitterAPISecret    string
	TwitterAccessToken  string
	TwitterAccessSecret string
	VercelDeployHook    string
	UploadDir           string
	Port                string
}

// LoadConfig loads configuration from environment variables
func LoadConfig() (*Config, error) {
	// Load .env file if it exists
	if err := godotenv.Load(); err != nil {
		logrus.Warn("No .env file found, using environment variables")
	}

	config := &Config{
		OpenAIAPIKey:        getEnv("OPENAI_API_KEY", ""),
		Art19Username:       getEnv("ART19_USERNAME", ""),
		Art19Password:       getEnv("ART19_PASSWORD", ""),
		TwitterAPIKey:       getEnv("TWITTER_API_KEY", ""),
		TwitterAPISecret:    getEnv("TWITTER_API_SECRET", ""),
		TwitterAccessToken:  getEnv("TWITTER_ACCESS_TOKEN", ""),
		TwitterAccessSecret: getEnv("TWITTER_ACCESS_SECRET", ""),
		VercelDeployHook:    getEnv("VERCEL_DEPLOY_HOOK", ""),
		UploadDir:           getEnv("UPLOAD_DIR", "uploads"),
		Port:                getEnv("PORT", "8080"),
	}

	// Validate required configuration
	if err := validateConfig(config); err != nil {
		return nil, err
	}

	return config, nil
}

// getEnv gets an environment variable with a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// validateConfig checks if all required configuration values are set
func validateConfig(config *Config) error {
	required := map[string]string{
		"OPENAI_API_KEY":       config.OpenAIAPIKey,
		"ART19_USERNAME":       config.Art19Username,
		"ART19_PASSWORD":       config.Art19Password,
		"TWITTER_API_KEY":      config.TwitterAPIKey,
		"TWITTER_API_SECRET":   config.TwitterAPISecret,
		"TWITTER_ACCESS_TOKEN": config.TwitterAccessToken,
		"VERCEL_DEPLOY_HOOK":   config.VercelDeployHook,
	}

	for key, value := range required {
		if value == "" {
			return fmt.Errorf("required environment variable %s is not set", key)
		}
	}

	return nil
}
