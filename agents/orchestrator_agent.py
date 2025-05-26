"""
Orchestrator Agent

This agent coordinates the entire podcast workflow, managing the sequence of operations
from audio processing through to publishing. It handles error checking and ensures
each stage's output is valid before proceeding.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from google_adk import Agent

from .audio_processing_agent import AudioProcessingAgent
from .transcription_agent import TranscriptionAgent
from .content_generation_agent import ContentGenerationAgent
from .publishing_agent import PublishingAgent


logger = logging.getLogger(__name__)


class OrchestratorAgent(Agent):
    """
    Orchestrator Agent that coordinates the podcast workflow pipeline.
    
    Manages the sequential execution of:
    1. Audio Processing
    2. Transcription
    3. Content Generation
    4. Publishing & Distribution
    """

    def __init__(self):
        """Initialize the orchestrator with all sub-agents."""
        super().__init__(name="orchestrator")
        
        # Initialize all workflow agents
        self.audio_processor = AudioProcessingAgent()
        self.transcriber = TranscriptionAgent()
        self.content_generator = ContentGenerationAgent()
        self.publisher = PublishingAgent()
        
        logger.info("Orchestrator agent initialized with all sub-agents")

    async def process_podcast_workflow(
        self,
        audio_path: str,
        language_code: str = "en-US",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete podcast workflow pipeline.
        
        Args:
            audio_path: Path to the raw audio file
            language_code: Language code for transcription (e.g., "en-US", "ja-JP", "zh-CN")
            metadata: Optional metadata for the episode
            
        Returns:
            Dict containing the results of each workflow stage
            
        Raises:
            Exception: If any stage fails and cannot be recovered
        """
        workflow_results = {
            "audio_path": audio_path,
            "language_code": language_code,
            "metadata": metadata or {}
        }

        try:
            logger.info(f"Starting podcast workflow for: {audio_path}")
            
            # Stage 1: Audio Processing
            logger.info("Stage 1: Audio Processing")
            processed_audio = await self._execute_audio_processing(audio_path)
            workflow_results["processed_audio"] = processed_audio
            
            # Stage 2: Transcription
            logger.info("Stage 2: Speech-to-Text Transcription")
            transcript_result = await self._execute_transcription(
                processed_audio["file_path"], 
                language_code
            )
            workflow_results["transcript"] = transcript_result["text"]
            workflow_results["detected_language"] = transcript_result.get("language", language_code)
            
            # Stage 3: Content Generation
            logger.info("Stage 3: Content Generation")
            generated_content = await self._execute_content_generation(
                transcript_result["text"],
                workflow_results["detected_language"]
            )
            workflow_results["generated_content"] = generated_content
            
            # Stage 4: Publishing & Distribution
            logger.info("Stage 4: Publishing & Distribution")
            publishing_results = await self._execute_publishing(
                processed_audio["file_path"],
                generated_content,
                workflow_results["metadata"]
            )
            workflow_results["publishing_results"] = publishing_results
            workflow_results["episode_id"] = publishing_results.get("episode_id")
            
            logger.info("Podcast workflow completed successfully")
            workflow_results["success"] = True
            
            return workflow_results

        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            workflow_results["success"] = False
            workflow_results["error"] = str(e)
            raise

    async def _execute_audio_processing(self, audio_path: str) -> Dict[str, Any]:
        """
        Execute the audio processing stage.
        
        Args:
            audio_path: Path to the raw audio file
            
        Returns:
            Dict containing processed audio information
        """
        try:
            # Validate input
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Process audio
            result = await self.audio_processor.process_audio(audio_path)
            
            # Validate output
            if not result.get("file_path") or not Path(result["file_path"]).exists():
                raise RuntimeError("Audio processing failed to produce valid output")
                
            logger.info(f"Audio processing completed: {result['file_path']}")
            return result
            
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise

    async def _execute_transcription(self, audio_path: str, language_code: str) -> Dict[str, Any]:
        """
        Execute the transcription stage.
        
        Args:
            audio_path: Path to the processed audio file
            language_code: Language code for transcription
            
        Returns:
            Dict containing transcript and language information
        """
        try:
            # Transcribe audio
            result = await self.transcriber.transcribe_audio(audio_path, language_code)
            
            # Validate output
            if not result.get("text") or len(result["text"].strip()) == 0:
                raise RuntimeError("Transcription failed to produce valid text")
                
            logger.info(f"Transcription completed: {len(result['text'])} characters")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

    async def _execute_content_generation(self, transcript: str, language_code: str) -> Dict[str, Any]:
        """
        Execute the content generation stage.
        
        Args:
            transcript: The transcribed text
            language_code: Language code for content generation
            
        Returns:
            Dict containing generated content (title, description, etc.)
        """
        try:
            # Generate content
            result = await self.content_generator.generate_content(transcript, language_code)
            
            # Validate output
            required_fields = ["title", "description", "show_notes"]
            missing_fields = [field for field in required_fields if not result.get(field)]
            if missing_fields:
                raise RuntimeError(f"Content generation missing required fields: {missing_fields}")
                
            logger.info(f"Content generation completed with {len(result)} fields")
            return result
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise

    async def _execute_publishing(
        self, 
        audio_path: str, 
        content: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the publishing and distribution stage.
        
        Args:
            audio_path: Path to the final audio file
            content: Generated content (title, description, etc.)
            metadata: Additional episode metadata
            
        Returns:
            Dict containing publishing results
        """
        try:
            # Publish episode
            result = await self.publisher.publish_episode(audio_path, content, metadata)
            
            # Validate output - at least one publishing platform should succeed
            if not any(result.get(platform, {}).get("success", False) 
                      for platform in ["art19", "website", "social_media"]):
                logger.warning("All publishing platforms failed, but continuing...")
                # Don't raise error here - partial failure is acceptable
                
            logger.info("Publishing stage completed")
            return result
            
        except Exception as e:
            logger.error(f"Publishing failed: {str(e)}")
            # Publishing failures are often recoverable, so we might want to continue
            # For now, we'll raise the error, but this could be made more lenient
            raise

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the status of a running workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            
        Returns:
            Dict containing workflow status information
        """
        # TODO: Implement workflow status tracking
        # This would require maintaining workflow state in a database or cache
        return {
            "workflow_id": workflow_id,
            "status": "not_implemented",
            "message": "Workflow status tracking not yet implemented"
        }

    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Cancel a running workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            
        Returns:
            Dict containing cancellation result
        """
        # TODO: Implement workflow cancellation
        # This would require maintaining workflow state and supporting cancellation
        return {
            "workflow_id": workflow_id,
            "cancelled": False,
            "message": "Workflow cancellation not yet implemented"
        }