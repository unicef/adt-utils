# Production Deployment Guide

This guide explains how to move scripts from the `experiments/` folder to production use.

## Script Lifecycle

### 1. Development Phase (experiments/)
- Scripts are developed and tested in the `experiments/` folder
- Use `experiments/requirements.txt` for dependencies
- Test thoroughly before promotion

### 2. Production Readiness Checklist

Before moving a script to production:

**Code Quality**
- [ ] Code follows project conventions
- [ ] Error handling is comprehensive
- [ ] Logging is properly implemented
- [ ] Documentation is complete

**Testing**
- [ ] Unit tests written and passing
- [ ] Integration tests completed
- [ ] Performance validated on realistic datasets
- [ ] Edge cases handled

**Dependencies**
- [ ] Dependencies added to `pyproject.toml` 
- [ ] Version constraints specified
- [ ] Conflicts with existing deps resolved

### 3. Promotion Process

#### Step 1: Move Script to Core
```bash
# Move from experiments/ to appropriate src/ subfolder
mv experiments/my_script.py src/core/

# Or move from experiments subfolder
mv experiments/html_standardization/my_script.py src/core/
```

#### Step 2: Update Import Structure
```python
# Update imports to use src structure
from src.utils.file_operations import process_files
from src.core.validation import validate_html
```

#### Step 3: Add to Script Registry
```python
# In src/script_registry.py, register your script
PRODUCTION_SCRIPTS = {
    "my_script": {
        "module": "src.core.my_script",
        "function": "main",
        "description": "Production script description"
    }
}
```

#### Step 4: Update Dependencies
```toml
# Add to pyproject.toml [project.dependencies]
"new-dependency>=1.0.0",
```

#### Step 5: Add Makefile Target
```makefile
# In Makefile, add production target
run-my-script: build
	@echo "Running my script..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python -m src.core.my_script $(ARGS)
```

#### Step 6: Update Documentation
- Add script to main README.md
- Create usage examples
- Document CLI parameters

### 4. Docker Integration

#### Update Dockerfile if needed
```dockerfile
# Add any system dependencies
RUN apt-get update && apt-get install -y \
    additional-package
```

#### Test Docker Build
```bash
make build
docker run --rm adt-utils python -m src.core.my_script --help
```

### 5. Quality Gates

Before final deployment:

```bash
# Run code quality checks
black src/
isort src/
mypy src/

# Run tests
pytest

# Build and test Docker
make build
make validate TARGET_DIR=../test-project
```

### 6. Production Deployment

#### For Internal Use
1. Update version in `pyproject.toml`
2. Tag release in git
3. Build production Docker image
4. Deploy to target environment

#### For External Distribution
1. Create distribution package: `python -m build`
2. Test in clean environment
3. Publish to package registry if applicable

## Best Practices

- **Incremental Promotion**: Move one script at a time
- **Backward Compatibility**: Maintain support for existing workflows  
- **Environment Isolation**: Use virtual environments for testing
- **Rollback Plan**: Keep experiments/ version until production is stable
- **Monitoring**: Add logging to track production usage

## Example Migration

```bash
# 1. Move script from experiments subfolder
mv experiments/content_generation/generate_eli5.py src/core/

# 2. Update imports in the moved file
sed -i 's|from experiments.|from src.|g' src/core/generate_eli5.py

# 3. Add to registry with proper Script object
# Edit src/script_registry.py and add Script entry to PRODUCTION_SCRIPTS list

# 4. Test
python -m src.core.generate_eli5 --help

# 5. Add Makefile target
echo 'generate-eli5: build' >> Makefile
echo '	docker run --rm -v "$(PARENT_DIR):/workspace" $(DOCKER_IMAGE) python -m src.core.generate_eli5 $(ARGS)' >> Makefile
```

## Common Issues

- **Import Errors**: Update all relative imports to absolute `src.` imports
- **Path Issues**: Use proper path resolution for file operations
- **Dependency Conflicts**: Resolve version conflicts in pyproject.toml
- **Docker Build Failures**: Ensure all system dependencies are in Dockerfile

## Rollback Procedure

If production deployment fails:

1. Remove script from `src/`
2. Revert `pyproject.toml` changes
3. Remove Makefile targets
4. Rebuild Docker image
5. Continue development in `experiments/`