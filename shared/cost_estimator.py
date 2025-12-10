#!/usr/bin/env python3
"""
Cost Estimator - Predict job costs before execution

Estimates costs based on:
- Audio duration
- Workflow type
- Enabled stages  
- Model selection

Related: Phase 5 Week 4 - Feature 2
Status: ✅ Implemented
"""

# Standard library
import wave
from pathlib import Path
from typing import Dict, Tuple, List

# Local
from shared.cost_tracker import PRICING_DATABASE
from shared.logger import get_logger

logger = get_logger(__name__)


class CostEstimator:
    """Estimate job costs before execution."""
    
    def __init__(self):
        """Initialize cost estimator with pricing database."""
        self.pricing = PRICING_DATABASE
    
    def estimate_asr_cost(self, duration_sec: float, model: str = "large-v3") -> float:
        """
        Estimate ASR cost (local = $0.00).
        
        Args:
            duration_sec: Audio duration in seconds
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Local ASR (MLX, WhisperX) = $0.00
        return 0.0
    
    def estimate_translation_cost(self, segment_count: int, target_langs: list) -> float:
        """
        Estimate translation cost (local IndicTrans2 = $0.00).
        
        Args:
            segment_count: Number of segments to translate
            target_langs: List of target languages
            
        Returns:
            Estimated cost in USD
        """
        # Local IndicTrans2 = $0.00
        return 0.0
    
    def estimate_summarization_cost(
        self, 
        transcript_length: int, 
        provider: str = "openai",
        model: str = "gpt-4o"
    ) -> float:
        """
        Estimate AI summarization cost.
        
        Args:
            transcript_length: Transcript character count
            provider: AI provider (openai, gemini)
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Estimate tokens (rough: 1 token ≈ 4 characters)
        estimated_tokens = transcript_length / 4
        
        # Typical split: 80% input, 20% output for summarization
        input_tokens = int(estimated_tokens * 0.8)
        output_tokens = int(estimated_tokens * 0.2)
        
        # Get pricing
        provider_pricing = self.pricing.get(provider, {})
        model_pricing = provider_pricing.get(model, {})
        
        if not model_pricing:
            logger.warning(f"No pricing for {provider}/{model}, using defaults")
            input_cost_per_1k = 0.01
            output_cost_per_1k = 0.03
        else:
            input_cost_per_1k = model_pricing.get("input_per_1k", 0.01)
            output_cost_per_1k = model_pricing.get("output_per_1k", 0.03)
        
        # Calculate cost
        cost = (
            (input_tokens / 1000) * input_cost_per_1k +
            (output_tokens / 1000) * output_cost_per_1k
        )
        
        return cost
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """
        Get audio duration in seconds.
        
        Args:
            audio_path: Path to audio/video file
            
        Returns:
            Duration in seconds
        """
        try:
            # Try WAV file first (most common for processing)
            with wave.open(str(audio_path), 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                return frames / float(rate)
        except Exception:
            # Fallback: estimate from file size
            # Assuming 44.1kHz stereo 16-bit (176400 bytes/sec)
            try:
                file_size = audio_path.stat().st_size
                return file_size / 176400
            except Exception as e:
                logger.warning(f"Could not determine audio duration: {e}")
                return 600.0  # Default: 10 minutes
    
    def estimate_job_cost(
        self,
        audio_path: Path,
        workflow: str,
        target_langs: List[str] = None,
        enable_summarization: bool = False,
        ai_provider: str = "openai",
        ai_model: str = "gpt-4o"
    ) -> Tuple[Dict[str, float], float]:
        """
        Estimate total job cost.
        
        Args:
            audio_path: Path to audio file
            workflow: Workflow name (transcribe/translate/subtitle)
            target_langs: List of target languages
            enable_summarization: Whether AI summarization is enabled
            ai_provider: AI provider for summarization
            ai_model: AI model for summarization
            
        Returns:
            Tuple of (breakdown dict, total cost)
        """
        breakdown = {}
        
        # Get audio duration
        duration_sec = self.get_audio_duration(audio_path)
        minutes = duration_sec / 60
        
        logger.debug(f"Estimating costs for {minutes:.1f} min audio, workflow={workflow}")
        
        # Stage costs (all local processing = $0.00)
        breakdown["demux"] = 0.0
        breakdown["tmdb"] = 0.0
        breakdown["glossary_load"] = 0.0
        breakdown["source_separation"] = 0.0
        breakdown["pyannote_vad"] = 0.0
        breakdown["asr"] = self.estimate_asr_cost(duration_sec)
        breakdown["alignment"] = 0.0
        
        if workflow in ["translate", "subtitle"]:
            # Estimate segments (rough: 1 segment per 5 seconds of speech)
            # Assume 60% of audio is speech (rest is silence/music)
            speech_duration = duration_sec * 0.6
            segment_count = int(speech_duration / 5)
            
            breakdown["translation"] = self.estimate_translation_cost(
                segment_count, 
                target_langs or ["en"]
            )
        
        if workflow == "subtitle":
            breakdown["lyrics_detection"] = 0.0
            breakdown["hallucination_removal"] = 0.0
            breakdown["subtitle_generation"] = 0.0
            breakdown["mux"] = 0.0
        
        if enable_summarization:
            # Estimate transcript length (rough: 150 words per minute)
            word_count = int(minutes * 150)
            char_count = word_count * 6  # Average word length + space
            
            breakdown["ai_summarization"] = self.estimate_summarization_cost(
                char_count,
                provider=ai_provider,
                model=ai_model
            )
        
        total = sum(breakdown.values())
        return breakdown, total


def show_cost_estimate(
    audio_path: Path,
    workflow: str,
    target_langs: List[str] = None,
    enable_summarization: bool = False,
    ai_provider: str = "openai",
    ai_model: str = "gpt-4o",
    budget: float = 50.0
) -> float:
    """
    Display cost estimate to user.
    
    Args:
        audio_path: Path to audio file
        workflow: Workflow name
        target_langs: Target languages
        enable_summarization: Whether summarization enabled
        ai_provider: AI provider for summarization
        ai_model: AI model for summarization
        budget: Monthly budget limit
        
    Returns:
        Estimated total cost
    """
    estimator = CostEstimator()
    breakdown, total = estimator.estimate_job_cost(
        audio_path, workflow, target_langs, enable_summarization,
        ai_provider, ai_model
    )
    
    # Get audio duration for display
    duration_sec = estimator.get_audio_duration(audio_path)
    minutes = duration_sec / 60
    
    print("\n" + "=" * 70)
    print("💰 Estimated Job Cost")
    print("=" * 70)
    print(f"\n📊 Job Details:")
    print(f"   Audio duration:     {minutes:.1f} minutes")
    print(f"   Workflow:           {workflow}")
    if target_langs:
        print(f"   Target languages:   {', '.join(target_langs)}")
    if enable_summarization:
        print(f"   AI Summarization:   Enabled ({ai_provider}/{ai_model})")
    
    print(f"\n💵 Cost Breakdown:")
    
    # Show non-zero costs only
    has_costs = False
    for stage, cost in breakdown.items():
        if cost > 0:
            has_costs = True
            print(f"   {stage:25s} ${cost:.4f}")
    
    if not has_costs:
        print(f"   {'All stages (local)':25s} $0.00")
    
    print("   " + "-" * 68)
    print(f"   {'TOTAL ESTIMATED':25s} ${total:.4f}")
    
    # Budget info
    print(f"\n💳 Budget Status:")
    percent = (total / budget * 100) if budget > 0 else 0
    remaining = budget - total
    
    print(f"   Monthly budget:      ${budget:.2f}")
    print(f"   This job:            ${total:.4f} ({percent:.1f}% of budget)")
    print(f"   Remaining:           ${remaining:.2f}")
    
    # Alert if significant cost
    if total > 0:
        if percent >= 10:
            print(f"\n⚠️  Note: This job will use {percent:.1f}% of your monthly budget")
        if total > 1.0:
            print(f"\n💡 Tip: Consider using a cheaper model or shorter audio")
    else:
        print(f"\n✅ This job uses only local processing (no API costs)")
    
    print("=" * 70)
    print()
    
    return total
