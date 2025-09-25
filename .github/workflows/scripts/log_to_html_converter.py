#!/usr/bin/env python3
"""
Convert log files with ANSI escape sequences to HTML format.

This script converts terminal log files containing ANSI color codes
to properly formatted HTML files with CSS styling for web browser viewing.
"""

import os
import re
import html
from typing import Dict, Tuple


class AnsiToHtmlConverter:
    """Convert ANSI escape sequences to HTML with CSS styling."""

    def __init__(self):
        """Initialize the converter with ANSI color mappings."""
        # ANSI color code mappings to CSS classes
        self.ansi_colors = {
            # Standard colors
            '30': 'ansi-black',
            '31': 'ansi-red',
            '32': 'ansi-green',
            '33': 'ansi-yellow',
            '34': 'ansi-blue',
            '35': 'ansi-magenta',
            '36': 'ansi-cyan',
            '37': 'ansi-white',

            # Bright colors
            '90': 'ansi-bright-black',
            '91': 'ansi-bright-red',
            '92': 'ansi-bright-green',
            '93': 'ansi-bright-yellow',
            '94': 'ansi-bright-blue',
            '95': 'ansi-bright-magenta',
            '96': 'ansi-bright-cyan',
            '97': 'ansi-bright-white',

            # Background colors
            '40': 'ansi-bg-black',
            '41': 'ansi-bg-red',
            '42': 'ansi-bg-green',
            '43': 'ansi-bg-yellow',
            '44': 'ansi-bg-blue',
            '45': 'ansi-bg-magenta',
            '46': 'ansi-bg-cyan',
            '47': 'ansi-bg-white',

            # Text formatting
            '1': 'ansi-bold',
            '2': 'ansi-dim',
            '3': 'ansi-italic',
            '4': 'ansi-underline',
            '7': 'ansi-reverse',
            '9': 'ansi-strikethrough',
        }

        # Pattern to match ANSI escape sequences (colors and cursor control)
        self.ansi_pattern = re.compile(r'\x1b\[[0-9;]*m|\[[0-9;]*m')

        # Pattern to match terminal control sequences (cursor positioning, screen clearing, etc.)
        self.control_pattern = re.compile(r'\x1b\[[0-9;]*[A-Za-z]|\[[0-9;]*[A-Za-z]|[0-9]+\[\?[0-9]+[a-z]|\x1b\[[0-9;]*[HJKfhlr]')

    def get_css_styles(self) -> str:
        """Generate CSS styles for ANSI colors."""
        return """
        <style>
            .log-container {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                background-color: #1e1e1e;
                color: #d4d4d4;
                padding: 20px;
                margin: 0;
                white-space: pre-wrap;
                font-size: 14px;
                line-height: 1.4;
                overflow-x: auto;
            }

            .log-line {
                display: block;
                margin: 0;
                padding: 0;
                line-height: 1.4;
                min-height: auto;
            }

            /* Standard colors */
            .ansi-black { color: #000000; }
            .ansi-red { color: #cd3131; }
            .ansi-green { color: #0dbc79; }
            .ansi-yellow { color: #e5e510; }
            .ansi-blue { color: #2472c8; }
            .ansi-magenta { color: #bc3fbc; }
            .ansi-cyan { color: #11a8cd; }
            .ansi-white { color: #e5e5e5; }

            /* Bright colors */
            .ansi-bright-black { color: #666666; }
            .ansi-bright-red { color: #f14c4c; }
            .ansi-bright-green { color: #23d18b; }
            .ansi-bright-yellow { color: #f5f543; }
            .ansi-bright-blue { color: #3b8eea; }
            .ansi-bright-magenta { color: #d670d6; }
            .ansi-bright-cyan { color: #29b8db; }
            .ansi-bright-white { color: #ffffff; }

            /* Background colors */
            .ansi-bg-black { background-color: #000000; }
            .ansi-bg-red { background-color: #cd3131; }
            .ansi-bg-green { background-color: #0dbc79; }
            .ansi-bg-yellow { background-color: #e5e510; }
            .ansi-bg-blue { background-color: #2472c8; }
            .ansi-bg-magenta { background-color: #bc3fbc; }
            .ansi-bg-cyan { background-color: #11a8cd; }
            .ansi-bg-white { background-color: #e5e5e5; }

            /* Text formatting */
            .ansi-bold { font-weight: bold; }
            .ansi-dim { opacity: 0.6; }
            .ansi-italic { font-style: italic; }
            .ansi-underline { text-decoration: underline; }
            .ansi-reverse {
                background-color: #d4d4d4;
                color: #1e1e1e;
            }
            .ansi-strikethrough { text-decoration: line-through; }

            /* Box drawing characters */
            .box-drawing {
                color: #65d656;
                font-weight: bold;
            }

            /* Line numbers */
            .line-number {
                color: #858585;
                margin-right: 10px;
                user-select: none;
                display: inline-block;
                width: 60px;
                text-align: right;
                vertical-align: top;
                line-height: inherit;
            }

            /* Header styling */
            .log-header {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 10px 20px;
                margin: -20px -20px 20px -20px;
                border-bottom: 1px solid #3e3e42;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }

            .log-header h1 {
                margin: 0;
                font-size: 18px;
                font-weight: 600;
            }

            .log-header .log-meta {
                font-size: 12px;
                color: #999999;
                margin-top: 5px;
            }
        </style>
        """

    def parse_ansi_sequence(self, sequence: str) -> Tuple[str, bool]:
        """Parse an ANSI escape sequence and return CSS class and reset flag."""
        # Remove escape character and brackets
        codes = sequence.replace('\x1b[', '').replace('[', '').replace('m', '')

        if codes == '0' or codes == '':
            return '', True  # Reset sequence

        css_classes = []
        for code in codes.split(';'):
            if code in self.ansi_colors:
                css_classes.append(self.ansi_colors[code])

        return ' '.join(css_classes), False

    def clean_control_sequences(self, text: str) -> str:
        """Remove terminal control sequences (cursor positioning, screen clearing, etc.)."""
        # Remove various terminal control sequences
        # Common patterns found in logs:
        # - 7[?6l[24;1H[2K[1/1] - complex cursor control
        # - [1;23r - set scroll region
        # - [?6l - reset mode
        # - [24;1H - cursor position
        # - [2K - clear line
        # - [2J - clear screen
        # - [H - cursor home

        # Remove complex sequences like 7[?6l[24;1H[2K
        text = re.sub(r'[0-9]*\[\?[0-9]*[a-z]\[[0-9;]*[A-Za-z]\[[0-9]*[A-Za-z]', '', text)

        # Remove sequences like [1;23r (scroll region)
        text = re.sub(r'\[[0-9;]+r', '', text)

        # Remove cursor positioning sequences
        text = re.sub(r'\x1b\[[0-9;]*[HJKfhlrABCDEFG]', '', text)
        text = re.sub(r'\[[0-9;]*[HJKfhlrABCDEFG]', '', text)

        # Remove mode setting sequences like [?6l, [?25h
        text = re.sub(r'\x1b\[\?[0-9]+[a-z]', '', text)
        text = re.sub(r'\[\?[0-9]+[a-z]', '', text)

        # Remove standalone numbers at start that are part of control sequences
        text = re.sub(r'^[0-9]+(?=\[)', '', text, flags=re.MULTILINE)

        # Remove trailing standalone numbers that are control sequence remnants
        text = re.sub(r'[0-9]+$', '', text, flags=re.MULTILINE)

        # Remove any remaining isolated control characters
        text = re.sub(r'\x1b\[[0-9;]*[A-Za-z](?<!m)', '', text)
        text = re.sub(r'\[[0-9;]*[A-Za-z](?<!m)', '', text)

        # Clean up any remaining orphaned numbers that were part of sequences
        text = re.sub(r'(?<=\s)[0-9]+(?=\s|$)', '', text)
        text = re.sub(r'^[0-9]+(?=\s)', '', text, flags=re.MULTILINE)

        return text

    def highlight_box_drawing_chars(self, text: str) -> str:
        """Highlight box drawing characters with special styling."""
        # Unicode box drawing characters
        box_chars = '┌┬┐├┼┤└┴┘│─┏┳┓┣╋┫┗┻┛┃━╔╦╗╠╬╣╚╩╝║═'

        result = []
        i = 0
        while i < len(text):
            char = text[i]
            if char in box_chars:
                # Find consecutive box drawing characters
                j = i
                while j < len(text) and text[j] in box_chars:
                    j += 1

                # Wrap consecutive box chars in span
                box_text = text[i:j]
                result.append(f'<span class="box-drawing">{box_text}</span>')
                i = j
            else:
                result.append(char)
                i += 1

        return ''.join(result)

    def convert_line(self, line: str, line_number: int = None) -> str:
        """Convert a single line with ANSI codes to HTML."""
        # First clean up terminal control sequences
        line = self.clean_control_sequences(line)

        # Escape HTML characters
        line = html.escape(line.rstrip('\n\r'))

        # Track current CSS classes
        current_classes = []
        result = []

        # Add line number if provided
        if line_number is not None:
            result.append(f'<span class="line-number">{line_number:4d}</span>')

        # Split line by ANSI sequences
        parts = self.ansi_pattern.split(line)
        sequences = self.ansi_pattern.findall(line)

        # Process each part
        for i, part in enumerate(parts):
            if i > 0 and i <= len(sequences):
                # Process ANSI sequence
                sequence = sequences[i - 1]
                css_class, is_reset = self.parse_ansi_sequence(sequence)

                if is_reset:
                    # Close any open spans and reset classes
                    if current_classes:
                        result.append('</span>')
                        current_classes = []
                else:
                    # Close previous span if exists
                    if current_classes:
                        result.append('</span>')

                    # Update current classes
                    if css_class:
                        current_classes = css_class.split()
                        result.append(f'<span class="{css_class}">')
                    else:
                        current_classes = []

            # Add the text part with box drawing highlighting
            if part:
                highlighted_part = self.highlight_box_drawing_chars(part)
                result.append(highlighted_part)

        # Close any remaining open spans
        if current_classes:
            result.append('</span>')

        return ''.join(result)

    def convert_log_to_html(self, log_file_path: str, output_file_path: str = None,
                           include_line_numbers: bool = True) -> str:
        """Convert a log file to HTML format."""
        if output_file_path is None:
            output_file_path = log_file_path.replace('.txt', '.html').replace('.log', '.html')

        # Read the log file
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"❌ Error reading log file {log_file_path}: {e}")
            return output_file_path

        # Get file info
        file_name = os.path.basename(log_file_path)
        file_size = os.path.getsize(log_file_path)

        # Generate HTML
        html_content = []
        html_content.append('<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_content.append(f'<title>Log File: {file_name}</title>')
        html_content.append(self.get_css_styles())
        html_content.append('</head><body><div class="log-container"><div class="log-header">')
        html_content.append(f'<h1>{file_name}</h1><div class="log-meta">File size: {file_size:,} bytes | Lines: {len(lines):,}</div></div>')

        # Convert each line
        for i, line in enumerate(lines, 1):
            converted_line = self.convert_line(line, i if include_line_numbers else None)
            html_content.append(f'<div class="log-line">{converted_line}</div>')

        html_content.append('</div></body></html>')

        # Write HTML file
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(''.join(html_content))
            print(f"✅ Converted {log_file_path} → {output_file_path}")
            return output_file_path
        except Exception as e:
            print(f"❌ Error writing HTML file {output_file_path}: {e}")
            return output_file_path


def convert_logs_in_directory(logs_dir: str, output_dir: str = None):
    """Convert all log files in a directory to HTML."""
    if output_dir is None:
        output_dir = logs_dir

    converter = AnsiToHtmlConverter()
    converted_files = []

    print(f"🔍 Scanning for log files in: {logs_dir}")

    for root, dirs, files in os.walk(logs_dir):
        for file in files:
            if file.endswith(('.log', '.txt')) and not file.endswith('.html'):
                log_path = os.path.join(root, file)

                # Create corresponding output directory
                rel_path = os.path.relpath(root, logs_dir)
                if rel_path == '.':
                    output_root = output_dir
                else:
                    output_root = os.path.join(output_dir, rel_path)

                os.makedirs(output_root, exist_ok=True)

                # Generate output file path
                html_filename = file.replace('.txt', '.html').replace('.log', '.html')
                html_path = os.path.join(output_root, html_filename)

                # Convert the file
                result_path = converter.convert_log_to_html(log_path, html_path)
                converted_files.append(result_path)

    print(f"\n✅ Converted {len(converted_files)} log files to HTML")
    return converted_files


def main():
    """Main function for command-line usage."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python log_to_html_converter.py <log_file_or_directory> [output_path]")
        print("Examples:")
        print("  python log_to_html_converter.py build.log")
        print("  python log_to_html_converter.py ./logs/")
        print("  python log_to_html_converter.py build.log build.html")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if os.path.isfile(input_path):
        # Convert single file
        converter = AnsiToHtmlConverter()
        converter.convert_log_to_html(input_path, output_path)
    elif os.path.isdir(input_path):
        # Convert directory
        convert_logs_in_directory(input_path, output_path)
    else:
        print(f"❌ Path not found: {input_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
