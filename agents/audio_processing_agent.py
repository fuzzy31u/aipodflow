"""
Audio Processing Agent

This agent handles audio file processing, including format conversion, audio enhancement,
noise reduction, and preparation for transcription and publishing.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
import asyncio
from pathlib import Path
import tempfile
import os

# Audio processing libraries
from pydub import AudioSegment
import librosa
import numpy as np

from google.adk import Agent


logger = logging.getLogger(__name__)


class AudioProcessingAgent(Agent):
    """
    Audio Processing Agent that handles file format conversion, audio enhancement,
    and preparation for both transcription and publishing workflows.
    
    Handles all audio editing and processing tasks to prepare raw audio
    for transcription and final publishing.
    """
    
    # Define pydantic model fields
    target_format: str = "wav"  # Standard format for transcription
    target_sample_rate: int = 16000  # Standard for speech recognition
    target_channels: int = 1  # Mono for speech
    noise_threshold: int = -60  # dB threshold for silence removal
    normalize_target_db: int = -20  # Target volume level

    def __init__(self, **data):
        """Initialize the audio processing agent."""
        super().__init__(name="audio_processor", **data)
        logger.info("Audio processing agent initialized")

    async def process_audio(
        self,
        audio_path: str,
        output_dir: Optional[str] = None,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process raw audio file through the complete audio pipeline.
        
        Args:
            audio_path: Path to the input audio file
            output_dir: Directory for output files (uses temp if None)
            processing_options: Optional parameters for processing
            
        Returns:
            Dict containing processed audio information
        """
        try:
            logger.info(f"Starting audio processing for: {audio_path}")
            
            # Validate input file
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Set up output directory
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix="podcast_audio_")
            else:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Load audio file
            audio = self._load_audio(audio_path)
            
            # Apply processing pipeline
            processed_audio = await self._apply_processing_pipeline(
                audio, 
                processing_options or {}
            )
            
            # Save processed audio
            output_path = self._save_processed_audio(processed_audio, output_dir, audio_path)
            
            # Generate processing report
            result = {
                "file_path": output_path,
                "original_path": audio_path,
                "duration_seconds": len(processed_audio) / 1000,
                "sample_rate": processed_audio.frame_rate,
                "channels": processed_audio.channels,
                "format": self.target_format,
                "file_size_mb": Path(output_path).stat().st_size / (1024 * 1024),
                "processing_applied": []  # TODO: Track applied processing steps
            }
            
            logger.info(f"Audio processing completed: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise

    def _load_audio(self, audio_path: str) -> AudioSegment:
        """
        Load audio file using pydub with format detection.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            AudioSegment object
        """
        try:
            # Try to load with automatic format detection
            audio = AudioSegment.from_file(audio_path)
            logger.info(f"Loaded audio: {len(audio)}ms, {audio.frame_rate}Hz, {audio.channels} channels")
            return audio
            
        except Exception as e:
            logger.error(f"Failed to load audio file: {str(e)}")
            raise

    async def _apply_processing_pipeline(
        self,
        audio: AudioSegment,
        options: Dict[str, Any]
    ) -> AudioSegment:
        """
        Apply the complete audio processing pipeline.
        
        Args:
            audio: Input audio segment
            options: Processing options
            
        Returns:
            Processed audio segment
        """
        processed = audio
        
        # Step 1: Convert to standard format (mono, target sample rate)
        processed = self._standardize_format(processed)
        
        # Step 2: Remove silence (optional)
        if options.get("remove_silence", True):
            processed = self._remove_silence(processed)
        
        # Step 3: Normalize volume
        if options.get("normalize_volume", True):
            processed = self._normalize_volume(processed)
        
        # Step 4: Add intro/outro (if provided)
        if options.get("intro_path"):
            processed = self._add_intro(processed, options["intro_path"])
        if options.get("outro_path"):
            processed = self._add_outro(processed, options["outro_path"])
        
        # Step 5: Apply noise reduction (TODO: implement advanced noise reduction)
        if options.get("noise_reduction", False):
            processed = await self._apply_noise_reduction(processed)
        
        # Step 6: Final format conversion
        processed = self._final_format_conversion(processed)
        
        return processed

    def _standardize_format(self, audio: AudioSegment) -> AudioSegment:
        """
        Convert audio to standard format for processing.
        
        Args:
            audio: Input audio segment
            
        Returns:
            Standardized audio segment
        """
        # Convert to mono
        if audio.channels > 1:
            audio = audio.set_channels(self.target_channels)
            logger.info("Converted to mono")
        
        # Set target sample rate
        if audio.frame_rate != self.target_sample_rate:
            audio = audio.set_frame_rate(self.target_sample_rate)
            logger.info(f"Resampled to {self.target_sample_rate}Hz")
        
        return audio

    def _remove_silence(self, audio: AudioSegment) -> AudioSegment:
        """
        Remove silence from beginning and end of audio.
        
        Args:
            audio: Input audio segment
            
        Returns:
            Audio with silence removed
        """
        try:
            from pydub.silence import detect_leading_silence
            
            # Detect leading silence
            start_trim = detect_leading_silence(audio, silence_threshold=self.noise_threshold)
            
            # Detect trailing silence by reversing the audio
            end_trim = detect_leading_silence(audio.reverse(), silence_threshold=self.noise_threshold)
            
            # Trim the audio
            duration = len(audio)
            trimmed = audio[start_trim:duration-end_trim]
            
            if len(trimmed) < len(audio):
                logger.info(f"Removed {(len(audio) - len(trimmed)) / 1000:.1f}s of silence")
            
            return trimmed if len(trimmed) > 0 else audio
        
        except Exception as e:
            logger.warning(f"Silence removal failed: {str(e)}, skipping")
            return audio

    def _normalize_volume(self, audio: AudioSegment) -> AudioSegment:
        """
        Normalize audio volume to target level.
        
        Args:
            audio: Input audio segment
            
        Returns:
            Volume-normalized audio
        """
        try:
            # Get current peak volume
            current_db = audio.dBFS
            
            # Calculate adjustment needed
            adjustment = self.normalize_target_db - current_db
            
            # Apply volume adjustment
            normalized = audio + adjustment
            
            logger.info(f"Volume normalized: {current_db:.1f}dB → {normalized.dBFS:.1f}dB")
            return normalized
        
        except Exception as e:
            logger.warning(f"Volume normalization failed: {str(e)}, skipping")
            return audio

    def _add_intro(self, audio: AudioSegment, intro_path: str) -> AudioSegment:
        """
        Add intro audio to the beginning.
        
        Args:
            audio: Main audio segment
            intro_path: Path to intro audio file
            
        Returns:
            Audio with intro prepended
        """
        try:
            if Path(intro_path).exists():
                intro = AudioSegment.from_file(intro_path)
                # Match format to main audio
                intro = intro.set_frame_rate(audio.frame_rate).set_channels(audio.channels)
                combined = intro + audio
                logger.info(f"Added intro: {len(intro)}ms")
                return combined
            else:
                logger.warning(f"Intro file not found: {intro_path}")
                return audio
        
        except Exception as e:
            logger.warning(f"Failed to add intro: {str(e)}")
            return audio

    def _add_outro(self, audio: AudioSegment, outro_path: str) -> AudioSegment:
        """
        Add outro audio to the end.
        
        Args:
            audio: Main audio segment
            outro_path: Path to outro audio file
            
        Returns:
            Audio with outro appended
        """
        try:
            if Path(outro_path).exists():
                outro = AudioSegment.from_file(outro_path)
                # Match format to main audio
                outro = outro.set_frame_rate(audio.frame_rate).set_channels(audio.channels)
                combined = audio + outro
                logger.info(f"Added outro: {len(outro)}ms")
                return combined
            else:
                logger.warning(f"Outro file not found: {outro_path}")
                return audio
        
        except Exception as e:
            logger.warning(f"Failed to add outro: {str(e)}")
            return audio

    async def _apply_noise_reduction(self, audio: AudioSegment) -> AudioSegment:
        """
        Apply noise reduction to audio.
        
        Args:
            audio: Input audio segment
            
        Returns:
            Noise-reduced audio
        """
        # TODO: Implement advanced noise reduction using librosa or similar
        # For now, return the original audio
        logger.info("Advanced noise reduction not yet implemented")
        return audio

    def _final_format_conversion(self, audio: AudioSegment) -> AudioSegment:
        """
        Apply final format conversion for output.
        
        Args:
            audio: Input audio segment
            
        Returns:
            Final formatted audio
        """
        # Ensure final format matches target specifications
        if audio.frame_rate != self.target_sample_rate:
            audio = audio.set_frame_rate(self.target_sample_rate)
        
        if audio.channels != self.target_channels:
            audio = audio.set_channels(self.target_channels)
        
        return audio

    def _save_processed_audio(
        self,
        audio: AudioSegment,
        output_dir: str,
        original_path: str
    ) -> str:
        """
        Save processed audio to file.
        
        Args:
            audio: Processed audio segment
            output_dir: Output directory
            original_path: Original file path (for naming)
            
        Returns:
            Path to saved file
        """
        # Generate output filename
        original_name = Path(original_path).stem
        output_filename = f"{original_name}_processed.{self.target_format}"
        output_path = str(Path(output_dir) / output_filename)
        
        # Export audio with appropriate parameters
        audio.export(
            output_path,
            format=self.target_format,
            parameters=["-ac", str(self.target_channels), "-ar", str(self.target_sample_rate)]
        )
        
        logger.info(f"Saved processed audio: {output_path}")
        return output_path

    async def batch_process_audio(
        self,
        audio_paths: List[str],
        output_dir: str,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple audio files in batch.
        
        Args:
            audio_paths: List of audio file paths
            output_dir: Output directory for processed files
            processing_options: Processing options to apply to all files
            
        Returns:
            List of processing results
        """
        results = []
        
        for audio_path in audio_paths:
            try:
                result = await self.process_audio(audio_path, output_dir, processing_options)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch processing failed for {audio_path}: {str(e)}")
                results.append({
                    "file_path": audio_path,
                    "error": str(e),
                    "success": False
                })
        
        return results