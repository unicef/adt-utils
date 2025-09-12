# Promotion Guide: From Experiment to Production

## Step-by-Step Process

### 1. **Assess Readiness**
Your experimental script is ready for promotion when:
- ✅ It works reliably and handles edge cases
- ✅ It follows the standard argument pattern (`--start-page`, `--end-page`, `target_dir`)
- ✅ It has proper error handling and validation
- ✅ The logic is well-tested and stable

### 2. **Create Production Class**
Create a new class in `src/` that implements the appropriate interface:

```python
# src/your_module/your_processor.py
from src.core import PageRangeProcessor, PageProcessConfig, ProcessResult

class YourProcessor(PageRangeProcessor):
    def validate_config(self, config: PageProcessConfig) -> List[str]:
        # Validate configuration
        return []  # Return empty list if valid
    
    def process_page_range(self, config: PageProcessConfig, **kwargs) -> ProcessResult:
        # Your production logic here
        return ProcessResult(success=True, processed_pages=[])
```

### 3. **Create Pydantic Configuration**
Define a configuration model if your script has custom parameters:

```python
# src/core/models.py (add to existing file)
class YourProcessorConfig(PageProcessConfig):
    your_custom_param: str = Field(default="default_value")
    your_flag: bool = Field(default=False)
```

### 4. **Refactor Experiment Script**
Update the experimental script to use your production class:

```python
#!/usr/bin/env python3
# experiments/your_script.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.your_module import YourProcessor
from src.core import YourProcessorConfig
from src.utils import add_standard_args, parse_page_range

def main():
    parser = argparse.ArgumentParser(description="Your script description")
    parser = add_standard_args(parser)
    
    # Add your custom arguments
    parser.add_argument('--your-param', default='default')
    
    args = parser.parse_args()
    
    # Create config
    config = YourProcessorConfig(
        start_page=args.start_page,
        end_page=args.end_page,
        target_dir=Path(args.target_dir),
        your_custom_param=args.your_param
    )
    
    # Run processor
    processor = YourProcessor()
    result = processor.process_page_range(config)
    
    # Handle results...
```

### 5. **Update Dependencies**
If your script introduces new dependencies:
1. Add core dependencies to `requirements.txt`
2. Add experimental dependencies to `experiments/requirements.txt`

### 6. **Test Integration**
- Test the script with various page ranges
- Verify error handling works correctly
- Ensure compatibility with existing workflows

### 7. **Documentation**
- Update the script's docstring with clear usage examples
- Add any special considerations to `experiments/README.md`
- Update the main `README.md` if the functionality is significant

## Example: HTML Standardization Script

```python
# src/content/html_standardizer.py
from src.core import ContentProcessor, PageProcessConfig, ProcessResult

class HTMLStandardizer(ContentProcessor):
    def process_page_range(self, config: PageProcessConfig, **kwargs) -> ProcessResult:
        # Implementation here
        pass
    
    def process_content(self, content: str, page_number: int) -> str:
        # HTML processing logic
        return processed_content

# experiments/standardize_html.py  
from src.content import HTMLStandardizer
from src.core import PageProcessConfig

def main():
    # Standard argument parsing...
    config = PageProcessConfig(start_page=start, end_page=end, target_dir=target)
    standardizer = HTMLStandardizer()
    result = standardizer.process_page_range(config)
```

## Quality Checklist

Before promoting an experiment:
- [ ] Follows standard argument pattern
- [ ] Uses production classes from `src/`
- [ ] Has proper error handling
- [ ] Validates input parameters
- [ ] Returns standardized results
- [ ] Documentation is updated
- [ ] Dependencies are properly managed