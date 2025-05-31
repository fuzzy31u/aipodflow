# AIPodFlow - Podcast Workflow Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Enabled-blue.svg)](https://cloud.google.com/)

An intelligent podcast workflow automation system built with **Google's Agent Development Kit (ADK)** and **Google Cloud Services**. This system automates the complete podcast production pipeline from raw audio to published content across multiple platforms.

## 🎯 Overview

AIPodFlow transforms raw audio recordings into fully published podcast episodes with automated:
- **🎵 Audio processing and enhancement** (format conversion, noise reduction, normalization)
- **🗣️ Multi-language transcription** (Google Cloud Speech-to-Text with APAC language support)
- **✍️ AI-powered content generation** (titles, descriptions, show notes using Claude/Anthropic)
- **📡 Cross-platform publishing** (Art19, websites, social media)

## ✅ Current Status - Fully Functional

This system has been **successfully tested** with:
- ✅ **End-to-end workflow** completing successfully
- ✅ **Google Cloud Speech-to-Text** properly configured and working
- ✅ **Large file handling** (>10MB audio files supported)
- ✅ **Japanese podcast processing** tested and validated
- ✅ **Audio processing pipeline** producing optimized output files
- ✅ **CLI interface** fully operational

## 🏗️ Architecture

The system uses a modular agent-based architecture powered by Google ADK:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  Audio Input    │───▶│ Audio Processing │───▶│  Transcription  │───▶│ Content Generation│
│  (MP3/WAV/M4A) │    │   (FFmpeg/PyDub) │    │ (Google Cloud)  │    │  (Claude/GPT)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
                                                                                   │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐              │
│   Published     │◀───│    Publishing    │◀───│   Orchestrator  │◀─────────────┘
│    Content      │    │ (Art19/Twitter)  │    │     Agent       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Agents (Google ADK)

- **🎼 Orchestrator Agent**: Coordinates the entire workflow pipeline
- **🎵 Audio Processing Agent**: Handles audio editing, normalization, and format conversion (FFmpeg)
- **🗣️ Transcription Agent**: Google Cloud Speech-to-Text with speaker diarization
- **✍️ Content Generation Agent**: Creates content using Anthropic Claude or OpenAI GPT
- **📡 Publishing Agent**: Distributes content across platforms

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Google Cloud Project** with billing enabled
- **Google Cloud CLI** (`gcloud`) installed and configured
- **Homebrew** (macOS) for FFmpeg installation

### Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/fuzzy31u/aipodflow.git
   cd aipodflow
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # or .venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg** (Required for audio processing)
   ```bash
   # macOS
   brew install ffmpeg
   
   # Linux
   sudo apt-get install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

5. **Google Cloud Setup**
   ```bash
   # Install Google Cloud CLI if not already installed
   brew install google-cloud-sdk  # macOS
   
   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   
   # Set project
   gcloud config set project YOUR_PROJECT_ID
   
   # Enable required APIs
   gcloud services enable speech.googleapis.com
   gcloud services enable storage.googleapis.com
   ```

### Configuration

1. **Copy Environment Template**
   ```bash
   cp .env.example .env
   ```

2. **Configure Environment Variables**
   ```bash
   # Required for Google Cloud
   export GOOGLE_CLOUD_PROJECT=your-project-id
   
   # Optional API Keys for enhanced features
   export ANTHROPIC_API_KEY=your_anthropic_key
   export ART19_API_TOKEN=your_art19_token
   export ART19_SERIES_ID=your_series_id
   
   # Social Media (optional)
   export TWITTER_API_KEY=your_twitter_key
   export TWITTER_API_SECRET=your_twitter_secret
   export TWITTER_ACCESS_TOKEN=your_access_token
   export TWITTER_ACCESS_TOKEN_SECRET=your_token_secret
   export TWITTER_BEARER_TOKEN=your_bearer_token
   ```

### Usage

#### CLI Mode (Recommended)

Process a single podcast episode:

```bash
# Basic usage
python main.py --mode cli --audio /path/to/episode.mp3 --language ja-JP

# With all options
python main.py --mode cli \
  --audio momitfm81_edited_by_riverside.mp3 \
  --language ja-JP
```

#### Server Mode (HTTP API)

Run as a web service:

```bash
python main.py --mode server --host localhost --port 8080
```

Then make HTTP requests:

```bash
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://example.com/audio.mp3",
    "language_code": "ja-JP",
    "metadata": {"episode_number": 42}
  }'
```

## 🌍 Supported Languages

The system supports multiple APAC languages for transcription:

- **English**: `en-US`, `en-AU`
- **Japanese**: `ja-JP`  
- **Chinese**: `zh-CN` (Simplified), `zh-TW` (Traditional)
- **Korean**: `ko-KR`
- **Thai**: `th-TH`
- **Vietnamese**: `vi-VN`
- **Indonesian**: `id-ID`
- **Malay**: `ms-MY`
- **Filipino**: `tl-PH`
- **Hindi**: `hi-IN`
- **Tamil**: `ta-IN`
- **Telugu**: `te-IN`
- **Bengali**: `bn-IN`

## 📁 Output Files

After processing, you'll find:

### Processed Audio
- **Location**: Temporary directory (copied to project root)
- **Format**: `{original_name}_processed.wav`
- **Specs**: 16kHz, mono, WAV format (optimized for transcription)

### Generated Content
- **Episode ID**: Unique identifier for each processed episode
- **Transcript**: Full text transcription with confidence scores
- **Content**: AI-generated titles, descriptions, show notes
- **Metadata**: Processing statistics and language detection

## ⚙️ Advanced Configuration

### Large File Handling
- Files **≤10MB**: Direct upload to Google Cloud Speech-to-Text
- Files **>10MB**: Automatic fallback to alternative transcription methods
- **Cloud Storage**: Future enhancement for large file processing

### Audio Processing Pipeline
1. **Format standardization** (convert to WAV, 16kHz, mono)
2. **Silence removal** (trim leading/trailing silence)
3. **Volume normalization** (standardize audio levels)
4. **Quality optimization** (prepare for speech recognition)

### Error Handling
- **Graceful fallbacks** for each processing stage
- **Detailed logging** for troubleshooting
- **Partial success** handling (continue pipeline even if some stages fail)

## 🔧 Troubleshooting

### Common Issues

**1. FFmpeg not found**
```bash
# macOS
export PATH="/opt/homebrew/bin:$PATH"

# Or install FFmpeg
brew install ffmpeg
```

**2. Google Cloud authentication errors**
```bash
# Re-authenticate
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

**3. Large file upload errors**
```bash
# Files >10MB automatically use fallback transcription
# This is expected behavior - check logs for "Large file detected"
```

**4. Permission errors**
```bash
# Check Google Cloud billing is enabled
gcloud billing accounts list
gcloud billing projects link PROJECT_ID --billing-account=ACCOUNT_ID
```

## 🧪 Development

### Project Structure
```
aipodflow/
├── agents/                 # Google ADK agents
│   ├── audio_processing_agent.py
│   ├── transcription_agent.py
│   ├── content_generation_agent.py
│   ├── publishing_agent.py
│   └── orchestrator_agent.py
├── connectors/            # External API integrations
│   ├── anthropic_api.py
│   ├── art19_api.py
│   └── twitter_api.py
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── .env.example         # Configuration template
```

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Linting
flake8 .

# Type checking
mypy .
```

## 📊 Example Output

```
=== Workflow Completed ===
Episode ID: japanese-podcast-20250531-171448-19555b03
Original file: momitfm81_edited_by_riverside.mp3 (16MB)
Processed file: momitfm81_edited_by_riverside_processed.wav (64MB)
Transcript length: 1,245 characters
Generated content: ✅ Title, Description, Show Notes, Social Media
Publishing: ⚠️ Art19 (needs API key), ⚠️ Twitter (needs credentials)
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Agent Development Kit (ADK)** for the agent framework
- **Google Cloud Speech-to-Text** for transcription services
- **Anthropic Claude** for content generation
- **FFmpeg** for audio processing
