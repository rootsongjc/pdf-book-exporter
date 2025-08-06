--[[
Pandoc Lua filter to use minted for code blocks instead of listings
This filter converts fenced code blocks to minted environments
]]

function CodeBlock(elem)
    -- Get the language from the first class
    local lang = elem.classes[1] or "text"

    -- Convert common language aliases and unsupported languages
    local lang_map = {
        ["sh"] = "bash",
        ["shell"] = "bash",
        ["js"] = "javascript",
        ["ts"] = "typescript",
        ["py"] = "python",
        ["yml"] = "yaml",
        ["dockerfile"] = "docker",
        ["rs"] = "rust",
        ["go-html-template"] = "html",
        ["gotemplate"] = "html",
        ["go-template"] = "html"
    }

    if lang_map[lang] then
        lang = lang_map[lang]
    end

    -- List of known supported Pygments lexers for common languages
    local supported_lexers = {
        "text", "bash", "javascript", "typescript", "python", "yaml", "docker", "rust",
        "html", "css", "json", "xml", "go", "java", "c", "cpp", "sql", "markdown",
        "latex", "php", "ruby", "perl", "r", "scala", "swift", "kotlin", "dart"
    }

    -- Check if the language is supported, fallback to text if not
    local function is_supported(language)
        for _, supported in ipairs(supported_lexers) do
            if supported == language then
                return true
            end
        end
        return false
    end

    if not is_supported(lang) then
        lang = "text"
    end

    -- Use minted with mdframed and precise negative margins for line numbers inside frame
    local minted_begin = "\\begin{mdframed}[style=codeblockstyle]\n\\begin{minted}{" .. lang .. "}"
    local minted_end = "\\end{minted}\n\\end{mdframed}"

    -- Return raw LaTeX block
    return pandoc.RawBlock("latex", minted_begin .. "\n" .. elem.text .. "\n" .. minted_end)
end

-- Also handle inline code (if needed)
function Code(elem)
    -- For inline code, we can use \mintinline or just keep it as is
    return elem
end
