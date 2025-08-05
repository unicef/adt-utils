DOCKER_IMAGE = adt-utils
TARGET_DIR = ../target-folder
START ?= 6
END ?= 58

.PHONY: build run-all run-demo clean-json test-layout help shell

# Build the Docker image
build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE) .

# Run complete standardization
run-all: build
	@echo "Running complete standardization (pages $(START) to $(END))..."
	docker run --rm -v "$(shell pwd)/../:/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		-e ADT_JSON_DIR=/workspace/$(notdir $(TARGET_DIR))/content/i18n/ \
		$(DOCKER_IMAGE) python standardize_all.py $(START) $(END)

# Run demo standardization
run-demo: build
	@echo "Running demo standardization..."
	docker run --rm -v "$(shell pwd)/../:/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python demo_standardization.py 6 10

# Clean JSON files
clean-json: build
	@echo "Cleaning JSON files..."
	docker run --rm -v "$(shell pwd)/../:/workspace" \
		$(DOCKER_IMAGE) python clean_json_texts.py --dir /workspace/$(notdir $(TARGET_DIR))/content/i18n/

# Test single layout
test-layout: build
	@echo "Testing single layout (specify FILE=path/to/file.html)..."
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE=path/to/file.html"; \
		exit 1; \
	fi
	docker run --rm -v "$(shell pwd)/../:/workspace" \
		$(DOCKER_IMAGE) python test_single_layout.py /workspace/$(FILE)

# Run individual scripts
run-html: build
	docker run --rm -v "$(shell pwd)/../:/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python standardize_html.py $(START) $(END)

run-headings: build
	docker run --rm -v "$(shell pwd)/../:/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python standardize_headings.py $(START) $(END)

run-layouts: build
	docker run --rm -v "$(shell pwd)/../:/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python standardize_image_text_layouts.py

run-text: build
	docker run --rm -v "$(shell pwd)/../:/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python restructure_text_simple.py $(START) $(END)

# Shell access for debugging
shell: build
	@echo "Opening shell in container..."
	docker run --rm -it -v "$(shell pwd)/../:/workspace" \
		-e ADT_OUTPUT_DIR=/workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) /bin/bash

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
	@echo "Individual Scripts:"
	@echo "  make run-html START=6 END=58 - HTML structure only"
	@echo "  make run-headings START=6 END=58 - Headings only"
	@echo "  make run-layouts              - Image layouts only"
	@echo "  make run-text START=6 END=58 - Text restructuring only"
	@echo ""
	@echo "Testing & Debugging:"
	@echo "  make test-layout FILE=target-folder/file.html - Test single file"
	@echo "  make shell                    - Open container shell"
	@echo ""
	@echo "Configuration:"
	@echo "  TARGET_DIR (default: ../target-folder) - Target directory relative to parent"
	@echo "  START (default: 6) - Starting page number"
	@echo "  END (default: 58) - Ending page number"
	@echo ""
	@echo "Examples:"
	@echo "  make run-all TARGET_DIR=../my-project START=10 END=20"
	@echo "  make test-layout FILE=my-project/25_0_adt.html"
