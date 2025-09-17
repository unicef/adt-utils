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
                description="Target directory path containing HTML files for TTS regeneration",
                required=True,
                show_in_ui=False,
                default=None,
            ),
            ScriptArgument(
                name="start-page",
                type="int",
                description="Specific starting page to regenerate (empty for all pages)",
                required=False,
                show_in_ui=True,
                default="",
            ),
            ScriptArgument(
                name="end-page",
                type="int",
                description="Specific ending page to regenerate (empty for all pages)",
                required=False,
                show_in_ui=True,
                default="",
            ),
            ScriptArgument(
                name="languages",
                type="str",
                description="Comma-separated list of languages to regenerate (e.g. 'en,es')",
                required=True,
                show_in_ui=True,
                default=None,
            ),
            ScriptArgument(
                name="input_json",
                type="str",
                description="Path to input JSON file containing text content (overrides HTML parsing)",
                required=False,
                show_in_ui=False,
                default=None,
            ),
        ],
        examples=[
            ScriptExample(
                command="python3 {path} ./output --languages en,es",
                description="Regenerate the TTS of all strings in all HTML files in ./output directory into the output/audio folder in the desired languages",
            ),
            ScriptExample(
                command="python3 {path} ./output --start-page 1 --end-page 10  --languages en,es",
                description="Regenerate TTS for pages 1-10 only",
            ),
            ScriptExample(
                command="python3 {path} ./output --input-json changes.json --languages es",
                description="Regenerate TTS for texts specified in changes.json only, in Spanish",
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

        print(f"\nRequired Arguments:")
        for arg in script.arguments:
            print(f"  {arg.name} ({arg.type}): {arg.description}")

        print(f"\nOptional Arguments:")
        for arg in script.arguments:
            default_str = f" [default: {arg.default}]" if arg.default else ""
            print(f"  {arg.name} ({arg.type}): {arg.description}{default_str}")

        print(f"\nExamples:")
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
