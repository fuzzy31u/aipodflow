# AI Podcast Flow - Agent Development Kit Hackathon

An intelligent podcast workflow automation system built with Google's Agent Development Kit (ADK) for the Google Cloud Hackathon. This system automates the complete podcast production pipeline from raw audio to published content across multiple platforms.

## 🎯 Overview

AI Podcast Flow transforms raw audio recordings into fully published podcast episodes with automated:
- Audio processing and enhancement
- Multi-language transcription (APAC languages supported)
- AI-powered content generation (titles, descriptions, show notes)
- Cross-platform publishing (Art19, websites, social media)

## 🏗️ Architecture

The system uses a modular agent-based architecture with the following components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  Audio Input    │───▶│ Audio Processing │───▶│  Transcription  │───▶│ Content Generation│
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
                                                                                   │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐              │
│   Published     │◀───│    Publishing    │◀───│   Orchestrator  │◀─────────────┘
│    Content      │    │   & Distribution │    │     Agent       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Agents

- **🎼 Orchestrator Agent**: Coordinates the entire workflow
- **🎵 Audio Processing Agent**: Handles audio editing, normalization, and format conversion
- **🗣️ Transcription Agent**: Converts speech to text with APAC language support
- **✍️ Content Generation Agent**: Creates titles, descriptions, and social content using LLMs
- **📡 Publishing Agent**: Distributes content across platforms (Art19, Vercel, Twitter)

### External Connectors

- **🤖 Anthropic API**: Claude LLM for content generation
- **🎙️ Art19 API**: Podcast hosting and distribution
- **🐦 Twitter API**: Social media announcements
- **🚀 Vercel API**: Website deployment and updates

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project (for deployment)
- API keys for external services (see Configuration section)

### Local Development

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd aipodflow
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Run Locally**
   ```bash
   # CLI mode for single file processing
   python main.py --mode cli --audio /path/to/audio.wav --language en-US
   
   # Server mode for HTTP API
   python main.py --mode server --host localhost --port 8080
   ```

### Docker Deployment

1. **Build Container**
   ```bash
   docker build -f Dockerfile.python -t ai-podcast-flow .
   ```

2. **Run Container**
   ```bash
   docker run -p 8080:8080 --env-file .env ai-podcast-flow
   ```

### Google Cloud Run Deployment

1. **Build and Deploy**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT/ai-podcast-flow
   gcloud run deploy ai-podcast-flow \
     --image gcr.io/YOUR_PROJECT/ai-podcast-flow \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="$(cat .env | grep -v '^#' | tr '\n' ',')"
   ```

## ⚙️ Configuration

### Required Environment Variables

```bash
# AI/ML Services
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_CLOUD_LOCATION=us-central1

# Podcast Hosting (Art19)
ART19_API_TOKEN=your_art19_api_token
ART19_SERIES_ID=your_series_id
ART19_AUTO_PUBLISH=false

# Social Media (Twitter)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Website Deployment (Vercel)
VERCEL_DEPLOY_HOOK=your_vercel_deploy_hook_url
VERCEL_API_TOKEN=your_vercel_api_token
VERCEL_PROJECT_ID=your_project_id

# Application Settings
PORT=8080
SOCIAL_MEDIA_ENABLED=true
WEBSITE_ENABLED=true
```

### Supported Languages

The system supports multiple APAC languages for transcription and content generation:

- **English**: en-US, en-AU
- **Japanese**: ja-JP  
- **Chinese**: zh-CN (Simplified), zh-TW (Traditional)
- **Korean**: ko-KR
- **Thai**: th-TH
- **Vietnamese**: vi-VN
- **Indonesian**: id-ID
- **Malay**: ms-MY
- **Filipino**: tl-PH
- **Hindi**: hi-IN
- **Tamil**: ta-IN

## 📖 API Documentation

### HTTP Endpoints

#### `POST /process`
Process a podcast episode through the complete workflow.

**Request:**
```json
{
  "audio_url": "https://example.com/audio.mp3",
  "language_code": "ja-JP",
  "metadata": {
    "episode_number": 42,
    "tags": ["technology", "ai"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Podcast processed successfully",
  "episode_id": "episode-123",
  "transcript": "Transcribed text...",
  "generated_content": {
    "title": "Episode Title",
    "description": "Episode description...",
    "show_notes": "Detailed notes...",
    "social_media": {
      "twitter": "Tweet text...",
      "linkedin": "LinkedIn post..."
    }
  }
}
```

#### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "podcast-workflow-automation"
}
```

### File Upload Support

You can also upload audio files directly:

```bash
curl -X POST http://localhost:8080/process \
  -F "audio_file=@episode.wav" \
  -F "language_code=en-US"
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=connectors --cov-report=html

# Run specific test file
pytest tests/test_orchestrator_agent.py -v

# Run tests with logging
pytest -s --log-cli-level=INFO
```

### Test Structure

```
tests/
├── __init__.py
├── test_orchestrator_agent.py      # Workflow coordination tests
├── test_content_generation_agent.py # LLM content generation tests
├── test_audio_processing_agent.py   # Audio processing tests (TODO)
├── test_transcription_agent.py      # Speech-to-text tests (TODO)
├── test_publishing_agent.py         # Publishing platform tests (TODO)
└── conftest.py                      # Shared test fixtures (TODO)
```

## 🔧 Development

### Project Structure

```
aipodflow/
├── agents/                    # Core workflow agents
│   ├── __init__.py
│   ├── orchestrator_agent.py
│   ├── audio_processing_agent.py
│   ├── transcription_agent.py
│   ├── content_generation_agent.py
│   └── publishing_agent.py
├── connectors/               # External service integrations
│   ├── __init__.py
│   ├── anthropic_api.py
│   ├── art19_api.py
│   ├── twitter_api.py
│   └── vercel_api.py
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_orchestrator_agent.py
│   └── test_content_generation_agent.py
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile.python        # Container definition
└── README_PYTHON.md        # This file
```

### Adding New Agents

1. Create agent class inheriting from `google_adk.Agent`
2. Implement required methods with proper async/await
3. Add connector integration if needed
4. Update orchestrator to include new agent
5. Add comprehensive tests

### Adding New Connectors

1. Create connector class with authentication handling
2. Implement async methods for API interactions
3. Add proper error handling and retry logic
4. Include configuration validation
5. Add integration tests

## 🚀 Deployment Scenarios

### Development
- Local Python execution
- SQLite for state (if needed)
- Mock external services for testing

### Staging  
- Google Cloud Run
- Cloud SQL for state persistence
- Limited external service calls

### Production
- Google Cloud Run with auto-scaling
- Cloud SQL with read replicas
- Full external service integration
- Cloud Monitoring and Logging

## 🔍 Monitoring and Logging

The application includes structured logging for monitoring:

```python
import structlog
logger = structlog.get_logger(__name__)

# Logs are automatically structured for Cloud Logging
logger.info("Processing episode", episode_id="123", duration=120.5)
```

Key metrics to monitor:
- Processing time per episode
- Success/failure rates per platform
- API response times and errors
- Resource usage (memory, CPU)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all public methods
- Include type hints for function parameters and returns
- Write tests for new functionality
- Update documentation for significant changes

## 📋 TODO Items

### High Priority
- [ ] Implement actual audio processing logic (FFmpeg integration)
- [ ] Complete Google Cloud Speech-to-Text integration
- [ ] Add Whisper fallback for transcription
- [ ] Implement Art19 API authentication and episode creation
- [ ] Complete Twitter API v2 integration
- [ ] Add Vercel deployment webhook handling

### Medium Priority
- [ ] Add support for Google Gemini LLM
- [ ] Implement workflow state persistence
- [ ] Add batch processing capabilities
- [ ] Create web dashboard for monitoring
- [ ] Add support for more social media platforms (LinkedIn, Instagram)
- [ ] Implement advanced audio processing (noise reduction, speaker separation)

### Low Priority
- [ ] Add support for video podcasts
- [ ] Implement automatic episode numbering
- [ ] Add analytics and reporting features
- [ ] Create mobile app for workflow triggering
- [ ] Add support for live streaming integration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Cloud Agent Development Kit team
- Anthropic for Claude API
- Art19 for podcast hosting API
- Twitter for social media integration
- Vercel for deployment platform
- All open-source contributors

---

**Built for the Google Cloud Agent Development Kit Hackathon 2024**

For questions or support, please open an issue or contact the development team.