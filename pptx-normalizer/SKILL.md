---
name: pptx-normalizer
description: Standardize PPT/PPTX files by removing all animations, disabling auto-play, and unifying fonts to 微软雅黑. This skill should be used whenever the user asks to "统一PPT格式", "去掉动画", "统一字体", or needs to clean up a presentation file for classroom or presentation use. It bundles a Python script that handles the normalization.
agent_created: true
---

# PPTX Normalizer

Standardizes PowerPoint files by removing animations, disabling auto-play, and unifying fonts.

## When to Use

Use this skill when the user:
- Asks to "统一PPT格式" or "去掉动画"
- Wants to remove all transitions and auto-play from a PPT
- Needs fonts unified to 微软雅黑 (Microsoft YaHei)
- Is preparing slides for classroom presentation and wants them static

## Usage

```bash
python3 ~/.workbuddy/skills/pptx-normalizer/scripts/normalize.py <input.pptx> [output.pptx]
```

If `output.pptx` is omitted, the input file is overwritten (a `.bak` backup is saved automatically).

## What It Does

1. Removes all slide transition effects
2. Disables auto-advance timings — all slides advance on click only
3. Unifies all text fonts to 微软雅黑 (shapes, text frames, tables)
4. Reports the number of font changes applied

## Dependencies

Requires `python-pptx`. Install if not present:
```bash
pip install python-pptx
```
