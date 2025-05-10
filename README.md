# AIPodFlow

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![CI Status](https://github.com/fuzzy31u/aipodflow/workflows/CI/badge.svg)](https://github.com/fuzzy31u/aipodflow/actions)
[![Go Report Card](https://goreportcard.com/badge/github.com/fuzzy31u/aipodflow)](https://goreportcard.com/report/github.com/fuzzy31u/aipodflow)

AIPodFlow is an open-source CLI tool that leverages AI to streamline podcast production workflow. It automates the entire process from transcript processing to content generation and publishing, making podcast production faster and more efficient.

## 🚀 Features

- **AI-powered Content Generation**: 
  - Generate engaging title candidates based on transcript content
  - Create comprehensive show notes with proper formatting and emojis
  - Suggest optimal ad placement timecodes for monetization
- **Step-by-Step Workflow**: Execute each step of the podcast production process separately
  - Step 1: Process transcript and generate content with OpenAI
  - Step 2: Upload title, show notes, and audio to Art19
  - Step 3: Redeploy website on Vercel
  - Step 4: Create and post content to X (coming soon)
- **Interactive Selection**: Choose the best content from multiple AI-generated candidates
- **Non-interactive Mode**: Automatically select content for batch processing
- **Art19 Integration**: Seamlessly upload content to Art19 podcast hosting platform
- **PlayWright MCP Integration**: Automate browser-based workflows for podcast management and uploading
- **PlayWright-based Upload to Art19**: Upload podcast episodes to the Art19 platform using PlayWright automation
- **Complete LLM Content**: Ensures all LLM-generated content is preserved without omissions
- **Vercel Integration**: Automate website updates when new episodes are published
- **Social Media Support**: Generate content for Twitter/X posts

## 📋 Requirements

- Go 1.21 or higher
- OpenAI API key
- Art19 credentials (for publishing)
- PlayWright (Node.js, npm required) for browser automation features

## 🔧 Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/fuzzy31u/aipodflow.git
cd aipodflow

# Install dependencies
go mod download

# Build the binary
go build -o podcast-cli ./cmd/podcast-cli
```

## ⚙️ Configuration

Create a `config.yaml` file in the project root or in `$HOME/.aipodflow/` directory:

```yaml
# OpenAI API Configuration (required)
openai_api_key: "your_openai_api_key"

# Art19 Configuration (optional, for publishing)
art19_username: "your_art19_username"
art19_password: "your_art19_password"
```

## 🖥️ Usage

### Process a Podcast (Step by Step)

AIPodFlow now supports executing each step of the podcast processing workflow separately, giving you more control over the process:

```bash
# Step 1: Process transcript and call OpenAI API
./podcast-cli process step1 --input-transcript /path/to/transcript.txt --output-dir ./output

# Step 2: Upload title, shownote and audio to Art19
./podcast-cli process step2 --input-audio /path/to/audio.mp3 --content-file ./output/selected_content.txt

# Step 3: Redeploy website on Vercel
./podcast-cli process step3 --dry-run  # Validate configuration without triggering deployment
./podcast-cli process step3            # Trigger actual redeployment

# Step 4: Create text to post to X (not fully implemented yet)
./podcast-cli process step4
```

### Process a Transcript (Legacy Mode)

You can still use the legacy mode to process everything in a single command:

```bash
# Interactive mode (default)
./podcast-cli process all --input-transcript /path/to/transcript.txt

# Specify output directory for generated content
./podcast-cli process all --input-transcript /path/to/transcript.txt --output-dir ./output

# Include audio file for Art19 upload
./podcast-cli process all --input-transcript /path/to/transcript.txt --input-audio /path/to/audio.mp3

# Enable verbose logging
./podcast-cli process all --input-transcript /path/to/transcript.txt --verbose
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

#### Step 1: Process Transcript and Call OpenAI API

```
Usage:
  podcast-cli process step1 [flags]

Flags:
      --gen-shownotes             Generate show notes (default: true)
  -h, --help                      help for step1
  -t, --input-transcript string   Path to transcript file (required)
      --openai-key string         OpenAI API key (can also be set via OPENAI_API_KEY environment variable)
  -o, --output-dir string         Output directory for generated files
      --titles-only               Generate only titles, skip show notes
  -v, --verbose                   Enable verbose logging
```

#### Step 2: Upload to Art19

```
Usage:
  podcast-cli process step2 [flags]

Flags:
  -c, --content-file string      Path to content file with title and show notes (required)
  -h, --help                     help for step2
  -a, --input-audio string       Path to audio file (required)
  -v, --verbose                  Enable verbose logging
```

#### Step 3: Redeploy on Vercel

```
Usage:
  podcast-cli process step3 [flags]

Flags:
      --dry-run                  Validate configuration without triggering actual redeployment
  -h, --help                     help for step3
  -v, --verbose                  Enable verbose logging
```

#### Legacy Mode (All Steps)

```
Usage:
  podcast-cli process all [flags]

Flags:
      --api-only                  Stop after API call and display response
      --gen-shownotes             Generate show notes (default: true)
  -h, --help                      help for all
  -a, --input-audio string        Path to audio file (required)
  -t, --input-transcript string   Path to transcript file (required)
  -o, --output-dir string         Output directory for generated files
      --skip-upload               Skip uploading to Art19
      --titles-only               Generate only titles, skip show notes
  -v, --verbose                   Enable verbose logging
```

## 🤖 PlayWright MCP & Art19 Upload

### What is PlayWright MCP?
PlayWright MCP (Multi-Channel Publisher) is a Node.js-based automation tool that uses PlayWright to perform browser operations for podcast management. In AIPodFlow, it is used to automate the process of uploading podcast episodes and metadata to the Art19 platform, reducing manual steps and improving reliability.

### How It Works
- Automates browser actions for logging in, filling forms, and uploading files to Art19
- Can be extended to support other platforms with similar workflows

### Usage Example
See the [Usage](#usage) section above for a sample command.

## 🏗️ Architecture

AIPodFlow is built with a modular architecture:

- **CLI Layer**: Handles user input and command execution
- **Processor Layer**: Manages the content generation workflow
- **Service Layer**: Integrates with external APIs (OpenAI, Art19)
- **UI Layer**: Provides interactive selection interface
- **Model Layer**: Defines data structures for content processing

### Integrations

- OpenAI API for content generation
- Various podcast hosting platforms (Art19, Spotify, etc.)
- PlayWright for browser-based automation (Art19 upload)
- Vercel for website deployment
- Twitter/X API for social media distribution

### Key Components

- **OpenAI Integration**: Uses GPT-4o for high-quality content generation
- **Art19 API**: Enables direct upload of podcast content
- **Interactive UI**: Terminal-based interface for content selection

## 🧪 Development

The project uses:

- Go 1.21+
- Cobra for CLI commands
- Logrus for structured logging
- Viper for configuration management
- GitHub Actions for CI/CD

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
