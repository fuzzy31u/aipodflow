# Podcast Configuration Guide

## Overview
The AI Podcast Flow system uses a configurable approach where all podcast-specific styling, formatting, and branding are defined in a JSON configuration file rather than hardcoded in the source code. This makes the system reusable for any podcast.

## Configuration Files

### `podcast_config.json` 
The main configuration file used by the system. Currently configured for momit.fm.

### `sample_podcast_config.json`
A template showing how to customize the configuration for your own podcast.

## Configuration Structure

### 1. `podcast_info`
Basic information about your podcast:
- `name`: Podcast name
- `concept`: Main concept/tagline
- `current_episode`: Current episode number
- `hashtag`: Main hashtag for social media
- `hosts`: Host information
- `target_audience`: Description of your audience
- `website`: Podcast website URL

### 2. `content_style`
General style preferences:
- `title_format`: How episode titles should be structured
- `title_separator`: Character used to separate topics in titles
- `description_length`: Target length for descriptions
- `summary_length`: Target length for summaries

### 3. `content_themes`
Array of main topic areas your podcast covers. These help the AI understand what content to focus on when generating titles and descriptions.

### 4. `format_examples`
Detailed formatting specifications:

#### `description_format`
- `structure`: Overall structure of episode descriptions
- `topic_format`: How individual topics should be formatted
- `example`: A real example showing the exact style you want

#### `show_notes_format`
- `structure`: Overall structure of show notes
- `title_format`: How episode titles appear in show notes
- `date_format`: Date formatting preference
- `topic_format`: How topics are listed
- `separator`: Visual separator between sections
- `feedback_section`: Template for feedback requests
- `credits_section`: Template for credits

## How to Customize

1. **Copy the sample config**: Start with `sample_podcast_config.json`
2. **Update podcast_info**: Fill in your podcast's basic information
3. **Define your style**: Set your preferences in `content_style`
4. **List your themes**: Add your main topic areas to `content_themes`
5. **Create examples**: Most importantly, provide real examples in `format_examples` showing exactly how you want content formatted
6. **Save as podcast_config.json**: The system will automatically load this file

## Example Usage

```bash
# The system automatically loads podcast_config.json
python demo.py your_transcript.txt

# Or specify a different config file in the code:
agent = ContentGenerationAgent(config_file="my_custom_config.json")
```

## Tips for Best Results

1. **Provide real examples**: The AI works best when given concrete examples of your desired formatting
2. **Be specific about style**: Instead of "casual tone", describe exactly what that means for your audience
3. **Include actual text samples**: Show the AI exactly how you want things formatted with real examples
4. **Test and iterate**: Try generating content and adjust your config based on the results

## Language Support

The system supports multiple languages. Set your content in the language you want (Japanese, English, etc.) and the AI will generate content in that language while following your formatting preferences. 