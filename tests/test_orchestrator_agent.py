"""
Tests for Orchestrator Agent

Unit tests for the orchestrator agent that coordinates the podcast workflow pipeline.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile

import sys
sys.path.append(str(Path(__file__).parent.parent))

from agents.orchestrator_agent import OrchestratorAgent


class TestOrchestratorAgent:
    """Test suite for OrchestratorAgent."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator agent for testing."""
        return OrchestratorAgent()

    @pytest.fixture
    def sample_audio_file(self):
        """Create a temporary audio file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            # Write minimal WAV header
            f.write(b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00")
            f.write(b"\x00" * 2048)  # Some dummy audio data
            yield f.name
        Path(f.name).unlink()  # Clean up

    @pytest.fixture
    def mock_agents(self, orchestrator):
        """Mock all sub-agents for testing."""
        with patch.object(orchestrator, 'audio_processor') as mock_audio, \
             patch.object(orchestrator, 'transcriber') as mock_transcriber, \
             patch.object(orchestrator, 'content_generator') as mock_content, \
             patch.object(orchestrator, 'publisher') as mock_publisher:
            
            # Configure mock return values
            mock_audio.process_audio = AsyncMock(return_value={
                "file_path": "/tmp/processed_audio.wav",
                "duration_seconds": 120.5,
                "sample_rate": 16000,
                "channels": 1
            })
            
            mock_transcriber.transcribe_audio = AsyncMock(return_value={
                "text": "This is a sample transcript of the podcast episode.",
                "language": "en-US",
                "confidence": 0.95,
                "word_count": 10
            })
            
            mock_content.generate_content = AsyncMock(return_value={
                "title": "Sample Episode Title",
                "description": "This is a sample episode description.",
                "show_notes": "Sample show notes with key points.",
                "social_media": {
                    "twitter": "New episode: Sample Episode Title #podcast",
                    "linkedin": "Check out our latest episode..."
                },
                "summary": "Brief summary of the episode."
            })
            
            mock_publisher.publish_episode = AsyncMock(return_value={
                "episode_id": "test-episode-123",
                "published_platforms": ["art19", "website", "social_media"],
                "failed_platforms": [],
                "details": {
                    "art19": {"success": True, "episode_url": "https://art19.com/episode/123"},
                    "website": {"success": True, "deployment_id": "vercel-123"},
                    "social_media": {"success": True, "platforms": {"twitter": {"success": True}}}
                }
            })
            
            yield {
                "audio": mock_audio,
                "transcriber": mock_transcriber,
                "content": mock_content,
                "publisher": mock_publisher
            }

    @pytest.mark.asyncio
    async def test_process_podcast_workflow_success(self, orchestrator, sample_audio_file, mock_agents):
        """Test successful podcast workflow processing."""
        result = await orchestrator.process_podcast_workflow(
            audio_path=sample_audio_file,
            language_code="en-US"
        )
        
        # Verify workflow completion
        assert result["success"] is True
        assert "processed_audio" in result
        assert "transcript" in result
        assert "generated_content" in result
        assert "publishing_results" in result
        assert "episode_id" in result
        
        # Verify each stage was called
        mock_agents["audio"].process_audio.assert_called_once()
        mock_agents["transcriber"].transcribe_audio.assert_called_once()
        mock_agents["content"].generate_content.assert_called_once()
        mock_agents["publisher"].publish_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_podcast_workflow_missing_file(self, orchestrator):
        """Test workflow with missing audio file."""
        with pytest.raises(FileNotFoundError):
            await orchestrator.process_podcast_workflow(
                audio_path="/nonexistent/file.wav",
                language_code="en-US"
            )

    @pytest.mark.asyncio
    async def test_process_podcast_workflow_audio_processing_failure(self, orchestrator, sample_audio_file):
        """Test workflow when audio processing fails."""
        with patch.object(orchestrator, 'audio_processor') as mock_audio:
            mock_audio.process_audio = AsyncMock(side_effect=Exception("Audio processing failed"))
            
            with pytest.raises(Exception, match="Audio processing failed"):
                await orchestrator.process_podcast_workflow(
                    audio_path=sample_audio_file,
                    language_code="en-US"
                )

    @pytest.mark.asyncio
    async def test_process_podcast_workflow_transcription_failure(self, orchestrator, sample_audio_file):
        """Test workflow when transcription fails."""
        with patch.object(orchestrator, 'audio_processor') as mock_audio, \
             patch.object(orchestrator, 'transcriber') as mock_transcriber:
            
            mock_audio.process_audio = AsyncMock(return_value={"file_path": "/tmp/test.wav"})
            mock_transcriber.transcribe_audio = AsyncMock(side_effect=Exception("Transcription failed"))
            
            with pytest.raises(Exception, match="Transcription failed"):
                await orchestrator.process_podcast_workflow(
                    audio_path=sample_audio_file,
                    language_code="en-US"
                )

    @pytest.mark.asyncio
    async def test_process_podcast_workflow_with_metadata(self, orchestrator, sample_audio_file, mock_agents):
        """Test workflow with additional metadata."""
        metadata = {
            "episode_number": 42,
            "season_number": 2,
            "tags": ["technology", "ai", "podcast"],
            "category": "Technology"
        }
        
        result = await orchestrator.process_podcast_workflow(
            audio_path=sample_audio_file,
            language_code="ja-JP",
            metadata=metadata
        )
        
        assert result["success"] is True
        assert result["metadata"] == metadata
        assert result["language_code"] == "ja-JP"

    @pytest.mark.asyncio
    async def test_process_podcast_workflow_partial_publishing_failure(self, orchestrator, sample_audio_file):
        """Test workflow when some publishing platforms fail."""
        with patch.object(orchestrator, 'audio_processor') as mock_audio, \
             patch.object(orchestrator, 'transcriber') as mock_transcriber, \
             patch.object(orchestrator, 'content_generator') as mock_content, \
             patch.object(orchestrator, 'publisher') as mock_publisher:
            
            # Mock successful stages
            mock_audio.process_audio = AsyncMock(return_value={"file_path": "/tmp/test.wav"})
            mock_transcriber.transcribe_audio = AsyncMock(return_value={
                "text": "Sample transcript", "language": "en-US"
            })
            mock_content.generate_content = AsyncMock(return_value={
                "title": "Test Episode", "description": "Test description", "show_notes": "Notes"
            })
            
            # Mock partial publishing failure
            mock_publisher.publish_episode = AsyncMock(return_value={
                "episode_id": "test-123",
                "published_platforms": ["art19"],
                "failed_platforms": ["website", "social_media"],
                "details": {
                    "art19": {"success": True},
                    "website": {"success": False, "error": "Deployment failed"},
                    "social_media": {"success": False, "error": "API rate limit"}
                }
            })
            
            # Should complete workflow despite publishing failures
            result = await orchestrator.process_podcast_workflow(
                audio_path=sample_audio_file,
                language_code="en-US"
            )
            
            assert result["success"] is True
            assert len(result["publishing_results"]["failed_platforms"]) == 2

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.name == "orchestrator"
        assert hasattr(orchestrator, 'audio_processor')
        assert hasattr(orchestrator, 'transcriber')
        assert hasattr(orchestrator, 'content_generator')
        assert hasattr(orchestrator, 'publisher')

    @pytest.mark.asyncio
    async def test_get_workflow_status_not_implemented(self, orchestrator):
        """Test workflow status method (not yet implemented)."""
        result = await orchestrator.get_workflow_status("test-workflow-123")
        
        assert result["workflow_id"] == "test-workflow-123"
        assert result["status"] == "not_implemented"

    @pytest.mark.asyncio
    async def test_cancel_workflow_not_implemented(self, orchestrator):
        """Test workflow cancellation method (not yet implemented)."""
        result = await orchestrator.cancel_workflow("test-workflow-123")
        
        assert result["workflow_id"] == "test-workflow-123"
        assert result["cancelled"] is False