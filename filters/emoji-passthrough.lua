-- tools/pdf-book-exporter/filters/emoji-passthrough.lua
-- Advanced emoji processing filter for LaTeX PDF generation
--
-- This filter provides comprehensive emoji support for LaTeX documents:
-- 1. Detects Unicode emoji characters using strict range checking
-- 2. Handles emoji variation selectors (emoji vs text style)
-- 3. Wraps emojis with appropriate LaTeX font commands
-- 4. Provides fallback text representations for emoji in code contexts
-- 5. Processes inline code and code blocks with emoji-safe replacements
--
-- Key features:
-- - Precise emoji detection (avoids false positives with punctuation)
-- - Support for composite emoji sequences with variation selectors
-- - Context-aware processing (normal text vs code blocks)
-- - Comprehensive emoji-to-text mapping for accessibility
-- - Integration with LaTeX emoji font commands

-- Function to check if a character is an emoji
-- 
-- Uses strict Unicode range checking to identify genuine emoji characters
-- while avoiding false positives with:
-- - ASCII punctuation and symbols
-- - Mathematical operators  
-- - Currency symbols
-- - Arrows and technical symbols
--
-- Only includes actual emoji Unicode blocks:
-- - Miscellaneous Symbols and Pictographs (1F300-1F5FF)
-- - Emoticons (1F600-1F64F)
-- - Transport and Map Symbols (1F680-1F6FF) 
-- - Plus specific common emoji from other ranges
function is_emoji(char)
    local code = utf8.codepoint(char)
    if not code then return false end
    
    -- Exclude ASCII range entirely (0x00-0x7F)
    if code < 0x80 then
        return false  -- ASCII range, includes all punctuation, letters, numbers
    end
    
    -- Exclude Latin-1 supplement range (common punctuation)
    if code >= 0x80 and code <= 0xFF then
        return false
    end
    
    -- Exclude common punctuation ranges that might be misidentified
    if (code >= 0x2000 and code <= 0x206F) or    -- General Punctuation (includes quotes, dashes)
       (code >= 0x20A0 and code <= 0x20CF) or    -- Currency Symbols
       (code >= 0x2100 and code <= 0x214F and code ~= 0x2139) or    -- Letterlike Symbols (except info ℹ)
       (code >= 0x2150 and code <= 0x218F) or    -- Number Forms
       (code >= 0x2190 and code <= 0x21FF) or    -- Arrows (might be emoji-like but usually not)
       (code >= 0x2200 and code <= 0x22FF) or    -- Mathematical Operators
       (code >= 0x2300 and code <= 0x23FF and code ~= 0x2328) then  -- Miscellaneous Technical (except keyboard)
        return false
    end
    
    -- Be very specific about emoji ranges - only include actual emoji blocks
    return (code >= 0x1F300 and code <= 0x1F5FF) or  -- Symbols & Pictographs
           (code >= 0x1F600 and code <= 0x1F64F) or  -- Emoticons
           (code >= 0x1F680 and code <= 0x1F6FF) or  -- Transport & Map
           (code >= 0x1F700 and code <= 0x1F77F) or  -- Alchemical
           (code >= 0x1F780 and code <= 0x1F7FF) or  -- Geometric Shapes Extended
           (code >= 0x1F800 and code <= 0x1F8FF) or  -- Supplemental Arrows-C
           (code >= 0x1F900 and code <= 0x1F9FF) or  -- Supplemental Symbols
           (code >= 0x1FA00 and code <= 0x1FA6F) or  -- Chess Symbols
           (code >= 0x1FA70 and code <= 0x1FAFF) or  -- Symbols and Pictographs Extended-A
           (code >= 0x1F000 and code <= 0x1F02F) or  -- Mahjong & Dominoes
           -- Very specific common emoji symbols from Miscellaneous Symbols
           (code == 0x2600) or                        -- Sun
           (code == 0x2601) or                        -- Cloud
           (code == 0x2614) or                        -- Umbrella
           (code == 0x2615) or                        -- Coffee
           (code == 0x26A0) or                        -- Warning Sign ⚠
           (code == 0x26BD) or                        -- Soccer Ball
           (code == 0x26BE) or                        -- Baseball
           (code == 0x2728) or                        -- Sparkles ✨
           (code == 0x2764) or                        -- Heavy Black Heart ❤
           (code == 0x2B50) or                        -- White Medium Star ⭐
           (code == 0x2139) or                        -- Information Source ℹ
           (code == 0x2328) or                        -- Keyboard ⌨
           -- Specific technical/UI symbols that are commonly used as emoji
           (code == 0x2713) or                        -- Check Mark ✓
           (code == 0x2717) or                        -- Cross Mark ✗
           (code == 0x274C) or                        -- Cross Mark ❌
           (code == 0x2705)                           -- White Heavy Check Mark ✅
end

-- Function to check if a character is a variation selector
--
-- Variation selectors control whether Unicode characters appear in:
-- - Text style (VS15 - 0xFE0E): Black and white, text-like appearance
-- - Emoji style (VS16 - 0xFE0F): Colorful, pictographic appearance
--
-- This function detects these selectors to properly group them with
-- their base emoji characters for LaTeX processing
function is_variation_selector(char)
    local code = utf8.codepoint(char)
    if not code then return false end
    
    return code == 0xFE0F or                        -- Variation Selector-16 (emoji style)
           code == 0xFE0E or                        -- Variation Selector-15 (text style)
           (code >= 0xE0100 and code <= 0xE01EF)     -- Variation Selectors Supplement
end

-- Process text and wrap emojis, handling composite emojis with variation selectors
--
-- This function is the core text processor for normal document content:
-- 1. Iterates through text using UTF-8 aware character processing
-- 2. Identifies emoji characters using is_emoji function
-- 3. Looks ahead for variation selectors to build complete emoji sequences
-- 4. Wraps emoji sequences with {\emojifont ...} LaTeX commands
-- 5. Preserves non-emoji text unchanged
--
-- Special handling:
-- - Properly calculates UTF-8 character boundaries (1-4 bytes)
-- - Groups emojis with their variation selectors
-- - Uses direct font commands for better LaTeX compatibility
function process_text(text)
    local result = {}
    local i = 1

    while i <= #text do
        local char_start = i
        local char_end = i
        local byte = text:byte(i)

        if byte then
            -- Determine UTF-8 character length
            if byte < 0x80 then
                char_end = i
            elseif byte < 0xE0 then
                char_end = i + 1
            elseif byte < 0xF0 then
                char_end = i + 2
            else
                char_end = i + 3
            end

            local char = text:sub(char_start, char_end)

            if is_emoji(char) then
                -- Check if next character is a variation selector
                local next_i = char_end + 1
                local emoji_sequence = char

                -- Look ahead for variation selectors
                while next_i <= #text do
                    local next_byte = text:byte(next_i)
                    local next_char_end = next_i

                    if next_byte then
                        -- Determine next character length
                        if next_byte < 0x80 then
                            next_char_end = next_i
                        elseif next_byte < 0xE0 then
                            next_char_end = next_i + 1
                        elseif next_byte < 0xF0 then
                            next_char_end = next_i + 2
                        else
                            next_char_end = next_i + 3
                        end

                        local next_char = text:sub(next_i, next_char_end)

                        if is_variation_selector(next_char) then
                            -- Include the variation selector in the emoji sequence
                            emoji_sequence = emoji_sequence .. next_char
                            next_i = next_char_end + 1
                        else
                            break
                        end
                    else
                        break
                    end
                end

                -- Use direct emoji font command for better compatibility
                table.insert(result, '{\\emojifont ' .. emoji_sequence .. '}')
                i = next_i
            else
                -- Skip lone variation selectors that weren't processed with an emoji
                if not is_variation_selector(char) then
                    table.insert(result, char)
                end
                i = char_end + 1
            end
        else
            break
        end
    end

    return table.concat(result)
end

-- Convert emoji to text representation
--
-- Provides accessible fallback text for emojis in contexts where
-- emoji fonts are not available or appropriate (e.g., code blocks).
-- 
-- Maps common emojis to:
-- - Descriptive text (e.g., 😀 → ':grin:')
-- - Symbolic representations (e.g., ✅ → '[check]')
-- - Technical abbreviations (e.g., 🔧 → ':wrench:')
--
-- Covers major emoji categories:
-- - Facial expressions and emotions
-- - UI/UX symbols (check marks, warnings)
-- - Technical and office objects
-- - Nature and geography symbols
function emoji_to_text(emoji)
    local emoji_map = {
        ['😄'] = ':smile:',
        ['😀'] = ':grin:',
        ['😃'] = ':happy:',
        ['😁'] = ':beam:',
        ['😆'] = ':laugh:',
        ['😅'] = ':sweat:',
        ['😂'] = ':joy:',
        ['🤣'] = ':rofl:',
        ['✅'] = '[check]',
        ['❌'] = '[x]',
        ['⚠'] = '[warning]',
        ['ℹ'] = '[info]',
        ['🎉'] = ':party:',
        ['💥'] = ':boom:',
        ['📝'] = ':note:',
        ['👍'] = ':+1:',
        ['👎'] = ':-1:',
        ['👌'] = ':ok:',
        ['🤝'] = ':handshake:',
        ['👏'] = ':clap:',
        ['🙏'] = ':pray:',
        ['💪'] = ':muscle:',
        ['✊'] = ':fist:',
        ['🔥'] = ':fire:',
        ['💡'] = ':bulb:',
        ['🚀'] = ':rocket:',
        ['⭐'] = ':star:',
        ['💯'] = ':100:',
        ['🎯'] = ':target:',
        ['📊'] = ':chart:',
        ['📈'] = ':chart_up:',
        ['📉'] = ':chart_down:',
        ['🔧'] = ':wrench:',
        ['⚙'] = ':gear:',
        ['🛠'] = ':tools:',
        ['🔍'] = ':search:',
        ['📱'] = ':phone:',
        ['💻'] = ':computer:',
        ['🖥'] = ':desktop:',
        ['⌨'] = ':keyboard:',
        ['🖱'] = ':mouse:',
        ['🖨'] = ':printer:',
        ['📷'] = ':camera:',
        ['🎥'] = ':video:',
        ['🎵'] = ':music:',
        ['🎶'] = ':notes:',
        ['📚'] = ':books:',
        ['📖'] = ':book:',
        ['📝'] = ':memo:',
        ['✏'] = ':pencil:',
        ['🖊'] = ':pen:',
        ['📌'] = ':pin:',
        ['📎'] = ':paperclip:',
        ['🔗'] = ':link:',
        ['📧'] = ':email:',
        ['📨'] = ':inbox:',
        ['📩'] = ':outbox:',
        ['📤'] = ':outbox_tray:',
        ['📥'] = ':inbox_tray:',
        ['📦'] = ':package:',
        ['🏷'] = ':label:',
        ['🔖'] = ':bookmark:',
        ['📋'] = ':clipboard:',
        ['📄'] = ':page:',
        ['📃'] = ':document:',
        ['📑'] = ':pages:',
        ['📊'] = ':chart:',
        ['📈'] = ':trending_up:',
        ['📉'] = ':trending_down:',
        ['🗂'] = ':folder:',
        ['📁'] = ':folder_open:',
        ['📂'] = ':folder_closed:',
        ['🗃'] = ':file_cabinet:',
        ['🗄'] = ':filing_cabinet:',
        ['🗑'] = ':trash:',
        ['🔒'] = ':lock:',
        ['🔓'] = ':unlock:',
        ['🔐'] = ':locked:',
        ['🔑'] = ':key:',
        ['🗝'] = ':old_key:',
        ['🔨'] = ':hammer:',
        ['⚒'] = ':hammer_pick:',
        ['🛠'] = ':tools:',
        ['⚙'] = ':gear:',
        ['🔧'] = ':wrench:',
        ['🔩'] = ':nut_and_bolt:',
        ['⚡'] = ':zap:',
        ['🔋'] = ':battery:',
        ['🔌'] = ':plug:',
        ['💡'] = ':bulb:',
        ['🔦'] = ':flashlight:',
        ['🕯'] = ':candle:',
        ['🪔'] = ':lamp:',
        ['🔥'] = ':fire:',
        ['💧'] = ':droplet:',
        ['🌊'] = ':ocean:',
        ['❄'] = ':snowflake:',
        ['☀'] = ':sun:',
        ['🌙'] = ':moon:',
        ['⭐'] = ':star:',
        ['🌟'] = ':star2:',
        ['✨'] = ':sparkles:',
        ['⚡'] = ':zap:',
        ['☁'] = ':cloud:',
        ['🌈'] = ':rainbow:',
        ['🌍'] = ':earth_africa:',
        ['🌎'] = ':earth_americas:',
        ['🌏'] = ':earth_asia:',
        ['🌐'] = ':globe:',
        ['🗺'] = ':world_map:',
        ['🧭'] = ':compass:',
        ['🏔'] = ':mountain:',
        ['⛰'] = ':mountain_peak:',
        ['🌋'] = ':volcano:',
        ['🗻'] = ':mount_fuji:',
        ['🏕'] = ':camping:',
        ['🏖'] = ':beach:',
        ['🏜'] = ':desert:',
        ['🏝'] = ':island:',
        ['🏞'] = ':park:',
        ['🏟'] = ':stadium:',
        ['🏛'] = ':classical_building:',
        ['🏗'] = ':construction:',
        ['🧱'] = ':brick:',
        ['🏘'] = ':houses:',
        ['🏚'] = ':house_abandoned:',
        ['🏠'] = ':house:',
        ['🏡'] = ':house_garden:',
        ['🏢'] = ':office:',
        ['🏣'] = ':post_office:',
        ['🏤'] = ':european_post_office:',
        ['🏥'] = ':hospital:',
        ['🏦'] = ':bank:',
        ['🏨'] = ':hotel:',
        ['🏩'] = ':love_hotel:',
        ['🏪'] = ':convenience_store:',
        ['🏫'] = ':school:',
        ['🏬'] = ':department_store:',
        ['🏭'] = ':factory:',
        ['🏯'] = ':japanese_castle:',
        ['🏰'] = ':european_castle:',
        ['💒'] = ':wedding:',
        ['🗼'] = ':tokyo_tower:',
        ['🗽'] = ':statue_of_liberty:',
        ['⛪'] = ':church:',
        ['🕌'] = ':mosque:',
        ['🛕'] = ':hindu_temple:',
        ['🕍'] = ':synagogue:',
        ['⛩'] = ':shinto_shrine:',
        ['🕋'] = ':kaaba:'
    }

    return emoji_map[emoji] or ':emoji:'
end

-- Process text for code blocks - use a special marker that can be processed by LaTeX
function process_text_for_code(text)
    local result = {}
    local i = 1

    while i <= #text do
        local char_start = i
        local char_end = i
        local byte = text:byte(i)

        if byte then
            -- Determine UTF-8 character length
            if byte < 0x80 then
                char_end = i
            elseif byte < 0xE0 then
                char_end = i + 1
            elseif byte < 0xF0 then
                char_end = i + 2
            else
                char_end = i + 3
            end

            local char = text:sub(char_start, char_end)

            if is_emoji(char) then
                -- Check if next character is a variation selector
                local next_i = char_end + 1
                local emoji_sequence = char

                -- Look ahead for variation selectors
                while next_i <= #text do
                    local next_byte = text:byte(next_i)
                    local next_char_end = next_i

                    if next_byte then
                        -- Determine next character length
                        if next_byte < 0x80 then
                            next_char_end = next_i
                        elseif next_byte < 0xE0 then
                            next_char_end = next_i + 1
                        elseif next_byte < 0xF0 then
                            next_char_end = next_i + 2
                        else
                            next_char_end = next_i + 3
                        end

                        local next_char = text:sub(next_i, next_char_end)

                        if is_variation_selector(next_char) then
                            -- Include the variation selector in the emoji sequence
                            emoji_sequence = emoji_sequence .. next_char
                            next_i = next_char_end + 1
                        else
                            break
                        end
                    else
                        break
                    end
                end

                -- Use a special marker for code blocks that lstlisting can handle
                table.insert(result, '(*@\\emoji{' .. emoji_sequence .. '}@*)')
                i = next_i
            else
                -- Skip lone variation selectors that weren't processed with an emoji
                if not is_variation_selector(char) then
                    table.insert(result, char)
                end
                i = char_end + 1
            end
        else
            break
        end
    end

    return table.concat(result)
end

-- Main filter function for processing Str (string) elements
-- 
-- This is called by Pandoc for every string element in the document.
-- Only processes LaTeX output format to avoid interfering with other formats.
-- 
-- Process:
-- 1. Check if we're generating LaTeX output
-- 2. Process the text for emoji characters
-- 3. If emojis were found and wrapped, return as RawInline LaTeX
-- 4. Otherwise return original element unchanged
function Str(elem)
    if not FORMAT:match 'latex' then
        return elem
    end
    
    local processed = process_text(elem.text)
    if processed ~= elem.text then
        return pandoc.RawInline('latex', processed)
    end
    return elem
end

-- Process inline code elements with emoji-to-text conversion
--
-- Inline code requires special handling because:
-- 1. Emoji fonts may not work properly in monospace/code contexts
-- 2. Code should remain readable in all output formats
-- 3. Emojis in code often serve as UI indicators or comments
--
-- Process:
-- 1. Scan code text for emoji characters
-- 2. Replace emojis with descriptive text representations  
-- 3. Return as RawInline LaTeX with \texttt formatting if changes made
-- 4. Preserve all other characters including CJK text and HTML tags
function Code(elem)
    -- Process inline code with safe character replacements
    if not FORMAT:match 'latex' then
        return elem
    end

    local text = elem.text
    local result = {}
    local i = 1
    local changed = false

    -- Process each character (same logic as CodeBlock)
    while i <= #text do
        local char_start = i
        local char_end = i
        local byte = text:byte(i)

        if byte then
            -- Determine UTF-8 character length
            if byte < 0x80 then
                char_end = i
            elseif byte < 0xE0 then
                char_end = i + 1
            elseif byte < 0xF0 then
                char_end = i + 2
            else
                char_end = i + 3
            end

            local char = text:sub(char_start, char_end)

            -- Handle specific characters
            if is_emoji(char) then
                -- Convert emoji to text representation
                local emoji_text = emoji_to_text(char)
                table.insert(result, emoji_text)
                changed = true
            else
                -- Keep all other characters as-is (including Chinese characters and HTML tags)
                table.insert(result, char)
            end

            i = char_end + 1
        else
            break
        end
    end

    if changed then
        local processed_text = table.concat(result)
        return pandoc.RawInline('latex', '\\texttt{' .. processed_text .. '}')
    end
    return elem
end

-- Process code blocks with emoji-to-text conversion
--
-- Code blocks require emoji replacement because:
-- 1. LaTeX listings/minted packages may not handle emoji fonts properly
-- 2. Code blocks should maintain consistent monospace appearance
-- 3. Emojis in code are usually semantic indicators
--
-- Process:
-- 1. Scan entire code block content character by character
-- 2. Replace emoji characters with text equivalents
-- 3. Preserve syntax highlighting compatibility
-- 4. Maintain original code block attributes (language, etc.)
function CodeBlock(elem)
    -- For code blocks, replace problematic characters with safe alternatives
    if not FORMAT:match 'latex' then
        return elem
    end

    local text = elem.text
    local result = {}
    local i = 1
    local changed = false

    -- Process each character
    while i <= #text do
        local char_start = i
        local char_end = i
        local byte = text:byte(i)

        if byte then
            -- Determine UTF-8 character length
            if byte < 0x80 then
                char_end = i
            elseif byte < 0xE0 then
                char_end = i + 1
            elseif byte < 0xF0 then
                char_end = i + 2
            else
                char_end = i + 3
            end

            local char = text:sub(char_start, char_end)

            -- Handle specific characters
            if is_emoji(char) then
                -- Convert emoji to text representation
                local emoji_text = emoji_to_text(char)
                table.insert(result, emoji_text)
                changed = true
            else
                -- Keep all other characters as-is (including Chinese characters and HTML tags)
                table.insert(result, char)
            end

            i = char_end + 1
        else
            break
        end
    end

    if changed then
        return pandoc.CodeBlock(table.concat(result), elem.attr)
    end

    return elem
end
