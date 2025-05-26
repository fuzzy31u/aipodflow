"""
Transcription Agent

This agent handles speech-to-text conversion with support for multiple APAC languages.
It integrates with Google Cloud Speech-to-Text API and other ASR services.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from google_adk import Agent
from google.cloud import speech


logger = logging.getLogger(__name__)


class TranscriptionAgent(Agent):
    """
    Transcription Agent for converting audio to text.
    
    Supports multiple APAC languages and can integrate with various
    speech recognition services.
    """

    def __init__(self):
        """Initialize the transcription agent."""
        super().__init__(name="transcriber")
        
        # Supported APAC language codes
        self.supported_languages = {
            "en-US": "English (US)",
            "en-AU": "English (Australia)",
            "ja-JP": "Japanese",
            "zh-CN": "Chinese (Mandarin, Simplified)",
            "zh-TW": "Chinese (Traditional)",
            "ko-KR": "Korean",
            "th-TH": "Thai",
            "vi-VN": "Vietnamese",
            "id-ID": "Indonesian",
            "ms-MY": "Malay",
            "tl-PH": "Filipino",
            "hi-IN": "Hindi",
            "ta-IN": "Tamil",
            "te-IN": "Telugu",
            "bn-IN": "Bengali"
        }
        
        # Initialize Google Cloud Speech client
        self.speech_client = None
        self._initialize_speech_client()
        
        logger.info(f"Transcription agent initialized with {len(self.supported_languages)} languages")

    def _initialize_speech_client(self):
        """Initialize Google Cloud Speech client."""
        try:
            # TODO: Ensure Google Cloud credentials are properly configured
            # This should use Application Default Credentials or service account key
            self.speech_client = speech.SpeechClient()
            logger.info("Google Cloud Speech client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Cloud Speech client: {str(e)}")
            logger.warning("Transcription will use fallback methods")

    async def transcribe_audio(
        self,
        audio_path: str,
        language_code: str = "en-US",
        transcription_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to the audio file
            language_code: Language code for transcription
            transcription_options: Additional transcription options
            
        Returns:
            Dict containing transcript and metadata
        """
        try:
            logger.info(f"Starting transcription for: {audio_path} (language: {language_code})")
            
            # Validate inputs
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            if language_code not in self.supported_languages:
                logger.warning(f"Language {language_code} not in supported list, but trying anyway")
            
            # Choose transcription method
            if self.speech_client:
                result = await self._transcribe_with_google_cloud(
                    audio_path, language_code, transcription_options or {}
                )
            else:
                # Fallback to alternative transcription method
                result = await self._transcribe_with_fallback(
                    audio_path, language_code, transcription_options or {}
                )
            
            # Post-process transcript
            result = self._post_process_transcript(result)
            
            logger.info(f"Transcription completed: {len(result['text'])} characters")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

    async def _transcribe_with_google_cloud(
        self,
        audio_path: str,
        language_code: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Google Cloud Speech-to-Text.
        
        Args:
            audio_path: Path to the audio file
            language_code: Language code for transcription
            options: Additional transcription options
            
        Returns:
            Dict containing transcript and metadata
        """
        try:
            # Read audio file
            with open(audio_path, "rb") as audio_file:
                audio_content = audio_file.read()
            
            # Configure audio settings
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Configure recognition settings
            config = speech.RecognitionConfig(
                encoding=self._get_audio_encoding(audio_path),
                sample_rate_hertz=options.get("sample_rate", 16000),
                language_code=language_code,
                alternative_language_codes=options.get("alternative_languages", []),
                enable_automatic_punctuation=True,
                enable_speaker_diarization=options.get("speaker_diarization", False),
                diarization_speaker_count=options.get("speaker_count", 2),
                enable_word_time_offsets=True,
                enable_word_confidence=True,
                use_enhanced=True,
                model=options.get("model", "latest_long")  # Optimized for longer audio
            )
            
            # Handle long audio files (>1 minute) with long_running_recognize
            file_size_mb = Path(audio_path).stat().st_size / (1024 * 1024)
            
            if file_size_mb > 10:  # Use async for larger files
                logger.info("Using long-running recognition for large file")
                operation = self.speech_client.long_running_recognize(
                    config=config, audio=audio
                )
                response = operation.result(timeout=3600)  # 1 hour timeout
            else:
                logger.info("Using synchronous recognition")
                response = self.speech_client.recognize(config=config, audio=audio)
            
            # Process response
            return self._process_google_cloud_response(response, language_code)
            
        except Exception as e:
            logger.error(f"Google Cloud transcription failed: {str(e)}")
            raise

    def _get_audio_encoding(self, audio_path: str) -> speech.RecognitionConfig.AudioEncoding:
        """
        Determine audio encoding from file extension.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Google Cloud Speech audio encoding enum
        """
        extension = Path(audio_path).suffix.lower()
        
        encoding_map = {
            ".wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            ".flac": speech.RecognitionConfig.AudioEncoding.FLAC,
            ".mp3": speech.RecognitionConfig.AudioEncoding.MP3,
            ".m4a": speech.RecognitionConfig.AudioEncoding.MP3,  # Treat as MP3
            ".ogg": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            ".webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS
        }
        
        return encoding_map.get(extension, speech.RecognitionConfig.AudioEncoding.LINEAR16)

    def _process_google_cloud_response(
        self,
        response,
        language_code: str
    ) -> Dict[str, Any]:
        """
        Process Google Cloud Speech API response.
        
        Args:
            response: API response object
            language_code: Language code used for transcription
            
        Returns:
            Dict containing processed transcript data
        """
        # Combine all alternatives to get the best transcript
        transcript_parts = []
        confidence_scores = []
        word_details = []
        
        for result in response.results:
            if result.alternatives:
                best_alternative = result.alternatives[0]
                transcript_parts.append(best_alternative.transcript)
                confidence_scores.append(best_alternative.confidence)
                
                # Extract word-level details if available
                for word in getattr(best_alternative, 'words', []):
                    word_details.append({
                        "word": word.word,
                        "start_time": word.start_time.total_seconds(),
                        "end_time": word.end_time.total_seconds(),
                        "confidence": getattr(word, 'confidence', 0.0)
                    })
        
        # Combine transcript parts
        full_transcript = " ".join(transcript_parts)
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # TODO: Detect actual language if different from requested
        detected_language = language_code  # Google Cloud can provide this info
        
        return {
            "text": full_transcript,
            "language": detected_language,
            "confidence": overall_confidence,
            "word_count": len(full_transcript.split()),
            "duration_seconds": word_details[-1]["end_time"] if word_details else 0,
            "word_details": word_details,
            "provider": "google_cloud_speech"
        }

    async def _transcribe_with_fallback(
        self,
        audio_path: str,
        language_code: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback transcription method (e.g., using Whisper or other services).
        
        Args:
            audio_path: Path to the audio file
            language_code: Language code for transcription
            options: Additional transcription options
            
        Returns:
            Dict containing transcript and metadata
        """
        # TODO: Implement fallback transcription using Whisper or other services
        logger.warning("Using fallback transcription - not yet implemented")
        
        # For now, return a placeholder response
        return {
            "text": f"[PLACEHOLDER TRANSCRIPT] Audio file: {Path(audio_path).name}",
            "language": language_code,
            "confidence": 0.5,
            "word_count": 10,
            "duration_seconds": 60,
            "word_details": [],
            "provider": "fallback_placeholder"
        }

    def _post_process_transcript(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process the transcript for quality improvements.
        
        Args:
            transcript_data: Raw transcript data
            
        Returns:
            Enhanced transcript data
        """
        text = transcript_data.get("text", "")
        
        # Basic text cleaning
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # TODO: Add more sophisticated post-processing:
        # - Fix common transcription errors
        # - Add proper capitalization
        # - Format numbers and dates
        # - Handle APAC language-specific formatting
        
        # Update the transcript data
        transcript_data["text"] = text
        transcript_data["processed"] = True
        
        return transcript_data

    async def batch_transcribe(
        self,
        audio_files: List[str],
        language_codes: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribe multiple audio files in batch.
        
        Args:
            audio_files: List of audio file paths
            language_codes: List of language codes (one per file, or None for default)
            options: Transcription options
            
        Returns:
            List of transcription results
        """
        results = []
        
        # Prepare language codes
        if language_codes is None:
            language_codes = ["en-US"] * len(audio_files)
        elif len(language_codes) == 1:
            language_codes = language_codes * len(audio_files)
        
        # Process each file
        for i, audio_path in enumerate(audio_files):
            try:
                language_code = language_codes[i] if i < len(language_codes) else "en-US"
                result = await self.transcribe_audio(audio_path, language_code, options)
                result["file_index"] = i
                result["file_path"] = audio_path
                results.append(result)
            except Exception as e:
                logger.error(f"Batch transcription failed for {audio_path}: {str(e)}")
                results.append({
                    "file_index": i,
                    "file_path": audio_path,
                    "error": str(e),
                    "success": False
                })
        
        return results

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get the list of supported languages.
        
        Returns:
            Dict mapping language codes to language names
        """
        return self.supported_languages.copy()

    async def detect_language(self, audio_path: str) -> Dict[str, Any]:
        """
        Detect the language of an audio file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dict containing detected language information
        """
        # TODO: Implement language detection
        # This could use Google Cloud's language detection or other services
        logger.info("Language detection not yet implemented")
        
        return {
            "detected_language": "unknown",
            "confidence": 0.0,
            "alternative_languages": [],
            "method": "not_implemented"
        }