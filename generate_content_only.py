#!/usr/bin/env python3
"""
Content Generation Only Script

This script runs only the content generation part of the podcast workflow.
Use this to test content generation functionality step by step.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

from agents.content_generation_agent import ContentGenerationAgent


async def generate_content_only(transcript_file: str, language_code: str = "ja-JP"):
    """
    Run only the content generation step of the workflow.
    
    Args:
        transcript_file: Path to the transcript file
        language_code: Language code for content generation (default: ja-JP for Japanese)
    """
    # Expand the path to handle ~ and relative paths
    transcript_file = str(Path(transcript_file).expanduser().resolve())
    
    if not Path(transcript_file).exists():
        print(f"Error: Transcript file not found: {transcript_file}")
        return 1

    # Read the transcript
    try:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract just the transcript text (skip metadata)
        lines = content.split('\n')
        transcript_start = False
        transcript_lines = []
        
        for line in lines:
            if line.startswith('--------------------------------------------------'):
                transcript_start = True
                continue
            if transcript_start:
                transcript_lines.append(line)
        
        transcript = '\n'.join(transcript_lines).strip()
        
        if not transcript:
            print("Error: No transcript content found in file")
            return 1
            
    except Exception as e:
        print(f"Error reading transcript file: {e}")
        return 1

    print(f"Starting content generation for transcript: {transcript_file}")
    print(f"Language: {language_code}")
    print(f"Transcript length: {len(transcript)} characters")
    print("-" * 60)

    # Initialize content generation agent
    content_generator = ContentGenerationAgent()
    
    print("Step 1: Generating content with LLM...")
    try:
        # Generate content
        content_result = await content_generator.generate_content(
            transcript, 
            language_code
        )
        
        print("✅ Content generation completed!")
        print("=" * 60)
        
        # Display results
        if content_result.get('title'):
            print("📝 TITLE:")
            print(content_result['title'])
            print()
        
        if content_result.get('description'):
            print("📖 DESCRIPTION:")
            print(content_result['description'])
            print()
        
        if content_result.get('show_notes'):
            print("📋 SHOW NOTES:")
            print(content_result['show_notes'])
            print()
        
        if content_result.get('summary'):
            print("📄 SUMMARY:")
            print(content_result['summary'])
            print()
        
        if content_result.get('social_media'):
            print("📱 SOCIAL MEDIA:")
            social = content_result['social_media']
            
            if social.get('twitter'):
                print("🐦 Twitter/X:")
                print(social['twitter'])
                print()
            
            if social.get('linkedin'):
                print("💼 LinkedIn:")
                print(social['linkedin'])
                print()
            
            if social.get('instagram'):
                print("📸 Instagram:")
                print(social['instagram'])
                print()
        
        print("=" * 60)
        
        # Save results to file
        output_file = Path(transcript_file).stem.replace('_transcript', '') + "_content.json"
        
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content_result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Content saved to: {output_file}")
        
        return 0

    except Exception as e:
        print(f"❌ Content generation failed: {e}")
        
        # Show what went wrong
        print("\n🔍 Debugging information:")
        print(f"Anthropic API key available: {'ANTHROPIC_API_KEY' in os.environ}")
        print(f"Google Cloud project: {os.getenv('GOOGLE_CLOUD_PROJECT', 'Not set')}")
        
        if 'ANTHROPIC_API_KEY' not in os.environ:
            print("\n💡 To enable content generation:")
            print("1. Get an Anthropic API key from: https://console.anthropic.com/")
            print("2. Set it as environment variable: export ANTHROPIC_API_KEY=your_key_here")
            print("3. Or add it to your .env file")
        
        return 1


def main():
    """Main entry point for content generation script."""
    parser = argparse.ArgumentParser(description="Content Generation Only - Test content generation step")
    parser.add_argument(
        "transcript",
        nargs='?',
        default="momitfm81_riverside_edited_normal_transcript.txt",
        help="Path to transcript file (default: use the transcript we just created)"
    )
    parser.add_argument(
        "--language",
        default="ja-JP",
        help="Language code for content generation (e.g., ja-JP, en-US, zh-CN)"
    )

    args = parser.parse_args()

    # Run content generation only
    return asyncio.run(generate_content_only(
        args.transcript, 
        args.language
    ))


if __name__ == "__main__":
    sys.exit(main()) 