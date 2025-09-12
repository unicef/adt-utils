# Experiments Directory

This directory contains experimental scripts and tools for the ADT project. Scripts here are for testing, experimentation, and development - **they are not production-ready**.

## Directory Structure

```
experiments/
├── validate_adt.py              # Production validation script
├── fix_missing_data_ids.py      # Production data fixing script
├── html_standardization/        # HTML processing experiments
├── content_generation/          # Content generation experiments  
├── translation_tools/           # Translation experiments
├── tts_generation/             # Text-to-Speech experiments
└── templates/                  # Templates for new experiments
```

## Script Standards

All experiment scripts must follow these conventions:

### Required Arguments
Every script must accept these standard arguments:
- `--start-page` (default: -1) - Starting page number (-1 for all pages)
- `--end-page` (default: -1) - Ending page number (-1 for all pages)  
- `target_dir` - Target directory path (positional argument)

### Example Usage
```bash
python experiment_script.py /path/to/target --start-page 1 --end-page 10
python experiment_script.py /path/to/target  # Process all pages
```

### Script Template
Use the template in `templates/experiment_template.py` for new experiments.

## Dependencies

Experiments can use additional dependencies beyond the production requirements. Install with:
```bash
pip install -r experiments/requirements.txt
```

## Production Scripts

These scripts are production-ready and use the standardized interfaces from `src/`:
- `validate_adt.py` - Validates HTML files for missing data-id attributes
- `fix_missing_data_ids.py` - Automatically fixes missing data-id attributes

## Moving to Production

See `docs/PROMOTION_GUIDE.md` for detailed steps on promoting experimental scripts to production status.