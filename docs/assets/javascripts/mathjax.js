// MathJax 3 configuration for mkdocs-material via pymdownx.arithmatex
// (generic mode). The arithmatex extension wraps math in
// `\(…\)` (inline) and `\[…\]` (block); we tell MathJax to look for
// those delimiters and to ignore the rest of the page so we don't
// accidentally typeset prose containing dollar signs.
//
// Re-typesets after each instant-loading navigation (Material handles
// SPA-style page swaps; MathJax needs to be poked again).

window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

document$.subscribe(() => {
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});
