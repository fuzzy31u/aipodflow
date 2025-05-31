"""
Publishing Agent

This agent handles the publishing of podcast episodes and related content to various
platforms including podcast hosting services, social media, and content management systems.
"""

import logging
from typing import Dict, Any, Optional, List
import json
import asyncio
from pathlib import Path
import os

from google.adk import Agent

# Import platform-specific connectors
from connectors.art19_api import Art19Connector
from connectors.vercel_api import VercelConnector
from connectors.twitter_api import TwitterConnector


logger = logging.getLogger(__name__)


class PublishingAgent(Agent):
    """
    Publishing Agent that handles distribution of podcast episodes and content.
    
    Manages publishing to podcast platforms, websites, and social media channels
    with support for scheduling and multi-platform coordination.
    """
    
    # Define pydantic model fields
    art19_connector: Optional[Any] = None
    vercel_connector: Optional[Any] = None
    twitter_connector: Optional[Any] = None
    auto_publish: bool = False
    schedule_enabled: bool = False
    publishing_config: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        """Initialize the publishing agent."""
        super().__init__(name="publisher", **data)
        
        # Initialize platform connectors
        self._initialize_connectors()
        
        logger.info("Publishing agent initialized")

    def _initialize_connectors(self):
        """Initialize all platform connectors."""
        # Initialize publishing configuration
        self.publishing_config = {
            "art19": {
                "enabled": os.getenv("ART19_ENABLED", "true").lower() == "true",
                "series_id": os.getenv("ART19_SERIES_ID"),
                "auto_publish": os.getenv("ART19_AUTO_PUBLISH", "false").lower() == "true"
            },
            "website": {
                "enabled": os.getenv("WEBSITE_ENABLED", "true").lower() == "true",
                "deploy_hook": os.getenv("VERCEL_DEPLOY_HOOK"),
                "api_endpoint": os.getenv("WEBSITE_API_ENDPOINT")
            },
            "social_media": {
                "enabled": os.getenv("SOCIAL_MEDIA_ENABLED", "true").lower() == "true",
                "platforms": ["twitter"],
                "auto_post": os.getenv("SOCIAL_AUTO_POST", "false").lower() == "true"
            }
        }
        
        try:
            self.art19_connector = Art19Connector()
            logger.info("Art19 connector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Art19 connector: {e}")
            self.art19_connector = None
            
        try:
            self.vercel_connector = VercelConnector()
            logger.info("Vercel connector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Vercel connector: {e}")
            self.vercel_connector = None
            
        try:
            self.twitter_connector = TwitterConnector()
            logger.info("Twitter connector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Twitter connector: {e}")
            self.twitter_connector = None

    async def publish_episode(
        self,
        audio_path: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Publish episode across all configured platforms.
        
        Args:
            audio_path: Path to the final audio file
            content: Generated content (title, description, etc.)
            metadata: Additional episode metadata
            
        Returns:
            Dict containing publishing results for each platform
        """
        try:
            logger.info(f"Starting episode publishing for: {audio_path}")
            
            # Prepare episode data
            episode_data = self._prepare_episode_data(audio_path, content, metadata or {})
            
            # Publishing results
            results = {
                "episode_id": episode_data.get("episode_id"),
                "published_platforms": [],
                "failed_platforms": [],
                "details": {}
            }
            
            # List of publishing tasks
            publishing_tasks = []
            
            # Art19 Publishing
            if self.publishing_config["art19"]["enabled"]:
                publishing_tasks.append(self._publish_to_art19(episode_data))
            
            # Website Publishing
            if self.publishing_config["website"]["enabled"]:
                publishing_tasks.append(self._publish_to_website(episode_data))
            
            # Social Media Publishing
            if self.publishing_config["social_media"]["enabled"]:
                publishing_tasks.append(self._publish_to_social_media(episode_data))
            
            # Execute all publishing tasks concurrently
            if publishing_tasks:
                task_results = await asyncio.gather(*publishing_tasks, return_exceptions=True)
                
                # Process results
                platform_names = []
                if self.publishing_config["art19"]["enabled"]:
                    platform_names.append("art19")
                if self.publishing_config["website"]["enabled"]:
                    platform_names.append("website")
                if self.publishing_config["social_media"]["enabled"]:
                    platform_names.append("social_media")
                
                for i, result in enumerate(task_results):
                    platform = platform_names[i] if i < len(platform_names) else f"platform_{i}"
                    
                    if isinstance(result, Exception):
                        logger.error(f"Publishing to {platform} failed: {str(result)}")
                        results["failed_platforms"].append(platform)
                        results["details"][platform] = {
                            "success": False,
                            "error": str(result)
                        }
                    else:
                        if result.get("success", False):
                            results["published_platforms"].append(platform)
                        else:
                            results["failed_platforms"].append(platform)
                        results["details"][platform] = result
            
            # Generate overall episode URL if Art19 was successful
            if "art19" in results["published_platforms"]:
                art19_result = results["details"].get("art19", {})
                if art19_result.get("episode_url"):
                    results["episode_url"] = art19_result["episode_url"]
            
            success_rate = len(results["published_platforms"]) / len(publishing_tasks) if publishing_tasks else 0
            logger.info(f"Publishing completed: {len(results['published_platforms'])}/{len(publishing_tasks)} platforms successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Episode publishing failed: {str(e)}")
            raise

    def _prepare_episode_data(
        self,
        audio_path: str,
        content: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare episode data for publishing across platforms.
        
        Args:
            audio_path: Path to the audio file
            content: Generated content
            metadata: Additional metadata
            
        Returns:
            Standardized episode data dict
        """
        # Generate episode ID if not provided
        episode_id = metadata.get("episode_id") or self._generate_episode_id(content.get("title", ""))
        
        # Get audio file info
        audio_file = Path(audio_path)
        audio_size_mb = audio_file.stat().st_size / (1024 * 1024) if audio_file.exists() else 0
        
        episode_data = {
            "episode_id": episode_id,
            "title": content.get("title", "Untitled Episode"),
            "description": content.get("description", ""),
            "show_notes": content.get("show_notes", ""),
            "summary": content.get("summary", ""),
            "audio_path": audio_path,
            "audio_filename": audio_file.name,
            "audio_size_mb": audio_size_mb,
            "duration_seconds": metadata.get("duration_seconds", 0),
            "language": content.get("metadata", {}).get("language", "English"),
            "language_code": content.get("metadata", {}).get("language_code", "en-US"),
            "social_media": content.get("social_media", {}),
            "tags": metadata.get("tags", []),
            "category": metadata.get("category", "Technology"),
            "explicit": metadata.get("explicit", False),
            "publication_date": metadata.get("publication_date"),
            "author": metadata.get("author", "AI Podcast Flow"),
            "copyright": metadata.get("copyright", f"© {metadata.get('year', '2024')} AI Podcast Flow")
        }
        
        return episode_data

    async def _publish_to_art19(self, episode_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish episode to Art19 podcast hosting platform.
        
        Args:
            episode_data: Prepared episode data
            
        Returns:
            Publishing result dict
        """
        try:
            logger.info("Publishing to Art19")
            
            # Check if Art19 is configured
            series_id = self.publishing_config["art19"]["series_id"]
            if not series_id:
                raise ValueError("Art19 series ID not configured")
            
            # Prepare Art19-specific data
            art19_data = {
                "series_id": series_id,
                "title": episode_data["title"],
                "description": episode_data["description"],
                "audio_path": episode_data["audio_path"],
                "episode_number": episode_data.get("episode_number"),
                "season_number": episode_data.get("season_number"),
                "publication_date": episode_data.get("publication_date"),
                "tags": episode_data.get("tags", []),
                "explicit": episode_data.get("explicit", False),
                "auto_publish": self.publishing_config["art19"]["auto_publish"]
            }
            
            # Create episode on Art19
            result = await self.art19_connector.create_episode(art19_data)
            
            return {
                "success": True,
                "platform": "art19",
                "episode_id": result.get("episode_id"),
                "episode_url": result.get("episode_url"),
                "published": result.get("published", False),
                "message": "Episode successfully created on Art19"
            }
            
        except Exception as e:
            logger.error(f"Art19 publishing failed: {str(e)}")
            return {
                "success": False,
                "platform": "art19",
                "error": str(e),
                "message": f"Failed to publish to Art19: {str(e)}"
            }

    async def _publish_to_website(self, episode_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish episode to website via Vercel deployment or API.
        
        Args:
            episode_data: Prepared episode data
            
        Returns:
            Publishing result dict
        """
        try:
            logger.info("Publishing to website")
            
            # Check configuration
            deploy_hook = self.publishing_config["website"]["deploy_hook"]
            api_endpoint = self.publishing_config["website"]["api_endpoint"]
            
            if not deploy_hook and not api_endpoint:
                raise ValueError("Website deployment not configured (no deploy hook or API endpoint)")
            
            # Prepare website data
            website_data = {
                "episode_id": episode_data["episode_id"],
                "title": episode_data["title"],
                "description": episode_data["description"],
                "show_notes": episode_data["show_notes"],
                "summary": episode_data["summary"],
                "audio_url": "",  # Will be populated after audio upload
                "duration": episode_data["duration_seconds"],
                "language": episode_data["language"],
                "tags": episode_data["tags"],
                "publication_date": episode_data["publication_date"]
            }
            
            # Update website
            if api_endpoint:
                # Use API endpoint to add episode data
                result = await self.vercel_connector.update_episode_data(website_data)
            else:
                # Use deploy hook to trigger rebuild
                result = await self.vercel_connector.trigger_deployment(deploy_hook)
            
            return {
                "success": True,
                "platform": "website",
                "deployment_id": result.get("deployment_id"),
                "website_url": result.get("website_url"),
                "message": "Website successfully updated"
            }
            
        except Exception as e:
            logger.error(f"Website publishing failed: {str(e)}")
            return {
                "success": False,
                "platform": "website",
                "error": str(e),
                "message": f"Failed to update website: {str(e)}"
            }

    async def _publish_to_social_media(self, episode_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish episode announcement to social media platforms.
        
        Args:
            episode_data: Prepared episode data
            
        Returns:
            Publishing result dict
        """
        try:
            logger.info("Publishing to social media")
            
            social_results = {}
            
            # Get social media content
            social_content = episode_data.get("social_media", {})
            
            # Twitter posting
            if "twitter" in self.publishing_config["social_media"]["platforms"]:
                try:
                    twitter_post = social_content.get("twitter") or self._generate_default_twitter_post(episode_data)
                    twitter_result = await self.twitter_connector.post_tweet(twitter_post)
                    social_results["twitter"] = {
                        "success": True,
                        "post_id": twitter_result.get("post_id"),
                        "post_url": twitter_result.get("post_url")
                    }
                except Exception as e:
                    social_results["twitter"] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # TODO: Add more social media platforms (LinkedIn, Instagram, etc.)
            
            # Check if at least one platform succeeded
            success = any(result.get("success", False) for result in social_results.values())
            
            return {
                "success": success,
                "platform": "social_media",
                "platforms": social_results,
                "message": f"Social media posting completed for {len(social_results)} platforms"
            }
            
        except Exception as e:
            logger.error(f"Social media publishing failed: {str(e)}")
            return {
                "success": False,
                "platform": "social_media",
                "error": str(e),
                "message": f"Failed to post to social media: {str(e)}"
            }

    def _generate_episode_id(self, title: str) -> str:
        """
        Generate a unique episode ID from the title.
        
        Args:
            title: Episode title
            
        Returns:
            Generated episode ID
        """
        import re
        import hashlib
        from datetime import datetime
        
        # Clean title for ID
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        clean_title = re.sub(r'\s+', '-', clean_title.strip()).lower()
        
        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Create hash for additional uniqueness
        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
        
        return f"{clean_title}-{timestamp}-{title_hash}"

    def _generate_default_twitter_post(self, episode_data: Dict[str, Any]) -> str:
        """
        Generate a default Twitter post if none provided.
        
        Args:
            episode_data: Episode data
            
        Returns:
            Default Twitter post text
        """
        title = episode_data["title"]
        summary = episode_data.get("summary", "")
        
        # Extract first sentence of summary for tweet
        first_sentence = summary.split(".")[0] if summary else ""
        
        # Create tweet within character limit
        tweet = f"🎧 New episode: {title}"
        
        if first_sentence and len(tweet + " - " + first_sentence) < 250:
            tweet += f" - {first_sentence}"
        
        tweet += " #podcast #ai"
        
        return tweet[:280]  # Ensure Twitter character limit

    async def republish_episode(
        self,
        episode_id: str,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Republish an existing episode to specified platforms.
        
        Args:
            episode_id: Episode ID to republish
            platforms: List of platforms to republish to (None for all)
            
        Returns:
            Republishing results
        """
        # TODO: Implement episode republishing
        logger.warning("Episode republishing not yet implemented")
        
        return {
            "success": False,
            "message": "Republishing functionality not yet implemented",
            "episode_id": episode_id,
            "requested_platforms": platforms or []
        }

    async def get_publishing_status(self, episode_id: str) -> Dict[str, Any]:
        """
        Get the publishing status of an episode across platforms.
        
        Args:
            episode_id: Episode ID to check
            
        Returns:
            Publishing status information
        """
        # TODO: Implement status checking across platforms
        logger.warning("Publishing status checking not yet implemented")
        
        return {
            "episode_id": episode_id,
            "status": "unknown",
            "platforms": {},
            "message": "Status checking not yet implemented"
        }