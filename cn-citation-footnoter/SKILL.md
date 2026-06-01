---
name: cn-citation-footnoter
description: "Convert Chinese academic paper inline citations to Word footnotes. Normalize citation formats from various sources to standard legal citation style, then generate properly formatted docx with footnotes replacing in-text reference markers."
agent_created: true
---

# Chinese Citation-to-Footnote Converter

Convert inline citation markers in Chinese academic papers into proper Word footnotes.
Supports ALL common marker formats (［1］ [1] (1) ① 1. 1、 一、 etc.) and optional
citation format normalization from various input sources (CNKI, plain text, GB/T 7714).

## When to Use

- User has a .docx with inline citations in ANY of these formats: ［1］ [1] (1) ① 1. 1、 一、
- User provides a separate citation list file that needs format normalization
- User asks to "add footnotes", "convert citations to footnotes", or "format references"
- The paper is in Chinese and uses 《法学引注手册》 or similar citation style

## Citation Marker Detection

The skill automatically recognizes and normalizes ALL the following marker formats:

| Format | Example | Recognized |
|--------|---------|------------|
| Full-width brackets | ［1］ ［12］ | ✅ |
| Half-width brackets | [1] [12] | ✅ |
| Parentheses | (1) (12) | ✅ |
| Circled digits | ① ② ... ⑳ | ✅ (1-20) |
| Inverse circled | ⓵ ⓶ ... ⓾ | ✅ (1-10) |
| Parenthesized digits | ⑴ ⑵ ... ⒇ | ✅ (1-20) |
| Numbered list | 1. 12. | ✅ |
| Chinese enumeration | 1、12、 | ✅ |
| Chinese numerals | 一、十一、 | ✅ (1-20) |
| Closing paren | 1) 12) | ✅ |

The detection script (`scripts/detect_markers.py`) handles this normalization:

```bash
# Test marker detection
echo '参见［1］和[2]以及(3)和①。' | python3 scripts/detect_markers.py
# Output: all detected, normalized to ［1］［2］［3］［1］

# Batch normalize a file
python3 scripts/detect_markers.py --file paper.txt
```

## Workflow

### Phase 0: Detect and Normalize Markers

Before any processing, detect and normalize citation markers in the source text:

```bash
# If markers are in various formats, normalize them all to ［N］
python3 scripts/detect_markers.py --file body_text.txt
```

In the docx generation phase, the marker regex should match `［(\d+)］` after normalization.

### Phase 1: Normalize Citation List (if user provides a separate file)

When the user provides a citation list file (e.g., 引注.docx):

1. Extract text from the citation list file
2. Run `scripts/normalize_citations.py` on the extracted lines
3. Present normalized output to user for review before using
4. The normalized list becomes the canonical footnote content

```bash
# Extract text from citation docx, then normalize
python3 scripts/extract_paragraphs.py citations.docx /tmp/citations.json
# Extract text lines from JSON, pipe to normalizer
python3 scripts/normalize_citations.py /tmp/citation_lines.txt
```

### Phase 2: Extract Paragraphs from Source Document

Extract all paragraphs from the source .docx with formatting metadata:

```bash
python3 scripts/extract_paragraphs.py paper.docx /tmp/paragraphs.json
```

This produces a JSON file with `{text, bold, font_size, is_bib}` for each paragraph.
The `is_bib` flag detects bibliography entries (paragraphs starting with `[N]` or `［N］`).

### Phase 3: Build Reference Map

Parse the bibliography section from extracted paragraphs:
- Match `［N］` or `[N]` patterns at the start of bib paragraphs
- Build a map: `{ "1": "citation text", "2": "citation text", ... }`

If a separate normalized citation list was prepared in Phase 1, use it instead.

### Phase 4: Generate docx with Footnotes

Build a new .docx using `docx-js` (Node.js). For each body paragraph:

1. Find all `［N］` markers using regex `/［(\d+)］/g`
2. Replace each with a `FootnoteReferenceRun(id)` — the superscript number in text
3. Create corresponding `Footnote` entries with the reference text
4. Skip or remove the original bibliography section

**Critical formatting rules for docx-js:**

- Set explicit page size (A4: 11906×16838 DXA) and margins
- Use `SimSun` (宋体) for Chinese body text, `SimHei` (黑体) for headings
- Chinese text often contains curly quotes (`""`) which break JavaScript strings — pass text via JSON files, never embed directly in JS
- Footnote size: 小五 9pt (18 half-points in docx-js)
- Body text: 小四 12pt (24 half-points), fixed line spacing 20pt (400 twips)

**Example footnote creation in docx-js:**

```javascript
const footnotes = {
  1: { children: [new Paragraph({
    children: [new TextRun({ text: fnText, font: "SimSun", size: 18 })]
  })] }
};
// In paragraph:
children: [
  new TextRun({ text: "some text", font: "SimSun", size: 24 }),
  new FootnoteReferenceRun(1),
  new TextRun({ text: " more text", font: "SimSun", size: 24 }),
]
```

### Phase 5: Validate

After generation, unpack the output docx and verify:
- Footnote count matches reference count in body text
- Footnote content is correct
- No residual `［N］` markers remain in body
- Bibliography section is removed from body
- Font sizes and styles are applied

## Common Pitfalls

1. **Full-width vs half-width brackets**: Citation markers use `［］` (U+FF3B/U+FF3D), not `[]`. Regex must use `［(\d+)］`.
2. **Chinese quotes in JS**: Characters like `""` are valid JS string delimiters. Always pass Chinese text through JSON files, never embed in JS source.
3. **Merged bibliography entries**: Citation list docx files sometimes merge two entries into one paragraph (e.g., page number missing between entries). Split using author name boundaries.
4. **Same reference cited multiple times**: Creates duplicate footnotes with identical text. This is correct for Word; user can manually merge to "同上注" if desired.
5. **Newspaper citations**: Format differs from journal articles — use "年月日第X版" not "年第X期第XX页".

## Scripts

- `scripts/extract_paragraphs.py` — Extract paragraphs from docx with formatting metadata
- `scripts/detect_markers.py` — Detect and normalize ALL citation marker formats to canonical ［N］
- `scripts/normalize_citations.py` — Normalize citations from various formats to 《法学引注手册》 style

## References

- `references/citation_format.md` — 《法学引注手册》 format reference and examples
