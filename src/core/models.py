"""
Pydantic base models for ADT utilities.
Provides type validation and serialization for all operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from pathlib import Path


class PageProcessConfig(BaseModel):
    """Base configuration for page range processing."""
    start_page: int = Field(default=-1, description="Starting page (-1 for all pages)")
    end_page: int = Field(default=-1, description="Ending page (-1 for all pages)")
    target_dir: Optional[Path] = Field(default=None, description="Target directory path")
    
    @validator('start_page', 'end_page')
    def validate_page_numbers(cls, v):
        if v < -1:
            raise ValueError("Page numbers must be -1 or positive")
        return v
    
    @validator('end_page')
    def validate_page_range(cls, v, values):
        start = values.get('start_page', -1)
        if start != -1 and v != -1 and v < start:
            raise ValueError("end_page must be >= start_page")
        return v


class ProcessResult(BaseModel):
    """Standard result format for all processing operations."""
    success: bool
    processed_pages: List[int] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationConfig(PageProcessConfig):
    """Configuration for ADT validation operations."""
    verbose: bool = Field(default=False, description="Enable verbose output")
    generate_report: bool = Field(default=False, description="Generate validation report")
    fix_issues: bool = Field(default=False, description="Auto-fix validation issues")


class TranslationConfig(PageProcessConfig):
    """Configuration for translation operations."""
    source_lang: str = Field(default="es", description="Source language code")
    target_lang: str = Field(default="en", description="Target language code")
    api_key: Optional[str] = Field(default=None, description="API key for translation service")
    model: str = Field(default="gpt-4", description="Translation model to use")