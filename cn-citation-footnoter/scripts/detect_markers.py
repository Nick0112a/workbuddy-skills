#!/usr/bin/env python3
"""
Detect and normalize citation markers in Chinese academic text.

Supported marker formats:
  ［1］ → 1    [1] → 1    (1) → 1    ① → 1
  1. → 1      1、→ 1      1) → 1     一、→ 1
  ⓵ → 1      ⑴ → 1      十二、→ 12
"""

import re, sys

# Map of special digit characters to their numeric values
CIRCLED = {
    '①':1,'②':2,'③':3,'④':4,'⑤':5,'⑥':6,'⑦':7,'⑧':8,'⑨':9,'⑩':10,
    '⑪':11,'⑫':12,'⑬':13,'⑭':14,'⑮':15,'⑯':16,'⑰':17,'⑱':18,'⑲':19,'⑳':20,
}
INV_CIRCLED = {
    '⓵':1,'⓶':2,'⓷':3,'⓸':4,'⓹':5,'⓺':6,'⓻':7,'⓼':8,'⓽':9,'⓾':10,
}
PAREN_DIGITS = {
    '⑴':1,'⑵':2,'⑶':3,'⑷':4,'⑸':5,'⑹':6,'⑺':7,'⑻':8,'⑼':9,'⑽':10,
}
CN_NUMS = {
    '一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
    '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,
    '十六':16,'十七':17,'十八':18,'十九':19,'二十':20,
}

# Build regex patterns for each marker type
ARABIC_PATTERNS = [
    r'［(\d+)］',      # ［1］
    r'\[(\d+)\]',      # [1]
    r'\((\d+)\)',      # (1)
    r'(\d+)\)',        # 1)
    r'(\d+)、',        # 1、
    r'(\d+)\.(?=[\u4e00-\u9fff])',  # 1. (only when followed by CJK char, not digit)
]

def build_marker_regex():
    """Build unified regex for all marker types."""
    parts = []
    # Arabic digit patterns
    parts.extend(ARABIC_PATTERNS)
    # Special Unicode characters
    special_chars = (
        ''.join(CIRCLED.keys())
        + ''.join(INV_CIRCLED.keys())
        + ''.join(PAREN_DIGITS.keys())
    )
    parts.append(f'([{re.escape(special_chars)}])')
    # Chinese numerals followed by 、 or ）— include delimiter in match
    cn_keys = sorted(CN_NUMS.keys(), key=len, reverse=True)
    cn_pattern = '|'.join(re.escape(k) for k in cn_keys)
    parts.append(f'({cn_pattern})[、）\\)]')

    full = '(?:' + '|'.join(parts) + ')'
    return re.compile(full)

MARKER_RE = build_marker_regex()

def detect_markers(text):
    """Find all citation markers and return list of {position, end, number, original}."""
    markers = []
    for m in MARKER_RE.finditer(text):
        groups = m.groups()
        num = None
        for g in groups:
            if g is None:
                continue
            # Try Arabic
            try:
                num = int(g)
            except (ValueError, TypeError):
                pass
            if num is not None:
                break
            # Try special chars and Chinese numerals
            # For CN_NUMS, the group includes the delimiter (e.g., "十二、")
            raw_g = g
            # Strip trailing delimiter for CN lookup
            g_clean = re.sub(r'[、）\)]$', '', g) if g else g
            if g_clean in CIRCLED:
                num = CIRCLED[g_clean]
            elif g_clean in INV_CIRCLED:
                num = INV_CIRCLED[g_clean]
            elif g_clean in PAREN_DIGITS:
                num = PAREN_DIGITS[g_clean]
            elif g_clean in CN_NUMS:
                num = CN_NUMS[g_clean]
            if num is not None:
                break
        if num is not None:
            markers.append({
                'position': m.start(),
                'end': m.end(),
                'number': num,
                'original': m.group(0),
            })
    return markers

def normalize_to_brackets(text):
    """Replace all citation markers with canonical ［N］ format."""
    markers = detect_markers(text)
    if not markers:
        return text
    result = list(text)
    for m in reversed(markers):
        replacement = f'［{m["number"]}］'
        # Verify we're not replacing in the middle of a word
        # Check context: after replacement point, no Chinese char immediately before
        start = m['position']
        end = m['end']
        # Avoid false positives for Chinese numerals:
        # Valid context: preceded by punctuation, conjunction, whitespace, or start
        # Invalid context: preceded by word-forming Chinese character
        if m['original'][0] in CN_NUMS and start > 0:
            prev_char = text[start - 1]
            # Compound number: 二十, 十二 → skip
            if prev_char in CN_NUMS or prev_char.isdigit():
                continue
            # Accepted preceding characters: punctuation, conjunctions, whitespace
            accepted = set('，。；：！？、\u3000 \n\t\r和与及或见参')
            if prev_char not in accepted and '\u4e00' <= prev_char <= '\u9fff':
                continue  # part of a word like 统一、
        result[start:end] = list(replacement)
    return ''.join(result)

if __name__ == '__main__':
    if '--all' in sys.argv:
        print("Supported citation marker formats:")
        for name, examples in [
            ("Full-width brackets", "［1］ ［12］"),
            ("Half-width brackets", "[1] [12]"),
            ("Parentheses", "(1) (12)"),
            ("Circled digits", "① ② ... ⑳ (1-20)"),
            ("Inverse circled", "⓵ ⓶ ... ⓾ (1-10)"),
            ("Parenthesized digits", "⑴ ⑵ ... ⒇ (1-20)"),
            ("Number + dot", "1. 12."),
            ("Number + enumeration comma", "1、12、"),
            ("Chinese numerals", "一、十一、 (1-20)"),
            ("Closing paren", "1) 12)"),
        ]:
            print(f"  {name:25s}  {examples}")
        sys.exit(0)

    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        with open(sys.argv[idx+1], 'r', encoding='utf-8') as f:
            text = f.read()
    elif len(sys.argv) > 1:
        text = sys.argv[1]
    else:
        text = sys.stdin.read()

    markers = detect_markers(text)
    print(f"Found {len(markers)} markers:")
    for m in markers:
        ctx_start = max(0, m['position'] - 8)
        ctx_end = min(len(text), m['end'] + 8)
        ctx = text[ctx_start:ctx_end].replace('\n', ' ')
        print(f"  {m['original']:10s} → [{m['number']:2d}]  ...{ctx}...")

    if markers:
        normalized = normalize_to_brackets(text)
        print(f"\nNormalized ({len(normalized)} chars):")
        print(normalized[:400] + ('...' if len(normalized) > 400 else ''))
