"""
ADT Utils Script Registry

This module provides metadata about all production scripts available in this package.
External repositories can import this to discover which scripts are available,
their descriptions, arguments, and how to run them.
"""

import os
from pathlib import Path
import sys
from typing import List, Optional

sys.path.append(os.getcwd())

from src.structs.script import Script, ScriptCategory, ScriptArgument, ScriptExample


# Base path to this package
PACKAGE_ROOT = Path(__file__).parent

# Registry of all production scripts
PRODUCTION_SCRIPTS: List[Script] = [
    Script(
        id="validate_adt",
        name="ADT HTML Validator",
        description="Validates HTML files for required data-id attributes and ADT compliance",
        path=str(os.path.join("src", "validation", "scripts", "validate_adt.py")),
        category=ScriptCategory.VALIDATION,
        production_ready=True,
        arguments=[
            ScriptArgument(
                name="target_dir",
                type="str",
                description="Target directory path containing HTML files to validate",
                required=True,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="verbose",
                type="bool",
                description="Enable verbose output showing detailed validation issues",
                required=False,
                show_in_ui=True,
                default=False,
            ),
            ScriptArgument(
                name="output",
                type="str",
                description="Save detailed validation report to specified file",
                required=False,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="fix",
                type="bool",
                description="Attempt to auto-fix validation issues (experimental)",
                required=False,
                show_in_ui=False,
                default=False,
            ),
        ],
        examples=[
            ScriptExample(
                command="python3 {path} ./output",
                description="Validate all HTML files in ./output directory",
            ),
            ScriptExample(
                command="python3 {path} ./output --start-page 1 --end-page 10",
                description="Validate pages 1-10 only",
            ),
            ScriptExample(
                command="python3 {path} ./output --verbose --output report.txt",
                description="Validate with detailed output and save report to file",
            ),
        ],
    ),
    Script(
        id="fix_missing_data_ids",
        name="ADT Data-ID Auto-Fixer",
        description="Automatically adds missing data-id attributes to HTML elements using i18n JSON files",
        path=str(
            os.path.join("src", "validation", "scripts", "fix_missing_data_ids.py")
        ),
        category=ScriptCategory.FIXING,
        production_ready=True,
        arguments=[
            ScriptArgument(
                name="target_dir",
                type="str",
                description="Target directory path containing HTML files to validate",
                required=True,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="dry_run",
                type="bool",
                description="Preview changes without modifying files",
                required=False,
                show_in_ui=False,
                default=False,
            ),
            ScriptArgument(
                name="verbose",
                type="bool",
                description="Show detailed information about each fix",
                required=False,
                show_in_ui=True,
                default=False,
            ),
            ScriptArgument(
                name="auto-format",
                type="bool",
                description="Format modified HTML files with Prettier after fixes",
                required=False,
                show_in_ui=True,
                default=False,
            ),
        ],
        examples=[
            ScriptExample(
                command="python3 {path} ./output",
                description="Preview what would be fixed without making changes",
            ),
            ScriptExample(
                command="python3 {path} ./output",
                description="Fix missing data-id attributes in all HTML files",
            ),
            ScriptExample(
                command="python3 {path} ./output --start-page 5 --end-page 15 --verbose",
                description="Fix pages 5-15 with detailed output",
            ),
        ],
    ),
    Script(
        id="regenerate_tts",
        name="ADT TTS Regenerator",
        description="Regenerates TTS audio files for HTML content using OpenAI API",
        path=str(os.path.join("src", "regeneration", "scripts", "regenerate_tts.py")),
        category=ScriptCategory.REGENERATION,
        production_ready=True,
        arguments=[
            ScriptArgument(
                name="target_dir",
                type="str",
                description="Target directory containing content/i18n",
                required=True,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="start-page",
                type="int",
                description="Starting page number (inclusive)",
                required=False,
                show_in_ui=True,
                default=None,
            ),
            ScriptArgument(
                name="end-page",
                type="int",
                description="Ending page number (inclusive)",
                required=False,
                show_in_ui=True,
                default=None,
            ),
            ScriptArgument(
                name="language",
                type="str",
                description="Comma-separated list of languages to regenerate (e.g. 'en', 'es', or 'en,es')",
                required=True,
                show_in_ui=True,
                default=None,
            ),
            ScriptArgument(
                name="input-json",
                type="str",
                description="Path to input JSON file containing text content (overrides HTML parsing)",
                required=False,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="api-key",
                type="str",
                description="OpenAI API key (or set OPENAI_API_KEY env variable)",
                required=False,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="data-ids",
                type="str",
                description="Comma-separated list of data IDs to regenerate (e.g. 'text-01-01,text-01-02')",
                required=False,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="instruction",
                type="str",
                description="Custom instruction to override config/default for TTS generation",
                required=False,
                show_in_ui=False,
                default=None,
            ),
        ],
        examples=[
            ScriptExample(
                command="python3 {path} ./output --language en,es",
                description="Regenerate the TTS of all strings in all HTML files in ./output directory into the output/audio folder in the desired languages",
            ),
            ScriptExample(
                command="python3 {path} ./output --start-page 1 --end-page 10 --language en,es",
                description="Regenerate TTS for pages 1-10 only",
            ),
            ScriptExample(
                command="python3 {path} ./output --input-json changes.json --language es",
                description="Regenerate TTS for texts specified in changes.json only, in Spanish",
            ),
            ScriptExample(
                command="python3 {path} ./output --api-key sk-xxx --language en",
                description="Regenerate TTS using a specific OpenAI API key",
            ),
        ],
    ),
    Script(
        id="language_flattening",
        name="HTML Language Flattening",
        description="Overrides HTML text content using translations from texts.json files based on config.json default language",
        path=str(os.path.join("src", "language_flattening", "scripts", "language_flattening.py")),
        category=ScriptCategory.FIXING,
        production_ready=True,
        arguments=[
            ScriptArgument(
                name="target_dir",
                type="str",
                description="Target directory containing HTML files and assets/content/config.json",
                required=True,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="start-page",
                type="int",
                description="Starting page number (extracted from data-id attributes)",
                required=False,
                show_in_ui=True,
                default=None,
            ),
            ScriptArgument(
                name="end-page",
                type="int",
                description="Ending page number (extracted from data-id attributes)",
                required=False,
                show_in_ui=True,
                default=None,
            ),
            ScriptArgument(
                name="verbose",
                type="bool",
                description="Enable verbose output showing detailed processing information",
                required=False,
                show_in_ui=True,
                default=False,
            ),
            ScriptArgument(
                name="dry-run",
                type="bool",
                description="Show what would be changed without modifying files",
                required=False,
                show_in_ui=True,
                default=False,
            ),
        ],
        examples=[
            ScriptExample(
                command="python3 {path} ./target_directory",
                description="Override all HTML files with default language texts from config.json",
            ),
            ScriptExample(
                command="python3 {path} ./target_directory --start-page 50 --end-page 60",
                description="Override HTML files for pages 50-60 only (based on data-id attributes)",
            ),
            ScriptExample(
                command="python3 {path} ./target_directory --dry-run --verbose",
                description="Preview changes with detailed output without modifying files",
            ),
            ScriptExample(
                command="python3 {path} ./target_directory --verbose",
                description="Override files with detailed logging output",
            ),
        ],
    ),
    Script(
        id="generate_timecodes",
        name="ADT Audio Timecode Generator",
        description="Generates timecode JSON files from ADT audio files using Whisper transcription. Existing output files with \"locked\": true at the top level are preserved across re-runs so hand-corrections are not overwritten.",
        path=str(
            os.path.join(
                "src", "timecode_generation", "scripts", "generate_timecodes.py"
            )
        ),
        category=ScriptCategory.REGENERATION,
        production_ready=True,
        arguments=[
            ScriptArgument(
                name="target_dir",
                type="str",
                description="Root ADT directory containing content/i18n/{language}/audio",
                required=True,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="language",
                type="str",
                description="Language code to process (for example: es, en)",
                required=False,
                show_in_ui=True,
                default=None,
            ),
            ScriptArgument(
                name="start-page",
                type="int",
                description="Starting page number from audio filename prefix",
                required=False,
                show_in_ui=True,
                default=None,
            ),
            ScriptArgument(
                name="end-page",
                type="int",
                description="Ending page number from audio filename prefix",
                required=False,
                show_in_ui=True,
                default=None,
            ),
            ScriptArgument(
                name="api-key",
                type="str",
                description="OpenAI API key (or set OPENAI_API_KEY env variable)",
                required=False,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="model",
                type="str",
                description="OpenAI transcription model to use. whisper-1 (default) returns word-level timestamps. gpt-4o-transcribe has no timestamps and falls back to proportional allocation via ffprobe.",
                required=False,
                show_in_ui=False,
                default="whisper-1",
            ),
            ScriptArgument(
                name="text-model",
                type="str",
                description="Optional hybrid mode. Fetch text content from this model (e.g. gpt-4o-transcribe) and word timings from --model (e.g. whisper-1). Doubles the API cost per page.",
                required=False,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="dry-run",
                type="bool",
                description="Preview output generation without writing files",
                required=False,
                show_in_ui=True,
                default=False,
            ),
            ScriptArgument(
                name="non-strict-data-ids",
                type="bool",
                description="Allow generation when element count does not exactly match texts.json data-id count",
                required=False,
                show_in_ui=True,
                default=False,
            ),
            ScriptArgument(
                name="verbose",
                type="bool",
                description="Enable verbose output showing detailed processing information",
                required=False,
                show_in_ui=True,
                default=False,
            ),
            ScriptArgument(
                name="char-timing",
                type="bool",
                description="Derive word durations from character count instead of Whisper. No API key required. Rule: 1–3 letters = 0.2 s, 4–7 = 0.4 s, 8+ = 0.6 s; 0.6 s inter-element gap.",
                required=False,
                show_in_ui=True,
                default=False,
            ),
        ],
        examples=[
            ScriptExample(
                command="python3 {path} ./target_adt --language es",
                description="Generate timecodes for all Spanish audio files using Whisper (default, word-level timestamps)",
            ),
            ScriptExample(
                command="python3 {path} ./target_adt --language es --start-page 6 --end-page 20",
                description="Generate timecodes for pages 6-20 only",
            ),
            ScriptExample(
                command="python3 {path} ./target_adt --language es --model whisper-1 --text-model gpt-4o-transcribe",
                description="Hybrid mode: gpt-4o-transcribe for accurate word order, whisper-1 for precise word timings (2x API cost, best quality)",
            ),
            ScriptExample(
                command="python3 {path} ./target_adt --language es --model gpt-4o-transcribe",
                description="Text-only mode: gpt-4o-transcribe for accurate transcription, timing allocated proportionally via ffprobe (no word-level timestamps)",
            ),
            ScriptExample(
                command="python3 {path} ./target_adt --language es --char-timing",
                description="Char-timing mode: derive word durations from letter count (no API key needed, use when Whisper fails or produces collapsed elements)",
            ),
            ScriptExample(
                command="python3 {path} ./target_adt --language es --start-page 49 --end-page 49 --char-timing",
                description="Char-timing for a single problematic page (fixes start==end errors without an API call)",
            ),
            ScriptExample(
                command="python3 {path} ./target_adt --language es --non-strict-data-ids --verbose",
                description="Generate timecodes allowing element/data-id count mismatches, with verbose logs",
            ),
            ScriptExample(
                command="python3 {path} ./target_adt --language en --dry-run --verbose",
                description="Preview generation with verbose logs without writing files",
            ),
        ],
    ),
]


def get_script_info(script_id: str) -> Optional[Script]:
    """
    Get information about a specific script.

    Args:
        script_id: The ID of the script to get information about

    Returns:
        A Script object, or None if the script is not found
    """
    return next(
        (script for script in PRODUCTION_SCRIPTS if script.id == script_id), None
    )


def list_scripts(
    category: Optional[ScriptCategory] = None, production_only: bool = True
) -> List[Script]:
    """
    List all available scripts, optionally filtered by category.

    Args:
        category: The category of the scripts to list
        production_only: Whether to only include production-ready scripts

    Returns:
        A list of Script objects
    """
    scripts = []
    for script in PRODUCTION_SCRIPTS:
        if category and script.category != category:
            continue
        if production_only and not script.production_ready:
            continue

        scripts.append(script)
    return scripts


def get_script_command(script_id: str, **kwargs) -> Optional[str]:
    """
    Generate a command to run a specific script with given arguments.

    Args:
        script_id: The ID of the script to run
        **kwargs: Additional arguments to pass to the script

    Returns:
        A string containing the command to run the script, or None if the script is not found
    """
    script = get_script_info(script_id)
    if not script:
        return None

    path = script.path
    cmd_parts = [f"python3 {path}"]

    # Add positional arguments first (required arguments)
    for arg in script.arguments:
        if arg.required:
            arg_name = arg.name
            if arg_name in kwargs:
                cmd_parts.append(str(kwargs[arg_name]))
            else:
                cmd_parts.append(f"<{arg_name}>")

    # Add optional arguments (flags)
    for arg in script.arguments:
        if not arg.required:
            arg_name = arg.name

            if arg_name in kwargs:
                if arg.type == "bool" and kwargs[arg_name]:
                    cmd_parts.append(f"--{arg_name}")
                elif arg.type != "bool" and kwargs[arg_name] is not None:
                    cmd_parts.append(f"--{arg_name} {kwargs[arg_name]}")

    return " ".join(cmd_parts)


def print_script_help(script: Script | None = None):
    """
    Print help information for a specific script or all scripts.

    Args:
        script_id: The ID of the script to print help for, or None to print help for all scripts
    """
    if script:
        print(f"\n=== {script.name} ===")
        print(f"ID: {script.id}")
        print(f"Name: {script.name}")
        print(f"Description: {script.description}")
        print(f"Path: {script.path}")
        print(f"Category: {script.category}")

        print("\nRequired Arguments:")
        for arg in script.arguments:
            print(f"  {arg.name} ({arg.type}): {arg.description}")

        print("\nOptional Arguments:")
        for arg in script.arguments:
            default_str = f" [default: {arg.default}]" if arg.default else ""
            print(f"  {arg.name} ({arg.type}): {arg.description}{default_str}")

        print("\nExamples:")
        for example in script.examples:
            cmd = example.command.format(path=script.path)
            print(f"  {cmd}")
            print(f"    → {example.description}")

    else:
        print("\n=== ADT Utils Production Scripts ===")
        for script in PRODUCTION_SCRIPTS:
            status = "✅" if script.production_ready else "🧪"
            print(f"{status} {script.id}: {script.description}")


if __name__ == "__main__":
    # When run directly, show help for all scripts
    print_script_help()

    for script in PRODUCTION_SCRIPTS:
        print_script_help(script)
