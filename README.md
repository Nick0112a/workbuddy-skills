# WorkBuddy Skills

> 两个实用的 WorkBuddy AI 助手技能

## 📦 PPTX Normalizer

统一 PPT 格式：去除所有动画和自动播放，字体统一为微软雅黑。

### 功能
- 移除所有幻灯片切换动画
- 禁用自动播放，所有幻灯片改为点击手动切换
- 全文字体统一为微软雅黑（文本框、表格）
- 自动备份原文件为 `.bak`

### 使用
```bash
pip install python-pptx
python3 pptx-normalizer/scripts/normalize.py <input.pptx> [output.pptx]
```

---

## 📝 CN Citation Footnoter

中文学术论文引注转 Word 脚注。支持从不同来源标准化引用格式。

### 功能
- 识别正文中 `[1]` `[1-3]` `[1,2,3]` 等引用标记
- 自动转换为 Word 原生脚注（非伪脚注）
- 支持《法学引注手册》等标准格式

### 使用
```bash
pip install python-docx lxml
```

---

## 安装

将对应文件夹复制到 `~/.workbuddy/skills/`：
```bash
cp -r pptx-normalizer ~/.workbuddy/skills/
cp -r cn-citation-footnoter ~/.workbuddy/skills/
```
WorkBuddy 会自动识别并加载。
