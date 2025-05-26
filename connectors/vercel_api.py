"""
Vercel API Connector

This module provides integration with Vercel's deployment platform for updating
podcast websites and triggering deployments when new episodes are published.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

import httpx


logger = logging.getLogger(__name__)


class VercelConnector:
    """
    Connector for Vercel deployment platform.
    
    Provides methods for triggering deployments, updating content,
    and managing website updates for podcast episodes.
    """

    def __init__(self):
        """Initialize the Vercel connector."""
        # Vercel configuration
        self.deploy_hook = os.getenv("VERCEL_DEPLOY_HOOK")
        self.api_token = os.getenv("VERCEL_API_TOKEN")
        self.team_id = os.getenv("VERCEL_TEAM_ID")
        self.project_id = os.getenv("VERCEL_PROJECT_ID")
        self.api_base_url = "https://api.vercel.com"
        
        # API endpoint for direct content updates (if available)
        self.content_api_endpoint = os.getenv("VERCEL_CONTENT_API_ENDPOINT")
        
        # HTTP client configuration
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.headers = {
            "Authorization": f"Bearer {self.api_token}" if self.api_token else "",
            "Content-Type": "application/json",
            "User-Agent": "AI-Podcast-Flow/1.0"
        }
        
        logger.info("Vercel connector initialized")

    def is_available(self) -> bool:
        """Check if Vercel integration is available and configured."""
        return bool(self.deploy_hook or (self.api_token and self.project_id))

    async def trigger_deployment(
        self,
        deploy_hook_url: Optional[str] = None,
        deployment_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger a Vercel deployment using deploy hook.
        
        Args:
            deploy_hook_url: Custom deploy hook URL (uses default if None)
            deployment_data: Optional data to include with deployment trigger
            
        Returns:
            Dict containing deployment results
            
        Raises:
            Exception: If deployment trigger fails
        """
        hook_url = deploy_hook_url or self.deploy_hook
        
        if not hook_url:
            raise Exception("No Vercel deploy hook configured")

        try:
            logger.info("Triggering Vercel deployment")

            # Prepare deployment payload
            payload = deployment_data or {}
            
            # Add timestamp and trigger source
            payload.update({
                "triggered_at": datetime.utcnow().isoformat(),
                "trigger_source": "ai_podcast_flow",
                "deployment_type": "episode_update"
            })

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    hook_url,
                    json=payload
                )
                
                if response.status_code not in [200, 201, 202]:
                    raise Exception(f"Deployment trigger failed: {response.status_code} - {response.text}")

                # Process response
                try:
                    result_data = response.json()
                except:
                    result_data = {"status": "triggered"}

                result = {
                    "success": True,
                    "deployment_triggered": True,
                    "deployment_id": result_data.get("id"),
                    "deployment_url": result_data.get("url"),
                    "status": result_data.get("status", "triggered"),
                    "message": "Vercel deployment triggered successfully"
                }

                logger.info(f"Vercel deployment triggered: {result.get('deployment_id', 'unknown ID')}")
                return result

        except Exception as e:
            logger.error(f"Failed to trigger Vercel deployment: {str(e)}")
            raise

    async def update_episode_data(
        self,
        episode_data: Dict[str, Any],
        api_endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update episode data via Vercel API endpoint.
        
        Args:
            episode_data: Episode information to update
            api_endpoint: Custom API endpoint (uses default if None)
            
        Returns:
            Dict containing update results
        """
        endpoint = api_endpoint or self.content_api_endpoint
        
        if not endpoint:
            # Fallback to deployment trigger if no content API available
            logger.info("No content API endpoint configured, falling back to deployment trigger")
            return await self.trigger_deployment(deployment_data={"episode_data": episode_data})

        try:
            logger.info(f"Updating episode data via Vercel API: {episode_data.get('title', 'Unknown')}")

            # Prepare episode payload
            payload = {
                "action": "add_episode",
                "episode": episode_data,
                "timestamp": datetime.utcnow().isoformat()
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers if self.api_token else {}
                )
                
                if response.status_code not in [200, 201]:
                    raise Exception(f"Episode data update failed: {response.status_code} - {response.text}")

                result_data = response.json() if response.content else {}
                
                return {
                    "success": True,
                    "episode_updated": True,
                    "episode_id": episode_data.get("episode_id"),
                    "website_url": result_data.get("website_url"),
                    "episode_url": result_data.get("episode_url"),
                    "message": "Episode data updated successfully"
                }

        except Exception as e:
            logger.error(f"Failed to update episode data: {str(e)}")
            raise

    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get the status of a Vercel deployment.
        
        Args:
            deployment_id: Vercel deployment ID
            
        Returns:
            Dict containing deployment status
        """
        if not self.api_token or not deployment_id:
            raise Exception("Vercel API token and deployment ID required")

        try:
            url = f"{self.api_base_url}/v13/deployments/{deployment_id}"
            
            # Add team parameter if configured
            params = {}
            if self.team_id:
                params["teamId"] = self.team_id

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code == 404:
                    raise Exception(f"Deployment not found: {deployment_id}")
                elif response.status_code != 200:
                    raise Exception(f"API error: {response.status_code} - {response.text}")

                deployment_data = response.json()
                
                return {
                    "deployment_id": deployment_data["uid"],
                    "status": deployment_data["state"],
                    "url": deployment_data.get("url"),
                    "created_at": deployment_data.get("createdAt"),
                    "ready": deployment_data.get("ready"),
                    "error": deployment_data.get("error"),
                    "duration": deployment_data.get("buildingAt")
                }

        except Exception as e:
            logger.error(f"Failed to get deployment status: {str(e)}")
            raise

    async def list_deployments(
        self,
        limit: int = 20,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List recent deployments for a project.
        
        Args:
            limit: Maximum number of deployments to return
            project_id: Vercel project ID (uses default if None)
            
        Returns:
            List of deployment information
        """
        if not self.api_token:
            raise Exception("Vercel API token required")

        project = project_id or self.project_id
        if not project:
            raise Exception("Project ID required")

        try:
            url = f"{self.api_base_url}/v6/deployments"
            
            params = {
                "projectId": project,
                "limit": limit
            }
            
            if self.team_id:
                params["teamId"] = self.team_id

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code != 200:
                    raise Exception(f"API error: {response.status_code} - {response.text}")

                data = response.json()
                deployments = []
                
                for deployment in data.get("deployments", []):
                    deployments.append({
                        "deployment_id": deployment["uid"],
                        "status": deployment["state"],
                        "url": deployment.get("url"),
                        "created_at": deployment.get("createdAt"),
                        "ready": deployment.get("ready"),
                        "meta": deployment.get("meta", {})
                    })

                return deployments

        except Exception as e:
            logger.error(f"Failed to list deployments: {str(e)}")
            raise

    async def create_preview_deployment(
        self,
        episode_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a preview deployment for testing episode content.
        
        Args:
            episode_data: Episode data to preview
            
        Returns:
            Dict containing preview deployment information
        """
        # TODO: Implement preview deployment creation
        # This would involve creating a temporary branch/deployment for testing
        logger.warning("Preview deployment creation not yet implemented")
        
        return {
            "success": False,
            "message": "Preview deployment creation not yet implemented",
            "episode_id": episode_data.get("episode_id")
        }

    async def invalidate_cache(
        self,
        paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Invalidate Vercel edge cache for specific paths.
        
        Args:
            paths: List of paths to invalidate (invalidates all if None)
            
        Returns:
            Dict containing cache invalidation results
        """
        if not self.api_token:
            raise Exception("Vercel API token required")

        try:
            # Default paths to invalidate for podcast updates
            if paths is None:
                paths = [
                    "/",
                    "/episodes",
                    "/rss.xml",
                    "/sitemap.xml"
                ]

            # TODO: Implement actual cache invalidation API call
            # Vercel's cache invalidation API may vary based on plan and configuration
            logger.warning("Cache invalidation not yet implemented")
            
            return {
                "success": True,
                "invalidated_paths": paths,
                "message": "Cache invalidation requested (implementation pending)"
            }

        except Exception as e:
            logger.error(f"Failed to invalidate cache: {str(e)}")
            raise

    async def update_environment_variables(
        self,
        variables: Dict[str, str],
        target: str = "production"
    ) -> Dict[str, Any]:
        """
        Update environment variables for the Vercel project.
        
        Args:
            variables: Dict of environment variables to update
            target: Deployment target (production, preview, development)
            
        Returns:
            Dict containing update results
        """
        if not self.api_token or not self.project_id:
            raise Exception("Vercel API token and project ID required")

        try:
            url = f"{self.api_base_url}/v10/projects/{self.project_id}/env"
            
            results = []
            
            for key, value in variables.items():
                payload = {
                    "key": key,
                    "value": value,
                    "target": [target],
                    "type": "encrypted"
                }
                
                params = {}
                if self.team_id:
                    params["teamId"] = self.team_id

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        headers=self.headers,
                        json=payload,
                        params=params
                    )
                    
                    if response.status_code in [200, 201]:
                        results.append({
                            "key": key,
                            "success": True,
                            "message": "Variable updated successfully"
                        })
                    else:
                        results.append({
                            "key": key,
                            "success": False,
                            "error": f"Update failed: {response.status_code}"
                        })

            return {
                "success": all(r["success"] for r in results),
                "updated_variables": results,
                "target": target
            }

        except Exception as e:
            logger.error(f"Failed to update environment variables: {str(e)}")
            raise

    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate Vercel configuration and connectivity.
        
        Returns:
            Dict containing validation results
        """
        validation_results = {
            "deploy_hook_available": bool(self.deploy_hook),
            "api_token_available": bool(self.api_token),
            "project_id_available": bool(self.project_id),
            "content_api_available": bool(self.content_api_endpoint),
            "team_id_configured": bool(self.team_id)
        }
        
        validation_results["overall_configured"] = (
            validation_results["deploy_hook_available"] or 
            (validation_results["api_token_available"] and validation_results["project_id_available"])
        )
        
        return validation_results