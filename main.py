#!/usr/bin/env python3
"""
Podcast Workflow Automation - Main Entry Point

This module serves as the main entry point for the podcast workflow automation system.
It can run as either a CLI tool or an HTTP server for Cloud Run deployment.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel

from agents.orchestrator_agent import OrchestratorAgent


class ProcessRequest(BaseModel):
    """Request model for processing audio via URL or file reference."""
    audio_url: Optional[str] = None
    audio_file_path: Optional[str] = None
    language_code: Optional[str] = "en-US"  # Default to English, support APAC languages


class ProcessResponse(BaseModel):
    """Response model for processing results."""
    success: bool
    message: str
    episode_id: Optional[str] = None
    transcript: Optional[str] = None
    generated_content: Optional[dict] = None


app = FastAPI(
    title="Podcast Workflow Automation",
    description="Automated podcast production pipeline from audio to published content",
    version="1.0.0"
)

# Initialize orchestrator agent
orchestrator = OrchestratorAgent()


@app.get("/")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy", "service": "podcast-workflow-automation"}


@app.post("/process", response_model=ProcessResponse)
async def process_podcast(
    audio_file: Optional[UploadFile] = File(None),
    request: Optional[ProcessRequest] = None
):
    """
    Process a podcast episode through the complete workflow.
    
    Accepts either an uploaded file or a request with audio URL/path.
    """
    try:
        # TODO: Handle file upload and save to temporary location
        if audio_file:
            # Save uploaded file temporarily
            temp_path = f"/tmp/{audio_file.filename}"
            with open(temp_path, "wb") as f:
                content = await audio_file.read()
                f.write(content)
            audio_path = temp_path
            language_code = "en-US"  # TODO: Auto-detect or accept as parameter
        elif request and request.audio_file_path:
            audio_path = request.audio_file_path
            language_code = request.language_code or "en-US"
        elif request and request.audio_url:
            # TODO: Download audio from URL
            audio_path = request.audio_url
            language_code = request.language_code or "en-US"
        else:
            raise HTTPException(status_code=400, detail="No audio source provided")

        # Run the orchestrator workflow
        result = await orchestrator.process_podcast_workflow(
            audio_path=audio_path,
            language_code=language_code
        )

        return ProcessResponse(
            success=True,
            message="Podcast processed successfully",
            episode_id=result.get("episode_id"),
            transcript=result.get("transcript"),
            generated_content=result.get("generated_content")
        )

    except Exception as e:
        return ProcessResponse(
            success=False,
            message=f"Processing failed: {str(e)}"
        )


async def run_cli(audio_path: str, language_code: str = "en-US"):
    """
    Run the podcast workflow via CLI.
    
    Args:
        audio_path: Path to the audio file to process
        language_code: Language code for transcription (default: en-US)
    """
    if not Path(audio_path).exists():
        print(f"Error: Audio file not found: {audio_path}")
        return 1

    print(f"Starting podcast workflow for: {audio_path}")
    print(f"Language: {language_code}")

    try:
        result = await orchestrator.process_podcast_workflow(
            audio_path=audio_path,
            language_code=language_code
        )

        print("\n=== Workflow Completed ===")
        print(f"Episode ID: {result.get('episode_id', 'N/A')}")
        print(f"Transcript length: {len(result.get('transcript', ''))} characters")
        print(f"Generated content: {result.get('generated_content', {}).keys()}")
        
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """Main entry point supporting both CLI and server modes."""
    parser = argparse.ArgumentParser(description="Podcast Workflow Automation")
    parser.add_argument(
        "--mode",
        choices=["cli", "server"],
        default="server",
        help="Run mode: CLI for local processing or server for HTTP API"
    )
    parser.add_argument(
        "--audio",
        help="Path to audio file (CLI mode only)"
    )
    parser.add_argument(
        "--language",
        default="en-US",
        help="Language code for transcription (e.g., ja-JP, zh-CN, en-US)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (server mode only)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", 8080)),
        help="Server port (server mode only)"
    )

    args = parser.parse_args()

    if args.mode == "cli":
        if not args.audio:
            print("Error: --audio is required in CLI mode")
            return 1
        
        # Run CLI mode
        return asyncio.run(run_cli(args.audio, args.language))
    
    else:
        # Run server mode
        print(f"Starting server on {args.host}:{args.port}")
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            log_level="info"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())