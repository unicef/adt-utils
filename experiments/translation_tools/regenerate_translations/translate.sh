#!/bin/bash

# Translation helper script for ADT Manual
# Usage: ./translate.sh [page_start] [page_end] [--dry-run]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "translate_page_range.py" ]; then
    print_error "translate_page_range.py not found. Please run this script from the project root."
    exit 1
fi

# Check if Spanish JSON exists
if [ ! -f "content/i18n/es/texts.json" ]; then
    print_error "Spanish translation file not found at content/i18n/es/texts.json"
    exit 1
fi

# Display help if no arguments
if [ $# -eq 0 ]; then
    echo "🌐 ADT Manual Translation Helper"
    echo ""
    echo "Usage:"
    echo "  ./translate.sh <page_start> [page_end] [--dry-run]"
    echo ""
    echo "Examples:"
    echo "  ./translate.sh 23              # Translate page 23"
    echo "  ./translate.sh 23 30           # Translate pages 23-30"
    echo "  ./translate.sh 23 30 --dry-run # Preview translations"
    echo ""
    echo "Options:"
    echo "  --dry-run    Show translations without saving"
    echo ""
    exit 0
fi

# Show what we're about to do
if [ "$3" = "--dry-run" ] || [ "$2" = "--dry-run" ]; then
    print_info "Running in DRY-RUN mode (no files will be modified)"
fi

if [ -n "$2" ] && [ "$2" != "--dry-run" ]; then
    print_info "Translating pages $1 to $2..."
else
    print_info "Translating page $1..."
fi

# Create backup of English file if it exists and we're not in dry-run mode
if [ -f "content/i18n/en/texts.json" ] && [ "$3" != "--dry-run" ] && [ "$2" != "--dry-run" ]; then
    backup_file="content/i18n/en/texts.json.backup.$(date +%Y%m%d_%H%M%S)"
    cp "content/i18n/en/texts.json" "$backup_file"
    print_info "Backup created: $backup_file"
fi

# Run the Python script
print_info "Running translation script..."
python3 translate_page_range.py "$@"

if [ $? -eq 0 ]; then
    if [ "$3" != "--dry-run" ] && [ "$2" != "--dry-run" ]; then
        print_success "Translation completed successfully!"
        print_info "English translations updated in content/i18n/en/texts.json"
    else
        print_success "Dry run completed successfully!"
    fi
else
    print_error "Translation failed. Check the output above for details."
    exit 1
fi
