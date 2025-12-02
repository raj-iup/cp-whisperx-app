#!/usr/bin/env python3
"""
DEPRECATED: Use UnifiedGlossaryManager from shared.glossary_manager instead.

This module is maintained for backwards compatibility only.
All new code should use UnifiedGlossaryManager.

Migration Guide:
    Old:
        from shared.glossary_unified import UnifiedGlossary
        glossary = UnifiedGlossary(glossary_path=path)
    
    New:
        from shared.glossary_manager import UnifiedGlossaryManager
        manager = UnifiedGlossaryManager(
            project_root=project_root,
            film_title=title,
            film_year=year
        )
"""

import warnings
from shared.glossary_manager import UnifiedGlossaryManager

# Issue deprecation warning
warnings.warn(
    "glossary_unified.UnifiedGlossary is deprecated. "
    "Use UnifiedGlossaryManager from shared.glossary_manager instead. "
    "See module docstring for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backwards compatibility
__all__ = ['UnifiedGlossary', 'load_glossary']


class UnifiedGlossary(UnifiedGlossaryManager):
    """
    DEPRECATED: Legacy wrapper around UnifiedGlossaryManager.
    
    This class is maintained for backwards compatibility only.
    New code should use UnifiedGlossaryManager directly.
    """
    
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "UnifiedGlossary is deprecated. Use UnifiedGlossaryManager instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Adapt old-style arguments to new-style
        if 'glossary_path' in kwargs and 'project_root' not in kwargs:
            glossary_path = kwargs.pop('glossary_path')
            if glossary_path:
                kwargs['project_root'] = glossary_path.parent.parent
        
        super().__init__(*args, **kwargs)


def load_glossary(glossary_path, **kwargs):
    """
    DEPRECATED: Legacy function for loading glossary.
    
    Use UnifiedGlossaryManager directly instead:
        manager = UnifiedGlossaryManager(project_root=root)
        manager.load_all_sources()
    """
    warnings.warn(
        "load_glossary() is deprecated. Use UnifiedGlossaryManager instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Adapt arguments
    project_root = glossary_path.parent.parent if glossary_path else None
    manager = UnifiedGlossaryManager(project_root=project_root, **kwargs)
    manager.load_all_sources()
    return manager
