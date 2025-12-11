#!/usr/bin/env python3
"""
Unit tests for AI Summarizer Module

Tests the unified AI summarizer wrapper for multiple providers.
"""

# Standard library
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Third-party
import pytest

# Local
from shared.ai_summarizer import (
    SummaryRequest,
    SummaryResponse,
    AISummarizer,
    create_summarizer,
    OpenAIProvider
)


class TestSummaryRequest:
    """Test SummaryRequest dataclass."""
    
    def test_create_basic_request(self):
        """Test creating basic summary request."""
        request = SummaryRequest(transcript_text="This is a test transcript.")
        
        assert request.transcript_text == "This is a test transcript."
        assert request.media_url is None
        assert request.max_tokens == 500  # default
        assert request.language == "en"  # default
        assert request.include_timestamps is False  # default
    
    def test_create_full_request(self):
        """Test creating request with all parameters."""
        request = SummaryRequest(
            transcript_text="Full transcript text here.",
            media_url="https://example.com/video",
            max_tokens=1000,
            language="hi",
            include_timestamps=True
        )
        
        assert request.transcript_text == "Full transcript text here."
        assert request.media_url == "https://example.com/video"
        assert request.max_tokens == 1000
        assert request.language == "hi"
        assert request.include_timestamps is True


class TestSummaryResponse:
    """Test SummaryResponse dataclass."""
    
    def test_create_basic_response(self):
        """Test creating basic summary response."""
        response = SummaryResponse(
            summary="This is the summary.",
            key_points=["Point 1", "Point 2"]
        )
        
        assert response.summary == "This is the summary."
        assert len(response.key_points) == 2
        assert response.key_points[0] == "Point 1"
        assert response.timestamps is None  # default
        assert response.source_attribution is None  # default
        assert response.provider == ""  # default
        assert response.tokens_used == 0  # default
    
    def test_create_full_response(self):
        """Test creating response with all fields."""
        response = SummaryResponse(
            summary="Full summary text.",
            key_points=["Key 1", "Key 2", "Key 3"],
            timestamps=[{"timestamp": "00:05", "description": "Introduction"}],
            source_attribution="Source: https://example.com",
            provider="openai",
            tokens_used=350
        )
        
        assert response.summary == "Full summary text."
        assert len(response.key_points) == 3
        assert len(response.timestamps) == 1
        assert response.source_attribution == "Source: https://example.com"
        assert response.provider == "openai"
        assert response.tokens_used == 350


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    def test_initialization(self):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider(api_key="sk-test123")
        
        assert provider.api_key == "sk-test123"
        assert provider.model == "gpt-4-turbo"  # default
    
    def test_initialization_with_model(self):
        """Test initialization with custom model."""
        provider = OpenAIProvider(api_key="sk-test123", model="gpt-4o")
        
        assert provider.model == "gpt-4o"
    
    def test_build_prompt(self):
        """Test prompt building."""
        provider = OpenAIProvider(api_key="sk-test123")
        request = SummaryRequest(transcript_text="Sample transcript for testing.")
        
        prompt = provider._build_prompt(request)
        
        assert "Summarize the following transcript" in prompt
        assert "Executive summary" in prompt
        assert "Key points" in prompt
        assert "Sample transcript for testing." in prompt
    
    def test_build_prompt_with_timestamps(self):
        """Test prompt building with timestamps enabled."""
        provider = OpenAIProvider(api_key="sk-test123")
        request = SummaryRequest(
            transcript_text="Test transcript.",
            include_timestamps=True
        )
        
        prompt = provider._build_prompt(request)
        
        assert "Key moments with timestamps" in prompt
    
    def test_extract_key_points_bullets(self):
        """Test extracting key points from bullet list."""
        provider = OpenAIProvider(api_key="sk-test123")
        summary_text = """
Executive summary here.

Key takeaways:
- First key point
- Second key point
- Third key point
"""
        
        key_points = provider._extract_key_points(summary_text)
        
        assert len(key_points) == 3
        assert key_points[0] == "First key point"
        assert key_points[1] == "Second key point"
        assert key_points[2] == "Third key point"
    
    def test_extract_key_points_numbered(self):
        """Test extracting key points from numbered list."""
        provider = OpenAIProvider(api_key="sk-test123")
        summary_text = """
Summary paragraph.

Key points:
1. First numbered point
2. Second numbered point
3. Third numbered point
"""
        
        key_points = provider._extract_key_points(summary_text)
        
        assert len(key_points) == 3
        assert "First numbered point" in key_points[0]
        assert "Second numbered point" in key_points[1]
        assert "Third numbered point" in key_points[2]
    
    def test_extract_key_points_empty(self):
        """Test extracting key points from text without bullets."""
        provider = OpenAIProvider(api_key="sk-test123")
        summary_text = "Just a plain summary without any bullet points or lists."
        
        key_points = provider._extract_key_points(summary_text)
        
        assert len(key_points) == 1
        assert key_points[0] == "No key points extracted"


class TestAISummarizer:
    """Test unified AISummarizer class."""
    
    def test_initialization_openai(self):
        """Test initializing with OpenAI provider."""
        summarizer = AISummarizer(provider="openai", api_key="sk-test123")
        
        assert summarizer.provider_name == "openai"
        assert isinstance(summarizer.provider, OpenAIProvider)
    
    def test_initialization_gemini(self):
        """Test initializing with Gemini provider."""
        summarizer = AISummarizer(provider="gemini", api_key="test-key")
        
        assert summarizer.provider_name == "gemini"
    
    def test_initialization_unsupported_provider(self):
        """Test initialization with unsupported provider raises error."""
        with pytest.raises(ValueError) as exc_info:
            AISummarizer(provider="unsupported", api_key="test")
        
        assert "Unsupported provider" in str(exc_info.value)
        assert "openai" in str(exc_info.value)  # Shows available providers
    
    def test_create_summarizer_factory(self):
        """Test factory function."""
        summarizer = create_summarizer("openai", api_key="sk-test123")
        
        assert isinstance(summarizer, AISummarizer)
        assert summarizer.provider_name == "openai"
    
    def test_create_summarizer_with_model(self):
        """Test factory with custom model."""
        summarizer = create_summarizer("openai", api_key="sk-test", model="gpt-4o")
        
        assert summarizer.provider.model == "gpt-4o"


class TestProviderRegistry:
    """Test provider registry."""
    
    def test_available_providers(self):
        """Test that expected providers are registered."""
        available = list(AISummarizer.PROVIDERS.keys())
        
        assert "openai" in available
        assert "gemini" in available
    
    def test_provider_classes(self):
        """Test that provider classes are correct."""
        assert AISummarizer.PROVIDERS["openai"] == OpenAIProvider


# Integration tests would go here (require real API keys)
# class TestIntegration:
#     @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No OpenAI API key")
#     def test_real_openai_summarization(self):
#         ...
