"""
alignment.py - Word-level alignment handling

Handles:
- In-process WhisperX alignment
- Subprocess isolation for MLX backend (prevents segfaults)
- Hybrid alignment architecture (AD-008)
- Word-level timestamp generation

Extracted from whisperx_integration.py (Phase 6 - AD-002 + AD-009)
Status: ✅ FUNCTIONAL (Direct extraction per AD-009)

Note: Logger is passed as a parameter (not created here)
"""

# Standard library
import subprocess
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Local (logger import for compliance - logger is passed as parameter)
from shared.logger import get_logger  # noqa: F401

# Get project root for subprocess paths
PROJECT_ROOT = Path(__file__).parent.parent.parent


class AlignmentEngine:
    """
    Word-level alignment engine with hybrid architecture
    
    Implements hybrid alignment strategy per AD-008:
    - MLX backend: Uses WhisperX subprocess (prevents segfaults)
    - WhisperX backend: Uses native in-process alignment (faster)
    
    Extracted from WhisperXProcessor.align_segments() and
    WhisperXProcessor.align_with_whisperx_subprocess()
    """
    
    def __init__(self, backend: Any, device: str, logger: Any):
        """
        Initialize alignment engine
        
        Args:
            backend: Backend instance (with .name and .align_segments())
            device: Device (cpu, cuda, mps)
            logger: Logger instance
        """
        self.backend = backend
        self.device = device
        self.logger = logger
    
    def align(
        self,
        result: Dict[str, Any],
        audio_file: str,
        target_lang: str
    ) -> Dict[str, Any]:
        """
        Add word-level alignment to segments
        
        Uses hybrid architecture per AD-008:
        - If backend is MLX: Uses WhisperX subprocess (prevents segfault)
        - If backend is WhisperX: Uses backend's built-in alignment
        
        Args:
            result: Whisper transcription result with segments
            audio_file: Path to audio/video file
            target_lang: Target language for alignment
        
        Returns:
            Result with word-level timestamps added to segments
        """
        if not self.backend:
            self.logger.warning("Backend not loaded, skipping alignment")
            return result
        
        self.logger.info("Aligning segments for word-level timestamps...")
        
        try:
            # Check if using MLX backend - use subprocess for stability
            if self.backend.name == "mlx-whisper":
                self.logger.info("  MLX backend detected: using WhisperX subprocess")
                aligned_result = self.align_subprocess(
                    result.get("segments", []),
                    audio_file,
                    target_lang
                )
                return aligned_result
            else:
                # WhisperX or other backend - use native alignment
                aligned_result = self.backend.align_segments(
                    result.get("segments", []),
                    audio_file,
                    target_lang
                )
                self.logger.info("  ✓ Alignment complete")
                return aligned_result
        
        except Exception as e:
            self.logger.warning(f"  ⚠ Alignment failed: {e}")
            return result
    
    def align_subprocess(
        self,
        segments: List[Dict[str, Any]],
        audio_file: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Run WhisperX alignment in separate subprocess for stability
        
        This prevents MLX segfaults by using WhisperX alignment model
        in an isolated subprocess. Used when backend is MLX (AD-008).
        
        Args:
            segments: Transcription segments
            audio_file: Path to audio file
            language: Language code
        
        Returns:
            Dict with aligned segments including word-level timestamps
        """
        self.logger.info("  Running alignment in subprocess (WhisperX)...")
        
        # Write segments to temp file for IPC
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"segments": segments}, f)
            segments_file = f.name
        
        try:
            # Run alignment in subprocess using WhisperX environment
            cmd = [
                str(PROJECT_ROOT / "venv" / "whisperx" / "bin" / "python"),
                str(PROJECT_ROOT / "scripts" / "align_segments.py"),
                "--audio", str(audio_file),
                "--segments", segments_file,
                "--language", language,
                "--device", self.device
            ]
            
            self.logger.debug(f"  Subprocess command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                aligned = json.loads(result.stdout)
                num_segments = len(aligned.get("segments", []))
                self.logger.info(f"  ✓ Alignment complete: {num_segments} segments with word timestamps")
                return aligned
            else:
                self.logger.warning(f"  ⚠ Alignment subprocess failed (exit code {result.returncode})")
                if result.stderr:
                    self.logger.warning(f"  Error output: {result.stderr}")
                self.logger.info("  Returning segments without word-level timestamps")
                return {"segments": segments}  # Return original
        
        except subprocess.TimeoutExpired:
            self.logger.error("  ✗ Alignment subprocess timed out after 5 minutes", exc_info=True)
            return {"segments": segments}
        except Exception as e:
            self.logger.error(f"  ✗ Alignment subprocess error: {e}", exc_info=True)
            return {"segments": segments}
        finally:
            # Clean up temp file
            try:
                Path(segments_file).unlink(missing_ok=True)
            except Exception:
                pass


__all__ = ['AlignmentEngine']
