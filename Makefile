DOCKER_IMAGE = adt-utils
TARGET_DIR = ../target-folder
START ?= 6
END ?= 58

# OS-agnostic path resolution using Make built-in functions
CURRENT_DIR := $(CURDIR)
PARENT_DIR := $(dir $(CURRENT_DIR:/=))

.PHONY: build run-all run-demo clean-json test-layout validate validate-verbose validate-report help shell debug

# Build the Docker image
build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE) .

# Run complete standardization
run-all: build
	@echo "Running complete standardization (pages $(START) to $(END))..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		-e ADT_JSON_DIR=/workspace/$(notdir $(TARGET_DIR))/content/i18n/ \
		$(DOCKER_IMAGE) python standardize_all.py $(START) $(END)

# Run demo standardization
run-demo: build
	@echo "Running demo standardization..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python demo_standardization.py 6 10

# Clean JSON files
clean-json: build
	@echo "Cleaning JSON files..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python clean_json_texts.py --dir /workspace/$(notdir $(TARGET_DIR))/content/i18n/

# Validate HTML files for data-id attributes
validate: build
	@echo "Validating HTML files in $(TARGET_DIR)..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python validate_adt.py /workspace/$(notdir $(TARGET_DIR))

# Validate with verbose output
validate-verbose: build
	@echo "Validating HTML files in $(TARGET_DIR) (verbose)..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python validate_adt.py /workspace/$(notdir $(TARGET_DIR)) --verbose

# Validate and save detailed report
validate-report: build
	@echo "Validating HTML files and saving report..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python validate_adt.py /workspace/$(notdir $(TARGET_DIR)) --output /workspace/validation_report.txt
	@echo "Report saved to ../validation_report.txt"

# Test single layout
test-layout: build
	@echo "Testing single layout (specify FILE=path/to/file.html)..."
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE=path/to/file.html"; \
		exit 1; \
	fi
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python test_single_layout.py /workspace/$(FILE)

# Run individual scripts
run-html: build
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python standardize_html.py $(START) $(END)

run-headings: build
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python standardize_headings.py $(START) $(END)

run-layouts: build
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python standardize_image_text_layouts.py

run-text: build
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python restructure_text_simple.py $(START) $(END)

# Shell access for debugging
shell: build
	@echo "Opening shell in container..."
	docker run --rm -it -v "$(PARENT_DIR):/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) /bin/bash

# Debugging target
debug:
	@echo "Current directory: $(CURDIR)"
	@echo "Parent directory: $(PARENT_DIR)"
	@echo "Target directory: $(TARGET_DIR)"
	@echo "Target basename: $(notdir $(TARGET_DIR))"

# Help
help:
	@echo "ADT Utils Docker Commands"
	@echo "========================="
	@echo ""
	@echo "Basic Usage:"
	@echo "  make build                    - Build Docker image"
	@echo "  make run-all START=6 END=58  - Run complete standardization"
	@echo "  make run-demo                 - Run demo (pages 6-10)"
	@echo "  make clean-json               - Clean JSON files"
	@echo ""
	@echo "Validation:"
	@echo "  make validate                 - Validate HTML files for data-id attributes"
	@echo "  make validate-verbose         - Validate with detailed violation output"
	@echo "  make validate-report          - Validate and save report to ../validation_report.txt"
	@echo ""
	@echo "Individual Scripts:"
	@echo "  make run-html START=6 END=58 - HTML structure only"
	@echo "  make run-headings START=6 END=58 - Headings only"
	@echo "  make run-layouts              - Image layouts only"
	@echo "  make run-text START=6 END=58 - Text restructuring only"
	@echo ""
	@echo "Testing & Debugging:"
	@echo "  make test-layout FILE=target-folder/file.html - Test single file"
	@echo "  make shell                    - Open container shell"
	@echo "  make debug                    - Show debug information"
	@echo ""
	@echo "Configuration:"
	@echo "  TARGET_DIR (default: ../target-folder) - Target directory relative to parent"
	@echo "  START (default: 6) - Starting page number"
	@echo "  END (default: 58) - Ending page number"
	@echo ""
	@echo "Examples:"
	@echo "  make run-all TARGET_DIR=../my-project START=10 END=20"
	@echo "  make validate TARGET_DIR=../my-project"
	@echo "  make validate-verbose TARGET_DIR=../my-project"
	@echo "  make test-layout FILE=my-project/25_0_adt.html"
