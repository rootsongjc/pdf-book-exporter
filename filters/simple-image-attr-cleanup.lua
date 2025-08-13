--[[
Simple image attribute cleanup filter
This filter removes standalone paragraphs that contain only image attributes
like {width=1486 height=518}
]]

function Para(elem)
    -- Get the text content of the paragraph
    local content_str = pandoc.utils.stringify(elem)
    
    -- Check if this paragraph contains only image attribute syntax
    -- Patterns to match various formats:
    -- {width=123 height=456}
    -- {height=456 width=123}  
    -- {width=123}
    -- {height=456}
    local patterns = {
        "^%s*{%s*width%s*=%s*%d+%s+height%s*=%s*%d+%s*}%s*$",
        "^%s*{%s*height%s*=%s*%d+%s+width%s*=%s*%d+%s*}%s*$",
        "^%s*{%s*width%s*=%s*%d+%s*}%s*$",
        "^%s*{%s*height%s*=%s*%d+%s*}%s*$"
    }
    
    -- Check if content matches any image attribute pattern
    for _, pattern in ipairs(patterns) do
        if content_str:match(pattern) then
            return {}  -- Remove this paragraph completely
        end
    end
    
    -- Return unchanged if not an image attribute
    return elem
end
