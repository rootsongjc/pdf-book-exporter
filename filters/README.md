# PDF Book Exporter Filters

A collection of Pandoc Lua filters for enhanced PDF book generation.

## Available Filters

### emoji-passthrough.lua

Handles emoji characters for LaTeX output with proper font switching.

### minted-filter.lua

Converts fenced code blocks to minted environments for better syntax highlighting.

### table-wrap.lua

Converts pipe tables to longtable format for better page wrapping.

### cleanup-filter.lua

Cleans up problematic characters and formatting issues.

### ansi-cleanup.lua

Removes ANSI escape codes from content.

### fix-lstinline.lua

Fixes inline code styling issues with CJK characters.

### symbol-fallback-filter.lua

Provides fallback handling for special symbols and characters.

## Usage

These filters are automatically applied by the `cli.py` script. They are located in the `filters/` directory and are applied in the correct order during PDF generation.

## Requirements

- Pandoc with Lua support
- LaTeX distribution with required packages (see main documentation)

## Filter Details

Each filter serves a specific purpose in the PDF generation pipeline:

- **emoji-passthrough.lua**: Ensures proper emoji rendering with font switching
- **minted-filter.lua**: Provides enhanced syntax highlighting for code blocks
- **table-wrap.lua**: Improves table formatting and page breaks
- **cleanup-filter.lua**: Removes problematic characters that can break LaTeX compilation
- **ansi-cleanup.lua**: Strips ANSI escape sequences from content
- **fix-lstinline.lua**: Fixes inline code rendering issues with CJK characters
- **symbol-fallback-filter.lua**: Handles special symbols and provides fallbacks
