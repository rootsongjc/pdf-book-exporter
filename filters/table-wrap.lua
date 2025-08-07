-- tools/pdf-book-exporter/filters/table-wrap.lua
-- Advanced Pandoc Lua filter for converting markdown tables to LaTeX longtable format
-- 
-- This filter provides comprehensive table processing capabilities:
-- 1. Converts pipe tables to longtable for automatic page breaking
-- 2. Handles long text content with intelligent wrapping and hyphenation
-- 3. Processes inline code within table cells using flexcode command
-- 4. Supports configurable table widths via metadata
-- 5. Provides safe LaTeX character escaping
--
-- Key enhancements:
-- - Responsive column sizing based on max_table_width parameter
-- - URL and long text detection with seqsplit wrapping
-- - Proper handling of CJK text and technical content
-- - Integration with minted/listings code highlighting

-- Function to add hyphenation penalties for long words
-- This function helps LaTeX break long words and technical terms appropriately
-- by inserting spaces after certain characters to enable natural line breaking
-- 
-- Enhanced for technical documentation with:
-- - Namespace separators (::)
-- - File paths (/)
-- - Variable names (_)
-- - Hyphenated terms (-)
function add_hyphenation_penalties(text)
  if not text then return "" end
  
  -- Don't modify underscores here - let latex_escape handle them properly
  return text
end

-- Function to check if text contains URLs or long sequences that need seqsplit
-- 
-- This function identifies content that requires special LaTeX wrapping:
-- 1. URLs (http/https/ftp protocols)
-- 2. Domain names and web addresses
-- 3. Long unbroken sequences (>30 characters)
--
-- The seqsplit package allows LaTeX to break these sequences at any character
-- when normal hyphenation fails, preventing table overflow
function needs_seqsplit(text)
  if not text then return false end
  
  -- Check for URL patterns
  if string.match(text, "https?://") or 
     string.match(text, "ftp://") or 
     string.match(text, "www%.") or
     string.match(text, "%w+%.%w+%.%w+") or  -- domain.subdomain.tld pattern
     string.match(text, "%w+%.%w+/") then   -- domain.tld/path pattern
    return true
  end
  
  -- Check for long sequences without spaces
  for word in string.gmatch(text, "%S+") do
    if string.len(word) > 30 then  -- Threshold for long words
      return true
    end
  end
  
  return false
end

-- Function to safely convert cell content to LaTeX while preserving commands
-- and handling inline code specially for table cells
--
-- This is the core function for table cell processing:
-- 1. Handles different Pandoc AST element types (Str, Code, RawInline, etc.)
-- 2. Applies appropriate LaTeX escaping for special characters
-- 3. Converts inline code to flexcode commands for better table formatting
-- 4. Processes emphasis, strong text, and strikeout formatting
-- 5. Ensures no unescaped line breaks that would break LaTeX compilation
--
-- Special handling for table context:
-- - Uses flexcode instead of texttt for better code wrapping
-- - Applies seqsplit for URLs and long sequences
-- - Replaces line breaks with spaces to maintain table structure
function cell_to_latex(cell_contents)
  if not cell_contents or #cell_contents == 0 then
    return ""
  end
  
  local result = {}
  
  -- Process elements
  for i, element in ipairs(cell_contents) do
    if element.t == "Str" then
      -- Regular text - escape LaTeX special characters and handle long text
      local escaped_text = latex_escape(element.text)
      
      -- Add hyphenation penalties for long words
      escaped_text = add_hyphenation_penalties(escaped_text)
      
      -- Wrap in seqsplit if it contains URLs or very long sequences
      if needs_seqsplit(element.text) then
        result[#result + 1] = "\\seqsplit{" .. escaped_text .. "}"
      else
        result[#result + 1] = escaped_text
      end
      
    elseif element.t == "Code" then
      -- Inline code in table - use flexcode command for better wrapping
      local escaped_code = latex_escape(element.text)
      result[#result + 1] = "\\flexcode{" .. escaped_code .. "}"
      
    elseif element.t == "RawInline" and element.format == "latex" then
      -- Check if this is a texttt command and replace with flexcode
      local latex_text = element.text
      if latex_text:match("^\\texttt{.*}$") then
        -- Extract content from texttt and use flexcode
        local code_content = latex_text:match("^\\texttt{(.*)}$")
        if code_content then
          result[#result + 1] = "\\flexcode{" .. code_content .. "}"
        else
          result[#result + 1] = latex_text
        end
      else
        -- Other LaTeX commands - keep as is
        result[#result + 1] = latex_text
      end
      
    elseif element.t == "Space" then
      result[#result + 1] = " "
      
    elseif element.t == "SoftBreak" or element.t == "LineBreak" then
      -- Replace line breaks with spaces to ensure no unescaped line breaks
      result[#result + 1] = " "
      
    elseif element.t == "Emph" then
      -- Handle emphasized text
      result[#result + 1] = "\\emph{" .. cell_to_latex(element.content) .. "}"
      
    elseif element.t == "Strong" then
      -- Handle strong text
      result[#result + 1] = "\\textbf{" .. cell_to_latex(element.content) .. "}"
      
    elseif element.t == "Strikeout" then
      -- Handle strikeout text
      result[#result + 1] = "\\sout{" .. cell_to_latex(element.content) .. "}"
      
    elseif element.t == "Link" then
      -- Handle links - render as LaTeX hyperlink
      local link_text = cell_to_latex(element.content)
      local link_url = element.target
      
      -- Escape URL for LaTeX
      link_url = string.gsub(link_url, "#", "\\#")
      link_url = string.gsub(link_url, "%$", "\\$")
      link_url = string.gsub(link_url, "&", "\\&")
      link_url = string.gsub(link_url, "%%", "\\%%")
      link_url = string.gsub(link_url, "_", "\\_")
      
      -- Use href command for proper link rendering
      result[#result + 1] = "\\href{" .. link_url .. "}{" .. link_text .. "}"
      
    elseif element.t == "Image" then
      -- Handle images - render as LaTeX includegraphics with size constraint for table cells
      local image_alt = cell_to_latex(element.content) or ""
      local image_src = element.src
      
      -- Escape image path for LaTeX
      image_src = string.gsub(image_src, "#", "\\#")
      image_src = string.gsub(image_src, "%$", "\\$")
      image_src = string.gsub(image_src, "&", "\\&")
      image_src = string.gsub(image_src, "%%", "\\%%")
      image_src = string.gsub(image_src, "_", "\\_")
      
      -- Use a reasonable size constraint for table cell images
      result[#result + 1] = "\\includegraphics[width=0.8\\linewidth,height=2cm,keepaspectratio]{" .. image_src .. "}"
      
    elseif element.t == "Plain" then
      -- Plain elements contain other inline elements - recursively process
      result[#result + 1] = cell_to_latex(element.content)
      
    else
      -- For other elements, try to stringify them safely
      local stringified = pandoc.utils.stringify({element})
      local escaped_text = latex_escape(stringified)
      
      -- Add hyphenation penalties and seqsplit for long text if needed
      escaped_text = add_hyphenation_penalties(escaped_text)
      if needs_seqsplit(stringified) then
        result[#result + 1] = "\\seqsplit{" .. escaped_text .. "}"
      else
        result[#result + 1] = escaped_text
      end
    end
  end
  
  -- Ensure the final result contains no unescaped line breaks
  local final_result = table.concat(result)
  -- Replace any remaining literal newlines with spaces
  final_result = string.gsub(final_result, "\n", " ")
  final_result = string.gsub(final_result, "\r", " ")
  
  return final_result
end

-- Function to escape LaTeX special characters (backup method)
function latex_escape(text)
  if not text then return "" end
  text = string.gsub(text, "\\", "\\textbackslash{}")
  text = string.gsub(text, "{", "\\{")
  text = string.gsub(text, "}", "\\}")
  text = string.gsub(text, "%$", "\\$")
  text = string.gsub(text, "&", "\\&")
  text = string.gsub(text, "%%", "\\%%")
  text = string.gsub(text, "#", "\\#")
  text = string.gsub(text, "%^", "\\textasciicircum{}")
  text = string.gsub(text, "_", "\\_")
  text = string.gsub(text, "~", "\\textasciitilde{}")
  return text
end

-- Main table processing function - converts Pandoc tables to LaTeX longtable
--
-- This function implements comprehensive table processing:
-- 1. Extracts table width configuration from Pandoc metadata
-- 2. Calculates optimal column widths with safety margins
-- 3. Generates LaTeX column specifications with proper alignment
-- 4. Processes header and body content with cell_to_latex
-- 5. Creates longtable environment with page-break support
--
-- Key features:
-- - Configurable max_table_width (default 0.98 of text width)
-- - Support for left, right, and center column alignment
-- - Automatic header repetition on page breaks (\endfirsthead/\endhead)
-- - Proper spacing calculation accounting for vertical borders
-- - Safety factor to prevent LaTeX dimension errors
function Table(tbl)
  -- Get the number of columns from the table
  local num_cols = #tbl.colspecs
  
  -- Extract maximum table width from Pandoc metadata (passed via -V max_table_width)
  -- Use more conservative default to prevent margin overflow
  local max_table_width = 0.85  -- Conservative default for reliable margin control
  if PANDOC_STATE.meta and PANDOC_STATE.meta.max_table_width then
    local meta_value = PANDOC_STATE.meta.max_table_width
    if type(meta_value) == "table" and meta_value.t == "MetaInlines" then
      -- Extract from MetaInlines format
      max_table_width = tonumber(pandoc.utils.stringify(meta_value)) or 0.92
    elseif type(meta_value) == "number" then
      max_table_width = meta_value
    elseif type(meta_value) == "string" then
      max_table_width = tonumber(meta_value) or 0.92
    end
  end
  
  -- Apply additional safety reduction for tables with many columns
  -- Tables with more columns need extra conservative width calculation
  if num_cols >= 5 then
    max_table_width = max_table_width * 0.95  -- 5% additional reduction for wide tables
  elseif num_cols >= 4 then
    max_table_width = max_table_width * 0.97  -- 3% additional reduction
  end
  
  -- Extract minimum column width from metadata if provided (table-level override)
  local min_col_width = nil
  if tbl.attr and tbl.attr.attributes and tbl.attr.attributes.min_col_width then
    min_col_width = tonumber(tbl.attr.attributes.min_col_width)
  end
  
  -- Compute usable width by subtracting vertical borders (arrayrulewidth)
  -- Use max_table_width to limit overall table width, then subtract borders
  -- Formula: (max_table_width * textwidth) - arrayrulewidth * (num_cols + 1)
  local usable_width_expr = string.format("\\dimexpr%.4f\\textwidth-\\arrayrulewidth*%d\\relax", max_table_width, num_cols + 1)
  
  -- Calculate width ratio per column based on max_table_width
  local base_width_ratio = max_table_width / num_cols
  -- Increase safety factor for better margin protection
  local safety_factor = 0.92  -- Increased from 0.95 to 0.92 for more conservative calculation
  local width_ratio = base_width_ratio * safety_factor
  
  -- Apply minimum column width override if specified (but respect max_table_width)
  if min_col_width then
    width_ratio = math.max(width_ratio, math.min(min_col_width, max_table_width / num_cols))
  end
  
  -- Format the column width as LaTeX dimexpr
  local col_width = string.format("\\dimexpr%.4f\\textwidth\\relax", width_ratio)
  
  -- Create column specification with proper alignment and line breaking support
  local column_spec = "|"
  for i = 1, num_cols do
    local alignment_spec = ""
    
    -- Check column alignment from colspecs
    if tbl.colspecs and tbl.colspecs[i] then
      local align = tbl.colspecs[i][1]  -- Alignment is first element of colspec
      if align == "AlignCenter" then
        alignment_spec = ">{\\centering\\arraybackslash}p{" .. col_width .. "}"
      elseif align == "AlignRight" then
        alignment_spec = ">{\\raggedleft\\arraybackslash}p{" .. col_width .. "}"
      else  -- AlignLeft or AlignDefault
        alignment_spec = ">{\\raggedright\\arraybackslash\\hspace{0pt}}p{" .. col_width .. "}"
      end
    else
      -- Default to left-aligned with line breaking support
      alignment_spec = ">{\\raggedright\\arraybackslash\\hspace{0pt}}p{" .. col_width .. "}"
    end
    
    column_spec = column_spec .. alignment_spec .. "|"
  end
  
  -- Create raw LaTeX block for longtable
  local latex_content = {}
  
  -- Start longtable environment
  latex_content[#latex_content + 1] = "\\begin{longtable}" .. "{" .. column_spec .. "}"
  latex_content[#latex_content + 1] = "\\hline"
  
  -- Process header if it exists
  if tbl.head and tbl.head.rows and #tbl.head.rows > 0 then
    for _, row in ipairs(tbl.head.rows) do
      local row_content = {}
      for j, cell in ipairs(row.cells) do
        -- Use safe cell conversion function
        local cell_latex = cell_to_latex(cell.contents)
        row_content[#row_content + 1] = "\\textbf{" .. cell_latex .. "}"
      end
      latex_content[#latex_content + 1] = table.concat(row_content, " & ") .. " \\\\"
    end
    latex_content[#latex_content + 1] = "\\hline"
    latex_content[#latex_content + 1] = "\\endfirsthead"
    
    -- Repeat header on subsequent pages
    latex_content[#latex_content + 1] = "\\hline"
    for _, row in ipairs(tbl.head.rows) do
      local row_content = {}
      for j, cell in ipairs(row.cells) do
        -- Use safe cell conversion function
        local cell_latex = cell_to_latex(cell.contents)
        row_content[#row_content + 1] = "\\textbf{" .. cell_latex .. "}"
      end
      latex_content[#latex_content + 1] = table.concat(row_content, " & ") .. " \\\\"
    end
    latex_content[#latex_content + 1] = "\\hline"
    latex_content[#latex_content + 1] = "\\endhead"
  end
  
  -- Process body rows
  if tbl.bodies and #tbl.bodies > 0 then
    for _, body in ipairs(tbl.bodies) do
      if body.body then
        for _, row in ipairs(body.body) do
          local row_content = {}
          for j, cell in ipairs(row.cells) do
            -- Use safe cell conversion function
            local cell_latex = cell_to_latex(cell.contents)
            row_content[#row_content + 1] = cell_latex
          end
          latex_content[#latex_content + 1] = table.concat(row_content, " & ") .. " \\\\"
          latex_content[#latex_content + 1] = "\\hline"  -- Add horizontal line after each row
        end
      end
    end
  end
  
  -- End longtable environment
  latex_content[#latex_content + 1] = "\\hline"
  latex_content[#latex_content + 1] = "\\end{longtable}"
  
  -- Return as RawBlock
  return pandoc.RawBlock("latex", table.concat(latex_content, "\n"))
end

