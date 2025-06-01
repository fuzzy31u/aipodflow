# Content Generation Agent - Configuration Guide

## Overview

The Content Generation Agent now uses a **configurable, external JSON system** that:
- ✅ **Eliminates hallucination** by focusing on actual transcript content
- ✅ **Makes the system reusable** for any podcast
- ✅ **Separates content from code** for easy customization

## Quick Start

### 1. **Create Your Podcast Configuration**

Copy `podcast_config.json` and customize it for your podcast:

```bash
cp podcast_config.json my_podcast_config.json
```

### 2. **Run Content Generation**

```bash
# Use default config (podcast_config.json)
python generate_content_only.py transcript.txt

# Use custom config
python -c "
import sys; sys.path.append('.')
from agents.content_generation_agent import ContentGenerationAgent
import asyncio

async def generate():
    agent = ContentGenerationAgent(config_file='my_podcast_config.json')
    # ... rest of generation code
"
```

## Configuration File Structure

### Required Sections:

#### **podcast_info**
```json
{
  "podcast_info": {
    "name": "Your Podcast Name",
    "concept": "Your podcast concept/tagline",
    "current_episode": 42,
    "hashtag": "#YourHashtag",
    "feedback_hashtag": "#YourFeedbackTag",
    "hosts": "Host description",
    "target_audience": "Your target audience",
    "website": "https://yourwebsite.com",
    "feedback_form": "How people can give feedback"
  }
}
```

#### **content_style**
```json
{
  "content_style": {
    "title_format": "Topic1 / Topic2 / Topic3",
    "title_separator": " / ",
    "title_max_topics": 3,
    "title_language_mix": "Language style description",
    "description_tone": "Tone for descriptions",
    "description_length": "Character count range",
    "show_notes_format": "Format structure",
    "summary_length": "Summary length requirement"
  }
}
```

#### **content_themes**
```json
{
  "content_themes": [
    "Main topic area 1",
    "Main topic area 2", 
    "Main topic area 3"
  ]
}
```

#### **format_examples**
```json
{
  "format_examples": {
    "title_style": "Style guidance for titles",
    "description_style": "Style guidance for descriptions",
    "show_notes_style": "Style guidance for show notes",
    "social_media_style": "Style guidance for social posts"
  }
}
```

## Anti-Hallucination Features

### ✅ **What the System Now Does:**
- **Extract ONLY actual topics** from the transcript
- **Use real quotes and insights** discussed in the episode
- **Follow your style/format** without creating fictional content
- **Base all content on transcript** rather than making assumptions

### ✅ **Prompt Engineering:**
- Clear instructions: "Extract ONLY actual topics discussed"
- Emphasis: "Do NOT create fictional content"
- Focus: "Base content ONLY on actual transcript content"

## Example Configurations

### **momit.fm Style (Japanese + English mix)**
```json
{
  "podcast_info": {
    "name": "momit.fm",
    "concept": "「子育てをテクノロジーでハッピーに🌈」",
    "title_language_mix": "Japanese with English tech terms"
  }
}
```

### **Professional Tech Podcast**
```json
{
  "podcast_info": {
    "name": "Tech Talk Weekly",
    "concept": "Weekly discussions on emerging technology trends",
    "title_language_mix": "English with technical terminology"
  }
}
```

## Usage in Code

### **Basic Usage:**
```python
from agents.content_generation_agent import ContentGenerationAgent

# Use default config
agent = ContentGenerationAgent()

# Use custom config
agent = ContentGenerationAgent(config_file="my_podcast_config.json")

# Generate content
content = await agent.generate_content(transcript, language_code="ja-JP")
```

### **Advanced Usage:**
```python
# Custom options per generation
content_options = {
    "max_title_length": 100,
    "include_timestamps": True,
    "social_platforms": ["twitter", "linkedin"]
}

content = await agent.generate_content(
    transcript=transcript_text,
    language_code="ja-JP", 
    content_options=content_options
)
```

### **Model Configuration:**
The system will automatically try:
1. **Vertex AI Gemini** (primary) - Latest models like `gemini-2.0-flash-001`
2. **Anthropic Claude** (fallback) - If `ANTHROPIC_API_KEY` is provided
3. **Basic generation** (last resort) - If no LLM models are available

## For Other Podcasters

### **Step 1: Copy Template**
```bash
cp demo_podcast_config.json your_podcast_config.json
```

### **Step 2: Customize Your Config**
- Update `podcast_info` with your podcast details
- Adjust `content_style` to match your format preferences
- Set `content_themes` to your topic areas
- Customize `format_examples` for your style

### **Step 3: Test Generation**
```bash
python generate_content_only.py your_transcript.txt
```

The system will automatically load `podcast_config.json` by default, or you can specify a custom config file.

## Benefits

### **For You (momit.fm):**
- ✅ No more hallucinated content
- ✅ Consistent with your established style
- ✅ Focuses on actual episode content
- ✅ Maintains your Japanese + English tech mix

### **For Other Podcasters:**
- ✅ Completely customizable for any podcast format
- ✅ No hard-coded content - purely configuration-driven
- ✅ Easy to maintain and update
- ✅ Professional, non-hallucinating output

## Troubleshooting

### **Config File Not Found:**
- System will use default generic configuration
- Check file path and ensure JSON is valid

### **Generated Content Too Generic:**
- Add more specific `content_themes`
- Refine `format_examples` descriptions
- Adjust `content_style` parameters

### **Hallucination Issues:**
- Verify transcript quality and length
- Check if LLM model is working properly
- Review prompt templates for clarity 