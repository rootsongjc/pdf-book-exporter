-- table-filter.lua
-- Pandoc filter to generate tables with black outer border and gray inner lines

function Table(elem)
    -- Only process if we're generating LaTeX
    if FORMAT ~= "latex" then
        return elem
    end

    -- Get table dimensions
    local num_cols = #elem.colspecs

    -- Build LaTeX table manually with custom column separators
    local latex_lines = {}

    -- Define custom column types with gray vertical rules
    table.insert(latex_lines, "\\newcolumntype{G}{!{\\color{gray!40}\\vrule}}")
    table.insert(latex_lines, "\\newcolumntype{B}{!{\\color{black}\\vrule}}")

    -- Create column specification: black outer borders, gray inner separators
    -- Use >{\\raggedright\\arraybackslash} for left-aligned, top-aligned text
    local colspec = "B"
    for i = 1, num_cols do
        colspec = colspec .. ">{\\raggedright\\arraybackslash}p{" .. string.format("%.2f", 0.9 / num_cols) .. "\\textwidth}"
        if i < num_cols then
            colspec = colspec .. "G"  -- Gray separator between columns
        end
    end
    colspec = colspec .. "B"  -- Black right border

    -- Start table with black outer border and improved styling
    table.insert(latex_lines, "\\sloppy")  -- Encourage line breaks without overfull hboxes
    table.insert(latex_lines, "\\arrayrulecolor{black}")
    table.insert(latex_lines, "\\begin{longtable}{" .. colspec .. "}")
    table.insert(latex_lines, "\\tablefontsize")  -- Shrink font if necessary
    table.insert(latex_lines, "\\hline")

    -- Process header if exists
    if elem.head and elem.head.rows and #elem.head.rows > 0 then
        for _, row in ipairs(elem.head.rows) do
            local row_content = {}
            for _, cell in ipairs(row.cells) do
                -- Convert cell contents to LaTeX, preserving formatting
                local cell_latex = pandoc.write(pandoc.Pandoc(cell.contents), 'latex')
                -- Clean up the LaTeX output (remove extra newlines and paragraph tags)
                cell_latex = cell_latex:gsub("\\par\n", "")
                cell_latex = cell_latex:gsub("\n", " ")
                cell_latex = cell_latex:gsub("^%s+", "")
                cell_latex = cell_latex:gsub("%s+$", "")
                -- Make header text bold
                cell_latex = "\\textbf{" .. cell_latex .. "}"
                table.insert(row_content, cell_latex)
            end
            -- Add light gray background for header row
            table.insert(latex_lines, "\\rowcolor{gray!10}")
            table.insert(latex_lines, table.concat(row_content, " & ") .. " \\\\")
            -- Gray line after header
            table.insert(latex_lines, "\\arrayrulecolor{gray!40}")
            table.insert(latex_lines, "\\hline")
        end
    end

    -- Process body rows
    if elem.bodies and #elem.bodies > 0 then
        for _, body in ipairs(elem.bodies) do
            for i, row in ipairs(body.body) do
                local row_content = {}
                for _, cell in ipairs(row.cells) do
                    -- Convert cell contents to LaTeX, preserving formatting
                    local cell_latex = pandoc.write(pandoc.Pandoc(cell.contents), 'latex')
                    -- Clean up the LaTeX output (remove extra newlines and paragraph tags)
                    cell_latex = cell_latex:gsub("\\par\n", "")
                    cell_latex = cell_latex:gsub("\n", " ")
                    cell_latex = cell_latex:gsub("^%s+", "")
                    cell_latex = cell_latex:gsub("%s+$", "")
                    table.insert(row_content, cell_latex)
                end
                table.insert(latex_lines, table.concat(row_content, " & ") .. " \\\\")
                -- Gray lines between rows, black line for last row
                if i < #body.body then
                    table.insert(latex_lines, "\\arrayrulecolor{gray!40}")
                    table.insert(latex_lines, "\\hline")
                else
                    table.insert(latex_lines, "\\arrayrulecolor{black}")
                    table.insert(latex_lines, "\\hline")
                end
            end
        end
    end

    -- End table
    table.insert(latex_lines, "\\end{longtable}")
    table.insert(latex_lines, "\\relax")  -- Reset line breaking behavior
    table.insert(latex_lines, "\\arrayrulecolor{black}") -- Reset to black

    -- Return as raw LaTeX
    return pandoc.RawBlock("latex", table.concat(latex_lines, "\n"))
end
