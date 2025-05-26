"""
Art19 API Connector

This module provides integration with Art19's podcast hosting platform API.
Handles episode creation, uploading, and publishing workflows.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import asyncio
from pathlib import Path
import json
from datetime import datetime

import httpx
import aiofiles


logger = logging.getLogger(__name__)


class Art19Connector:
    """
    Connector for Art19 podcast hosting platform API.
    
    Provides methods for creating episodes, uploading audio files,
    and managing podcast content on Art19.
    """

    def __init__(self):
        """Initialize the Art19 connector."""
        self.api_token = os.getenv("ART19_API_TOKEN")
        self.api_base_url = os.getenv("ART19_API_BASE_URL", "https://api.art19.com")
        self.series_id = os.getenv("ART19_SERIES_ID")
        
        if not self.api_token:
            logger.warning("ART19_API_TOKEN not found in environment variables")
        
        if not self.series_id:
            logger.warning("ART19_SERIES_ID not found in environment variables")
        
        # HTTP client configuration
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.headers = {
            "Authorization": f"Bearer {self.api_token}" if self.api_token else "",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
            "User-Agent": "AI-Podcast-Flow/1.0"
        }
        
        logger.info("Art19 connector initialized")

    def is_available(self) -> bool:
        """Check if the Art19 API is available and configured."""
        return bool(self.api_token and self.series_id)

    async def create_episode(self, episode_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new episode on Art19.
        
        Args:
            episode_data: Episode information including title, description, audio_path, etc.
            
        Returns:
            Dict containing episode creation results
            
        Raises:
            Exception: If episode creation fails
        """
        if not self.is_available():
            raise Exception("Art19 API not properly configured. Check API token and series ID.")

        try:
            logger.info(f"Creating episode on Art19: {episode_data.get('title', 'Untitled')}")

            # First, upload the audio file
            audio_upload_result = await self._upload_audio_file(episode_data["audio_path"])
            
            # Prepare episode payload for Art19 API
            episode_payload = self._prepare_episode_payload(episode_data, audio_upload_result)
            
            # Create episode via API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base_url}/episodes",
                    headers=self.headers,
                    json=episode_payload
                )
                
                if response.status_code not in [200, 201]:
                    raise Exception(f"Art19 API error: {response.status_code} - {response.text}")
                
                result_data = response.json()
                
                # Extract episode information
                episode_info = self._extract_episode_info(result_data)
                
                # Optionally publish the episode immediately
                if episode_data.get("auto_publish", False):
                    await self._publish_episode(episode_info["episode_id"])
                    episode_info["published"] = True
                
                logger.info(f"Episode created successfully on Art19: {episode_info['episode_id']}")
                return episode_info

        except Exception as e:
            logger.error(f"Failed to create episode on Art19: {str(e)}")
            raise

    async def _upload_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """
        Upload audio file to Art19's storage.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dict containing upload results including file URL
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            logger.info(f"Uploading audio file to Art19: {audio_path}")
            
            # Get upload URL from Art19
            upload_url_data = await self._get_upload_url(audio_path)
            
            # Upload file to the provided URL
            upload_result = await self._perform_file_upload(audio_path, upload_url_data)
            
            logger.info(f"Audio file uploaded successfully: {upload_result['file_url']}")
            return upload_result

        except Exception as e:
            logger.error(f"Audio file upload failed: {str(e)}")
            raise

    async def _get_upload_url(self, audio_path: str) -> Dict[str, Any]:
        """
        Get a pre-signed upload URL from Art19.
        
        Args:
            audio_path: Path to the audio file (for filename and size info)
            
        Returns:
            Dict containing upload URL and parameters
        """
        audio_file = Path(audio_path)
        file_size = audio_file.stat().st_size
        
        upload_request = {
            "data": {
                "type": "audio_uploads",
                "attributes": {
                    "filename": audio_file.name,
                    "file_size": file_size,
                    "content_type": self._get_content_type(audio_file.suffix)
                }
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base_url}/audio_uploads",
                headers=self.headers,
                json=upload_request
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to get upload URL: {response.status_code} - {response.text}")
            
            return response.json()

    async def _perform_file_upload(self, audio_path: str, upload_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform the actual file upload using the pre-signed URL.
        
        Args:
            audio_path: Path to the audio file
            upload_data: Upload URL and parameters from Art19
            
        Returns:
            Dict containing upload results
        """
        # Extract upload information from Art19 response
        upload_info = upload_data["data"]["attributes"]
        upload_url = upload_info["upload_url"]
        upload_fields = upload_info.get("upload_fields", {})
        
        # Prepare multipart form data
        async with aiofiles.open(audio_path, 'rb') as audio_file:
            files = {"file": await audio_file.read()}
            
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:  # Longer timeout for upload
                response = await client.post(
                    upload_url,
                    data=upload_fields,
                    files={"file": (Path(audio_path).name, files["file"])}
                )
                
                if response.status_code not in [200, 201, 204]:
                    raise Exception(f"File upload failed: {response.status_code} - {response.text}")
        
        return {
            "file_url": upload_info.get("file_url", upload_url),
            "upload_id": upload_data["data"]["id"],
            "file_size": Path(audio_path).stat().st_size,
            "filename": Path(audio_path).name
        }

    def _prepare_episode_payload(
        self, 
        episode_data: Dict[str, Any], 
        audio_upload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare the episode payload for Art19 API.
        
        Args:
            episode_data: Episode information
            audio_upload: Audio upload results
            
        Returns:
            Art19 API-compatible episode payload
        """
        # Convert publication date to ISO format if provided
        publication_date = episode_data.get("publication_date")
        if publication_date and not isinstance(publication_date, str):
            publication_date = publication_date.isoformat()

        payload = {
            "data": {
                "type": "episodes",
                "attributes": {
                    "title": episode_data["title"],
                    "description": episode_data.get("description", ""),
                    "content": episode_data.get("show_notes", ""),
                    "audio_upload_id": audio_upload["upload_id"],
                    "episode_number": episode_data.get("episode_number"),
                    "season_number": episode_data.get("season_number", 1),
                    "published_at": publication_date,
                    "explicit": episode_data.get("explicit", False),
                    "tags": episode_data.get("tags", [])
                },
                "relationships": {
                    "series": {
                        "data": {
                            "type": "series",
                            "id": self.series_id
                        }
                    }
                }
            }
        }
        
        # Remove None values
        payload["data"]["attributes"] = {
            k: v for k, v in payload["data"]["attributes"].items() 
            if v is not None
        }
        
        return payload

    def _extract_episode_info(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract episode information from Art19 API response.
        
        Args:
            api_response: Raw API response from Art19
            
        Returns:
            Cleaned episode information
        """
        episode_data = api_response["data"]
        attributes = episode_data["attributes"]
        
        return {
            "episode_id": episode_data["id"],
            "title": attributes["title"],
            "description": attributes.get("description", ""),
            "episode_url": attributes.get("canonical_url", ""),
            "embed_url": attributes.get("embed_url", ""),
            "audio_url": attributes.get("audio_url", ""),
            "duration_seconds": attributes.get("duration", 0),
            "published": attributes.get("published", False),
            "published_at": attributes.get("published_at"),
            "episode_number": attributes.get("episode_number"),
            "season_number": attributes.get("season_number"),
            "explicit": attributes.get("explicit", False),
            "created_at": attributes.get("created_at"),
            "updated_at": attributes.get("updated_at")
        }

    async def _publish_episode(self, episode_id: str) -> Dict[str, Any]:
        """
        Publish an episode that was created in draft mode.
        
        Args:
            episode_id: Art19 episode ID
            
        Returns:
            Publishing result
        """
        publish_payload = {
            "data": {
                "type": "episodes",
                "id": episode_id,
                "attributes": {
                    "published": True,
                    "published_at": datetime.utcnow().isoformat() + "Z"
                }
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.api_base_url}/episodes/{episode_id}",
                headers=self.headers,
                json=publish_payload
            )
            
            if response.status_code not in [200, 204]:
                raise Exception(f"Failed to publish episode: {response.status_code} - {response.text}")
            
            return {"published": True, "episode_id": episode_id}

    def _get_content_type(self, file_extension: str) -> str:
        """
        Get the appropriate content type for an audio file.
        
        Args:
            file_extension: File extension (e.g., '.mp3', '.wav')
            
        Returns:
            MIME type string
        """
        content_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".aac": "audio/aac",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg"
        }
        
        return content_types.get(file_extension.lower(), "audio/mpeg")

    async def get_episode(self, episode_id: str) -> Dict[str, Any]:
        """
        Get episode information from Art19.
        
        Args:
            episode_id: Art19 episode ID
            
        Returns:
            Episode information
        """
        if not self.is_available():
            raise Exception("Art19 API not configured")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base_url}/episodes/{episode_id}",
                    headers=self.headers
                )
                
                if response.status_code == 404:
                    raise Exception(f"Episode not found: {episode_id}")
                elif response.status_code != 200:
                    raise Exception(f"API error: {response.status_code} - {response.text}")
                
                return self._extract_episode_info(response.json())

        except Exception as e:
            logger.error(f"Failed to get episode {episode_id}: {str(e)}")
            raise

    async def update_episode(
        self, 
        episode_id: str, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing episode on Art19.
        
        Args:
            episode_id: Art19 episode ID
            updates: Dict of fields to update
            
        Returns:
            Updated episode information
        """
        if not self.is_available():
            raise Exception("Art19 API not configured")

        try:
            update_payload = {
                "data": {
                    "type": "episodes",
                    "id": episode_id,
                    "attributes": updates
                }
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    f"{self.api_base_url}/episodes/{episode_id}",
                    headers=self.headers,
                    json=update_payload
                )
                
                if response.status_code not in [200, 204]:
                    raise Exception(f"Update failed: {response.status_code} - {response.text}")
                
                # Fetch updated episode data
                return await self.get_episode(episode_id)

        except Exception as e:
            logger.error(f"Failed to update episode {episode_id}: {str(e)}")
            raise

    async def delete_episode(self, episode_id: str) -> bool:
        """
        Delete an episode from Art19.
        
        Args:
            episode_id: Art19 episode ID
            
        Returns:
            True if deletion was successful
        """
        if not self.is_available():
            raise Exception("Art19 API not configured")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.api_base_url}/episodes/{episode_id}",
                    headers=self.headers
                )
                
                if response.status_code in [200, 204, 404]:  # 404 means already deleted
                    logger.info(f"Episode {episode_id} deleted successfully")
                    return True
                else:
                    raise Exception(f"Deletion failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Failed to delete episode {episode_id}: {str(e)}")
            raise

    async def list_episodes(
        self, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List episodes in the series.
        
        Args:
            limit: Maximum number of episodes to return
            offset: Number of episodes to skip
            
        Returns:
            List of episode information
        """
        if not self.is_available():
            raise Exception("Art19 API not configured")

        try:
            params = {
                "filter[series_id]": self.series_id,
                "page[limit]": limit,
                "page[offset]": offset
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base_url}/episodes",
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code != 200:
                    raise Exception(f"API error: {response.status_code} - {response.text}")
                
                data = response.json()
                return [self._extract_episode_info({"data": episode}) for episode in data["data"]]

        except Exception as e:
            logger.error(f"Failed to list episodes: {str(e)}")
            raise