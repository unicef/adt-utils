# ADT Utils Script Usage

This document shows how external repositories can discover and use ADT Utils production scripts.

## For External Repositories

When you include `adt-utils` as a dependency, you can programmatically discover available scripts:

### Basic Script Discovery

```python
# Import the script registry
from adt_utils.src import PRODUCTION_SCRIPTS, get_script_info, list_scripts

# List all production scripts
scripts = list_scripts()
for script in scripts:
    print(f"{script['id']}: {script['description']}")

# Get specific script information
validator_info = get_script_info('validate_adt')
print(f"Script path: {validator_info['path']}")
print(f"Description: {validator_info['description']}")
```

### Generate Commands Programmatically

```python
from adt_utils.src import get_script_command

# Generate a command with specific arguments
cmd = get_script_command(
	script_id='validate_adt', 
	target_dir='./my-content',
	verbose=True,
	start_page=1,
	end_page=10
)
print(cmd)

# Output: python3 /path/to/adt-utils/src/validation/scripts/validate_adt.py ./my-content --start-page 1 --end-page 10 --verbose
```

### Run Scripts from Python

```python
import subprocess

from adt_utils.src import get_script_info

# Get script path and run it
script_info = get_script_info('validate_adt')
script_path = script_info['path']

# Run the script
result = subprocess.run([
    'python3', str(script_path),
    './my-content',
    '--verbose'
], capture_output=True, text=True)

print(f"Exit code: {result.returncode}")
print(f"Output: {result.stdout}")
```

### Follow Recommended Workflow

```python
from adt_utils.src import RECOMMENDED_WORKFLOW, get_script_info

# Display the recommended workflow
print("Recommended ADT Processing Workflow:")
for step in RECOMMENDED_WORKFLOW:
    script_info = get_script_info(step['script'])
    print(f"{step['step']}. {script_info['name']}")
    print(f"   Purpose: {step['purpose']}")
```

## Available Scripts

### 1. validate_adt

- **Purpose**: Validates HTML files for required data-id attributes and ADT compliance
- **Path**: `src/validation/scripts/validate_adt.py`
- **Usage**: `python3 {path} target_dir [options]`

**Arguments**:

- `target_dir` (required): Target directory path containing HTML files
- `--start-page N`: Starting page number (-1 for all pages)
- `--end-page N`: Ending page number (-1 for all pages)
- `--verbose`: Enable verbose output
- `--output FILE`: Save detailed report to file
- `--fix`: Attempt to auto-fix validation issues (experimental)

**Examples**:

```bash
# Validate all files
python3 src/validation/scripts/validate_adt.py ./output

# Validate specific page range with verbose output
python3 src/validation/scripts/validate_adt.py ./output --start-page 1 --end-page 10 --verbose

# Generate report
python3 src/validation/scripts/validate_adt.py ./output --output report.txt
```

### 2. fix_missing_data_ids

- **Purpose**: Automatically adds missing data-id attributes to HTML elements using i18n JSON files
- **Path**: `src/validation/scripts/fix_missing_data_ids.py`
- **Usage**: `python3 {path} target_dir [options]`

**Arguments**:

- `target_dir` (required): Target directory with HTML files and content/i18n/ structure
- `--start-page N`: Starting page number (-1 for all pages)
- `--end-page N`: Ending page number (-1 for all pages)
- `--dry-run`: Preview changes without modifying files
- `--verbose`: Show detailed information about each fix

**Prerequisites**:

- HTML files in target directory
- `content/i18n/[lang]/texts.json` structure in target directory

**Examples**:

```bash
# Preview fixes without making changes
python3 src/validation/scripts/fix_missing_data_ids.py ../target-folder --dry-run

# Fix all missing data-ids
python3 src/validation/scripts/fix_missing_data_ids.py ../target-folder

# Fix specific page range with verbose output
python3 src/validation/scripts/fix_missing_data_ids.py ../target-folder --start-page 5 --end-page 15 --verbose
```

## Recommended Workflow

1. **Validate** (`validate_adt`): Identify validation issues and missing data-id attributes
2. **Fix** (`fix_missing_data_ids`): Automatically fix missing data-id attributes
3. **Verify** (`validate_adt`): Verify that all issues have been resolved

```bash
# Step 1: Find issues
python3 src/validation/scripts/validate_adt.py ./target-folder --verbose

# Step 2: Fix issues (preview first)
python3 src/validation/scripts/fix_missing_data_ids.py ./target-folder --dry-run
python3 src/validation/scripts/fix_missing_data_ids.py ./target-folder

# Step 3: Verify fixes
python3 src/validation/scripts/validate_adt.py ./target-folder
```

## Integration Examples

### In a Makefile

```makefile
# ADT Utils commands
validate-adt:
	python3 $(shell python3 -c "from adt_utils.src import get_script_info; print(get_script_info('validate_adt')['path'])") ./output --verbose

fix-data-ids:
	python3 $(shell python3 -c "from adt_utils.src import get_script_info; print(get_script_info('fix_missing_data_ids')['path'])") ./output
```

### In a CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Validate ADT compliance
  run: |
    python3 -c "from adt_utils.src import get_script_info; import subprocess; subprocess.run(['python3', str(get_script_info('validate_adt')['path']), './output', '--verbose'], check=True)"
```
