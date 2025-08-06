--[[
ANSI Cleanup Filter for LaTeX PDF Generation
This filter comprehensively removes ANSI escape codes from all content
to prevent LaTeX compilation errors
]]

-- Comprehensive ANSI escape code removal
local function strip_ansi_codes(text)
    if not text or type(text) ~= "string" then
        return text
    end
    
    -- Remove various forms of ANSI escape sequences
    
    -- Standard ANSI color codes (ESC[...m)
    text = text:gsub("\27%[[%d;]*m", "")  -- Literal ESC character
    text = text:gsub("\\033%[[%d;]*m", "") -- Octal escape \033
    text = text:gsub("\\x1[bB]%[[%d;]*m", "") -- Hex escape \x1b or \x1B
    text = text:gsub("\\e%[[%d;]*m", "") -- Short escape \e
    
    -- ANSI escape sequences with other terminators
    text = text:gsub("\27%[[%d;]*[A-Za-z]", "") -- Literal ESC
    text = text:gsub("\\033%[[%d;]*[A-Za-z]", "") -- Octal
    text = text:gsub("\\x1[bB]%[[%d;]*[A-Za-z]", "") -- Hex
    text = text:gsub("\\e%[[%d;]*[A-Za-z]", "") -- Short
    
    -- Handle shell variable assignments containing ANSI codes
    -- Patterns like: RED='\033[0;31m' or RED="\033[0;31m"
    text = text:gsub("='\\033%[[%d;]*m'", "=''")
    text = text:gsub('="\\033%[[%d;]*m"', '=""')
    text = text:gsub("='\\e%[[%d;]*m'", "=''")
    text = text:gsub('="\\e%[[%d;]*m"', '=""')
    text = text:gsub("='\\x1[bB]%[[%d;]*m'", "=''")
    text = text:gsub('="\\x1[bB]%[[%d;]*m"', '=""')
    
    -- Handle assignments without quotes
    text = text:gsub("=\\033%[[%d;]*m", "=")
    text = text:gsub("=\\e%[[%d;]*m", "=")
    text = text:gsub("=\\x1[bB]%[[%d;]*m", "=")
    
    -- Handle more complex variable assignments with color codes
    text = text:gsub("([%w_]+)=(['\"])\\\\*033%[[%d;]*m%2", "%1=%2%2")
    text = text:gsub("([%w_]+)=(['\"])\\\\*e%[[%d;]*m%2", "%1=%2%2")
    text = text:gsub("([%w_]+)=(['\"])\\\\*x1[bB]%[[%d;]*m%2", "%1=%2%2")
    
    -- Remove any remaining problematic backslash sequences
    -- This handles cases where \033 might be interpreted as LaTeX command
    text = text:gsub("\\033", "\\\\textbackslash{}033")
    text = text:gsub("\\x1[bB]", "\\\\textbackslash{}x1b")
    
    -- Handle raw octal sequences that might cause issues
    text = text:gsub("\\(%d%d%d)%[", function(digits)
        if digits == "033" then
            return "[ESC_" .. digits .. "]["
        else
            return "\\\\" .. digits .. "["
        end
    end)
    
    return text
end

-- Apply ANSI cleanup to code blocks
function CodeBlock(elem)
    if elem.text then
        elem.text = strip_ansi_codes(elem.text)
    end
    return elem
end

-- Apply ANSI cleanup to inline code
function Code(elem)
    if elem.text then
        elem.text = strip_ansi_codes(elem.text)
    end
    return elem
end

-- Apply ANSI cleanup to raw blocks
function RawBlock(elem)
    if elem.text then
        elem.text = strip_ansi_codes(elem.text)
    end
    return elem
end

-- Apply ANSI cleanup to raw inline
function RawInline(elem)
    if elem.text then
        elem.text = strip_ansi_codes(elem.text)
    end
    return elem
end

-- Apply ANSI cleanup to string elements
function Str(elem)
    if elem.text then
        elem.text = strip_ansi_codes(elem.text)
    end
    return elem
end

-- Apply ANSI cleanup to link URLs and titles
function Link(elem)
    if elem.target then
        elem.target = strip_ansi_codes(elem.target)
    end
    if elem.title then
        elem.title = strip_ansi_codes(elem.title)
    end
    return elem
end

-- Apply ANSI cleanup to image URLs and titles  
function Image(elem)
    if elem.src then
        elem.src = strip_ansi_codes(elem.src)
    end
    if elem.title then
        elem.title = strip_ansi_codes(elem.title)
    end
    return elem
end
