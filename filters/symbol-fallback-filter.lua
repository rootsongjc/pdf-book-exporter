-- tools/pdf-book-exporter/filters/symbol-fallback-filter.lua
-- Symbol fallback filter for LaTeX PDF generation
--
-- This filter handles special Unicode symbols that may not be available in all fonts
-- by replacing them with LaTeX commands that provide proper fallbacks.
--
-- Key functionality:
-- 1. Replaces currency symbols with LaTeX currency commands
-- 2. Handles special punctuation and technical symbols
-- 3. Provides font-independent symbol rendering
-- 4. Avoids processing code contexts where symbols should be preserved
--
-- Implementation approach:
-- - Simple and reliable processing of only Str elements
-- - Avoids complex AST traversal that could cause issues
-- - Uses direct string replacement with LaTeX commands
-- - Preserves code blocks and inline code unchanged

-- Define the symbol mapping table
-- 
-- Maps Unicode symbols to LaTeX commands that provide reliable fallbacks.
-- Each command should be defined in the LaTeX template or through packages.
--
-- Categories:
-- 1. Currency symbols - Various international currencies
-- 2. Special punctuation - Rare punctuation marks
-- 3. Technical symbols - UI/UX and interface symbols
--
-- Note: LaTeX commands like \rupee{} should be defined in the template
-- with appropriate fallback mechanisms for missing fonts
local symbol_map = {
    -- Currency symbols
    ["₹"] = "\\rupee{}",           -- Indian Rupee
    ["₽"] = "\\ruble{}",           -- Russian Ruble  
    ["₪"] = "\\shekel{}",          -- Israeli Shekel
    ["₡"] = "\\colon{}",           -- Costa Rican Colon
    ["₢"] = "\\cruzeiro{}",        -- Brazilian Cruzeiro
    ["₣"] = "\\franc{}",           -- French Franc
    ["₤"] = "\\lira{}",            -- Italian Lira
    ["₥"] = "\\mill{}",            -- Mill symbol
    ["₦"] = "\\naira{}",           -- Nigerian Naira
    ["₧"] = "\\peseta{}",          -- Spanish Peseta
    ["₨"] = "\\rupeeold{}",        -- Old Rupee symbol
    
    -- Special punctuation and symbols
    ["‴"] = "\\tripleprime{}",     -- Triple prime
    ["⁏"] = "\\reversedSemicolon{}", -- Reversed semicolon
    ["⏳"] = "\\hourglass{}",       -- Hourglass
    ["ℹ"] = "\\infoSymbol{}",      -- Information symbol
    ["✊"] = "\\raisedFist{}",      -- Raised fist
    ["⌨"] = "\\keyboardSymbol{}",  -- Keyboard symbol
}

-- Simple and reliable approach: only process Str elements
-- This avoids complex data structure issues with pandoc.walk_inline/walk_block
--
-- Processing strategy:
-- 1. Only handle Str (string) elements to avoid AST complexity
-- 2. Use simple string replacement for reliability
-- 3. Return RawInline LaTeX when changes are made
-- 4. Explicitly avoid processing Code and CodeBlock elements
-- 5. Only process LaTeX output format

-- Process Str elements (inline text)
-- 
-- Main processing function for regular text content.
-- Scans through the symbol mapping table and replaces any found symbols
-- with their corresponding LaTeX commands.
--
-- Process:
-- 1. Check if generating LaTeX output
-- 2. Apply string replacements for each symbol in the mapping
-- 3. Return RawInline LaTeX if any changes were made
-- 4. Otherwise return the original element unchanged
function Str(elem)
    -- Only process LaTeX output
    if not FORMAT:match 'latex' then
        return elem
    end
    
    local text = elem.text
    local changed = false
    
    -- Replace each symbol with its LaTeX command
    for symbol, command in pairs(symbol_map) do
        local new_text = text:gsub(symbol, command)
        if new_text ~= text then
            text = new_text
            changed = true
        end
    end
    
    -- If any changes were made, return as raw LaTeX
    if changed then
        return pandoc.RawInline('latex', text)
    end
    
    -- Otherwise return original element
    return elem
end

-- Don't process inline code
-- 
-- Inline code should preserve symbols exactly as written.
-- Users may intentionally include Unicode symbols in code examples.
function Code(elem)
    return elem
end

-- Don't process code blocks
--
-- Code blocks should preserve all original characters.
-- Symbol replacement could break code syntax or meaning.
function CodeBlock(elem)
    return elem
end
