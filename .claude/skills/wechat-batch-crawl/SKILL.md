# WeChat Batch Crawl Skill

## Overview
批量爬取微信公众号文章，支持智能反爬、日期过滤、自动去重。

## Quick Start
```bash
# 爬取今天的文章
python resources/wechat_batch_scraper.py --date today

# 爬取指定日期
python resources/wechat_batch_scraper.py --date 2026-01-20

# 仅列出文章(不爬取)
python resources/wechat_batch_scraper.py --date today --list-only
```

## Natural Language Patterns

| Intent | Supported Phrases |
|--------|-------------------|
| 爬取今天 | "爬取今天的微信文章" / "获取今天的文章" / "抓今天的公众号" |
| 爬取昨天 | "爬取昨天的微信文章" / "获取昨天的文章" |
| 爬取指定日期 | "爬取1月20号的文章" / "获取上周一的文章" |
| 仅列出 | "今天有哪些文章" / "列出今天的文章" / "看看有啥新文章" |
| 增量爬取 | "继续爬取" / "爬取新增的文章" |

## Decision Boundaries

### ✅ Claude May Decide
- Date parsing from natural language formats
- Output directory naming and organization
- Retry strategy within configured limits
- Log verbosity and report format

### ❌ Claude Must NOT Change
- RSS feed URL configuration
- Anti-crawl delays (must stay 5-15 seconds)
- Max workers (must not exceed 3)
- Retry limits (max 3 retries)
- Request method (must use curl via subprocess)

## Core Implementation

### Anti-Crawl: Use curl via subprocess
```python
result = subprocess.run(
    ['curl', '-s', '-A',
     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
     url],
    capture_output=True,
    text=True,
    timeout=30
)
```

### Smart Delay: Adaptive by time
```python
def get_adaptive_delay(self):
    hour = datetime.now().hour
    if 9 <= hour <= 18:    return random.uniform(10, 15)  # 白天高峰
    if 19 <= hour <= 23:   return random.uniform(7, 12)   # 晚间
    return random.uniform(3, 7)                            # 深夜
```

### Deduplication: Filter before scraping
```python
def filter_existing(self, urls, output_dir):
    scraped_urls = collect_scraped_urls(output_dir)
    return [url for url in urls if url not in scraped_urls]
```

## Hooks

### Pre-check (hooks/pre_check.py)
```python
def check_dependencies():
    required = ['bs4', 'html2text', 'feedparser']
    missing = [p for p in required if not is_installed(p)]
    if missing:
        print(f"缺少依赖: pip install {' '.join(missing)}")
        return False
    return True
```

### Post-summary (hooks/post_summary.py)
```python
def generate_summary(results):
    success = sum(1 for r in results if r['success'])
    print(f"完成: {success}/{len(results)} ({success/len(results)*100:.1f}%)")
```

## Output Structure
```
output_dir/
└── 2026-01-20/
    ├── 001_文章标题.md
    ├── 002_文章标题.md
    └── _metadata.json
```

## Workflow Integration
```
wechat-batch-crawl → content-summarizer → knowledge-manager
     (爬取)              (总结亮点)          (更新知识库)
```

## Troubleshooting

| 问题 | 解决方案 |
|------|----------|
| 502 错误 | 确认使用 curl，非 requests |
| 频繁失败 | 检查是否高峰期，增加延迟 |
| 重复爬取 | 检查 output_dir 路径 |
