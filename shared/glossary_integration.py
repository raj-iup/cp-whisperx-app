#!/usr/bin/env python3
"""
Glossary Integration Helper for Downstream Stages

Provides easy glossary loading and application for stages that need
to enforce glossary terms (subtitle_gen, translation, etc.).

Usage:
    from shared.glossary_integration import load_glossary_for_stage
    
    # In your stage
    glossary = load_glossary_for_stage(
        stage_io=stage_io,
        config=config,
        logger=logger,
        fallback_to_master=True
    )
    
    if glossary:
        # Apply to text
        enforced_text = glossary.apply_to_text(original_text)
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from shared.glossary_manager import UnifiedGlossaryManager
    MANAGER_AVAILABLE = True
except ImportError:
    MANAGER_AVAILABLE = False

try:
    from shared.glossary_unified import load_glossary as load_glossary_legacy
    LEGACY_AVAILABLE = True
except ImportError:
    LEGACY_AVAILABLE = False


def load_glossary_for_stage(
    stage_io,
    config,
    logger: Optional[logging.Logger] = None,
    project_root: Optional[Path] = None,
    fallback_to_master: bool = True
) -> Optional[Any]:
    """
    Load glossary for downstream stage with intelligent fallback
    
    Priority:
    1. Film-specific glossary from glossary_load stage (best)
    2. Master glossary from project (fallback)
    3. Legacy glossary loading (deprecated)
    4. None (no glossary)
    
    Args:
        stage_io: StageIO instance for path resolution
        config: Configuration object
        logger: Optional logger
        project_root: Project root path (auto-detected if None)
        fallback_to_master: Whether to fall back to master glossary
    
    Returns:
        Glossary manager instance or None
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if project_root is None:
        project_root = Path(__file__).parent.parent
    
    # Check if glossary is enabled in config
    glossary_enabled = getattr(config, 'glossary_enabled', True)
    if not glossary_enabled:
        logger.info("Glossary disabled in configuration")
        return None
    
    glossary = None
    glossary_source = None
    
    # Try loading with UnifiedGlossaryManager (preferred)
    if MANAGER_AVAILABLE:
        try:
            # Try film-specific glossary from glossary_load stage
            glossary_file = stage_io.get_input_path("film_glossary.tsv", from_stage="glossary_load")
            
            if glossary_file.exists():
                logger.info(f"Loading film-specific glossary from: {glossary_file}")
                
                film_title = getattr(config, 'title', None)
                film_year = getattr(config, 'year', None)
                
                glossary = UnifiedGlossaryManager(
                    project_root=project_root,
                    film_title=film_title,
                    film_year=film_year,
                    enable_cache=False,  # Already cached
                    logger=logger
                )
                
                stats = glossary.load_all_sources()
                term_count = stats.get('total_terms', 0)
                
                logger.info(f"✓ Loaded film-specific glossary: {term_count} terms")
                logger.info(f"  Master: {stats.get('master_terms', 0)}, "
                           f"TMDB: {stats.get('tmdb_terms', 0)}, "
                           f"Film: {stats.get('film_terms', 0)}")
                
                glossary_source = "film_specific"
                stage_io.track_input(glossary_file, "film_glossary", format="tsv")
                
            elif fallback_to_master:
                # Fallback: Master glossary only
                logger.info("Film-specific glossary not found, using master glossary")
                
                glossary_path = project_root / getattr(config, 'glossary_path', 'glossary/hinglish_master.tsv')
                
                if glossary_path.exists():
                    glossary = UnifiedGlossaryManager(
                        project_root=project_root,
                        enable_cache=False,
                        logger=logger
                    )
                    
                    stats = glossary.load_all_sources()
                    term_count = stats.get('total_terms', 0)
                    
                    logger.info(f"✓ Loaded master glossary: {term_count} terms")
                    glossary_source = "master_only"
                else:
                    logger.warning(f"Master glossary not found: {glossary_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load glossary with UnifiedGlossaryManager: {e}")
            glossary = None
    
    # Fallback to legacy loading (deprecated)
    if glossary is None and LEGACY_AVAILABLE and fallback_to_master:
        logger.warning("Falling back to deprecated glossary loading")
        logger.warning("Update to UnifiedGlossaryManager for better performance")
        
        try:
            glossary_path = project_root / getattr(config, 'glossary_path', 'glossary/unified_glossary.tsv')
            
            if glossary_path.exists():
                film_title = getattr(config, 'title', '')
                film_year = getattr(config, 'year', '')
                film_name = f"{film_title}_{film_year}" if film_title and film_year else None
                
                glossary = load_glossary_legacy(glossary_path, film_name, logger)
                glossary_source = "legacy"
                
                if glossary:
                    logger.info("✓ Loaded glossary (legacy method)")
        except Exception as e:
            logger.warning(f"Failed to load legacy glossary: {e}")
    
    # Log result
    if glossary is None:
        logger.info("Glossary not loaded - terms will not be enforced")
        logger.info("Tip: Run glossary_load stage for better term preservation")
    else:
        logger.info(f"✓ Glossary ready (source: {glossary_source})")
    
    return glossary


def apply_glossary_to_text(
    text: str,
    glossary: Any,
    context: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> str:
    """
    Apply glossary to text with error handling
    
    Args:
        text: Original text
        glossary: Glossary manager instance
        context: Optional context hint
        logger: Optional logger
    
    Returns:
        Text with glossary terms enforced
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if glossary is None:
        return text
    
    try:
        # Try new method
        if hasattr(glossary, 'apply_to_text'):
            return glossary.apply_to_text(text, context=context)
        # Try legacy method
        elif hasattr(glossary, 'apply'):
            return glossary.apply(text)
        else:
            logger.warning("Glossary has no apply method")
            return text
    except Exception as e:
        logger.warning(f"Glossary application failed: {e}")
        return text


def get_glossary_stats(glossary: Any) -> Dict[str, Any]:
    """
    Get statistics from glossary
    
    Args:
        glossary: Glossary manager instance
    
    Returns:
        Dictionary of statistics
    """
    if glossary is None:
        return {}
    
    try:
        if hasattr(glossary, 'get_statistics'):
            return glossary.get_statistics()
        elif hasattr(glossary, 'stats'):
            return glossary.stats
        else:
            return {}
    except Exception:
        return {}


# Convenience function for backwards compatibility
def load_film_glossary(job_dir: Path, logger: Optional[logging.Logger] = None) -> Optional[Any]:
    """
    DEPRECATED: Load film glossary from job directory
    
    Use load_glossary_for_stage() instead for better integration.
    
    Args:
        job_dir: Job output directory
        logger: Optional logger
    
    Returns:
        Glossary manager instance or None
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.warning("load_film_glossary() is deprecated. Use load_glossary_for_stage() instead.")
    
    if not MANAGER_AVAILABLE:
        logger.error("UnifiedGlossaryManager not available")
        return None
    
    try:
        # Look for glossary in job directory
        glossary_file = job_dir / "03_glossary_load" / "film_glossary.tsv"
        
        if not glossary_file.exists():
            logger.warning(f"Film glossary not found: {glossary_file}")
            return None
        
        # Extract project root and film info from job dir
        project_root = job_dir.parent.parent.parent.parent.parent
        
        # Try to load from glossary file metadata
        glossary = UnifiedGlossaryManager(
            project_root=project_root,
            enable_cache=False,
            logger=logger
        )
        
        stats = glossary.load_all_sources()
        logger.info(f"✓ Loaded film glossary: {stats.get('total_terms', 0)} terms")
        
        return glossary
        
    except Exception as e:
        logger.error(f"Failed to load film glossary: {e}")
        return None
