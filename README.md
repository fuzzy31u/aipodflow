# MCP (Model Context Protocol) Server

MCP is an automated podcast production and publishing system that streamlines the workflow from audio processing to social media distribution.

## Features

- Audio processing and enhancement
- AI-powered transcription and show notes generation
- Automated Art19 episode publishing
- Vercel deployment automation
- Social media integration (X/Twitter)

## Architecture

The MCP server is built using Go and implements a REST API for controlling the podcast production pipeline. It integrates with various services:

- OpenAI Whisper API for transcription
- Art19 for podcast hosting
- Vercel for website deployment
- X (Twitter) API for social media distribution

## Setup

1. Install dependencies:

```bash
go mod download
```

2. Create a `.env` file with required credentials:

```env
OPENAI_API_KEY=your_openai_key
ART19_USERNAME=your_art19_username
ART19_PASSWORD=your_art19_password
TWITTER_API_KEY=your_twitter_key
TWITTER_API_SECRET=your_twitter_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
VERCEL_DEPLOY_HOOK=your_vercel_hook_url
```

3. Run the server:

```bash
go run main.go
```

## API Endpoints

- `POST /api/v1/process` - Start the podcast processing pipeline
- `GET /api/v1/status/:id` - Check pipeline status
- `GET /health` - Health check endpoint

## Development

The project uses:

- Go 1.21+
- Gin for HTTP routing
- Logrus for logging
- Godotenv for environment management

## License

MIT
