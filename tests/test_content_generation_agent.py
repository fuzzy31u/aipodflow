"""
Tests for Content Generation Agent

Unit tests for the content generation agent that creates podcast metadata and content.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from agents.content_generation_agent import ContentGenerationAgent


class TestContentGenerationAgent:
    """Test suite for ContentGenerationAgent."""

    @pytest.fixture
    def content_agent(self):
        """Create a content generation agent for testing."""
        return ContentGenerationAgent()

    @pytest.fixture
    def sample_transcript(self):
        """Sample podcast transcript for testing."""
        return """
        Welcome to the AI Technology Podcast. Today we're discussing the latest developments 
        in artificial intelligence and machine learning. Our guest is Dr. Sarah Chen, 
        a leading researcher in neural networks.
        
        We'll be covering topics like deep learning, natural language processing, 
        and the future of AI in healthcare. This is a fascinating conversation that 
        you won't want to miss.
        
        Let's dive right into the discussion about transformer architectures and 
        their impact on modern AI applications.
        """

    @pytest.mark.asyncio
    async def test_generate_content_success(self, content_agent, sample_transcript):
        """Test successful content generation."""
        # Mock the LLM call
        with patch.object(content_agent, '_call_llm') as mock_llm:
            mock_llm.side_effect = [
                "AI Technology Deep Dive with Dr. Sarah Chen",  # title
                "Join us for an in-depth discussion about AI...",  # description
                "• Introduction to neural networks\n• Deep learning...",  # show notes
                "Twitter: Check out our latest AI podcast!\nLinkedIn: New episode...",  # social media
                "This episode covers the latest AI developments..."  # summary
            ]
            
            result = await content_agent.generate_content(
                transcript=sample_transcript,
                language_code="en-US"
            )
            
            # Verify all content types are generated
            assert "title" in result
            assert "description" in result
            assert "show_notes" in result
            assert "social_media" in result
            assert "summary" in result
            assert "metadata" in result
            
            # Verify metadata
            metadata = result["metadata"]
            assert metadata["language"] == "English"
            assert metadata["language_code"] == "en-US"
            assert metadata["transcript_length"] > 0
            assert metadata["word_count"] > 0
            
            # Verify LLM was called 5 times (once for each content type)
            assert mock_llm.call_count == 5

    @pytest.mark.asyncio
    async def test_generate_content_japanese(self, content_agent, sample_transcript):
        """Test content generation for Japanese language."""
        with patch.object(content_agent, '_call_llm') as mock_llm:
            mock_llm.side_effect = [
                "AIテクノロジー詳解",  # title in Japanese
                "最新のAI技術について詳しく議論します...",  # description
                "• ニューラルネットワークの紹介...",  # show notes
                "Twitter: 最新のAIポッドキャストをチェック！",  # social media
                "このエピソードでは最新のAI開発について..."  # summary
            ]
            
            result = await content_agent.generate_content(
                transcript=sample_transcript,
                language_code="ja-JP"
            )
            
            assert result["metadata"]["language"] == "Japanese"
            assert result["metadata"]["language_code"] == "ja-JP"
            assert "AIテクノロジー詳解" in result["title"]

    @pytest.mark.asyncio
    async def test_generate_content_with_options(self, content_agent, sample_transcript):
        """Test content generation with custom options."""
        options = {
            "target_audience": "developers",
            "show_style": "technical",
            "notes_format": "detailed",
            "brand_voice": "professional"
        }
        
        with patch.object(content_agent, '_call_llm') as mock_llm:
            mock_llm.return_value = "Generated content"
            
            await content_agent.generate_content(
                transcript=sample_transcript,
                language_code="en-US",
                content_options=options
            )
            
            # Verify options were passed to prompt templates
            call_args = [call[0][0] for call in mock_llm.call_args_list]
            assert any("developers" in arg for arg in call_args)
            assert any("technical" in arg for arg in call_args)

    @pytest.mark.asyncio
    async def test_call_llm_anthropic_success(self, content_agent):
        """Test successful Anthropic LLM call."""
        # Mock Anthropic client
        mock_client = Mock()
        mock_message = Mock()
        mock_content_block = Mock()
        mock_content_block.text = "Generated response text"
        mock_message.content = [mock_content_block]
        mock_message.model = "claude-3-sonnet"
        mock_message.role = "assistant"
        mock_message.usage = Mock(input_tokens=100, output_tokens=50)
        
        mock_client.messages.create.return_value = mock_message
        content_agent.anthropic_client = mock_client
        
        result = await content_agent._call_llm("Test prompt")
        
        assert result == "Generated response text"
        mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_llm_no_client_available(self, content_agent):
        """Test LLM call when no client is available."""
        content_agent.anthropic_client = None
        content_agent.gemini_client = None
        
        result = await content_agent._call_llm("Test prompt")
        
        assert "PLACEHOLDER CONTENT" in result
        assert "LLM not configured" in result

    @pytest.mark.asyncio
    async def test_call_llm_anthropic_failure(self, content_agent):
        """Test LLM call when Anthropic API fails."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        content_agent.anthropic_client = mock_client
        
        with pytest.raises(Exception, match="API Error"):
            await content_agent._call_llm("Test prompt")

    def test_extract_language_from_code(self, content_agent):
        """Test language extraction from language codes."""
        assert content_agent._extract_language_from_code("en-US") == "English"
        assert content_agent._extract_language_from_code("ja-JP") == "Japanese"
        assert content_agent._extract_language_from_code("zh-CN") == "Chinese"
        assert content_agent._extract_language_from_code("xx-XX") == "English"  # fallback

    def test_truncate_transcript(self, content_agent):
        """Test transcript truncation."""
        long_transcript = "This is a sentence. " * 1000  # Very long transcript
        
        truncated = content_agent._truncate_transcript(long_transcript, 500)
        
        assert len(truncated) <= 500
        assert "Transcript truncated" in truncated

    def test_truncate_transcript_short(self, content_agent):
        """Test transcript truncation with short text."""
        short_transcript = "This is a short transcript."
        
        truncated = content_agent._truncate_transcript(short_transcript, 500)
        
        assert truncated == short_transcript

    def test_extract_social_media_posts(self, content_agent):
        """Test extraction of social media posts from LLM response."""
        response = """
        Twitter: Check out our latest podcast episode! #AI #tech
        LinkedIn: We're excited to share our new episode about artificial intelligence...
        Instagram: New podcast episode is live! 🎧 #podcast #AI
        """
        
        twitter_post = content_agent._extract_twitter_post(response)
        assert len(twitter_post) <= 280
        assert "#AI" in twitter_post or "podcast" in twitter_post.lower()

    def test_get_preferred_model(self, content_agent):
        """Test preferred model detection."""
        # Test with Anthropic client
        content_agent.anthropic_client = Mock()
        content_agent.gemini_client = None
        assert content_agent._get_preferred_model() == "claude-3-sonnet"
        
        # Test with no clients
        content_agent.anthropic_client = None
        content_agent.gemini_client = None
        assert content_agent._get_preferred_model() == "none"

    @pytest.mark.asyncio
    async def test_generate_translations(self, content_agent):
        """Test content translation to multiple languages."""
        content = {
            "title": "AI Technology Podcast",
            "description": "A discussion about AI",
            "summary": "AI developments"
        }
        
        with patch.object(content_agent, '_translate_text') as mock_translate:
            mock_translate.side_effect = [
                "AIテクノロジーポッドキャスト",  # Japanese title
                "AIについての議論",  # Japanese description
                "AI開発"  # Japanese summary
            ]
            
            translations = await content_agent.generate_translations(
                content, ["ja-JP"]
            )
            
            assert "ja-JP" in translations
            japanese_content = translations["ja-JP"]
            assert "AIテクノロジーポッドキャスト" in japanese_content["title"]
            assert mock_translate.call_count == 3  # One call per content field

    @pytest.mark.asyncio
    async def test_translate_text(self, content_agent):
        """Test text translation."""
        with patch.object(content_agent, '_call_llm') as mock_llm:
            mock_llm.return_value = "Bonjour le monde"
            
            result = await content_agent._translate_text("Hello world", "French")
            
            assert result == "Bonjour le monde"
            
            # Verify the prompt included the target language
            call_args = mock_llm.call_args[0][0]
            assert "French" in call_args
            assert "Hello world" in call_args

    def test_initialization(self, content_agent):
        """Test content generation agent initialization."""
        assert content_agent.name == "content_generator"
        assert hasattr(content_agent, 'prompt_templates')
        assert hasattr(content_agent, 'supported_languages')
        assert len(content_agent.supported_languages) > 0
        
        # Verify prompt templates exist
        assert "title" in content_agent.prompt_templates
        assert "description" in content_agent.prompt_templates
        assert "show_notes" in content_agent.prompt_templates
        assert "social_media" in content_agent.prompt_templates
        assert "summary" in content_agent.prompt_templates