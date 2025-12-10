#!/usr/bin/env python3
"""
AI Summarizer Module

Unified API wrapper for multiple AI chatbot providers:
- OpenAI (ChatGPT)
- Google Gemini
- Azure OpenAI (Copilot)
- Perplexity AI

Provides consistent interface for transcript summarization across providers.

Architecture Decision: AD-015 (User Profile Architecture) - Task #19
Related: PRD-2025-12-10-03-ai-summarization
"""

# Standard library
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, List
from pathlib import Path

# Local
from shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SummaryRequest:
    """
    Request for AI summarization.
    
    Attributes:
        transcript_text: Full transcript text to summarize
        media_url: Optional source URL for attribution
        max_tokens: Maximum tokens in summary (default: 500)
        language: Target language for summary (default: 'en')
        include_timestamps: Whether to extract key timestamps
    """
    transcript_text: str
    media_url: Optional[str] = None
    max_tokens: int = 500
    language: str = "en"
    include_timestamps: bool = False


@dataclass
class SummaryResponse:
    """
    Response from AI summarization.
    
    Attributes:
        summary: Generated summary text
        key_points: List of key takeaways
        timestamps: Optional key moment timestamps
        source_attribution: Source URL attribution
        provider: AI provider used
        tokens_used: Tokens consumed
    """
    summary: str
    key_points: List[str]
    timestamps: Optional[List[Dict[str, str]]] = None
    source_attribution: Optional[str] = None
    provider: str = ""
    tokens_used: int = 0


class AIProvider(ABC):
    """Abstract base class for AI chatbot providers."""
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize AI provider.
        
        Args:
            api_key: API key for authentication
            **kwargs: Provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def summarize(self, request: SummaryRequest) -> SummaryResponse:
        """
        Generate summary from transcript.
        
        Args:
            request: Summary request with transcript text
            
        Returns:
            SummaryResponse with generated summary
            
        Raises:
            ValueError: If request is invalid
            RuntimeError: If API call fails
        """
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate API credentials.
        
        Returns:
            True if credentials valid, False otherwise
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI ChatGPT provider."""
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize OpenAI provider."""
        super().__init__(api_key, **kwargs)
        self.model = kwargs.get('model', 'gpt-4-turbo')
        
        # Lazy import (OpenAI SDK not always installed)
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self._available = True
        except ImportError:
            logger.warning("OpenAI SDK not installed (pip install openai)")
            self._available = False
    
    def validate_credentials(self) -> bool:
        """Validate OpenAI API key."""
        if not self._available:
            return False
        
        try:
            # Simple API test
            self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI credential validation failed: {e}")
            return False
    
    def summarize(self, request: SummaryRequest) -> SummaryResponse:
        """Generate summary using OpenAI."""
        if not self._available:
            raise RuntimeError("OpenAI SDK not available")
        
        # Build prompt
        prompt = self._build_prompt(request)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes transcripts concisely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=request.max_tokens,
                temperature=0.3
            )
            
            # Parse response
            summary_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Extract key points (simple split on bullet points)
            key_points = self._extract_key_points(summary_text)
            
            # Build source attribution
            attribution = None
            if request.media_url:
                attribution = f"Source: {request.media_url}"
            
            return SummaryResponse(
                summary=summary_text,
                key_points=key_points,
                source_attribution=attribution,
                provider="openai",
                tokens_used=tokens_used
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise RuntimeError(f"OpenAI summarization failed: {e}")
    
    def _build_prompt(self, request: SummaryRequest) -> str:
        """Build summarization prompt."""
        prompt_parts = [
            "Summarize the following transcript, focusing on key takeaways:",
            "",
            "Format:",
            "1. Executive summary (2-3 sentences)",
            "2. Key points (bullet list)",
            "",
            "Transcript:",
            request.transcript_text[:10000]  # Limit to avoid token overflow
        ]
        
        if request.include_timestamps:
            prompt_parts.insert(5, "3. Key moments with timestamps (if mentioned)")
        
        return "\n".join(prompt_parts)
    
    def _extract_key_points(self, summary_text: str) -> List[str]:
        """Extract key points from summary."""
        lines = summary_text.split('\n')
        key_points = []
        
        for line in lines:
            # Look for bullet points or numbered lists
            if line.strip().startswith(('-', '•', '*')) or (len(line) > 0 and line[0].isdigit()):
                point = line.strip().lstrip('-•*0123456789. ')
                if point:
                    key_points.append(point)
        
        return key_points if key_points else ["No key points extracted"]


class GeminiProvider(AIProvider):
    """Google Gemini provider."""
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize Gemini provider."""
        super().__init__(api_key, **kwargs)
        self.model = kwargs.get('model', 'gemini-pro')
        
        # Lazy import
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.model)
            self._available = True
        except ImportError:
            logger.warning("Google Gemini SDK not installed (pip install google-generativeai)")
            self._available = False
    
    def validate_credentials(self) -> bool:
        """Validate Gemini API key."""
        if not self._available:
            return False
        
        try:
            # Simple test
            response = self.client.generate_content("Test")
            return True
        except Exception as e:
            logger.error(f"Gemini credential validation failed: {e}")
            return False
    
    def summarize(self, request: SummaryRequest) -> SummaryResponse:
        """Generate summary using Gemini."""
        if not self._available:
            raise RuntimeError("Gemini SDK not available")
        
        prompt = self._build_prompt(request)
        
        try:
            response = self.client.generate_content(prompt)
            summary_text = response.text
            
            # Gemini doesn't return token count directly
            tokens_used = len(summary_text.split()) * 1.3  # Rough estimate
            
            key_points = self._extract_key_points(summary_text)
            
            attribution = None
            if request.media_url:
                attribution = f"Source: {request.media_url}"
            
            return SummaryResponse(
                summary=summary_text,
                key_points=key_points,
                source_attribution=attribution,
                provider="gemini",
                tokens_used=int(tokens_used)
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            raise RuntimeError(f"Gemini summarization failed: {e}")
    
    def _build_prompt(self, request: SummaryRequest) -> str:
        """Build summarization prompt."""
        return f"""Summarize this transcript concisely:

Format:
1. Executive summary (2-3 sentences)
2. Key takeaways (bullet list)

Transcript:
{request.transcript_text[:10000]}
"""
    
    def _extract_key_points(self, summary_text: str) -> List[str]:
        """Extract key points from summary."""
        lines = summary_text.split('\n')
        key_points = []
        
        for line in lines:
            if line.strip().startswith(('-', '•', '*')) or (len(line) > 0 and line[0].isdigit()):
                point = line.strip().lstrip('-•*0123456789. ')
                if point:
                    key_points.append(point)
        
        return key_points if key_points else ["No key points extracted"]


class AISummarizer:
    """
    Unified AI summarizer supporting multiple providers.
    
    Usage:
        summarizer = AISummarizer(provider="openai", api_key="sk-...")
        request = SummaryRequest(transcript_text="...", media_url="...")
        response = summarizer.summarize(request)
        print(response.summary)
    """
    
    PROVIDERS = {
        'openai': OpenAIProvider,
        'gemini': GeminiProvider,
        # Future: 'azure_openai': AzureOpenAIProvider,
        # Future: 'perplexity': PerplexityProvider
    }
    
    def __init__(self, provider: str, api_key: str, **kwargs):
        """
        Initialize AI summarizer.
        
        Args:
            provider: Provider name ('openai', 'gemini')
            api_key: API key for authentication
            **kwargs: Provider-specific configuration
            
        Raises:
            ValueError: If provider unsupported
        """
        if provider not in self.PROVIDERS:
            available = ', '.join(self.PROVIDERS.keys())
            raise ValueError(f"Unsupported provider '{provider}'. Available: {available}")
        
        provider_class = self.PROVIDERS[provider]
        self.provider = provider_class(api_key, **kwargs)
        self.provider_name = provider
        
        logger.info(f"Initialized AI summarizer: provider={provider}")
    
    def validate(self) -> bool:
        """
        Validate provider credentials.
        
        Returns:
            True if valid, False otherwise
        """
        return self.provider.validate_credentials()
    
    def summarize(self, request: SummaryRequest) -> SummaryResponse:
        """
        Generate summary from transcript.
        
        Args:
            request: Summary request
            
        Returns:
            Summary response with generated content
            
        Raises:
            RuntimeError: If summarization fails
        """
        logger.info(f"Generating summary: provider={self.provider_name}, tokens={request.max_tokens}")
        
        try:
            response = self.provider.summarize(request)
            logger.info(f"Summary generated: tokens_used={response.tokens_used}")
            return response
        except Exception as e:
            logger.error(f"Summarization failed: {e}", exc_info=True)
            raise


def create_summarizer(provider: str, api_key: str, **kwargs) -> AISummarizer:
    """
    Factory function to create AI summarizer.
    
    Args:
        provider: Provider name ('openai', 'gemini')
        api_key: API key
        **kwargs: Provider configuration
        
    Returns:
        Configured AISummarizer instance
        
    Example:
        summarizer = create_summarizer("openai", api_key="sk-...")
    """
    return AISummarizer(provider, api_key, **kwargs)
