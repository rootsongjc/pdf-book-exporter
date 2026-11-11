-- Pandoc Lua filter: map Hugo-derived fenced divs onto Typst template functions.
--
--   ::: {.callout type="note" title="..."}  ->  #callout(kind: "note", title: [...])[ ... ]
--   ::: {.table-title title="..."}          ->  caption on the wrapped table
--   ::: {.part title="..."}                 ->  #part([...])[ part introduction ]

local function typst_string(s)
  return '"' .. s:gsub('\\', '\\\\'):gsub('"', '\\"') .. '"'
end

local function inlines_to_typst(inlines)
  local doc = pandoc.Pandoc({ pandoc.Plain(inlines) })
  return (pandoc.write(doc, 'typst'):gsub('%s+$', ''))
end

function Div(div)
  if div.classes:includes('callout') then
    local kind = div.attributes['type'] or 'note'
    local title = div.attributes['title']
    local head = '#callout(kind: ' .. typst_string(kind)
    if title and title ~= '' then
      head = head .. ', title: [' .. inlines_to_typst(pandoc.utils.blocks_to_inlines(
        pandoc.read(title, 'commonmark').blocks)) .. ']'
    end
    local blocks = pandoc.List({ pandoc.RawBlock('typst', head .. ')[') })
    blocks:extend(div.content)
    blocks:insert(pandoc.RawBlock('typst', ']'))
    return blocks
  end

  if div.classes:includes('part') then
    local title = inlines_to_typst(pandoc.Inlines({ pandoc.Str(div.attributes['title'] or '') }))
    local blocks = pandoc.List({ pandoc.RawBlock('typst', '#part([' .. title .. '])[') })
    blocks:extend(div.content)
    blocks:insert(pandoc.RawBlock('typst', ']'))
    return blocks
  end

  if div.classes:includes('table-title') then
    local title = div.attributes['title'] or ''
    for i, block in ipairs(div.content) do
      if block.t == 'Table' and title ~= '' then
        local caption = pandoc.read(title, 'commonmark').blocks
        block.caption = pandoc.Caption(caption)
        div.content[i] = block
      end
    end
    return div.content
  end
end

-- commonmark_x leaves "[x]" / "[ ]" task markers as text; render them as boxes.
local function task_marker(inlines)
  local first = inlines[1]
  if not first or first.t ~= 'Str' then return nil, 0 end
  if first.text == '[x]' or first.text == '[X]' or first.text == '\u{2612}' then return true, 1 end
  if first.text == '\u{2610}' then return false, 1 end
  if first.text == '[' and inlines[2] and inlines[2].t == 'Space'
      and inlines[3] and inlines[3].t == 'Str' and inlines[3].text == ']' then
    return false, 3
  end
  return nil, 0
end

function BulletList(list)
  local changed = false
  local all_tasks = #list.content > 0
  for _, item in ipairs(list.content) do
    local block = item[1]
    if block and (block.t == 'Plain' or block.t == 'Para') then
      local checked, consumed = task_marker(block.content)
      if checked ~= nil then
        for _ = 1, consumed do block.content:remove(1) end
        if block.content[1] and block.content[1].t == 'Space' then block.content:remove(1) end
        block.content:insert(1, pandoc.RawInline('typst', '#taskbox(' .. tostring(checked) .. ') '))
        changed = true
      else
        all_tasks = false
      end
    else
      all_tasks = false
    end
  end
  if changed and all_tasks then
    return { pandoc.RawBlock('typst', '#[\n#set list(marker: none)'), list, pandoc.RawBlock('typst', ']') }
  elseif changed then
    return list
  end
end

-- Pandoc's raw Typst for `---` differs across versions (#horizontalrule, #divider()),
-- so emit our own template function instead.
function HorizontalRule()
  return pandoc.RawBlock('typst', '#hrule()')
end

-- Hugo renders ```mermaid etc. client-side; in print we keep the source but mark the language.
function CodeBlock(block)
  if block.classes[1] == 'mermaid' then
    block.classes[1] = 'text'
  end
  return block
end
