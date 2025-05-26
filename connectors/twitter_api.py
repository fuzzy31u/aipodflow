"""
Twitter API Connector

This module provides integration with Twitter API v2 for posting episode announcements
and managing social media content related to podcast episodes.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import asyncio

import tweepy


logger = logging.getLogger(__name__)


class TwitterConnector:
    """
    Connector for Twitter API v2.
    
    Provides methods for posting tweets, managing content,
    and handling Twitter authentication.
    """

    def __init__(self):
        """Initialize the Twitter connector."""
        # Twitter API credentials
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        # Initialize Twitter clients
        self.client_v2 = None
        self.api_v1 = None
        
        self._initialize_clients()
        
        # Tweet configuration
        self.max_tweet_length = 280
        self.max_thread_length = 10
        
        logger.info("Twitter connector initialized")

    def _initialize_clients(self):
        """Initialize Twitter API clients."""
        try:
            # Initialize v2 client (preferred for posting)
            if all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
                self.client_v2 = tweepy.Client(
                    bearer_token=self.bearer_token,
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                    wait_on_rate_limit=True
                )
                logger.info("Twitter API v2 client initialized")
            else:
                logger.warning("Twitter API credentials incomplete for v2 client")
            
            # Initialize v1.1 client (for media uploads if needed)
            if all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
                auth = tweepy.OAuth1UserHandler(
                    self.api_key,
                    self.api_secret,
                    self.access_token,
                    self.access_token_secret
                )
                self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
                logger.info("Twitter API v1.1 client initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twitter clients: {str(e)}")

    def is_available(self) -> bool:
        """Check if Twitter API is available and configured."""
        return self.client_v2 is not None

    async def post_tweet(
        self,
        text: str,
        reply_to_id: Optional[str] = None,
        media_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Post a tweet to Twitter.
        
        Args:
            text: Tweet content
            reply_to_id: ID of tweet to reply to (optional)
            media_paths: List of paths to media files to attach (optional)
            
        Returns:
            Dict containing tweet posting results
            
        Raises:
            Exception: If posting fails or client not available
        """
        if not self.client_v2:
            raise Exception("Twitter client not available. Check API credentials.")

        try:
            logger.info(f"Posting tweet: {text[:50]}...")

            # Validate tweet length
            if len(text) > self.max_tweet_length:
                logger.warning(f"Tweet length ({len(text)}) exceeds limit ({self.max_tweet_length})")
                text = self._truncate_tweet(text)

            # Handle media uploads if provided
            media_ids = None
            if media_paths:
                media_ids = await self._upload_media(media_paths)

            # Post tweet
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client_v2.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=reply_to_id,
                    media_ids=media_ids
                )
            )

            # Process response
            result = self._process_tweet_response(response)
            
            logger.info(f"Tweet posted successfully: {result['post_id']}")
            return result

        except Exception as e:
            logger.error(f"Failed to post tweet: {str(e)}")
            raise

    async def post_thread(
        self,
        messages: List[str],
        media_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Post a Twitter thread.
        
        Args:
            messages: List of messages for the thread
            media_paths: Optional media files for the first tweet
            
        Returns:
            Dict containing thread posting results
        """
        if not self.client_v2:
            raise Exception("Twitter client not available")

        if len(messages) > self.max_thread_length:
            raise ValueError(f"Thread too long: {len(messages)} > {self.max_thread_length}")

        try:
            logger.info(f"Posting Twitter thread with {len(messages)} tweets")

            thread_results = []
            reply_to_id = None

            for i, message in enumerate(messages):
                # Add thread indicators
                if len(messages) > 1:
                    thread_indicator = f" ({i+1}/{len(messages)})"
                    if len(message) + len(thread_indicator) <= self.max_tweet_length:
                        message += thread_indicator

                # Upload media only for the first tweet
                current_media = media_paths if i == 0 else None

                # Post tweet
                tweet_result = await self.post_tweet(
                    text=message,
                    reply_to_id=reply_to_id,
                    media_paths=current_media
                )

                thread_results.append(tweet_result)
                reply_to_id = tweet_result["post_id"]

                # Brief delay between tweets to avoid rate limits
                if i < len(messages) - 1:
                    await asyncio.sleep(1)

            return {
                "success": True,
                "thread_id": thread_results[0]["post_id"],
                "thread_url": thread_results[0]["post_url"],
                "tweets": thread_results,
                "tweet_count": len(thread_results)
            }

        except Exception as e:
            logger.error(f"Failed to post thread: {str(e)}")
            raise

    async def _upload_media(self, media_paths: List[str]) -> List[str]:
        """
        Upload media files to Twitter.
        
        Args:
            media_paths: List of paths to media files
            
        Returns:
            List of media IDs
        """
        if not self.api_v1:
            raise Exception("Twitter v1.1 API required for media uploads")

        media_ids = []

        for media_path in media_paths:
            try:
                if not os.path.exists(media_path):
                    logger.warning(f"Media file not found: {media_path}")
                    continue

                # Upload media using v1.1 API
                media = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.api_v1.media_upload(media_path)
                )
                
                media_ids.append(media.media_id)
                logger.info(f"Media uploaded: {media_path} -> {media.media_id}")

            except Exception as e:
                logger.error(f"Failed to upload media {media_path}: {str(e)}")

        return media_ids

    def _process_tweet_response(self, response) -> Dict[str, Any]:
        """
        Process Twitter API response.
        
        Args:
            response: Twitter API response object
            
        Returns:
            Processed response data
        """
        tweet_data = response.data
        
        return {
            "success": True,
            "post_id": tweet_data["id"],
            "post_url": f"https://twitter.com/i/status/{tweet_data['id']}",
            "text": tweet_data["text"],
            "created_at": tweet_data.get("created_at"),
            "public_metrics": getattr(tweet_data, "public_metrics", {}),
            "response_data": tweet_data
        }

    def _truncate_tweet(self, text: str) -> str:
        """
        Truncate tweet text to fit within character limit.
        
        Args:
            text: Original tweet text
            
        Returns:
            Truncated tweet text
        """
        if len(text) <= self.max_tweet_length:
            return text

        # Reserve space for ellipsis
        max_length = self.max_tweet_length - 3

        # Try to cut at a sentence boundary
        truncated = text[:max_length]
        last_period = truncated.rfind(".")
        last_space = truncated.rfind(" ")

        # Use sentence boundary if available, otherwise word boundary
        if last_period > max_length * 0.7:
            truncated = text[:last_period + 1]
        elif last_space > max_length * 0.7:
            truncated = text[:last_space]
        else:
            truncated = text[:max_length]

        return truncated + "..."

    async def generate_podcast_tweet(
        self,
        episode_title: str,
        episode_url: str,
        summary: Optional[str] = None,
        hashtags: Optional[List[str]] = None
    ) -> str:
        """
        Generate a podcast episode tweet.
        
        Args:
            episode_title: Episode title
            episode_url: URL to the episode
            summary: Brief episode summary
            hashtags: List of hashtags to include
            
        Returns:
            Generated tweet text
        """
        # Start with basic format
        tweet = f"🎧 New episode: {episode_title}"

        # Add summary if provided and space allows
        if summary:
            summary_text = f"\n\n{summary}"
            if len(tweet + summary_text) < self.max_tweet_length - 50:  # Leave space for URL and hashtags
                tweet += summary_text

        # Add hashtags
        if hashtags:
            hashtag_text = " " + " ".join(f"#{tag}" for tag in hashtags)
            if len(tweet + hashtag_text) < self.max_tweet_length - 30:  # Leave space for URL
                tweet += hashtag_text

        # Add URL (Twitter will auto-shorten)
        tweet += f"\n\n{episode_url}"

        # Final truncation if needed
        if len(tweet) > self.max_tweet_length:
            tweet = self._truncate_tweet(tweet)

        return tweet

    async def search_mentions(
        self,
        username: str,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for mentions of a username.
        
        Args:
            username: Username to search for (without @)
            max_results: Maximum number of results
            
        Returns:
            List of tweet mentions
        """
        if not self.client_v2:
            raise Exception("Twitter client not available")

        try:
            query = f"@{username}"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client_v2.search_recent_tweets(
                    query=query,
                    max_results=min(max_results, 100),
                    tweet_fields=['created_at', 'author_id', 'public_metrics']
                )
            )

            if not response.data:
                return []

            mentions = []
            for tweet in response.data:
                mentions.append({
                    "id": tweet.id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "created_at": tweet.created_at,
                    "public_metrics": getattr(tweet, "public_metrics", {}),
                    "url": f"https://twitter.com/i/status/{tweet.id}"
                })

            return mentions

        except Exception as e:
            logger.error(f"Failed to search mentions: {str(e)}")
            raise

    async def get_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """
        Get a specific tweet by ID.
        
        Args:
            tweet_id: Twitter tweet ID
            
        Returns:
            Tweet information
        """
        if not self.client_v2:
            raise Exception("Twitter client not available")

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client_v2.get_tweet(
                    tweet_id,
                    tweet_fields=['created_at', 'author_id', 'public_metrics']
                )
            )

            if not response.data:
                raise Exception(f"Tweet not found: {tweet_id}")

            return self._process_tweet_response(response)

        except Exception as e:
            logger.error(f"Failed to get tweet {tweet_id}: {str(e)}")
            raise

    async def delete_tweet(self, tweet_id: str) -> bool:
        """
        Delete a tweet.
        
        Args:
            tweet_id: Twitter tweet ID
            
        Returns:
            True if deletion was successful
        """
        if not self.client_v2:
            raise Exception("Twitter client not available")

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client_v2.delete_tweet(tweet_id)
            )

            return response.data.get("deleted", False)

        except Exception as e:
            logger.error(f"Failed to delete tweet {tweet_id}: {str(e)}")
            raise

    def validate_credentials(self) -> bool:
        """
        Validate Twitter API credentials.
        
        Returns:
            True if credentials are valid
        """
        if not self.client_v2:
            return False

        try:
            # Make a simple API call to verify credentials
            me = self.client_v2.get_me()
            if me.data:
                logger.info(f"Twitter credentials valid for user: {me.data.username}")
                return True
            return False

        except Exception as e:
            logger.error(f"Twitter credential validation failed: {str(e)}")
            return False