# TRD: AI-Powered Transcript Summarization

**ID:** TRD-2025-12-10-03  
**Created:** 2025-12-10  
**Status:** Draft  
**Related BRD:** [BRD-2025-12-10-03-ai-summarization](../brd/BRD-2025-12-10-03-ai-summarization.md)  
**Related PRD:** [PRD-2025-12-10-03-ai-summarization](../prd/PRD-2025-12-10-03-ai-summarization.md)

---

## I. Executive Summary

### Summary

Implement optional AI-powered transcript summarization as Stage 13 in the transcribe workflow. Users configure AI chatbot credentials (ChatGPT, Copilot, Gemini, Perplexity) once in their user profile, then receive automatic summaries with source attribution after transcription completes.

**Key Technical Principles:**
- User profile architecture (AD-015)
- Optional stage (graceful degradation)
- Unified API wrapper (provider abstraction)
- No pipeline changes (Stages 01-07 unchanged)
- StageIO pattern compliance

### Approach

**Architecture Philosophy:**
```
User Profile → Credential Extraction → Stage 13 (Optional) → Summary Output
```

**Single Responsibility:**
1. **User Profile:** Store AI credentials persistently (AD-015)
2. **prepare-job.sh:** Extract credentials and validate
3. **shared/ai_summarizer.py:** Unified API wrapper (4 providers)
4. **scripts/13_ai_summarization.py:** Stage implementation
5. **Existing Pipeline:** Unchanged (Stages 01-07)

**Data Flow:**
```
Transcript (Stage 07) → Read transcript.txt
        ↓
Load AI credentials from user profile
        ↓
Call selected AI provider API
        ↓
Receive summary text
        ↓
Append source attribution
        ↓
Save transcript_summary.txt (Stage 13)
```

---

## II. Architecture Changes

### Affected Components

**NEW Components:**
```
shared/ai_summarizer.py              # Unified API wrapper (~300 LOC)
scripts/13_ai_summarization.py       # New stage (~200 LOC)
requirements/requirements-ai.txt     # AI SDK dependencies
```

**MODIFIED Components:**
```
prepare-job.sh                       # +20 LOC (extract AI credentials)
config/.env.pipeline                 # +25 LOC (AI configuration section)
config/user.profile.template         # +40 LOC ([ai_chatbots] section)
```

**UNCHANGED Components:**
```
scripts/01_demux.py → 07_alignment.py    # All existing stages
shared/config_loader.py                   # Reused as-is
shared/user_profile.py                    # Reused (AD-015)
shared/logger.py                          # Reused as-is
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ User Profile (config/user.profile)                          │
│   [ai_chatbots]                                              │
│     openai_api_key=sk-...                                    │
│     gemini_api_key=...                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ prepare-job.sh: Extract credentials if --enable-summarization│
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Transcription Pipeline (Stages 01-07) - UNCHANGED           │
│   Output: transcript.txt                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
            ┌─────────────┴──────────────┐
            │                            │
    Summarization       Summarization
    Enabled?            Disabled?
            │                            │
            ↓                            ↓
┌─────────────────────────┐   ┌──────────────────┐
│ Stage 13: AI Summary    │   │ Skip Stage 13    │
│                         │   │ Job completes    │
│ shared/ai_summarizer:   │   └──────────────────┘
│  - Load credentials     │
│  - Select provider      │
│  - Call API             │
│  - Handle errors        │
│  - Append source        │
│  - Save summary         │
└─────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────────────┐
│ Output: transcript_summary.txt + stage_manifest.json        │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

**1. prepare-job.sh Integration:**
```bash
# Add after argument parsing, before job creation

# NEW: Check if summarization enabled
if [[ "$ENABLE_SUMMARIZATION" == "true" ]]; then
    # Load user profile
    if [[ -f "config/user.profile" ]]; then
        # Extract AI chatbot credentials
        eval $(python3 shared/user_profile.py --export ai_chatbots)
    else
        log_error "AI summarization enabled but no user profile found"
        log_error "Create config/user.profile with [ai_chatbots] section"
        exit 1
    fi
    
    # Validate credentials for selected provider
    PROVIDER="${AI_PROVIDER:-}"
    if [[ -z "$PROVIDER" ]]; then
        # Auto-detect first configured provider
        if [[ -n "$OPENAI_API_KEY" ]]; then
            PROVIDER="openai"
        elif [[ -n "$GEMINI_API_KEY" ]]; then
            PROVIDER="gemini"
        elif [[ -n "$AZURE_OPENAI_API_KEY" ]]; then
            PROVIDER="azure_openai"
        elif [[ -n "$PERPLEXITY_API_KEY" ]]; then
            PROVIDER="perplexity"
        else
            log_error "No AI provider credentials found in user profile"
            log_error "Configure at least one provider in config/user.profile"
            exit 1
        fi
    fi
    
    # Validate provider-specific credentials
    case "$PROVIDER" in
        openai)
            [[ -z "$OPENAI_API_KEY" ]] && log_error "OpenAI API key missing" && exit 1
            ;;
        gemini)
            [[ -z "$GEMINI_API_KEY" ]] && log_error "Gemini API key missing" && exit 1
            ;;
        azure_openai)
            [[ -z "$AZURE_OPENAI_API_KEY" ]] && log_error "Azure OpenAI key missing" && exit 1
            ;;
        perplexity)
            [[ -z "$PERPLEXITY_API_KEY" ]] && log_error "Perplexity key missing" && exit 1
            ;;
        *)
            log_error "Invalid AI provider: $PROVIDER"
            log_error "Valid: openai, azure_openai, gemini, perplexity"
            exit 1
            ;;
    esac
    
    log_info "AI summarization enabled (provider: $PROVIDER)"
fi

# Continue with normal job creation
```

**2. Configuration Integration:**
```bash
# config/.env.pipeline (new section)

# ============================================================================
# AI Summarization
# ============================================================================
# Status: ⏳ Implemented (v3.2)
# Purpose: Enable AI-powered transcript summarization

# Enable AI summarization globally (true/false)
# Default: true (but requires --enable-summarization flag per job)
# Impact: Allows Stage 13 to run when enabled per job
AI_SUMMARIZATION_ENABLED=true

# Default AI provider (if not specified in job)
# Options: openai, azure_openai, gemini, perplexity
# Default: first configured provider in user profile
# Impact: Used when --ai-provider not specified
AI_SUMMARIZATION_DEFAULT_PROVIDER=

# API timeout (seconds)
# Default: 60
# Impact: Longer transcripts may need more time
AI_SUMMARIZATION_TIMEOUT=60

# Maximum transcript length (tokens)
# Default: 100000 (approx 400 pages)
# Impact: Longer transcripts may be truncated or chunked
AI_SUMMARIZATION_MAX_TOKENS=100000

# Default prompt template
# Default: "Summarize the key takeaways from the following transcript:"
# Impact: Sent to AI along with transcript text
# Note: Phase 2 will support custom prompts
AI_SUMMARIZATION_PROMPT="Summarize the key takeaways from the following transcript:"

# Token usage warnings
# Warn if estimated cost exceeds threshold (USD)
# Default: 1.00
# Impact: User notified before API call if cost >$1
AI_SUMMARIZATION_COST_WARNING_USD=1.00

# Retry configuration
# Retry on transient failures (network errors, rate limits)
# Default: 2 retries with exponential backoff
AI_SUMMARIZATION_MAX_RETRIES=2

# NOTE: API credentials are stored in config/user.profile (not here)
# See: config/user.profile.template for setup instructions
```

```ini
# config/user.profile (template extension)

# ============================================================================
# AI Chatbot Credentials
# ============================================================================
# Configure your preferred AI chatbot(s) for transcript summarization
# You only need to configure the provider(s) you want to use
# This file is NOT version controlled (.gitignore)

[ai_chatbots]
# OpenAI (ChatGPT)
# Get API key: https://platform.openai.com/api-keys
# Pricing: ~$0.01-0.03 per summary (gpt-4-turbo)
# Models: gpt-4-turbo (recommended), gpt-3.5-turbo (faster/cheaper)
openai_api_key=
openai_model=gpt-4-turbo

# Azure OpenAI (Microsoft Copilot)
# Requires Azure account and OpenAI resource
# Get credentials: https://portal.azure.com
# Pricing: Similar to OpenAI
azure_openai_api_key=
azure_openai_endpoint=
azure_openai_deployment=
azure_openai_api_version=2024-02-01

# Google Gemini
# Get API key: https://makersuite.google.com/app/apikey
# Pricing: Free tier available, then $0.00025/1K chars
# Models: gemini-pro
gemini_api_key=
gemini_model=gemini-pro

# Perplexity AI
# Get API key: https://www.perplexity.ai/settings/api
# Pricing: $0.20-1.00 per 1M tokens
# Models: pplx-7b-online (fast), pplx-70b-online (better quality)
perplexity_api_key=
perplexity_model=pplx-7b-online
```

**3. Stage Pipeline Integration:**
```
Transcribe workflow with summarization:
  Stage 01: Demux
  Stage 02: [SKIPPED - TMDB not needed]
  Stage 03: Glossary Load
  Stage 04: Source Separation (optional)
  Stage 05: PyAnnote VAD
  Stage 06: WhisperX ASR
  Stage 07: Alignment → transcript.txt
  Stage 13: AI Summarization (NEW - optional) → transcript_summary.txt
```

---

## III. Design Decisions

### Decision 1: User Profile for Credentials (AD-015)

**Problem:** Where to store AI API credentials?

**Options:**
1. **CLI parameters** - ❌ Rejected
   - Reason: Insecure (visible in process list, shell history)
   
2. **Environment variables** - ❌ Rejected
   - Reason: Can leak, not persistent
   
3. **Per-job config** - ❌ Rejected
   - Reason: User must re-enter for every job
   
4. **User profile (config/user.profile)** - ✅ Selected
   - Reason: Persistent, secure, AD-015 compliant
   - Follows established pattern from online media integration
   - Single configuration point for all jobs

**Rationale:**
- Consistent with AD-015 (User Profile Architecture)
- Configure once, use in all jobs
- Never version controlled
- User controls data (can delete anytime)

---

### Decision 2: Optional Stage (Graceful Degradation)

**Problem:** Should summarization failure break the job?

**Options:**
1. **Fail entire job on API failure** - ❌ Rejected
   - Reason: User loses transcript work due to external API issue
   
2. **Graceful degradation** - ✅ Selected
   - Reason: Transcript is primary output, summary is bonus
   - Log warning (not error) on API failure
   - Job completes successfully (exit code 0)
   - User gets transcript even if summary fails

**Rationale:**
- Transcription is the core feature
- Summary is value-add (optional)
- External API failures shouldn't break pipeline
- User can retry summarization later if needed

---

### Decision 3: Unified API Wrapper

**Problem:** How to integrate 4 different AI providers?

**Options:**
1. **Direct SDK calls in stage** - ❌ Rejected
   - Reason: Code duplication, hard to maintain
   
2. **Separate stage per provider** - ❌ Rejected
   - Reason: 4x code duplication, complex pipeline
   
3. **Unified wrapper (shared/ai_summarizer.py)** - ✅ Selected
   - Reason: Single interface, provider abstraction
   - Easy to add new providers
   - Centralized error handling
   - Token tracking in one place

**Rationale:**
- Follow DRY principle
- Provider-agnostic stage implementation
- Easy to test (mock wrapper)
- Scalable (add providers without changing stage)

---

### Decision 4: New Stage vs. Post-Processing

**Problem:** Where to add summarization logic?

**Options:**
1. **Modify Stage 07 (alignment)** - ❌ Rejected
   - Reason: Violates single responsibility
   - Stage 07 should only do alignment
   
2. **Post-processing script** - ❌ Rejected
   - Reason: Not tracked in manifest
   - Harder to manage (outside pipeline)
   
3. **New Stage 13** - ✅ Selected
   - Reason: Clean separation of concerns
   - Proper manifest tracking
   - Optional stage (can be skipped)
   - Follows established pattern

**Rationale:**
- Maintains single responsibility per stage
- Proper input/output tracking
- Stage manifest includes tokens/cost
- Easy to enable/disable per job

---

### Decision 5: Source Attribution Format

**Problem:** How to attribute the source in summaries?

**Options:**
1. **No attribution** - ❌ Rejected
   - Reason: Users lose reference to original content
   
2. **Metadata file** - ❌ Rejected
   - Reason: Extra file, easy to lose association
   
3. **Append to summary** - ✅ Selected
   - Reason: Self-contained, always together
   - Format: "\n\nSource: [media_source]"
   - Works for online URLs and local files

**Rationale:**
- Content creators need source for citations
- Researchers need reference for papers
- Single file easier to manage
- Follows common practice (email signatures, etc.)

---

## IV. Implementation Requirements

### Code Changes

#### New Files

**1. shared/ai_summarizer.py** (~300 LOC)
```python
#!/usr/bin/env python3
"""
Unified AI Summarizer Wrapper for CP-WhisperX-App

Responsibilities:
- Abstract 4 AI provider APIs (OpenAI, Azure, Gemini, Perplexity)
- Handle authentication and requests
- Track token usage and estimate costs
- Implement retry logic for transient failures
- Never log credentials or API responses
"""

from pathlib import Path
from typing import Optional, Dict, Tuple
from abc import ABC, abstractmethod
import time

# Key Classes:

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def summarize(self, text: str, prompt: str) -> Tuple[str, Dict]:
        """
        Generate summary from text
        
        Returns:
            Tuple[summary_text, metadata]
            metadata includes: tokens_input, tokens_output, cost_usd
        """
        pass

class OpenAIProvider(AIProvider):
    """OpenAI (ChatGPT) implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def summarize(self, text: str, prompt: str) -> Tuple[str, Dict]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes transcripts."},
                {"role": "user", "content": f"{prompt}\n\n{text}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        summary = response.choices[0].message.content
        metadata = {
            "tokens_input": response.usage.prompt_tokens,
            "tokens_output": response.usage.completion_tokens,
            "tokens_total": response.usage.total_tokens,
            "cost_usd": self._estimate_cost(response.usage),
            "model": self.model
        }
        
        return summary, metadata
    
    def _estimate_cost(self, usage) -> float:
        # gpt-4-turbo: $0.01/1K input, $0.03/1K output
        input_cost = (usage.prompt_tokens / 1000) * 0.01
        output_cost = (usage.completion_tokens / 1000) * 0.03
        return round(input_cost + output_cost, 4)

class GeminiProvider(AIProvider):
    """Google Gemini implementation"""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
    
    def summarize(self, text: str, prompt: str) -> Tuple[str, Dict]:
        full_prompt = f"{prompt}\n\n{text}"
        response = self.model.generate_content(full_prompt)
        
        summary = response.text
        # Gemini doesn't provide token counts directly, estimate
        tokens_input = len(full_prompt) // 4
        tokens_output = len(summary) // 4
        
        metadata = {
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "tokens_total": tokens_input + tokens_output,
            "cost_usd": self._estimate_cost(tokens_input, tokens_output),
            "model": self.model_name
        }
        
        return summary, metadata
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Gemini: $0.00025/1K chars (approx $0.001/1K tokens)
        return round((input_tokens + output_tokens) / 1000 * 0.001, 4)

class AzureOpenAIProvider(AIProvider):
    """Azure OpenAI (Copilot) implementation"""
    # Similar to OpenAIProvider but with Azure endpoint

class PerplexityProvider(AIProvider):
    """Perplexity AI implementation"""
    # Similar to OpenAIProvider (compatible API)

class AISummarizer:
    """Main wrapper class"""
    
    def __init__(self, provider_name: str, credentials: Dict, logger):
        self.logger = logger
        self.provider = self._create_provider(provider_name, credentials)
        self.provider_name = provider_name
    
    def _create_provider(self, name: str, creds: Dict) -> AIProvider:
        """Factory method to create provider instance"""
        if name == "openai":
            return OpenAIProvider(
                api_key=creds["openai_api_key"],
                model=creds.get("openai_model", "gpt-4-turbo")
            )
        elif name == "gemini":
            return GeminiProvider(
                api_key=creds["gemini_api_key"],
                model=creds.get("gemini_model", "gemini-pro")
            )
        # ... other providers
        else:
            raise ValueError(f"Unknown provider: {name}")
    
    def summarize_transcript(self, 
                           transcript_path: Path, 
                           prompt: str,
                           max_tokens: int = 100000,
                           timeout: int = 60) -> Tuple[str, Dict]:
        """
        Summarize transcript file
        
        Returns:
            Tuple[summary_text, metadata]
        """
        # Read transcript
        with open(transcript_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Check length
        estimated_tokens = len(text) // 4
        if estimated_tokens > max_tokens:
            self.logger.warning(
                f"Transcript length ({estimated_tokens} tokens) exceeds max ({max_tokens})"
            )
            # Truncate or chunk (Phase 2 feature)
            text = text[:max_tokens * 4]
        
        # Call provider with retry logic
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                summary, metadata = self.provider.summarize(text, prompt)
                metadata["provider"] = self.provider_name
                return summary, metadata
                
            except Exception as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(
                        f"API call failed (attempt {attempt+1}/{max_retries+1}): {e}"
                    )
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise  # Final attempt failed, re-raise
```

**2. scripts/13_ai_summarization.py** (~200 LOC)
```python
#!/usr/bin/env python3
"""
Stage 13: AI-Powered Transcript Summarization

Responsibilities:
- Read transcript from Stage 07
- Load AI provider credentials from user profile
- Call AI API to generate summary
- Append source attribution
- Save summary file
- Track token usage in manifest
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config_loader import load_config
from shared.stage_utils import StageIO
from shared.ai_summarizer import AISummarizer

def run_stage(job_dir: Path, stage_name: str = "13_ai_summarization") -> int:
    """
    Run AI summarization stage
    
    Returns:
        0 on success, 1 on failure
    """
    # Initialize StageIO
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        # Load configuration
        config = load_config(job_dir)
        
        # Check if summarization is enabled
        if not config.get("AI_SUMMARIZATION_ENABLED", "true").lower() == "true":
            logger.info("AI summarization disabled in config, skipping")
            io.finalize_stage_manifest(exit_code=0, skipped=True)
            return 0
        
        # Load job metadata for source attribution
        import json
        job_json_path = job_dir / "job.json"
        with open(job_json_path) as f:
            job_data = json.load(f)
        
        media_source = job_data.get("media_source", "unknown")
        ai_provider = job_data.get("ai_provider", "openai")
        
        # Find transcript file
        transcript_path = io.job_dir / "07_alignment" / "transcript.txt"
        if not transcript_path.exists():
            logger.error(f"Transcript not found: {transcript_path}")
            io.finalize_stage_manifest(exit_code=1)
            return 1
        
        io.manifest.add_input(transcript_path, io.compute_hash(transcript_path))
        
        # Load AI credentials from job config (extracted from user profile)
        credentials = {}
        if ai_provider == "openai":
            credentials["openai_api_key"] = config.get("OPENAI_API_KEY")
            credentials["openai_model"] = config.get("OPENAI_MODEL", "gpt-4-turbo")
        elif ai_provider == "gemini":
            credentials["gemini_api_key"] = config.get("GEMINI_API_KEY")
            credentials["gemini_model"] = config.get("GEMINI_MODEL", "gemini-pro")
        # ... other providers
        
        # Validate credentials
        api_key_field = f"{ai_provider}_api_key"
        if not credentials.get(api_key_field):
            logger.error(f"Missing API key for provider: {ai_provider}")
            logger.error("Check config/user.profile [ai_chatbots] section")
            io.finalize_stage_manifest(exit_code=1)
            return 1
        
        # Initialize AI summarizer
        logger.info(f"Initializing AI summarizer (provider: {ai_provider})...")
        summarizer = AISummarizer(ai_provider, credentials, logger)
        
        # Get configuration
        prompt = config.get(
            "AI_SUMMARIZATION_PROMPT",
            "Summarize the key takeaways from the following transcript:"
        )
        max_tokens = int(config.get("AI_SUMMARIZATION_MAX_TOKENS", "100000"))
        timeout = int(config.get("AI_SUMMARIZATION_TIMEOUT", "60"))
        
        # Generate summary
        logger.info("Calling AI API to generate summary...")
        try:
            summary, metadata = summarizer.summarize_transcript(
                transcript_path=transcript_path,
                prompt=prompt,
                max_tokens=max_tokens,
                timeout=timeout
            )
        except Exception as e:
            logger.warning(f"AI summarization failed: {e}", exc_info=True)
            logger.warning("Skipping summary generation, job continues")
            io.finalize_stage_manifest(exit_code=0, skipped=True)
            return 0  # Graceful degradation
        
        # Log token usage
        logger.info(
            f"Summary generated: {metadata['tokens_total']} tokens, "
            f"estimated cost: ${metadata['cost_usd']:.4f}"
        )
        
        # Append source attribution
        source_line = f"\n\nSource: {media_source}"
        summary_with_source = summary + source_line
        
        # Save summary
        summary_path = io.stage_dir / "transcript_summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_with_source)
        
        io.manifest.add_output(summary_path, io.compute_hash(summary_path))
        
        # Add metadata to manifest
        io.manifest.metadata.update(metadata)
        
        logger.info(f"Summary saved: {summary_path}")
        logger.info(f"Summary length: {len(summary.split())} words")
        
        # Finalize
        io.finalize_stage_manifest(exit_code=0)
        return 0
        
    except Exception as e:
        logger.error(f"Stage failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: 13_ai_summarization.py <job_dir>")
        sys.exit(1)
    
    job_dir = Path(sys.argv[1])
    sys.exit(run_stage(job_dir))
```

**3. requirements/requirements-ai.txt**
```
# AI Summarization Dependencies
openai>=1.3.0
google-generativeai>=0.3.0
requests>=2.31.0
```

#### Modified Files

**1. prepare-job.sh** (+20 LOC)
- Extract AI credentials from user profile if `--enable-summarization`
- Validate credentials for selected provider
- Store in job config for Stage 13

**2. config/.env.pipeline** (+25 LOC)
- Add AI Summarization section
- Document all configuration parameters
- Reference user profile for credentials

**3. config/user.profile.template** (+40 LOC)
- Add [ai_chatbots] section
- Document all 4 providers
- Include API key instructions and pricing

---

## V. API Specifications

### shared/ai_summarizer.py API

**AISummarizer Class:**
```python
class AISummarizer:
    """Main wrapper for AI summarization"""
    
    def __init__(self, 
                 provider_name: str, 
                 credentials: Dict[str, str], 
                 logger: logging.Logger):
        """
        Initialize summarizer
        
        Args:
            provider_name: "openai", "gemini", "azure_openai", or "perplexity"
            credentials: Dict with API keys and models
            logger: Logger instance
        """
        pass
    
    def summarize_transcript(self, 
                           transcript_path: Path, 
                           prompt: str,
                           max_tokens: int = 100000,
                           timeout: int = 60) -> Tuple[str, Dict]:
        """
        Generate summary from transcript file
        
        Args:
            transcript_path: Path to transcript.txt
            prompt: Instruction for AI
            max_tokens: Maximum input length
            timeout: API timeout in seconds
            
        Returns:
            Tuple[summary_text, metadata_dict]
            
        Raises:
            FileNotFoundError: Transcript not found
            ValueError: Invalid provider or credentials
            TimeoutError: API timeout
            Exception: API errors
        """
        pass
```

**Metadata Dictionary:**
```python
{
    "provider": "openai",
    "model": "gpt-4-turbo",
    "tokens_input": 5234,
    "tokens_output": 387,
    "tokens_total": 5621,
    "cost_usd": 0.0254,
    "duration_seconds": 42.3
}
```

### scripts/13_ai_summarization.py API

**run_stage Function:**
```python
def run_stage(job_dir: Path, stage_name: str = "13_ai_summarization") -> int:
    """
    Run AI summarization stage
    
    Args:
        job_dir: Path to job directory
        stage_name: Stage identifier
        
    Returns:
        0: Success or graceful skip
        1: Failure (only on critical errors like missing transcript)
        
    Side Effects:
        - Creates 13_ai_summarization/ directory
        - Writes transcript_summary.txt
        - Writes stage_manifest.json
        - Logs to stage log file
    """
    pass
```

---

## VI. Data Models

### Stage Manifest Schema

```json
{
  "stage": "13_ai_summarization",
  "status": "completed",
  "timestamp_start": "2025-12-10T14:30:00Z",
  "timestamp_end": "2025-12-10T14:30:42Z",
  "duration_seconds": 42.3,
  "exit_code": 0,
  "inputs": {
    "transcript": {
      "path": "07_alignment/transcript.txt",
      "hash": "sha256:abc123...",
      "size_bytes": 52341
    }
  },
  "outputs": {
    "summary": {
      "path": "13_ai_summarization/transcript_summary.txt",
      "hash": "sha256:def456...",
      "size_bytes": 1234
    }
  },
  "metadata": {
    "ai_provider": "openai",
    "model": "gpt-4-turbo",
    "prompt": "Summarize the key takeaways from the following transcript:",
    "tokens_input": 5234,
    "tokens_output": 387,
    "tokens_total": 5621,
    "estimated_cost_usd": 0.0254,
    "source_attribution": "https://youtube.com/watch?v=VIDEO_ID"
  },
  "errors": [],
  "warnings": []
}
```

### User Profile Schema

```ini
[ai_chatbots]
# Provider credentials (choose one or more)
openai_api_key=sk-proj-...
openai_model=gpt-4-turbo

gemini_api_key=AIza...
gemini_model=gemini-pro

azure_openai_api_key=...
azure_openai_endpoint=https://resource.openai.azure.com/
azure_openai_deployment=gpt-4
azure_openai_api_version=2024-02-01

perplexity_api_key=pplx-...
perplexity_model=pplx-7b-online
```

---

## VII. Security Considerations

### Credential Storage

**Requirements:**
- ✅ Store in user profile (config/user.profile)
- ✅ File permissions: 600 (user read/write only)
- ✅ Never version controlled (.gitignore)
- ✅ Never logged (not in stage logs or manifest)
- ✅ Extracted per job by prepare-job.sh
- ✅ Job config includes credentials (local to job)

**Implementation:**
```python
# In ai_summarizer.py
# NEVER log credentials
logger.debug(f"Using provider: {provider_name}")  # OK
# logger.debug(f"API key: {api_key}")  # WRONG!

# In stage_manifest.json
# Redact credentials
"metadata": {
    "ai_provider": "openai",  # OK
    "model": "gpt-4-turbo",  # OK
    # NO: "api_key": "sk-..."  # NEVER include
}
```

### API Communication

**Requirements:**
- ✅ HTTPS only (enforced by SDKs)
- ✅ Official provider SDKs (trusted)
- ✅ Timeout handling (60 seconds default)
- ✅ Rate limit handling (exponential backoff)
- ✅ Error messages don't leak credentials

**Implementation:**
```python
try:
    response = client.chat.completions.create(...)
except OpenAI.APIError as e:
    # Log error without exposing key
    logger.error(f"OpenAI API error: {type(e).__name__}")
    # NOT: logger.error(f"API error: {e}")  # May contain key
```

### Input Validation

**Requirements:**
- ✅ Validate provider name (whitelist)
- ✅ Validate transcript path (exists, readable)
- ✅ Validate token limits (prevent huge costs)
- ✅ Sanitize prompt (prevent injection)

**Implementation:**
```python
VALID_PROVIDERS = ["openai", "azure_openai", "gemini", "perplexity"]

if provider_name not in VALID_PROVIDERS:
    raise ValueError(f"Invalid provider: {provider_name}")

if not transcript_path.exists():
    raise FileNotFoundError(f"Transcript not found: {transcript_path}")

if estimated_tokens > max_tokens:
    logger.warning(f"Transcript too long, truncating to {max_tokens} tokens")
```

---

## VIII. Testing Requirements

### Unit Tests

**tests/unit/test_ai_summarizer.py** (~200 LOC)
```python
"""Unit tests for AI summarizer wrapper"""

def test_openai_provider_initialization():
    """Test OpenAI provider setup"""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")
    assert provider.model == "gpt-4"

def test_summarize_with_mock():
    """Test summarization with mocked API"""
    # Mock OpenAI API response
    # Verify summary text and metadata

def test_cost_estimation():
    """Test token cost calculation"""
    # gpt-4-turbo: $0.01/1K input, $0.03/1K output
    cost = provider._estimate_cost(usage)
    assert cost == 0.0254  # Example

def test_error_handling():
    """Test API error scenarios"""
    # Test timeout, rate limit, invalid key

def test_provider_factory():
    """Test provider creation"""
    summarizer = AISummarizer("openai", creds, logger)
    assert isinstance(summarizer.provider, OpenAIProvider)
```

### Integration Tests

**tests/integration/test_ai_summarization_stage.py** (~250 LOC)
```python
"""Integration tests for Stage 13"""

def test_stage_with_real_api():
    """Test with actual API (requires API key in env)"""
    # Skip if no API key
    # Create test transcript
    # Run stage
    # Verify summary file created
    # Verify source attribution

def test_stage_graceful_failure():
    """Test with invalid API key"""
    # Set invalid key
    # Run stage
    # Verify exit code 0 (graceful)
    # Verify no summary file
    # Verify warning logged

def test_all_providers():
    """Test all 4 providers if keys available"""
    # Test OpenAI, Gemini, Azure, Perplexity
    # Compare summary quality
    # Compare costs

def test_source_attribution():
    """Test source appending"""
    # Test with online URL
    # Test with local file
    # Verify format
```

### Functional Tests

**tests/functional/test_transcribe_with_summarization.py** (~150 LOC)
```python
"""End-to-end workflow tests"""

def test_full_workflow_with_summary():
    """Test complete transcribe + summarize workflow"""
    # Use standard test media
    # Run with --enable-summarization
    # Verify transcript.txt
    # Verify transcript_summary.txt
    # Verify manifest tracking

def test_online_media_with_summary():
    """Test with YouTube URL + summarization"""
    # Requires YouTube Premium credentials
    # Download video
    # Transcribe
    # Summarize
    # Verify URL in source attribution
```

---

## IX. Performance Requirements

### Response Times

**Target Performance:**
- ✅ Typical transcript (1hr content): 30-60 seconds
- ✅ Short transcript (<5min content): 10-20 seconds
- ✅ Long transcript (2+hr content): 60-120 seconds
- ✅ Timeout: 60 seconds (configurable)

**Performance Testing:**
```python
# Benchmark script
def benchmark_summarization():
    transcripts = [
        ("short.txt", 500),   # 5 min content
        ("medium.txt", 3000), # 30 min content
        ("long.txt", 12000),  # 2 hr content
    ]
    
    for name, tokens in transcripts:
        start = time.time()
        summary, metadata = summarizer.summarize_transcript(path)
        duration = time.time() - start
        
        print(f"{name}: {duration:.1f}s ({tokens} tokens)")
        # Verify within acceptable range
```

### Scalability

**Token Limits:**
- ✅ Default max: 100,000 tokens (~400 pages)
- ✅ Configurable via AI_SUMMARIZATION_MAX_TOKENS
- ✅ Truncate or chunk if exceeded (Phase 2)

**Concurrent Jobs:**
- ✅ Independent API calls (no shared state)
- ✅ User responsible for API rate limits
- ✅ No job queue needed (simple parallelism)

---

## X. Deployment & Operations

### Deployment Steps

1. **Install Dependencies:**
```bash
pip install -r requirements/requirements-ai.txt
```

2. **Update User Profile Template:**
```bash
# Add [ai_chatbots] section to config/user.profile.template
# Users copy to config/user.profile and add keys
```

3. **Update .gitignore:**
```bash
# Ensure user.profile excluded
echo "config/user.profile" >> .gitignore
```

4. **Verify Installation:**
```bash
# Test imports
python3 -c "import openai; import google.generativeai"

# Test stage
python3 scripts/13_ai_summarization.py test-job-dir
```

### Configuration Management

**System Config (.env.pipeline):**
- AI_SUMMARIZATION_ENABLED=true
- AI_SUMMARIZATION_TIMEOUT=60
- AI_SUMMARIZATION_MAX_TOKENS=100000
- AI_SUMMARIZATION_PROMPT="..."
- AI_SUMMARIZATION_COST_WARNING_USD=1.00

**User Profile (user.profile):**
- [ai_chatbots] section
- API keys for chosen providers
- Model preferences

### Monitoring & Logging

**Key Metrics:**
- Summary success rate (target: 95%+)
- Average tokens per summary
- Average cost per summary
- Provider usage distribution
- API timeout rate
- Graceful skip rate

**Logging:**
```
[INFO] AI summarization enabled (provider: openai)
[INFO] Calling AI API to generate summary...
[INFO] Summary generated: 5621 tokens, estimated cost: $0.0254
[INFO] Summary saved: transcript_summary.txt
[WARNING] AI summarization failed (timeout), skipping
```

### Error Handling

**Critical Errors (Exit Code 1):**
- Missing transcript file
- No user profile when summarization enabled
- No configured providers
- Invalid provider name

**Graceful Errors (Exit Code 0):**
- API timeout
- API rate limit
- Network failure
- Malformed API response

---

## XI. Maintenance & Support

### Troubleshooting Guide

**Issue: "Missing API key" error**
- Check config/user.profile exists
- Verify [ai_chatbots] section present
- Confirm API key format correct
- Check file permissions (should be 600)

**Issue: "API timeout" warnings**
- Increase AI_SUMMARIZATION_TIMEOUT
- Try different provider (Gemini often faster)
- Check network connectivity
- Verify API status (provider may be down)

**Issue: Poor summary quality**
- Try different provider (OpenAI usually best)
- Use better model (gpt-4-turbo vs gpt-3.5-turbo)
- Phase 2: Custom prompts

**Issue: High API costs**
- Use cheaper model (gpt-3.5-turbo, gemini-pro)
- Set AI_SUMMARIZATION_MAX_TOKENS lower
- Enable cost warnings

### Future Enhancements

**Phase 2 (v3.3):**
- Custom prompt templates
- Summary formats (bullet points, structured)
- Multi-language summaries
- Token usage dashboard

**Phase 3 (v3.4):**
- Local LLM support (Ollama)
- Batch summarization (multiple transcripts)
- Sentiment analysis
- Topic extraction

---

## XII. Appendix

### Related Documents

**BRD:**
- [BRD-2025-12-10-03-ai-summarization.md](../brd/BRD-2025-12-10-03-ai-summarization.md)

**PRD:**
- [PRD-2025-12-10-03-ai-summarization.md](../prd/PRD-2025-12-10-03-ai-summarization.md)

**Implementation:**
- [IMPLEMENTATION_TRACKER.md](../../../IMPLEMENTATION_TRACKER.md) - Task T-XXX

**Architecture:**
- [ARCHITECTURE.md](../../../ARCHITECTURE.md) - AD-015 (User Profile), AD-016 (AI Summarization)

### API Documentation

**OpenAI:**
- https://platform.openai.com/docs
- Models: https://platform.openai.com/docs/models
- Pricing: https://openai.com/pricing

**Google Gemini:**
- https://ai.google.dev/docs
- Pricing: https://ai.google.dev/pricing

**Azure OpenAI:**
- https://learn.microsoft.com/en-us/azure/ai-services/openai/

**Perplexity:**
- https://docs.perplexity.ai/

### Code Examples

**Basic Usage:**
```python
from shared.ai_summarizer import AISummarizer

# Initialize
summarizer = AISummarizer(
    provider_name="openai",
    credentials={"openai_api_key": "sk-...", "openai_model": "gpt-4-turbo"},
    logger=logger
)

# Summarize
summary, metadata = summarizer.summarize_transcript(
    transcript_path=Path("transcript.txt"),
    prompt="Summarize the key takeaways",
    max_tokens=100000,
    timeout=60
)

print(f"Summary: {summary}")
print(f"Cost: ${metadata['cost_usd']:.4f}")
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-10  
**Next Review:** Upon implementation completion

**Status:** ✅ Ready for Implementation  
**Estimated LOC:** ~500 new + 60 modified  
**Estimated Effort:** 10-12 hours total
