--[[
Keep a heading and its immediately following block quote on the same page.

Every chapter page in the handbook opens with an epigraph-style block quote
right below the section heading. The quote box is typeset as one unbreakable
block (see the quote environments in template.tex), so when that pair meets
the end of a page there must be room for the heading plus at least the first
lines of the box, or the pair has to move to the next page as a unit.

Reserving vertical space *before* the heading is what makes the pair move
together: reserving it after the heading could only orphan the heading at
the bottom of the page.
]]

function Pandoc(doc)
    local blocks = doc.blocks
    local out = pandoc.List()
    for i = 1, #blocks do
        local b = blocks[i]
        if b.t == 'Header' and b.level >= 2
            and blocks[i + 1] and blocks[i + 1].t == 'BlockQuote' then
            -- room for the heading (incl. its before/after skips, possibly
            -- wrapping to two lines) plus the first line of the quote box
            out:insert(pandoc.RawBlock('latex', '\\needspace{7\\baselineskip}'))
        end
        out:insert(b)
    end
    doc.blocks = out
    return doc
end
