-- Enhanced fix-lstinline filter
-- This filter fixes the issue where Pandoc generates \passthrough{\lstinline!...!}
-- and ensures inline code uses our template's table-aware wrapping logic

function RawInline(elem)
    -- Only process LaTeX output
    if not FORMAT:match 'latex' then
        return elem
    end
    
    -- Check if this is a passthrough lstinline command
    local content = elem.text
    if content:match("^\\passthrough{\\lstinline!.*!}$") then
        -- Extract the content between the exclamation marks
        local inline_content = content:match("\\passthrough{\\lstinline!(.-)}$")
        if inline_content then
            -- Remove the trailing exclamation mark
            inline_content = inline_content:gsub("!$", "")
            -- Use our template's texttt command which has table-aware line breaking
            return pandoc.RawInline('latex', '\\texttt{' .. inline_content .. '}')
        end
    end
    
    return elem
end

-- Function to escape LaTeX special characters for safe inclusion in texttt
function escape_latex_special_chars(text)
    if not text then return "" end
    -- Escape characters that could cause issues in LaTeX
    text = text:gsub("\\", "\\textbackslash{}")
    text = text:gsub("{", "\\{")
    text = text:gsub("}", "\\}")
    text = text:gsub("%$", "\\$")
    text = text:gsub("&", "\\&")
    text = text:gsub("%%", "\\%%")
    text = text:gsub("#", "\\#")
    text = text:gsub("%^", "\\textasciicircum{}")
    text = text:gsub("_", "\\_")
    text = text:gsub("~", "\\textasciitilde{}")
    return text
end

-- Handle Code elements directly - use template's texttt command
function Code(elem)
    -- Don't process if we're not generating LaTeX
    if not FORMAT:match 'latex' then
        return elem
    end
    
    -- Escape special characters and use our template's texttt command
    local escaped_text = escape_latex_special_chars(elem.text)
    return pandoc.RawInline('latex', '\\texttt{' .. escaped_text .. '}')
end
