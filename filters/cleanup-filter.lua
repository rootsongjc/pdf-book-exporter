--[[
Cleanup filter to fix common LaTeX line break issues
This filter addresses problems with empty lines that have trailing backslashes
]]

-- Clean up code blocks by removing trailing empty lines and ANSI escape codes
function CodeBlock(elem)
    -- Remove ANSI escape codes
    local clean_text = elem.text:gsub("\27%[[%d;]+m", "")
    clean_text = clean_text:gsub("\\033%[[%d;]+m", "")

    -- Remove trailing empty lines from code
    local lines = {}
    for line in clean_text:gmatch("[^\r\n]*") do
        table.insert(lines, line)
    end
    
    -- Remove trailing empty lines
    while #lines > 0 and lines[#lines]:match("^%s*$") do
        table.remove(lines)
    end
    
    elem.text = table.concat(lines, "\n")
    return elem
end

-- Clean up paragraphs to remove problematic content
function Para(elem)
    -- Check if paragraph contains only whitespace or breaks
    local content_str = pandoc.utils.stringify(elem)
    if content_str:match("^%s*$") then
        -- Return empty block instead of empty paragraph
        return {}
    end
    return elem
end

-- Clean up raw blocks
function RawBlock(elem)
    if elem.format == "latex" then
        -- Remove ANSI escape codes
        local cleaned = elem.text:gsub("\27%[[%d;]+m", "")
        cleaned = cleaned:gsub("\\033%[[%d;]+m", "")

        -- Remove trailing backslashes from empty lines
        cleaned = cleaned:gsub("\n%s*\\\\%s*\n", "\n\n")
        -- Remove lines that are just whitespace followed by \\
        cleaned = cleaned:gsub("\n%s+\\\\%s*\n", "\n")
        -- Remove double backslashes at end of content
        cleaned = cleaned:gsub("\\\\%s*$", "")
        
        -- Fix specific problematic NormalTok patterns, but only if they are truly empty
        -- and not part of minted code blocks
        
        -- Only clean up NormalTok patterns that are clearly problematic
        -- Avoid cleaning patterns that might be legitimate LaTeX from minted
        
        -- Remove empty NormalTok followed by double backslash
        cleaned = cleaned:gsub("\\NormalTok{%s*}\\\\%s*\n", "\n")
        
        -- Remove empty tokens at line endings
        cleaned = cleaned:gsub("\\[%a]+Tok{%s*}\\\\%s*$", "")
        
        -- Fix double newlines after tokens
        cleaned = cleaned:gsub("}\\\\%s*\n%s*\n", "}\n\n")
        
        elem.text = cleaned
    end
    return elem
end

-- Clean up table cells to prevent empty line break issues
function Table(tbl)
    -- Clean up all cells in the table
    local function clean_cell_contents(contents)
        if not contents then return {} end
        
        local cleaned = {}
        for i, element in ipairs(contents) do
            if element.t == "Str" then
                -- Keep non-empty strings
                if element.text and element.text ~= "" then
                    table.insert(cleaned, element)
                end
            elseif element.t == "Space" then
                -- Keep spaces only if they're not at the end
                table.insert(cleaned, element)
            elseif element.t ~= "SoftBreak" and element.t ~= "LineBreak" then
                -- Keep other elements except breaks
                table.insert(cleaned, element)
            end
        end
        return cleaned
    end
    
    -- Process header
    if tbl.head and tbl.head.rows then
        for _, row in ipairs(tbl.head.rows) do
            for _, cell in ipairs(row.cells) do
                cell.contents = clean_cell_contents(cell.contents)
            end
        end
    end
    
    -- Process body
    if tbl.bodies then
        for _, body in ipairs(tbl.bodies) do
            if body.body then
                for _, row in ipairs(body.body) do
                    for _, cell in ipairs(row.cells) do
                        cell.contents = clean_cell_contents(cell.contents)
                    end
                end
            end
        end
    end
    
    return tbl
end
