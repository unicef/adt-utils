#!/bin/bash

# GPT-5 Translation helper script for ADT Manual
# Usage: ./translate_gpt5.sh [page_start] [page_end] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_ai() {
    echo -e "${PURPLE}🤖 $1${NC}"
}

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "translate_gpt5.py" ]; then
    print_error "translate_gpt5.py not found. Please run this script from the project root."
    exit 1
fi

# Check if Spanish JSON exists
if [ ! -f "content/i18n/es/texts.json" ]; then
    print_error "Spanish translation file not found at content/i18n/es/texts.json"
    exit 1
fi

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OPENAI_API_KEY environment variable not set."
    print_info "You can set it with: export OPENAI_API_KEY='your-api-key-here'"
    print_info "Or use the --api-key option with the script."
    echo ""
fi

# Display help if no arguments
if [ $# -eq 0 ]; then
    echo "🤖 ADT Manual GPT-5 Translation Helper"
    echo ""
    echo "Usage:"
    echo "  ./translate_gpt5.sh <page_start> [page_end] [options]"
    echo ""
    echo "Examples:"
    echo "  ./translate_gpt5.sh 23                    # Translate page 23"
    echo "  ./translate_gpt5.sh 23 30                 # Translate pages 23-30"
    echo "  ./translate_gpt5.sh 23 30 --dry-run       # Preview translations"
    echo "  ./translate_gpt5.sh 23 --context-size 15  # Use 15 previous translations for context"
    echo ""
    echo "Options:"
    echo "  --dry-run         Show translations without saving or calling API"
    echo "  --api-key KEY     Use specific OpenAI API key"
    echo "  --context-size N  Number of previous translations to keep for context (default: 10)"
    echo ""
    echo "Environment:"
    echo "  OPENAI_API_KEY    Your OpenAI API key (required unless using --api-key)"
    echo ""
    echo "Features:"
    echo "  🧠 Sequential translation with context memory"
    echo "  📚 Builds on previous translations for consistency"
    echo "  🎯 Professional self-care terminology"
    echo "  💾 Automatic backup and merging"
    echo ""
    exit 0
fi

# Parse arguments
PAGE_START=""
PAGE_END=""
DRY_RUN=""
API_KEY=""
CONTEXT_SIZE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --api-key)
            API_KEY="--api-key $2"
            shift 2
            ;;
        --context-size)
            CONTEXT_SIZE="--context-size $2"
            shift 2
            ;;
        -*)
            print_error "Unknown option: $1"
            exit 1
            ;;
        *)
            if [ -z "$PAGE_START" ]; then
                PAGE_START="$1"
            elif [ -z "$PAGE_END" ]; then
                PAGE_END="$1"
            else
                print_error "Too many arguments"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate page start
if [ -z "$PAGE_START" ]; then
    print_error "Page start is required"
    exit 1
fi

# Show what we're about to do
if [ -n "$DRY_RUN" ]; then
    print_info "Running in DRY-RUN mode (no API calls, no files modified)"
fi

if [ -n "$PAGE_END" ]; then
    print_ai "Translating pages $PAGE_START to $PAGE_END using GPT-5..."
else
    print_ai "Translating page $PAGE_START using GPT-5..."
fi

if [ -n "$CONTEXT_SIZE" ]; then
    print_info "Using context size: ${CONTEXT_SIZE#--context-size }"
else
    print_info "Using default context size: 10"
fi

# Create backup of English file if it exists and we're not in dry-run mode
if [ -f "content/i18n/en/texts.json" ] && [ -z "$DRY_RUN" ]; then
    backup_file="content/i18n/en/texts.json.backup.$(date +%Y%m%d_%H%M%S)"
    cp "content/i18n/en/texts.json" "$backup_file"
    print_info "Backup created: $backup_file"
fi

# Build command
CMD="python3 translate_gpt5.py $PAGE_START"
if [ -n "$PAGE_END" ]; then
    CMD="$CMD $PAGE_END"
fi
if [ -n "$DRY_RUN" ]; then
    CMD="$CMD $DRY_RUN"
fi
if [ -n "$API_KEY" ]; then
    CMD="$CMD $API_KEY"
fi
if [ -n "$CONTEXT_SIZE" ]; then
    CMD="$CMD $CONTEXT_SIZE"
fi

# Run the Python script
print_ai "Running GPT-5 translation script..."
eval $CMD

if [ $? -eq 0 ]; then
    if [ -z "$DRY_RUN" ]; then
        print_success "Translation completed successfully!"
        print_info "English translations updated in content/i18n/en/texts.json"
        print_ai "GPT-5 has learned from the context and provided consistent translations!"
    else
        print_success "Dry run completed successfully!"
    fi
else
    print_error "Translation failed. Check the output above for details."
    exit 1
fi
