"""
Abstract base classes defining standard interfaces for ADT utilities.
All production classes must implement these interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path

from .models import PageProcessConfig, ProcessResult


class PageRangeProcessor(ABC):
    """Base interface for all page range processing operations."""
    
    @abstractmethod
    def process_page_range(self, config: PageProcessConfig, **kwargs) -> ProcessResult:
        """
        Process a range of pages with the given configuration.
        
        Args:
            config: PageProcessConfig with start_page, end_page, etc.
            **kwargs: Additional processor-specific arguments
            
        Returns:
            ProcessResult with success status, processed pages, and any errors
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: PageProcessConfig) -> List[str]:
        """
        Validate configuration before processing.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        pass


class Validator(PageRangeProcessor):
    """Interface for validation operations."""
    
    @abstractmethod
    def validate_page(self, page_number: int, page_path: Path) -> Dict[str, Any]:
        """Validate a single page."""
        pass


class DataFixer(PageRangeProcessor):
    """Interface for data fixing operations."""
    
    @abstractmethod
    def fix_page(self, page_number: int, page_path: Path) -> Dict[str, Any]:
        """Fix issues in a single page."""
        pass


class ContentProcessor(PageRangeProcessor):
    """Interface for content processing operations."""
    
    @abstractmethod
    def process_content(self, content: str, page_number: int) -> str:
        """Process content for a single page."""
        pass


class Translator(PageRangeProcessor):
    """Interface for translation operations."""
    
    @abstractmethod
    def translate_content(self, content: str, source_lang: str, target_lang: str) -> str:
        """Translate content from source to target language."""
        pass