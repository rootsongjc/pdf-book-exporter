// Book template for pdf-book-exporter.
//
// Entry point: `#show: book.with(...)`. Also exports `part` and `callout`,
// which the Pandoc side emits as raw Typst.

#let accent = rgb("#0a84ff")
#let accent-dark = rgb("#0060df")
#let ink = rgb("#1d1d1f")
#let muted = rgb("#6b7280")
#let rule = rgb("#e5e7eb")
#let rule-dark = rgb("#c7cdd6")

#let callout-styles = (
  note: (color: rgb("#0a84ff"), label-zh: "注意", label-en: "Note"),
  info: (color: rgb("#0a84ff"), label-zh: "说明", label-en: "Info"),
  tip: (color: rgb("#15803d"), label-zh: "提示", label-en: "Tip"),
  success: (color: rgb("#15803d"), label-zh: "提示", label-en: "Tip"),
  warning: (color: rgb("#b45309"), label-zh: "注意", label-en: "Warning"),
  caution: (color: rgb("#b91c1c"), label-zh: "警告", label-en: "Caution"),
  danger: (color: rgb("#b91c1c"), label-zh: "警告", label-en: "Danger"),
  important: (color: rgb("#6d28d9"), label-zh: "重要", label-en: "Important"),
)

#let callout(kind: "note", title: none, body) = {
  let style = callout-styles.at(kind, default: callout-styles.note)
  let color = style.color
  block(
    width: 100%,
    breakable: true,
    stroke: (left: 2.5pt + color, top: 0.4pt + rule, bottom: 0.4pt + rule, right: 0.4pt + rule),
    inset: (x: 14pt, y: 11pt),
    above: 1.2em,
    below: 1.2em,
  )[
    #if title != none [
      #text(weight: 700, fill: color.darken(15%), size: 0.95em)[#title]
      #v(0.3em)
    ]
    #set text(size: 0.95em)
    #body
  ]
}

// Parts are level-1 headings without numbering so they appear in the
// outline but do not advance the chapter counter. A part gets a divider page
// of its own; an optional introduction sits under the title.
#let part-marker = [Part]
#let appendix-mode = state("pbe-appendix", false)

#let part(title, ..intro) = {
  pagebreak(weak: true)
  align(center + horizon, block(width: 100%)[
    #align(center, line(length: 18%, stroke: 1pt + accent))
    #v(1.2em)
    #heading(level: 1, numbering: none, outlined: true, bookmarked: true, supplement: part-marker)[#title]
    #if intro.pos().len() > 0 {
      v(1.6em)
      block(width: 78%)[
        #set align(left)
        #set text(fill: muted)
        #intro.pos().first()
      ]
    }
  ])
  pagebreak(weak: true)
}

// Everything after this call is numbered A, A.1, ... and labelled as an appendix.
#let appendix() = {
  appendix-mode.update(true)
  counter(heading).update(0)
}

// Plain (non-contextual) numbering functions so PDF bookmarks keep their numbers.
#let heading-number(..nums) = {
  let n = nums.pos()
  numbering(if n.len() == 1 { "1" } else { "1.1" }, ..n)
}

#let appendix-heading-number(..nums) = {
  let n = nums.pos()
  numbering(if n.len() == 1 { "A" } else { "A.1" }, ..n)
}

#let figure-number(n) = context {
  let chapter = counter(heading).get().first()
  numbering(if appendix-mode.get() { "A-1" } else { "1-1" }, chapter, n)
}

// Figures, tables and footnotes are numbered per chapter.
#let reset-chapter-counters() = {
  counter(figure.where(kind: image)).update(0)
  counter(figure.where(kind: table)).update(0)
  counter(footnote).update(0)
}

// Thematic break (Markdown `---`), emitted by the Lua filter.
#let hrule() = align(center, block(above: 1.4em, below: 1.4em, line(length: 30%, stroke: 0.5pt + rule-dark)))

#let taskbox(checked) = box(
  baseline: 0.15em,
  width: 0.9em,
  height: 0.9em,
  radius: 2pt,
  stroke: 0.6pt + (if checked { accent } else { muted }),
  fill: if checked { accent } else { white },
  align(center + horizon, if checked { text(fill: white, size: 0.65em, weight: 700)[#sym.checkmark] }),
)

#let is-zh(lang) = lang.starts-with("zh")

#let chapter-label(lang, n) = context {
  if appendix-mode.get() {
    let letter = numbering("A", n)
    if is-zh(lang) [附录 #letter] else [Appendix #letter]
  } else {
    if is-zh(lang) [第 #n 章] else [Chapter #n]
  }
}

#let fit-image(body, max-width, max-height) = context {
  let size = measure(body)
  let scale = calc.min(1.0, max-width / size.width, max-height / size.height)
  if scale < 1.0 {
    set image(width: size.width * scale)
    body
  } else {
    body
  }
}

#let cover-page(image-path, text-config) = {
  let pos-align(p) = if p == "top" { top } else if p == "bottom" { bottom } else { horizon }
  page(margin: 0pt, header: none, footer: none, numbering: none)[
    #image(image-path, width: 100%, height: 100%, fit: "cover")
    #if text-config.overlay {
      place(top + left, dx: 0pt, dy: 0pt, block(width: 100%, height: 100%, inset: 10%)[
        #place(center + pos-align(text-config.title_position), block(width: 100%)[
          #set align(center)
          #text(size: text-config.title_size * 1pt, weight: 700, fill: rgb(text-config.title_color))[#text-config.title]
          #if text-config.subtitle != "" [
            #v(0.6em)
            #text(size: text-config.subtitle_size * 1pt, fill: rgb(text-config.subtitle_color))[#text-config.subtitle]
          ]
        ])
        #place(center + pos-align(text-config.author_position), block(width: 100%)[
          #set align(center)
          #text(size: text-config.author_size * 1pt, fill: rgb(text-config.author_color))[#text-config.author]
        ])
      ])
    }
  ]
}

#let title-page(title, subtitle, author, translator, publisher, lang) = {
  page(header: none, footer: none, numbering: none)[
    #v(1fr)
    #align(center)[
      #text(size: 30pt, weight: 700, fill: ink)[#title]
      #if subtitle != "" [
        #v(1em)
        #text(size: 15pt, fill: muted)[#subtitle]
      ]
      #v(3em)
      #line(length: 30%, stroke: 0.5pt + accent)
      #v(3em)
      #text(size: 15pt)[#author]
      #if translator != "" [
        #v(0.6em)
        #text(size: 12pt, fill: muted)[#if is-zh(lang) [#translator 译] else [Translated by #translator]]
      ]
    ]
    #v(2fr)
    #if publisher != "" [
      #align(center, text(size: 10pt, fill: muted)[#publisher])
    ]
  ]
}

#let colophon-page(title, author, translator, publisher, website, description, date, exported, lang) = {
  let zh = is-zh(lang)
  let rows = (
    (if zh [书名] else [Title], title),
    (if zh [作者] else [Author], author),
    (if zh [译者] else [Translator], translator),
    (if zh [出版] else [Publisher], publisher),
    (if zh [网址] else [Website], website),
    (if zh [版本] else [Edition], date),
    (if zh [导出时间] else [Exported], exported),
  ).filter(r => r.at(1) != "")
  page(header: none, footer: none, numbering: none)[
    #v(1fr)
    #if description != "" [
      #block(width: 100%, inset: (bottom: 2em))[
        #set par(justify: true)
        #text(size: 10pt, fill: ink.lighten(20%))[#description]
      ]
    ]
    #block(width: 100%, stroke: (top: 0.5pt + rule), inset: (top: 1.2em))[
      #set text(size: 9.5pt)
      #set par(justify: false)
      // Two columns, so the values line up whatever the label widths are.
      #grid(
        columns: (auto, 1fr),
        column-gutter: 1.2em,
        row-gutter: 0.8em,
        ..rows.map(r => (text(fill: muted, r.at(0)), r.at(1))).flatten(),
      )
    ]
  ]
}

#let book(
  title: "",
  subtitle: "",
  author: "",
  translator: "",
  publisher: "",
  website: "",
  description: "",
  date: "",
  exported: "",
  lang: "zh",
  region: "cn",
  cover: none,
  backcover: none,
  cover-text: (:),
  show-chapter-prefix: true,
  show-section-numbers: true,
  show-toc-numbers: true,
  show-figure-numbers: true,
  toc-depth: 2,
  paper: "a4",
  // font / monofont: fallback chains supplied by build.py, already reduced to installed families.
  font: (),
  monofont: (),
  body,
) = {
  let zh = is-zh(lang)
  // Same margin left and right: the text block sits at the same place on every page, so
  // the contents list and the body do not jump sideways between odd and even pages.
  let margin = (top: 2.4cm, bottom: 2.4cm, x: 2.4cm)
  let page-w = if paper == "us-letter" { 8.5in } else { 210mm }
  let page-h = if paper == "us-letter" { 11in } else { 297mm }
  let text-w = page-w - 2 * margin.x
  let text-h = page-h - margin.top - margin.bottom

  set document(title: title, author: author)
  set page(paper: paper, margin: margin)
  set text(font: font, size: 10.5pt, lang: lang, region: region, fill: ink, fallback: true)
  set par(justify: true, leading: 0.85em, spacing: 1.1em)
  show raw: set text(font: monofont, size: 0.92em)

  // ---- headings -----------------------------------------------------------
  set heading(numbering: heading-number)
  show heading.where(level: 1): it => {
    if it.numbering == none and it.supplement == part-marker {
      // Title of a part divider page; `part` lays out the page around it.
      block(text(size: 28pt, weight: 700)[#it.body])
    } else if it.numbering == none {
      // Unnumbered level-1 heading (not a part): plain chapter-style title.
      pagebreak(weak: true)
      v(2.5cm)
      block(below: 1.6em, text(size: 24pt, weight: 700)[#it.body])
    } else {
      pagebreak(weak: true)
      reset-chapter-counters()
      v(2.5cm)
      block(below: 1.6em)[
        #if show-chapter-prefix [
          #text(size: 13pt, weight: 500, fill: accent)[#chapter-label(lang, counter(heading).get().first())]
          #v(0.6em)
        ] else if show-section-numbers [
          #text(size: 13pt, weight: 500, fill: accent)[#counter(heading).display(heading-number)]
          #v(0.6em)
        ]
        #text(size: 24pt, weight: 700)[#it.body]
      ]
    }
  }
  show heading: it => {
    if it.level == 1 { return it }
    let size = (14pt, 12pt, 11pt, 10.5pt, 10.5pt).at(calc.min(it.level, 6) - 2)
    block(above: 1.6em, below: 0.9em)[
      #set text(size: size, weight: 700)
      #if show-section-numbers and it.numbering != none [
        #counter(heading).display(it.numbering)#h(0.6em)
      ]
      #it.body
    ]
  }

  // ---- outline ------------------------------------------------------------
  show outline.entry: it => {
    let prefix = if show-toc-numbers and it.element.numbering != none { it.prefix() } else { none }
    if it.level == 1 {
      v(1.2em, weak: true)
      let is-part = it.element.supplement == part-marker
      set text(weight: 700, fill: if is-part { accent } else { ink })
      if is-part {
        // sticky: a part title never ends a page with its chapters on the next one.
        block(sticky: true, it.indented(none, it.body()))
      } else {
        link(it.element.location(), it.indented(prefix, it.inner()))
      }
    } else {
      v(0.7em, weak: true)
      link(it.element.location(), it.indented(prefix, it.inner()))
    }
  }

  // ---- figures, tables, code, quotes, links ------------------------------
  // The chapter prefix (3-2) only helps when chapter numbers are printed; without them figures count 1, 2, ...
  let chapter-numbers-shown = show-chapter-prefix or show-section-numbers
  set figure(
    gap: 0.9em,
    numbering: if not show-figure-numbers { none } else if chapter-numbers-shown { figure-number } else { "1" },
  )
  show figure: set block(above: 1.4em, below: 1.4em)
  show figure.caption: set text(size: 9pt, fill: muted)
  show figure.caption: set par(justify: false)
  // Rebuild image figures by hand so the image can be scaled to the text block
  // without re-creating a figure (which would re-trigger this rule).
  show figure.where(kind: image): it => block(width: 100%, breakable: false)[
    #align(center)[#fit-image(it.body, text-w, text-h * 0.72)]
    #if it.caption != none [
      #v(0.6em)
      #align(center)[#it.caption]
    ]
  ]

  // Print-friendly tables: rules only, no fills. Heavy rule above and below
  // the header, hairlines between rows and columns.
  set table(
    inset: (x: 8pt, y: 6pt),
    stroke: (x, y) => (
      top: if y == 0 { 0.8pt + ink } else { none },
      bottom: if y == 0 { 0.8pt + ink } else { 0.4pt + rule },
      left: if x > 0 { 0.4pt + rule } else { none },
    ),
  )
  show table: set text(size: 9.3pt)
  show table: set par(justify: false)
  // Pandoc centres the whole table; cells without an explicit column alignment
  // would inherit that, so pin every cell to the left.
  show table.cell: set align(left + horizon)
  show table.cell.where(y: 0): set text(weight: 700)
  // Tables and their captions sit flush left. Pandoc wraps every table in
  // align(center); unwrap that here instead of patching the generated source.
  show figure.where(kind: table): it => block(width: 100%, breakable: true, above: 1.4em, below: 1.4em)[
    #set align(left)
    #show align: a => if a.alignment == center { a.body } else { a }
    #if it.caption != none [
      // sticky: the caption never gets stranded at the bottom of a page.
      #block(sticky: true, below: 0.6em, it.caption)
    ]
    #it.body
  ]

  show raw.where(block: true): it => block(
    width: 100%,
    stroke: 0.5pt + rule-dark,
    inset: 10pt,
    radius: 3pt,
    breakable: true,
  )[
    #set par(justify: false, leading: 0.65em)
    #set text(size: 8.6pt)
    #it
  ]

  show quote.where(block: true): it => block(
    width: 100%,
    stroke: (left: 2.5pt + accent.lighten(40%)),
    inset: (left: 14pt, y: 6pt),
    above: 1.2em,
    below: 1.2em,
  )[
    #set text(fill: ink.lighten(25%))
    #it.body
  ]

  show link: set text(fill: accent-dark)
  set list(indent: 0.8em, spacing: 0.75em)
  set enum(indent: 0.8em, spacing: 0.75em)
  set terms(hanging-indent: 1.5em)
  // `strong` adds its delta (300 by default) on top of the current weight, so a bare
  // `set text(weight: 700)` would land on 1000 and render Black. Zero the delta and pin
  // strong text to Bold everywhere, including inside headings and table headers.
  set strong(delta: 0)
  show strong: set text(weight: 700)

  // ---- front matter -------------------------------------------------------
  if cover != none { cover-page(cover, cover-text) } else { title-page(title, subtitle, author, translator, publisher, lang) }
  colophon-page(title, author, translator, publisher, website, description, date, exported, lang)

  set page(
    numbering: "i",
    footer: context align(center, text(size: 9pt, fill: muted, counter(page).display("i"))),
  )
  counter(page).update(1)
  v(2.5cm)
  text(size: 24pt, weight: 700)[#if zh [目录] else [Contents]]
  v(1.6em)
  outline(title: none, depth: toc-depth, indent: auto)

  // ---- body ---------------------------------------------------------------
  set page(
    numbering: "1",
    header: context {
      let page-no = here().page()
      let starts-here = query(heading.where(level: 1)).any(h => h.location().page() == page-no)
      if starts-here { return }
      let before = query(selector(heading.where(level: 1)).before(here()))
      let chapter = before.filter(h => h.numbering != none)
      set text(size: 8.5pt, fill: muted)
      // Verso: book title; recto: current chapter (classic running heads).
      if calc.even(page-no) [#title] else if chapter.len() > 0 { align(right, chapter.last().body) }
      v(-0.4em)
      line(length: 100%, stroke: 0.4pt + rule)
    },
    footer: context align(center, text(size: 9pt, fill: muted, counter(page).display("1"))),
  )
  counter(page).update(1)
  body

  // ---- back cover ---------------------------------------------------------
  if backcover != none {
    pagebreak(weak: true)
    page(margin: 0pt, header: none, footer: none, numbering: none)[
      #image(backcover, width: 100%, height: 100%, fit: "cover")
    ]
  }
}
