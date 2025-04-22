# AIPodFlow

AIPodFlow is an open-source CLI tool that leverages AI to streamline podcast production workflow, from transcript processing to content generation and publishing. It automates the generation of titles, show notes, and ad placement suggestions based on podcast transcripts.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Features

- **Transcript Processing**: Process podcast transcripts to extract key information
- **AI-powered Content Generation**: 
  - Generate engaging title candidates
  - Create comprehensive show notes based on transcript content
  - Suggest optimal ad placement timecodes
- **Interactive & Non-interactive Modes**: Choose content interactively or automatically
- **Automated Publishing**: Seamless integration with various podcast hosting platforms
- **PlayWright MCP Integration**: Automate browser-based workflows for podcast management and uploading
- **PlayWright-based Upload to Art19**: Upload podcast episodes to the Art19 platform using PlayWright automation
- **Vercel Integration**: Automate website updates when new episodes are published
- **Social Media Support**: Generate content for Twitter/X posts

## Installation

### Prerequisites

- Go 1.18 or higher
- OpenAI API key
- PlayWright (Node.js, npm required) for browser automation features
- Podcast platform credentials (for publishing)

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/aipodflow.git
cd aipodflow

# Install dependencies
go mod download

# Build the binary
go build -o aipodflow ./cmd/podcast-cli
```

## Configuration

Create a `.env` file in the project root with your API credentials:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_key

# Podcast Platform Configuration (optional)
# For Art19:
ART19_USERNAME=your_art19_username
ART19_PASSWORD=your_art19_password
# Other platforms can be added in the future

# Twitter API Configuration (optional)
TWITTER_API_KEY=your_twitter_key
TWITTER_API_SECRET=your_twitter_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret

# Vercel Configuration (optional)
VERCEL_DEPLOY_HOOK=your_vercel_hook_url
```

## Usage

### Process a Transcript

```bash
# Interactive mode
./aipodflow process-transcript --input-transcript /path/to/transcript.txt

# Non-interactive mode (auto-selects first candidates)
./aipodflow process-transcript --input-transcript /path/to/transcript.txt --non-interactive

# Specify output directory
./aipodflow process-transcript --input-transcript /path/to/transcript.txt --output-dir ./output

# Include audio file for podcast platform upload
./aipodflow process-transcript --input-transcript /path/to/transcript.txt --input-audio /path/to/audio.mp3
```

### Upload to Art19 with PlayWright MCP

PlayWright MCP enables automated uploading of episodes to the Art19 platform using browser automation. Make sure you have Node.js and PlayWright installed:

```bash
npm install -g playwright
playwright install
```

To upload an episode to Art19 via PlayWright MCP:

```bash
node scripts/art19_upload_title.js --audio /path/to/audio.mp3 --title "Episode Title" --show-notes /path/to/shownotes.txt
```

This script will launch a browser, log in to Art19, and upload your episode automatically.

### Command Options

```
Usage:
  podcast-cli process-transcript [flags]

Flags:
  -h, --help                      help for process-transcript
  -a, --input-audio string        Path to audio file (required for podcast platform upload)
  -t, --input-transcript string   Path to transcript file (required)
  -n, --non-interactive           Run in non-interactive mode (auto-select first candidates)
  -o, --output-dir string         Output directory for generated files
  -v, --verbose                   Enable verbose logging
```

## PlayWright MCP & Art19 Upload

### What is PlayWright MCP?
PlayWright MCP (Multi-Channel Publisher) is a Node.js-based automation tool that uses PlayWright to perform browser operations for podcast management. In AIPodFlow, it is used to automate the process of uploading podcast episodes and metadata to the Art19 platform, reducing manual steps and improving reliability.

### How It Works
- Automates browser actions for logging in, filling forms, and uploading files to Art19
- Can be extended to support other platforms with similar workflows

### Usage Example
See the [Usage](#usage) section above for a sample command.

## Architecture

AIPodFlow is built using Go and implements a CLI tool for controlling the podcast production pipeline. It integrates with various services:

- OpenAI API for content generation
- Various podcast hosting platforms (Art19, Spotify, etc.)
- PlayWright for browser-based automation (Art19 upload)
- Vercel for website deployment
- Twitter/X API for social media distribution

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
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
