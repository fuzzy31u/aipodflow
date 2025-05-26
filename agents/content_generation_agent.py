"""
Content Generation Agent

This agent uses Large Language Models (Claude, Gemini) to generate textual content
from podcast transcripts, including titles, descriptions, show notes, and social media content.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import json

from google_adk import Agent
import anthropic
from google.cloud import aiplatform


logger = logging.getLogger(__name__)


class ContentGenerationAgent(Agent):
    """
    Content Generation Agent for creating podcast metadata and promotional content.
    
    Uses LLMs to generate episode titles, descriptions, show notes, and social media
    content from transcripts. Supports multiple languages for APAC markets.
    """

    def __init__(self):
        """Initialize the content generation agent."""
        super().__init__(name="content_generator")
        
        # Initialize LLM clients
        self.anthropic_client = None
        self.gemini_client = None
        
        self._initialize_llm_clients()
        
        # Content generation templates
        self.prompt_templates = self._load_prompt_templates()
        
        # Supported output languages
        self.supported_languages = {
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese",
            "ko": "Korean",
            "th": "Thai",
            "vi": "Vietnamese",
            "id": "Indonesian",
            "ms": "Malay",
            "tl": "Filipino",
            "hi": "Hindi",
            "ta": "Tamil"
        }
        
        logger.info("Content generation agent initialized")

    def _initialize_llm_clients(self):
        """Initialize LLM clients for content generation."""
        # Initialize Anthropic Claude client
        try:
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
                logger.info("Anthropic Claude client initialized")
            else:
                logger.warning("ANTHROPIC_API_KEY not found in environment")
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client: {str(e)}")

        # Initialize Google Gemini client
        try:
            # TODO: Configure Google Cloud project and location
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            
            if project_id:
                aiplatform.init(project=project_id, location=location)
                # TODO: Initialize Gemini model client
                logger.info("Google Cloud AI Platform initialized")
            else:
                logger.warning("GOOGLE_CLOUD_PROJECT not found in environment")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Cloud AI: {str(e)}")

    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates for content generation."""
        return {
            "title": """
Based on the following podcast transcript, generate a compelling and engaging title for this episode.
The title should be:
- Catchy and attention-grabbing
- Accurately represent the main topic/theme
- Between 5-10 words
- Suitable for the target language and culture

Transcript:
{transcript}

Language: {language}
Target audience: {audience}

Generate only the title, no additional text:
""",

            "description": """
Create a compelling podcast episode description based on the following transcript.
The description should be:
- 2-3 paragraphs long
- Engaging and informative
- Include key topics covered
- End with a call-to-action
- Appropriate for the target language and culture

Transcript:
{transcript}

Language: {language}
Show style: {style}

Generate the description:
""",

            "show_notes": """
Create detailed show notes for this podcast episode based on the transcript.
Include:
- Key topics and timestamps (if available)
- Important quotes or insights
- Resources mentioned
- Guest information (if applicable)
- Bullet points for easy reading

Transcript:
{transcript}

Language: {language}
Format: {format}

Generate the show notes:
""",

            "social_media": """
Create social media content for this podcast episode based on the transcript.
Generate:
1. A Twitter/X post (under 280 characters)
2. A LinkedIn post (engaging but professional)
3. An Instagram caption (with relevant hashtags)

Make it engaging and include a call-to-action to listen to the episode.

Transcript:
{transcript}

Language: {language}
Brand voice: {voice}

Generate the social media content:
""",

            "summary": """
Create a concise summary of this podcast episode based on the transcript.
The summary should be:
- 1-2 paragraphs
- Capture the main points
- Written in an engaging style
- Suitable for newsletter or blog use

Transcript:
{transcript}

Language: {language}

Generate the summary:
"""
        }

    async def generate_content(
        self,
        transcript: str,
        language_code: str = "en-US",
        content_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate all content types from a transcript.
        
        Args:
            transcript: The podcast transcript
            language_code: Language code for content generation
            content_options: Additional options for content generation
            
        Returns:
            Dict containing all generated content
        """
        try:
            logger.info(f"Starting content generation for {len(transcript)} character transcript")
            
            # Prepare generation parameters
            options = content_options or {}
            language = self._extract_language_from_code(language_code)
            
            # Generate all content types
            content = {}
            
            # Generate title
            content["title"] = await self._generate_title(transcript, language, options)
            
            # Generate description
            content["description"] = await self._generate_description(transcript, language, options)
            
            # Generate show notes
            content["show_notes"] = await self._generate_show_notes(transcript, language, options)
            
            # Generate social media content
            content["social_media"] = await self._generate_social_media(transcript, language, options)
            
            # Generate summary
            content["summary"] = await self._generate_summary(transcript, language, options)
            
            # Add metadata
            content["metadata"] = {
                "language": language,
                "language_code": language_code,
                "transcript_length": len(transcript),
                "word_count": len(transcript.split()),
                "generation_model": self._get_preferred_model(),
                "content_types": list(content.keys())
            }
            
            logger.info(f"Content generation completed with {len(content)} content types")
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise

    async def _generate_title(
        self,
        transcript: str,
        language: str,
        options: Dict[str, Any]
    ) -> str:
        """Generate episode title."""
        prompt = self.prompt_templates["title"].format(
            transcript=self._truncate_transcript(transcript, 3000),
            language=language,
            audience=options.get("target_audience", "general")
        )
        
        return await self._call_llm(prompt, max_tokens=50)

    async def _generate_description(
        self,
        transcript: str,
        language: str,
        options: Dict[str, Any]
    ) -> str:
        """Generate episode description."""
        prompt = self.prompt_templates["description"].format(
            transcript=self._truncate_transcript(transcript, 4000),
            language=language,
            style=options.get("show_style", "conversational")
        )
        
        return await self._call_llm(prompt, max_tokens=300)

    async def _generate_show_notes(
        self,
        transcript: str,
        language: str,
        options: Dict[str, Any]
    ) -> str:
        """Generate show notes."""
        prompt = self.prompt_templates["show_notes"].format(
            transcript=self._truncate_transcript(transcript, 5000),
            language=language,
            format=options.get("notes_format", "bullet_points")
        )
        
        return await self._call_llm(prompt, max_tokens=800)

    async def _generate_social_media(
        self,
        transcript: str,
        language: str,
        options: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate social media content."""
        prompt = self.prompt_templates["social_media"].format(
            transcript=self._truncate_transcript(transcript, 2000),
            language=language,
            voice=options.get("brand_voice", "friendly and professional")
        )
        
        response = await self._call_llm(prompt, max_tokens=400)
        
        # Parse the response to extract different social media formats
        # TODO: Implement better parsing logic
        return {
            "twitter": self._extract_twitter_post(response),
            "linkedin": self._extract_linkedin_post(response),
            "instagram": self._extract_instagram_post(response),
            "raw_response": response
        }

    async def _generate_summary(
        self,
        transcript: str,
        language: str,
        options: Dict[str, Any]
    ) -> str:
        """Generate episode summary."""
        prompt = self.prompt_templates["summary"].format(
            transcript=self._truncate_transcript(transcript, 4000),
            language=language
        )
        
        return await self._call_llm(prompt, max_tokens=250)

    async def _call_llm(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Call the configured LLM with the given prompt.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
            
        Returns:
            Generated text response
        """
        try:
            # Try Anthropic Claude first
            if self.anthropic_client:
                return await self._call_anthropic(prompt, max_tokens, temperature)
            
            # Fallback to Gemini
            elif self.gemini_client:
                return await self._call_gemini(prompt, max_tokens, temperature)
            
            else:
                # Return placeholder if no LLM available
                logger.warning("No LLM client available, returning placeholder")
                return f"[PLACEHOLDER CONTENT] - LLM not configured\nPrompt length: {len(prompt)} characters"
                
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise

    async def _call_anthropic(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Call Anthropic Claude API."""
        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",  # Use latest Claude model
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {str(e)}")
            raise

    async def _call_gemini(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Call Google Gemini API."""
        # TODO: Implement Gemini API calls
        logger.warning("Gemini API integration not yet implemented")
        raise NotImplementedError("Gemini API integration pending")

    def _extract_language_from_code(self, language_code: str) -> str:
        """Extract language name from language code."""
        # Convert language code (e.g., "en-US") to language name
        base_lang = language_code.split("-")[0]
        return self.supported_languages.get(base_lang, "English")

    def _truncate_transcript(self, transcript: str, max_chars: int) -> str:
        """Truncate transcript to fit within token limits."""
        if len(transcript) <= max_chars:
            return transcript
        
        # Truncate and add indicator
        truncated = transcript[:max_chars - 100]
        # Try to cut at a sentence boundary
        last_period = truncated.rfind(".")
        if last_period > max_chars * 0.7:  # Only if we don't lose too much
            truncated = truncated[:last_period + 1]
        
        truncated += "\n\n[Transcript truncated for processing...]"
        return truncated

    def _extract_twitter_post(self, response: str) -> str:
        """Extract Twitter post from LLM response."""
        # TODO: Implement better parsing logic
        lines = response.split("\n")
        for line in lines:
            if "twitter" in line.lower() or len(line.strip()) < 280:
                return line.strip()
        return response.split("\n")[0][:280]  # Fallback

    def _extract_linkedin_post(self, response: str) -> str:
        """Extract LinkedIn post from LLM response."""
        # TODO: Implement better parsing logic
        return response  # Placeholder

    def _extract_instagram_post(self, response: str) -> str:
        """Extract Instagram post from LLM response."""
        # TODO: Implement better parsing logic
        return response  # Placeholder

    def _get_preferred_model(self) -> str:
        """Get the name of the preferred/available model."""
        if self.anthropic_client:
            return "claude-3-sonnet"
        elif self.gemini_client:
            return "gemini-pro"
        else:
            return "none"

    async def generate_translations(
        self,
        content: Dict[str, Any],
        target_languages: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate translations of content for multiple languages.
        
        Args:
            content: Original content dictionary
            target_languages: List of language codes to translate to
            
        Returns:
            Dict mapping language codes to translated content
        """
        translations = {}
        
        for lang_code in target_languages:
            try:
                language = self._extract_language_from_code(lang_code)
                
                # Translate each content type
                translated_content = {}
                for content_type, text in content.items():
                    if content_type == "metadata":
                        continue  # Skip metadata
                    
                    if isinstance(text, str):
                        translated_content[content_type] = await self._translate_text(
                            text, language
                        )
                    elif isinstance(text, dict):
                        # Handle nested dictionaries (like social_media)
                        translated_content[content_type] = {}
                        for key, value in text.items():
                            if isinstance(value, str):
                                translated_content[content_type][key] = await self._translate_text(
                                    value, language
                                )
                
                translated_content["metadata"] = {
                    "source_language": content.get("metadata", {}).get("language", "unknown"),
                    "target_language": language,
                    "target_language_code": lang_code
                }
                
                translations[lang_code] = translated_content
                
            except Exception as e:
                logger.error(f"Translation failed for {lang_code}: {str(e)}")
                translations[lang_code] = {"error": str(e)}
        
        return translations

    async def _translate_text(self, text: str, target_language: str) -> str:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language name
            
        Returns:
            Translated text
        """
        prompt = f"""
Translate the following text to {target_language}. 
Maintain the style, tone, and formatting of the original.
If the text is already in {target_language}, return it unchanged.

Text to translate:
{text}

Translation:
"""
        
        return await self._call_llm(prompt, max_tokens=len(text) + 100)