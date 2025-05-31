#!/usr/bin/env python3
"""
Transcription Only Script

This script runs only the transcription part of the podcast workflow.
Use this to test transcription functionality step by step.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

from agents.transcription_agent import TranscriptionAgent
from agents.audio_processing_agent import AudioProcessingAgent


async def transcribe_only(audio_path: str, language_code: str = "ja-JP", process_audio: bool = True):
    """
    Run only the transcription step of the workflow.
    
    Args:
        audio_path: Path to the audio file to transcribe
        language_code: Language code for transcription (default: ja-JP for Japanese)
        process_audio: Whether to process audio first (recommended)
    """
    # Expand the path to handle ~ and relative paths
    audio_path = str(Path(audio_path).expanduser().resolve())
    
    if not Path(audio_path).exists():
        print(f"Error: Audio file not found: {audio_path}")
        return 1

    print(f"Starting transcription for: {audio_path}")
    print(f"Language: {language_code}")
    print(f"Process audio first: {process_audio}")
    print("-" * 50)

    # Initialize agents
    transcriber = TranscriptionAgent()
    
    processed_audio_path = audio_path
    
    if process_audio:
        print("Step 1: Processing audio for optimal transcription...")
        try:
            audio_processor = AudioProcessingAgent()
            audio_result = await audio_processor.process_audio(audio_path)
            processed_audio_path = audio_result["file_path"]
            print(f"✅ Audio processed: {processed_audio_path}")
            print(f"   Original size: {audio_result.get('original_size', 'Unknown')}")
            print(f"   Processed size: {audio_result.get('processed_size', 'Unknown')}")
            print(f"   Format: {audio_result.get('format', 'Unknown')}")
        except Exception as e:
            print(f"⚠️  Audio processing failed: {e}")
            print("   Continuing with original file...")
            processed_audio_path = audio_path
    
    print("\nStep 2: Transcribing audio...")
    try:
        # Transcribe the audio
        transcript_result = await transcriber.transcribe_audio(
            processed_audio_path, 
            language_code
        )
        
        print("✅ Transcription completed!")
        print("-" * 50)
        print("RESULTS:")
        print(f"Language detected: {transcript_result.get('language', language_code)}")
        print(f"Confidence: {transcript_result.get('confidence', 'N/A')}")
        print(f"Text length: {len(transcript_result['text'])} characters")
        print(f"Word count: {len(transcript_result['text'].split())}")
        print("-" * 50)
        print("TRANSCRIPT:")
        print(transcript_result['text'])
        print("-" * 50)
        
        # Save transcript to file
        output_file = Path(audio_path).stem + "_transcript.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Audio file: {audio_path}\n")
            f.write(f"Language: {transcript_result.get('language', language_code)}\n")
            f.write(f"Confidence: {transcript_result.get('confidence', 'N/A')}\n")
            f.write(f"Text length: {len(transcript_result['text'])} characters\n")
            f.write(f"Word count: {len(transcript_result['text'].split())}\n")
            f.write("-" * 50 + "\n")
            f.write(transcript_result['text'])
        
        print(f"💾 Transcript saved to: {output_file}")
        
        return 0

    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return 1


def main():
    """Main entry point for transcription-only script."""
    parser = argparse.ArgumentParser(description="Transcription Only - Test transcription step")
    parser.add_argument(
        "audio",
        help="Path to audio file (can use ~ for home directory)"
    )
    parser.add_argument(
        "--language",
        default="ja-JP",
        help="Language code for transcription (e.g., ja-JP, en-US, zh-CN)"
    )
    parser.add_argument(
        "--no-process",
        action="store_true",
        help="Skip audio processing step (use original file directly)"
    )

    args = parser.parse_args()

    # Run transcription only
    return asyncio.run(transcribe_only(
        args.audio, 
        args.language, 
        process_audio=not args.no_process
    ))


if __name__ == "__main__":
    sys.exit(main()) 