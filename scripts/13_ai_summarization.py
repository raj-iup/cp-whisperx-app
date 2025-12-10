#!/usr/bin/env python3
"""
Stage 13: AI-Powered Transcript Summarization

Generates AI-powered summaries from transcripts using configured chatbot provider.

Optional stage (enable with --enable-summarization flag):
- Reads transcript from Stage 07 alignment output
- Uses AI provider credentials from user profile
- Generates executive summary + key points
- Appends source attribution if media URL provided
- Outputs transcript_summary.txt

Architecture Decision: AD-015 (User Profile Architecture) - Task #19
Related: PRD-2025-12-10-03-ai-summarization, TRD-2025-12-10-03-ai-summarization
"""

# Standard library
import sys
import json
from pathlib import Path
from typing import Optional

# Local
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config_loader import load_config
from shared.stage_utils import StageIO
from shared.ai_summarizer import create_summarizer, SummaryRequest


def run_stage(job_dir: Path, stage_name: str = "13_ai_summarization") -> int:
    """
    Run AI summarization stage.
    
    Args:
        job_dir: Job directory path
        stage_name: Stage name (default: 13_ai_summarization)
        
    Returns:
        Exit code (0=success, 1=error)
    """
    # Initialize StageIO with manifest tracking
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    logger.info("=" * 80)
    logger.info(f"STAGE 13: AI-POWERED SUMMARIZATION")
    logger.info("=" * 80)
    
    try:
        # Load configuration
        config = load_config(job_dir)
        
        # Check if summarization enabled
        enabled = config.get("SUMMARIZATION_ENABLED", "false").lower() == "true"
        if not enabled:
            logger.info("⏭️  AI summarization disabled (SUMMARIZATION_ENABLED=false)")
            logger.info("✅ Stage 13 skipped (disabled)")
            io.finalize_stage_manifest(exit_code=0)
            return 0
        
        # Load userId from job.json (AD-006)
        job_json_path = job_dir / "job.json"
        user_id = 1  # Default fallback
        if job_json_path.exists():
            try:
                with open(job_json_path, 'r') as f:
                    job_data = json.load(f)
                    user_id = int(job_data.get('user_id', 1))
                    logger.debug(f"Loaded userId from job.json: {user_id}")
            except Exception as e:
                logger.warning(f"Failed to load userId from job.json: {e}")
        
        # Load user profile for API credentials
        from shared.user_profile import UserProfile
        profile = UserProfile.load(user_id, logger_instance=logger)
        
        # Get AI provider configuration
        provider = config.get("AI_PROVIDER", "openai").lower()
        
        # Load API key from user profile (preferred) or fallback to config
        api_key = profile.get_credential(provider, 'api_key')
        if not api_key:
            # Fallback to config for backward compatibility
            api_key = config.get(f"{provider.upper()}_API_KEY", "")
        
        if not api_key:
            logger.error(f"❌ No API key found for provider '{provider}'")
            logger.error(f"   Add to user profile: users/{user_id}/profile.json")
            logger.error(f"   Or set {provider.upper()}_API_KEY in config")
            io.finalize_stage_manifest(exit_code=1)
            return 1
        
        logger.info(f"✓ Loaded {provider} API key from user profile (userId={user_id})")
        
        # Find transcript from Stage 07 (alignment)
        alignment_dir = io.job_dir / "07_alignment"
        transcript_file = alignment_dir / "transcript.txt"
        
        if not transcript_file.exists():
            logger.error(f"❌ Transcript not found: {transcript_file}")
            logger.error("   Stage 07 (alignment) must complete first")
            io.finalize_stage_manifest(exit_code=1)
            return 1
        
        # Track input
        io.manifest.add_input(transcript_file, io.compute_hash(transcript_file))
        logger.info(f"📄 Input transcript: {transcript_file.name} ({transcript_file.stat().st_size} bytes)")
        
        # Read transcript
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
        
        if not transcript_text.strip():
            logger.error("❌ Transcript is empty")
            io.finalize_stage_manifest(exit_code=1)
            return 1
        
        logger.info(f"📊 Transcript length: {len(transcript_text)} characters, {len(transcript_text.split())} words")
        
        # Get optional media URL for source attribution
        media_url = config.get("MEDIA_URL", None)
        if media_url:
            logger.info(f"🔗 Source attribution: {media_url}")
        
        # Get summarization parameters
        max_tokens = int(config.get("SUMMARIZATION_MAX_TOKENS", "500"))
        language = config.get("SUMMARIZATION_LANGUAGE", "en")
        include_timestamps = config.get("SUMMARIZATION_INCLUDE_TIMESTAMPS", "false").lower() == "true"
        
        logger.info(f"⚙️  Parameters: max_tokens={max_tokens}, language={language}, timestamps={include_timestamps}")
        
        # Initialize AI summarizer
        logger.info(f"🤖 Initializing AI summarizer: provider={provider}")
        try:
            summarizer = create_summarizer(provider, api_key)
        except Exception as e:
            logger.error(f"❌ Failed to initialize summarizer: {e}")
            io.finalize_stage_manifest(exit_code=1)
            return 1
        
        # Validate credentials
        logger.info(f"🔐 Validating {provider} credentials...")
        if not summarizer.validate():
            logger.error(f"❌ Invalid API credentials for {provider}")
            logger.error(f"   Check {provider.upper()}_API_KEY in config/user.profile")
            io.finalize_stage_manifest(exit_code=1)
            return 1
        
        logger.info(f"✅ Credentials valid for {provider}")
        
        # Create summary request
        request = SummaryRequest(
            transcript_text=transcript_text,
            media_url=media_url,
            max_tokens=max_tokens,
            language=language,
            include_timestamps=include_timestamps
        )
        
        # Generate summary
        logger.info(f"🧠 Generating summary using {provider}...")
        try:
            response = summarizer.summarize(request)
        except Exception as e:
            logger.error(f"❌ Summarization failed: {e}", exc_info=True)
            io.finalize_stage_manifest(exit_code=1)
            return 1
        
        logger.info(f"✅ Summary generated: {response.tokens_used} tokens used")
        logger.info(f"   Key points: {len(response.key_points)}")
        
        # Build summary output
        summary_parts = []
        summary_parts.append("# Transcript Summary")
        summary_parts.append("")
        summary_parts.append("## Executive Summary")
        summary_parts.append(response.summary)
        summary_parts.append("")
        summary_parts.append("## Key Takeaways")
        for i, point in enumerate(response.key_points, 1):
            summary_parts.append(f"{i}. {point}")
        summary_parts.append("")
        
        # Add timestamps if present
        if response.timestamps:
            summary_parts.append("## Key Moments")
            for ts in response.timestamps:
                summary_parts.append(f"- {ts['timestamp']}: {ts['description']}")
            summary_parts.append("")
        
        # Add source attribution
        if response.source_attribution:
            summary_parts.append("## Source")
            summary_parts.append(response.source_attribution)
            summary_parts.append("")
        
        # Add metadata
        summary_parts.append("---")
        summary_parts.append(f"*Generated by: {response.provider}*")
        summary_parts.append(f"*Tokens used: {response.tokens_used}*")
        
        summary_output = "\n".join(summary_parts)
        
        # Define output files
        summary_file = io.stage_dir / "transcript_summary.txt"
        summary_json = io.stage_dir / "summary_metadata.json"
        
        # Write summary text
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_output)
        
        io.manifest.add_output(summary_file, io.compute_hash(summary_file))
        logger.info(f"📝 Summary saved: {summary_file.name} ({summary_file.stat().st_size} bytes)")
        
        # Write summary metadata (JSON)
        metadata = {
            "provider": response.provider,
            "tokens_used": response.tokens_used,
            "key_points_count": len(response.key_points),
            "has_timestamps": response.timestamps is not None,
            "source_url": media_url,
            "language": language
        }
        
        with open(summary_json, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        io.manifest.add_output(summary_json, io.compute_hash(summary_json))
        logger.info(f"📊 Metadata saved: {summary_json.name}")
        
        # Success!
        logger.info("=" * 80)
        logger.info("✅ AI SUMMARIZATION COMPLETE")
        logger.info(f"   Summary: {len(summary_output)} characters")
        logger.info(f"   Key points: {len(response.key_points)}")
        logger.info(f"   Provider: {response.provider}")
        logger.info(f"   Tokens: {response.tokens_used}")
        logger.info("=" * 80)
        
        io.finalize_stage_manifest(exit_code=0)
        return 0
        
    except Exception as e:
        logger.error(f"❌ Stage 13 failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1


def main() -> int:
    """
    Main entry point for Stage 13.
    
    Usage:
        python3 scripts/13_ai_summarization.py <job_dir>
    
    Returns:
        Exit code
    """
    if len(sys.argv) != 2:
        logger = get_logger(__name__)
        logger.error("Usage: 13_ai_summarization.py <job_dir>")
        logger.error("Example: 13_ai_summarization.py out/2025/12/10/rpatel/1")
        return 1
    
    job_dir = Path(sys.argv[1])
    
    if not job_dir.exists():
        logger = get_logger(__name__)
        logger.error(f"Error: Job directory not found: {job_dir}")
        return 1
    
    return run_stage(job_dir)


if __name__ == "__main__":
    sys.exit(main())
