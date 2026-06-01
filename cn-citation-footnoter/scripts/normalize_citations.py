#!/usr/bin/env python3
"""
Normalize Chinese academic citations to 《法学引注手册》 format.

Supported input formats:
1. Standard 知网 GB/T 7714: 作者.篇名[J].刊名,年份(期):页码.
2. 知网文献节: 篇名[J].作者.刊名,年份(期)
3. Plain text: 作者：《篇名》，载《刊名》年份年第X期，第XX-XX页。
4. Bare: just author, title, journal, year, issue

Output: 《法学引注手册》 format
  期刊: 作者：《篇名》，载《刊名》年份年第X期，第XX-XX页。
  专著: 作者：《书名》，出版社年份版，第XX页。
  报纸: 作者：《篇名》，载《报纸名》年月日，第X版。
"""

import re, sys, json

# Import marker detection for stripping leading numbers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from detect_markers import MARKER_PATTERN, CIRCLED_DIGITS, INVERSE_CIRCLED, PARENTHESIZED, CN_NUMERALS
except ImportError:
    # Fallback: define inline
    MARKER_PATTERN = re.compile(
        r'^(?:［(\d+)］|\[(\d+)\]|\((\d+)\)|(\d+)\)|(\d+)、|[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳⓵⓶⓷⓸⓹⓺⓻⓼⓽⓾⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇]|(?:一|二|三|四|五|六|七|八|九|十|十一|十二|十三|十四|十五|十六|十七|十八|十九|二十)[、）\)])[.\s]*'
    )
    CIRCLED_DIGITS = {'①':1,'②':2,'③':3,'④':4,'⑤':5,'⑥':6,'⑦':7,'⑧':8,'⑨':9,'⑩':10}
    INVERSE_CIRCLED = {'⓵':1,'⓶':2,'⓷':3,'⓸':4,'⓹':5,'⓺':6,'⓻':7,'⓼':8,'⓽':9,'⓾':10}
    PARENTHESIZED = {'⑴':1,'⑵':2,'⑶':3,'⑷':4,'⑸':5,'⑹':6,'⑺':7,'⑻':8,'⑼':9,'⑽':10}
    CN_NUMERALS = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}

import os

def normalize_citations(lines):
    """Normalize a list of citation strings to standard format."""
    results = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove leading numbering in ANY supported format
        # e.g. ［1］ [1] (1) ① 1. 1、 一、 etc.
        m = MARKER_PATTERN.match(line)
        if m:
            line = line[m.end():].strip()

        norm = _normalize_one(line)
        if norm:
            results.append(norm)
        else:
            results.append(f"[无法识别] {line}")
    return results

def _normalize_one(text):
    """Normalize a single citation."""
    # Try each parser
    for parser in [_parse_standard, _parse_cnki, _parse_plain, _parse_newspaper]:
        result = parser(text)
        if result:
            return result
    return None

def _parse_standard(text):
    """Parse: 作者.篇名[J].刊名,年份(期):页码."""
    # Match author.title[J].journal,year(issue):pages
    m = re.match(
        r'^(.+?)\.(.+?)\[([JMD])\]\.(.+?),(\d{4})\((\d+)\)[:：]?(.+?)\.?$',
        text
    )
    if not m:
        return None

    author = m.group(1).strip()
    title = m.group(2).strip()
    rtype = m.group(3)
    journal = m.group(4).strip()
    year = m.group(5)
    issue = m.group(6)
    pages = m.group(7).strip().rstrip('.')

    issue = str(int(issue))  # Remove leading zeros
    if rtype == 'J':
        # Journal article
        if pages:
            return f'{author}：《{title}》，载《{journal}》{year}年第{issue}期，第{pages}页。'
        else:
            return f'{author}：《{title}》，载《{journal}》{year}年第{issue}期。'
    elif rtype == 'M':
        # Monograph
        if pages:
            return f'{author}：《{title}》，{journal}{year}年版，第{pages}页。'
        else:
            return f'{author}：《{title}》，{journal}{year}年版。'
    elif rtype == 'D':
        # Dissertation
        return f'{author}：《{title}》，博士论文，{journal}{year}年。'
    return None

def _parse_cnki(text):
    """Parse 知网文献节 format: 篇名[J].作者.刊名,年份(期)"""
    # Reverse order: title[J].author.journal,year(issue)
    m = re.match(
        r'^(.+?)\[([JMD])\]\.(.+?)\.(.+?),(\d{4})\((\d+)\)\.?$',
        text
    )
    if not m:
        return None

    title = m.group(1).strip()
    rtype = m.group(2)
    author = m.group(3).strip()
    journal = m.group(4).strip()
    year = m.group(5)
    issue = m.group(6)

    if rtype == 'J':
        return f'{author}：《{title}》，载《{journal}》{year}年第{issue}期。'
    elif rtype == 'M':
        return f'{author}：《{title}》，{journal}{year}年版。'
    elif rtype == 'D':
        return f'{author}：《{title}》，博士论文，{journal}{year}年。'
    return None

def _parse_plain(text):
    """Parse plain Chinese format: 作者：《篇名》，载《刊名》年份年第X期，第XX页。"""
    # Already in target format or close
    m = re.match(
        r'^(.+?)：(.+?)，载(.+?)(\d{4})年第(\d+)期[，,]\s*(.+?)。?$',
        text
    )
    if not m:
        return None

    author = m.group(1).strip()
    title = m.group(2).strip()
    # title may have 《》 which we should strip
    title = title.strip('《》')
    journal = m.group(3).strip()
    journal = journal.strip('《》')
    year = m.group(4)
    issue = m.group(5)
    pages = m.group(6).strip()

    return f'{author}：《{title}》，载《{journal}》{year}年第{issue}期，{pages}。'

def _parse_newspaper(text):
    """Parse newspaper: 作者：《篇名》，载《报纸》年月日第X版。"""
    m = re.match(
        r'^(.+?)：(.+?)，载(.+?)(\d{4})年(\d+)月(\d+)日第(\d+)版。?$',
        text
    )
    if not m:
        return None

    author = m.group(1).strip()
    title = m.group(2).strip().strip('《》')
    paper = m.group(3).strip().strip('《》')
    year = m.group(4)
    month = m.group(5)
    day = m.group(6)
    edition = m.group(7)

    return f'{author}：《{title}》，载《{paper}》{year}年{month}月{day}日，第{edition}版。'

if __name__ == '__main__':
    # Read from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()

    result = normalize_citations(lines)
    print(json.dumps(result, ensure_ascii=False, indent=2))
