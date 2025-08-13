DOCKER_IMAGE = adt-utils
TARGET_DIR = ../target-folder
START ?= 6
END ?= 58
SOURCE_LANG ?= es
TARGET_LANG ?= en

-include .env
export

# OS-agnostic path resolution using Make built-in functions
CURRENT_DIR := $(CURDIR)
PARENT_DIR := $(dir $(CURRENT_DIR:/=))

.PHONY: build run-all run-demo clean-json test-layout validate validate-verbose validate-report fix-data-ids validate-fix translate-simple translate-gpt5 translate-gpt5-dry regenerate-tts-en regenerate-tts-es regenerate-tts-both complete-workflow check-api-key create-env-template help shell debug

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
	-docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python validate_adt.py /workspace/$(notdir $(TARGET_DIR))

# Validate with verbose output
validate-verbose: build
	@echo "Validating HTML files in $(TARGET_DIR) (verbose)..."
	-docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python validate_adt.py /workspace/$(notdir $(TARGET_DIR)) --verbose

# Validate and save detailed report
validate-report: build
	@echo "Validating HTML files and saving report..."
	-docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python validate_adt.py /workspace/$(notdir $(TARGET_DIR)) --output /workspace/adt-utils/validation_report.txt
	@echo "Report saved to validation_report.txt"

# Fix missing data-id attributes
fix-data-ids: build
	@echo "Fixing missing data-id attributes..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python fix_missing_data_ids.py /workspace/$(notdir $(TARGET_DIR))

# Complete validation and fix workflow
validate-fix: build
	@echo "Running validation and fix workflow..."
	-docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python validate_adt.py /workspace/$(notdir $(TARGET_DIR))
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python fix_missing_data_ids.py /workspace/$(notdir $(TARGET_DIR))
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python validate_adt.py /workspace/$(notdir $(TARGET_DIR))

# Translation commands
translate-simple: build
	@echo "Translating pages $(START) to $(END) using simple translation..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-w /workspace/$(notdir $(TARGET_DIR)) \
		$(DOCKER_IMAGE) python /app/regenerate_translations/translate_page_range.py $(START) $(END)

translate-gpt5: build check-api-key
	@echo "Translating pages $(START) to $(END) from $(SOURCE_LANG) to $(TARGET_LANG) using GPT..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		$(DOCKER_IMAGE) python /app/regenerate_translations/translate_gpt5.py \
			/workspace/$(notdir $(TARGET_DIR)) $(START) $(END) \
			--source-lang $(SOURCE_LANG) --target-lang $(TARGET_LANG)

translate-gpt5-dry: build check-api-key
	@echo "Dry run: Translating pages $(START) to $(END) from $(SOURCE_LANG) to $(TARGET_LANG) using GPT..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		$(DOCKER_IMAGE) python /app/regenerate_translations/translate_gpt5.py \
			/workspace/$(notdir $(TARGET_DIR)) $(START) $(END) \
			--source-lang $(SOURCE_LANG) --target-lang $(TARGET_LANG) --dry-run

# TTS regeneration commands
regenerate-tts-en: build check-api-key
	@echo "Regenerating English TTS for pages $(START) to $(END)..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-w /workspace/$(notdir $(TARGET_DIR)) \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		$(DOCKER_IMAGE) python /app/regenerate_tts_es/regenerate_tts.py --start-page $(START) --end-page $(END) --language en

regenerate-tts-es: build check-api-key
	@echo "Regenerating Spanish TTS for pages $(START) to $(END)..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-w /workspace/$(notdir $(TARGET_DIR)) \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		$(DOCKER_IMAGE) python /app/regenerate_tts_es/regenerate_tts.py --start-page $(START) --end-page $(END) --language es

regenerate-tts-both: build check-api-key
	@echo "Regenerating TTS for both languages, pages $(START) to $(END)..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-w /workspace/$(notdir $(TARGET_DIR)) \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		$(DOCKER_IMAGE) python /app/regenerate_tts_es/regenerate_tts.py --start-page $(START) --end-page $(END) --language both

# Complete workflow: validate → fix → translate → regenerate TTS
complete-workflow: build check-api-key
	@echo "Running complete workflow: validate → fix → translate → TTS..."
	@echo "Step 1/4: Validating HTML files..."
	-docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python validate_adt.py /workspace/$(notdir $(TARGET_DIR))
	@echo "Step 2/4: Fixing missing data-id attributes..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		$(DOCKER_IMAGE) python fix_missing_data_ids.py /workspace/$(notdir $(TARGET_DIR))
	@echo "Step 3/4: Translating new text entries from $(SOURCE_LANG) to $(TARGET_LANG)..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		$(DOCKER_IMAGE) python /app/regenerate_translations/translate_gpt5.py \
			/workspace/$(notdir $(TARGET_DIR)) $(START) $(END) \
			--source-lang $(SOURCE_LANG) --target-lang $(TARGET_LANG)
	@echo "Step 4/4: Regenerating TTS audio files..."
	docker run --rm -v "$(PARENT_DIR):/workspace" \
		-w /workspace/$(notdir $(TARGET_DIR)) \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		$(DOCKER_IMAGE) python /app/regenerate_tts_es/regenerate_tts.py --start-page $(START) --end-page $(END) --language both
	@echo "✅ Complete workflow finished!"

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
	@echo "Setup:"
	@echo "  make create-env-template      - Create .env template file"
	@echo "  make check-api-key            - Verify OPENAI_API_KEY is set"
	@echo ""
	@echo "Basic Usage:"
	@echo "  make build                    - Build Docker image"
	@echo "  make run-all START=6 END=58  - Run complete standardization"
	@echo "  make run-demo                 - Run demo (pages 6-10)"
	@echo "  make clean-json               - Clean JSON files"
	@echo ""
	@echo "Validation & Fixing:"
	@echo "  make validate                 - Validate HTML files for data-id attributes"
	@echo "  make validate-verbose         - Validate with detailed violation output"
	@echo "  make validate-report          - Validate and save report to ../validation_report.txt"
	@echo "  make fix-data-ids             - Fix missing data-id attributes automatically"
	@echo "  make validate-fix             - Complete workflow: validate → fix → validate"
	@echo ""
	@echo "Translation (requires OPENAI_API_KEY):"
	@echo "  make translate-simple START=6 END=58         - Simple dictionary-based translation"
	@echo "  make translate-gpt5 START=6 END=58           - GPT translation with context (es→en by default)"
	@echo "  make translate-gpt5-dry START=6 END=58       - Dry run of GPT translation"
	@echo ""
	@echo "TTS Generation (requires OPENAI_API_KEY):"
	@echo "  make regenerate-tts-en START=6 END=58        - Regenerate English TTS audio"
	@echo "  make regenerate-tts-es START=6 END=58        - Regenerate Spanish TTS audio"
	@echo "  make regenerate-tts-both START=6 END=58      - Regenerate both language TTS"
	@echo ""
	@echo "Complete Workflows:"
	@echo "  make complete-workflow START=6 END=58        - Full pipeline: validate → fix → translate → TTS"
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
	@echo "  SOURCE_LANG (default: es) - Source language for translation"
	@echo "  TARGET_LANG (default: en) - Target language for translation"
	@echo "  OPENAI_API_KEY - Required for translation and TTS commands"
	@echo ""
	@echo "Examples:"
	@echo "  export OPENAI_API_KEY=your_api_key_here"
	@echo "  make run-all TARGET_DIR=../my-project START=10 END=20"
	@echo "  make validate TARGET_DIR=../my-project"
	@echo "  make complete-workflow TARGET_DIR=../my-project START=10 END=15"
	@echo "  make translate-gpt5 TARGET_DIR=../my-project START=10 END=12"
	@echo "  make translate-gpt5 TARGET_DIR=../my-project START=10 END=12 SOURCE_LANG=es TARGET_LANG=fr"
	@echo "  make regenerate-tts-both TARGET_DIR=../my-project START=10 END=12"

# Add a helper target for checking API key using Python
check-api-key:
    @python -c "import os; key=os.environ.get('OPENAI_API_KEY'); print('✅ API key is set' if key else '❌ Error: OPENAI_API_KEY not set'); exit(0 if key else 1)"

# Add a helper target for creating .env template
create-env-template:
	@echo "Creating .env template..."
	@echo "# ADT Utils Environment Variables" > .env.template
	@echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env.template
	@echo "SOURCE_LANG=es" >> .env.template
	@echo "TARGET_LANG=en" >> .env.template
	@echo "# Copy this to .env and fill in your actual values" >> .env.template
	@echo "✅ Template created: .env.template"
	@echo "📝 To use it:"
	@echo "   1. cp .env.template .env"
	@echo "   2. Edit .env with your actual API key"
