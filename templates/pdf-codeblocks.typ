// Light gray background for fenced code blocks in PDF output.
#show raw.where(block: true): it => {
  block(
    width: 100%,
    fill: luma(245),
    inset: 8pt,
    radius: 3pt,
    stroke: luma(220),
    it,
  )
}

// Style hyperlinks like conventional web links.
#show link: it => {
  set text(fill: rgb("#0563C1"))
  underline(it)
}
