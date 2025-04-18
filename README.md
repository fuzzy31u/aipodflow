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
- **Interactive Selection**: Choose the best content from multiple AI-generated candidates
- **Non-interactive Mode**: Automatically select content for batch processing
- **Art19 Integration**: Seamlessly upload content to Art19 podcast hosting platform
- **Complete LLM Content**: Ensures all LLM-generated content is preserved without omissions

## 📋 Requirements

- Go 1.21 or higher
- OpenAI API key
- Art19 credentials (optional, for publishing)

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

### Process a Transcript

```bash
# Interactive mode (default)
./podcast-cli process-transcript --input-transcript /path/to/transcript.txt

# Non-interactive mode (auto-selects first candidates)
./podcast-cli process-transcript --input-transcript /path/to/transcript.txt --non-interactive

# Specify output directory for generated content
./podcast-cli process-transcript --input-transcript /path/to/transcript.txt --output-dir ./output

# Include audio file for Art19 upload
./podcast-cli process-transcript --input-transcript /path/to/transcript.txt --input-audio /path/to/audio.mp3

# Enable verbose logging
./podcast-cli process-transcript --input-transcript /path/to/transcript.txt --verbose
```

### Command Options

```
Usage:
  podcast-cli process-transcript [flags]

Flags:
  -h, --help                      help for process-transcript
  -a, --input-audio string        Path to audio file (for Art19 upload)
  -t, --input-transcript string   Path to transcript file (required)
  -n, --non-interactive           Run in non-interactive mode (auto-select first candidates)
  -o, --output-dir string         Output directory for generated files
  -v, --verbose                   Enable verbose logging
```

## 🏗️ Architecture

AIPodFlow is built with a modular architecture:

- **CLI Layer**: Handles user input and command execution
- **Processor Layer**: Manages the content generation workflow
- **Service Layer**: Integrates with external APIs (OpenAI, Art19)
- **UI Layer**: Provides interactive selection interface
- **Model Layer**: Defines data structures for content processing

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
