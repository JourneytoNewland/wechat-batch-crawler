# 微信公众号批量爬虫

智能反爬的微信公众号文章批量爬取工具,支持日期过滤、自动去重、智能延迟。

## ✨ 功能特性

- 🚀 **智能反爬** - 使用 subprocess + curl 避免 502 错误
- 📅 **日期过滤** - 支持今天/昨天/指定日期爬取
- 🔄 **自动去重** - 基于元数据自动跳过已爬取文章
- ⏰ **智能延迟** - 根据时间段自适应调整延迟(白天 10-15s, 晚间 7-12s, 深夜 3-7s)
- 🧵 **多线程爬取** - 最多 3 个并发线程
- 📝 **Markdown 输出** - 自动转换为 Markdown 格式
- 📊 **统计报告** - 生成详细的爬取报告

## 📁 目录结构

```
wxmp_scrapy/
├── .claude/
│   └── skills/
│       └── wechat-batch-crawl/
│           ├── metadata.json            # 配置文件
│           ├── SKILL.md                 # 使用文档
│           ├── resources/
│           │   └── wechat_batch_scraper.py  # 核心爬虫
│           └── hooks/
│               ├── pre_check.py         # 前置检查
│               └── post_summary.py      # 后置汇总
├── requirements.txt                     # 依赖
└── README.md                            # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 2. 配置 RSS URL

编辑 [`.claude/skills/wechat-batch-crawl/metadata.json`](.claude/skills/wechat-batch-crawl/metadata.json):

```json
{
  "configuration": {
    "rss_feed_url": "http://your-rss-server:8001/feed/all.rss",
    "output_base_dir": "./output/微信批量爬取",
    "max_workers": 3,
    "delay_range": [5, 15],
    "retry_limit": 3,
    "timeout": 30
  }
}
```

### 3. 运行前置检查

```bash
python3 .claude/skills/wechat-batch-crawl/hooks/pre_check.py
```

### 4. 开始爬取

```bash
# 爬取今天的文章
python3 .claude/skills/wechat-batch-crawl/resources/wechat_batch_scraper.py --date today

# 爬取昨天的文章
python3 .claude/skills/wechat-batch-crawl/resources/wechat_batch_scraper.py --date yesterday

# 爬取指定日期
python3 .claude/skills/wechat-batch-crawl/resources/wechat_batch_scraper.py --date 2026-01-20

# 仅列出文章(不爬取)
python3 .claude/skills/wechat-batch-crawl/resources/wechat_batch_scraper.py --date today --list-only
```

## ⚙️ 配置说明

| 参数 | 说明 | 默认值 | 约束 |
|------|------|--------|------|
| `rss_feed_url` | RSS Feed 地址 | - | 必填 |
| `output_base_dir` | 输出目录 | `./output/微信批量爬取` | - |
| `max_workers` | 最大并发数 | 3 | ≤ 3 (Decision Boundary) |
| `delay_range` | 延迟范围(秒) | [5, 15] | 5-15 (Decision Boundary) |
| `retry_limit` | 重试次数 | 3 | ≤ 3 (Decision Boundary) |
| `timeout` | 请求超时(秒) | 30 | - |

## 📂 输出格式

### 文章文件

每篇文章保存为独立的 Markdown 文件:

```markdown
---
title: 文章标题
author: 公众号名称
publish_time: 2026-01-20 15:30:00
url: https://mp.weixin.qq.com/s/xxxxx
crawl_time: 2026-01-20 15:45:00
---

# 文章标题

**作者**: 公众号名称
**发布时间**: 2026-01-20 15:30:00
**原文链接**: https://mp.weixin.qq.com/s/xxxxx

---

[文章正文]
```

### 目录结构

```
output_base_dir/
├── 2026-01-20/
│   ├── 001_文章标题.md
│   ├── 002_文章标题.md
│   └── _metadata.json
├── 2026-01-19/
│   └── ...
└── _metadata.json
```

## 🔧 常见问题

### 1. 502 错误

**原因**: 使用了 requests 库被识别

**解决方案**: 本工具已使用 subprocess + curl,如仍有问题请检查:
- curl 命令是否可用: `curl --version`
- 增加延迟时间
- 减少并发数

### 2. 频繁失败

**可能原因**:
- 网络不稳定
- RSS 服务不可用
- 高峰期被限流

**解决方案**:
- 检查网络连接
- 增加 `delay_range`
- 减少爬取频率

### 3. 重复爬取

**原因**: 去重逻辑未生效

**解决方案**:
- 检查 `output_base_dir` 路径是否正确
- 确认 `_metadata.json` 文件存在
- 首次运行会爬取所有文章,后续会自动去重

### 4. 依赖安装失败

```bash
# macOS
pip3 install -r requirements.txt

# Linux
pip install -r requirements.txt

# Windows
pip install -r requirements.txt
```

如遇权限问题:
```bash
pip install --user -r requirements.txt
```

## 🎯 Decision Boundaries

以下参数为硬约束,不可修改(防止被封):

- ✅ **max_workers ≤ 3** - 并发数不可超过 3
- ✅ **delay_range 5-15 秒** - 延迟必须在 5-15 秒
- ✅ **retry_limit ≤ 3** - 重试不可超过 3 次
- ✅ **必须使用 curl** - 不可使用 requests

## 📊 工作流程

```
RSS Feed → 解析文章 → 日期过滤 → 去重检查 → 并发爬取 → 保存 Markdown → 更新元数据
```

## 🤝 相关技能

- **content-summarizer** - 批量总结文章亮点
- **knowledge-manager** - 更新知识库索引

## 📝 开发说明

### 核心设计

1. **配置集中管理** - 所有配置在 `metadata.json`
2. **防爬机制** - subprocess + curl, 智能延迟
3. **爬取前去重** - `filter_existing()` 在爬取前过滤
4. **边界锁死** - Decision Boundaries 防止误改

### 测试

```bash
# 前置检查
python3 .claude/skills/wechat-batch-crawl/hooks/pre_check.py

# 仅列出文章
python3 .claude/skills/wechat-batch-crawl/resources/wechat_batch_scraper.py --date today --list-only

# 实际爬取
python3 .claude/skills/wechat-batch-crawl/resources/wechat_batch_scraper.py --date today

# 生成报告
python3 .claude/skills/wechat-batch-crawl/hooks/post_summary.py --date 2026-01-20 --save
```

## 📄 许可证

MIT License

## 🙏 致谢

基于 3 个月实战经验总结的最佳实践
