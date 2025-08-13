--[[
Image attribute cleanup filter
This filter removes image attribute lines like {width=1486 height=518}
that appear immediately after images in markdown or LaTeX figure environments
]]

-- Track the type of the previous element
local previous_element_type = nil

function Image(elem)
    -- Mark that we just processed an image
    previous_element_type = "image"
    return elem
end

function RawBlock(elem)
    -- Check if this is a LaTeX figure environment
    if elem.format == "latex" and (elem.text:match("\\begin{figure}") or elem.text:match("\\includegraphics")) then
        previous_element_type = "latex_figure"
    else
        previous_element_type = "other"
    end
    return elem
end

function Para(elem)
    -- Check if this paragraph contains only image attributes
    local content_str = pandoc.utils.stringify(elem)
    
    -- More comprehensive patterns to match image attributes
    local patterns = {
        "^%s*{%s*width%s*=%s*%d+%s+height%s*=%s*%d+%s*}%s*$",           -- {width=123 height=456}
        "^%s*{%s*height%s*=%s*%d+%s+width%s*=%s*%d+%s*}%s*$",           -- {height=456 width=123}
        "^%s*{%s*width%s*=%s*%d+%s*}%s*$",                              -- {width=123}
        "^%s*{%s*height%s*=%s*%d+%s*}%s*$",                             -- {height=456}
        "^%s*{width%s*=%s*%d+%s+height%s*=%s*%d+}%s*$",                 -- {width=123 height=456} (no spaces around =)
        "^%s*{height%s*=%s*%d+%s+width%s*=%s*%d+}%s*$"                  -- {height=456 width=123} (no spaces around =)
    }
    
    -- Check if content matches any of the image attribute patterns
    local is_image_attr = false
    for _, pattern in ipairs(patterns) do
        if content_str:match(pattern) then
            is_image_attr = true
            break
        end
    end
    
    -- If previous element was image/figure and this paragraph contains only image attributes, remove it
    if (previous_element_type == "image" or previous_element_type == "latex_figure") and is_image_attr then
        previous_element_type = nil  -- Reset flag
        return {}  -- Remove this paragraph
    end
    
    -- Reset flag for non-image-attribute paragraphs
    previous_element_type = nil
    return elem
end

-- Reset flag for other block elements
function Header(elem)
    previous_element_type = nil
    return elem
end

function CodeBlock(elem)
    previous_element_type = nil
    return elem
end

function BlockQuote(elem)
    previous_element_type = nil
    return elem
end

function OrderedList(elem)
    previous_element_type = nil
    return elem
end

function BulletList(elem)
    previous_element_type = nil
    return elem
end

function Table(elem)
    previous_element_type = nil
    return elem
end

function Div(elem)
    previous_element_type = nil
    return elem
end
