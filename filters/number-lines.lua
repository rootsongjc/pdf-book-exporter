-- number-lines.lua
-- A Pandoc Lua filter to add line numbers to all code blocks
-- This filter adds the 'numberLines' attribute to CodeBlock elements
-- so that Pandoc's built-in syntax highlighter will output a two-column table
-- with line numbers in the left column

function CodeBlock(elem)
    -- Add the numberLines attribute to enable line numbering
    elem.attributes.numberLines = ""
    
    -- Set the starting line number (defaults to 1 if not specified)
    if not elem.attributes.startFrom then
        elem.attributes.startFrom = "1"
    end
    
    -- Force table format for line numbers in HTML output
    elem.attributes["number-lines"] = ""
    
    -- Return the modified code block
    return elem
end

-- Post-process to ensure line numbers are displayed as a table
function Div(elem)
    if elem.classes and elem.classes:includes("sourceCode") then
        -- Add additional styling class for better CSS targeting
        elem.classes:insert("numbered-code")
    end
    return elem
end
