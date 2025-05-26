"""
Anthropic API Connector

This module provides integration with Anthropic's Claude API for content generation.
Handles authentication, request formatting, and response processing.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import asyncio

import anthropic
from anthropic.types import Message


logger = logging.getLogger(__name__)


class AnthropicConnector:
    """
    Connector for Anthropic Claude API.
    
    Provides methods for content generation using Claude models with
    proper authentication and error handling.
    """

    def __init__(self):
        """Initialize the Anthropic connector."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not found in environment variables")
            self.client = None
        else:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Anthropic client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {str(e)}")
                self.client = None

        # Default model settings
        self.default_model = "claude-3-sonnet-20240229"
        self.default_max_tokens = 1000
        self.default_temperature = 0.7

    def is_available(self) -> bool:
        """Check if the Anthropic API is available and configured."""
        return self.client is not None

    async def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate content using Claude API.
        
        Args:
            prompt: The user prompt
            model: Model to use (defaults to claude-3-sonnet)
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature (0.0 to 1.0)
            system_message: Optional system message to set context
            
        Returns:
            Dict containing generated content and metadata
            
        Raises:
            Exception: If API call fails or client not available
        """
        if not self.client:
            raise Exception("Anthropic client not available. Check API key configuration.")

        try:
            # Use defaults if not specified
            model = model or self.default_model
            max_tokens = max_tokens or self.default_max_tokens
            temperature = temperature or self.default_temperature

            # Prepare messages
            messages = [{"role": "user", "content": prompt}]

            # Create request parameters
            request_params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }

            # Add system message if provided
            if system_message:
                request_params["system"] = system_message

            logger.info(f"Calling Claude API with model: {model}")
            
            # Make API call
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.client.messages.create(**request_params)
            )

            # Process response
            result = self._process_response(response, prompt)
            
            logger.info(f"Claude API call successful. Generated {len(result['content'])} characters")
            return result

        except Exception as e:
            logger.error(f"Claude API call failed: {str(e)}")
            raise

    def _process_response(self, response: Message, original_prompt: str) -> Dict[str, Any]:
        """
        Process Claude API response.
        
        Args:
            response: Claude API response object
            original_prompt: Original prompt for reference
            
        Returns:
            Processed response data
        """
        # Extract content from response
        content = ""
        if response.content:
            # Handle different content types
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    content += content_block.text
                else:
                    content += str(content_block)

        # Calculate token usage
        input_tokens = getattr(response.usage, 'input_tokens', 0) if hasattr(response, 'usage') else 0
        output_tokens = getattr(response.usage, 'output_tokens', 0) if hasattr(response, 'usage') else 0

        return {
            "content": content,
            "model": response.model,
            "role": response.role,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "stop_reason": getattr(response, 'stop_reason', None),
            "prompt_length": len(original_prompt),
            "response_length": len(content)
        }

    async def generate_batch_content(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_message: Optional[str] = None,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate content for multiple prompts in batch.
        
        Args:
            prompts: List of prompts to process
            model: Model to use for all prompts
            max_tokens: Maximum tokens per generation
            temperature: Generation temperature
            system_message: System message for all prompts
            max_concurrent: Maximum concurrent API calls
            
        Returns:
            List of generation results
        """
        if not self.client:
            raise Exception("Anthropic client not available")

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_single(prompt: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.generate_content(
                        prompt=prompt,
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system_message=system_message
                    )
                    result["prompt_index"] = index
                    result["success"] = True
                    return result
                except Exception as e:
                    logger.error(f"Batch generation failed for prompt {index}: {str(e)}")
                    return {
                        "prompt_index": index,
                        "success": False,
                        "error": str(e),
                        "content": ""
                    }

        # Execute all prompts concurrently
        tasks = [generate_single(prompt, i) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks)

        # Sort results by original order
        results.sort(key=lambda x: x["prompt_index"])
        
        successful_count = sum(1 for r in results if r.get("success", False))
        logger.info(f"Batch generation completed: {successful_count}/{len(prompts)} successful")

        return results

    async def generate_structured_content(
        self,
        content_types: Dict[str, str],
        context: str,
        model: Optional[str] = None,
        max_tokens_per_type: int = 300
    ) -> Dict[str, str]:
        """
        Generate multiple content types from a single context.
        
        Args:
            content_types: Dict mapping content type names to their prompts
            context: Shared context (e.g., transcript) for all content types
            model: Model to use
            max_tokens_per_type: Max tokens per content type
            
        Returns:
            Dict mapping content type names to generated content
        """
        if not self.client:
            raise Exception("Anthropic client not available")

        results = {}
        
        # Generate each content type
        for content_type, prompt_template in content_types.items():
            try:
                # Format prompt with context
                full_prompt = prompt_template.format(context=context)
                
                # Generate content
                result = await self.generate_content(
                    prompt=full_prompt,
                    model=model,
                    max_tokens=max_tokens_per_type
                )
                
                results[content_type] = result["content"]
                
            except Exception as e:
                logger.error(f"Failed to generate {content_type}: {str(e)}")
                results[content_type] = f"[Generation failed: {str(e)}]"

        return results

    def get_available_models(self) -> List[str]:
        """
        Get list of available Claude models.
        
        Returns:
            List of model names
        """
        # Note: Anthropic doesn't provide a models list API endpoint
        # Return known available models as of implementation date
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English
        # This is an approximation; actual tokenization may vary
        return len(text) // 4

    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a simple test call.
        
        Returns:
            True if API key is valid, False otherwise
        """
        if not self.client:
            return False

        try:
            # Make a minimal test call
            response = self.client.messages.create(
                model=self.default_model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False