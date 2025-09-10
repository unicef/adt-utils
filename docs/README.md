# ADT Utils Documentation

## Repository Structure

```
adt-utils/
├── src/                     # Production classes with standardized interfaces
│   ├── core/               # Base models (Pydantic) and interfaces (ABC)
│   ├── validation/         # Production validation tools
│   └── utils/              # Common utilities
├── experiments/            # All scripts (production & experimental)
│   ├── validate_adt.py    # ✅ Production ready
│   ├── fix_missing_data_ids.py # ✅ Production ready  
│   ├── html_standardization/   # 🧪 Experimental
│   ├── content_generation/     # 🧪 Experimental
│   ├── translation_tools/      # 🧪 Experimental
│   ├── tts_generation/         # 🧪 Experimental
│   └── templates/              # Script templates
└── docs/                   # Documentation
```

## Quick Start

### Installation
```bash
# Install production dependencies
pip install -r requirements.txt

# Install experimental dependencies (optional)
pip install -r experiments/requirements.txt
```

### Running Production Scripts
```bash
# Validate all pages
python experiments/validate_adt.py /path/to/target

# Validate specific page range
python experiments/validate_adt.py /path/to/target --start-page 1 --end-page 10

# Fix missing data IDs
python experiments/fix_missing_data_ids.py /path/to/target --start-page 5 --end-page 15
```

## Standards

### Script Arguments
All scripts must support:
- `--start-page` (default: -1 for all pages)
- `--end-page` (default: -1 for all pages)
- `target_dir` (positional argument)

### Production Classes
- Use Pydantic models for configuration validation
- Implement ABC interfaces for consistency
- Follow type hints and error handling standards

## See Also
- [Promotion Guide](PROMOTION_GUIDE.md) - Moving experiments to production
- [API Documentation](API.md) - Production class interfaces