package services

import (
	"context"
	"encoding/xml"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/sirupsen/logrus"
)

// RSSFeed represents the structure of an RSS feed
type RSSFeed struct {
	XMLName xml.Name `xml:"rss"`
	Channel struct {
		Title       string `xml:"title"`
		Description string `xml:"description"`
		Items       []struct {
			Title       string `xml:"title"`
			Link        string `xml:"link"`
			Description string `xml:"description"`
			PubDate     string `xml:"pubDate"`
			GUID        string `xml:"guid"`
		} `xml:"item"`
	} `xml:"channel"`
}

// SNSService handles generating text for social media posts
type SNSService struct {
	client *http.Client
	logger *logrus.Logger
}

// NewSNSService creates a new SNSService instance
func NewSNSService(logger *logrus.Logger) *SNSService {
	return &SNSService{
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
		logger: logger,
	}
}

// GetLatestEpisodeTitle fetches the latest episode title from the RSS feed
func (s *SNSService) GetLatestEpisodeTitle(ctx context.Context, rssURL string) (string, error) {
	s.logger.Debugf("Fetching latest episode title from RSS feed: %s", rssURL)
	
	feed, err := s.fetchRSSFeed(rssURL)
	if err != nil {
		return "", err
	}
	
	if len(feed.Channel.Items) == 0 {
		return "", fmt.Errorf("no episodes found in the RSS feed")
	}
	
	latestEpisode := feed.Channel.Items[0]
	s.logger.Debugf("Latest episode title: %s", latestEpisode.Title)
	
	return latestEpisode.Title, nil
}

// GetLatestSpotifyURL fetches the latest episode URL from Spotify
func (s *SNSService) GetLatestSpotifyURL(ctx context.Context, showURL string) (string, error) {
	s.logger.Debugf("Fetching latest episode URL from Spotify: %s", showURL)
	
	// Make a request to the Spotify show page
	req, err := http.NewRequestWithContext(ctx, "GET", showURL, nil)
	if err != nil {
		return "", fmt.Errorf("failed to create request for Spotify: %w", err)
	}
	
	resp, err := s.client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to fetch Spotify show page: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read Spotify response: %w", err)
	}
	
	// Find the latest episode URL using regex
	// This is a simplified approach and might need adjustment based on actual HTML structure
	re := regexp.MustCompile(`https://open\.spotify\.com/episode/[a-zA-Z0-9]+`)
	matches := re.FindStringSubmatch(string(body))
	
	if len(matches) == 0 {
		// If we can't find the episode link, return the show URL as fallback
		s.logger.Warn("Could not find latest episode URL from Spotify, using show URL as fallback")
		return showURL, nil
	}
	
	episodeURL := matches[0]
	s.logger.Debugf("Latest Spotify episode URL: %s", episodeURL)
	
	return episodeURL, nil
}

// GetLatestApplePodcastURL fetches the latest episode URL from Apple Podcasts
func (s *SNSService) GetLatestApplePodcastURL(ctx context.Context, showURL string) (string, error) {
	s.logger.Debugf("Fetching latest episode URL from Apple Podcasts: %s", showURL)
	
	// Make a request to the Apple Podcasts show page
	req, err := http.NewRequestWithContext(ctx, "GET", showURL, nil)
	if err != nil {
		return "", fmt.Errorf("failed to create request for Apple Podcasts: %w", err)
	}
	
	resp, err := s.client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to fetch Apple Podcasts show page: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read Apple Podcasts response: %w", err)
	}
	
	// Find the latest episode URL using regex
	// This is a simplified approach and might need adjustment based on actual HTML structure
	re := regexp.MustCompile(`https://podcasts\.apple\.com/us/podcast/[^"]+/id1589345170\?i=[0-9]+`)
	matches := re.FindStringSubmatch(string(body))
	
	if len(matches) == 0 {
		// If we can't find the episode link, return the show URL as fallback
		s.logger.Warn("Could not find latest episode URL from Apple Podcasts, using show URL as fallback")
		return showURL, nil
	}
	
	episodeURL := matches[0]
	s.logger.Debugf("Latest Apple Podcasts episode URL: %s", episodeURL)
	
	return episodeURL, nil
}

// CreateSNSPostText generates text for posting to social media platforms
func (s *SNSService) CreateSNSPostText(title, spotifyURL, applePodcastURL string) string {
	// Define the template parts
	header := "IT企業で働くママによる子育て×Tech Podcast momit.fm を配信しました🎙 w/@m2vela"
	divider := "—"
	spotifyPrefix := "👇Spotify"
	applePrefix := "👇Apple"
	hashtags := "#momitfm #子育テック"
	
	// Build the template using strings.Join for better readability
	parts := []string{
		header,
		divider,
		title,
		"",
		spotifyPrefix,
		spotifyURL,
		"",
		applePrefix,
		applePodcastURL,
		"",
		hashtags,
	}
	
	return strings.Join(parts, "\n")
}

// fetchRSSFeed fetches and parses an RSS feed from the given URL
func (s *SNSService) fetchRSSFeed(url string) (*RSSFeed, error) {
	resp, err := s.client.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch RSS feed: %w", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to fetch RSS feed, status code: %d", resp.StatusCode)
	}
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read RSS feed: %w", err)
	}
	
	var feed RSSFeed
	if err := xml.Unmarshal(body, &feed); err != nil {
		return nil, fmt.Errorf("failed to parse RSS feed: %w", err)
	}
	
	return &feed, nil
}
