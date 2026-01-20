#!/usr/bin/env python3
"""
后置汇总脚本
生成爬取统计报告
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def generate_summary(stats: Dict, output_dir: str) -> str:
    """
    生成爬取汇总报告

    Args:
        stats: 统计信息字典
        output_dir: 输出目录路径

    Returns:
        Markdown 格式的报告
    """
    # 计算耗时
    start_time = stats.get('start_time', datetime.now())
    end_time = stats.get('end_time', datetime.now())
    duration = (end_time - start_time).total_seconds()

    # 提取统计信息
    total = stats.get('total', 0)
    success = stats.get('success', 0)
    failed = stats.get('failed', 0)
    skipped = stats.get('skipped', 0)
    errors = stats.get('errors', [])

    # 计算成功率
    success_rate = f"{success/total*100:.1f}%" if total > 0 else "0%"

    # 生成报告
    report = f"""# 微信爬虫执行报告

## 📊 执行概要

**执行时间**: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_time.strftime('%Y-%m-%d %H:%M:%S')}
**总耗时**: {duration:.1f} 秒

## 📈 统计信息

| 指标 | 数量 | 占比 |
|------|------|------|
| 总文章数 | {total} | 100% |
| ✅ 成功爬取 | {success} | {success_rate} |
| ❌ 失败 | {failed} | {f"{failed/total*100:.1f}%" if total > 0 else "0%"} |
| ⏭️  跳过(已爬) | {skipped} | - |

"""

    # 失败列表
    if errors:
        report += "## ❌ 失败列表\n\n"
        for i, error in enumerate(errors, 1):
            url = error.get('url', 'Unknown URL')[:60]
            msg = error.get('error', error.get('message', 'Unknown error'))
            report += f"{i}. **{url}**\n   - 错误: {msg}\n\n"

    # 输出位置
    report += f"""## 📁 输出位置

- **文章目录**: `{output_dir}`
- **元数据**: `{output_dir}/_metadata.json`
- **日期元数据**: `{output_dir}/YYYY-MM-DD/_metadata.json`

## 🎯 下一步操作

- 查看爬取的文章: `ls {output_dir}`
- 查看失败的文章: 检查上述失败列表
- 重新爬取失败文章: 确认网络后重新运行

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    return report


def print_summary(results: List[Dict], date_str: str, start_time: datetime):
    """
    打印简化的汇总信息到控制台

    Args:
        results: 爬取结果列表
        date_str: 目标日期
        start_time: 开始时间
    """
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    total = len(results)
    success = sum(1 for r in results if r['success'])
    failed = total - success

    print(f"""
╔════════════════════════════════════════╗
║          爬取完成报告                  ║
╠════════════════════════════════════════╣
║ 日期: {date_str}              ║
║ 总数: {total:3d}                             ║
║ 成功: {success:3d}  ({success/total*100:.1f}%)                    ║
║ 失败: {failed:3d}                             ║
║ 耗时: {duration:5.1f} 秒                       ║
╚════════════════════════════════════════╝
    """)


def load_statistics_from_metadata(output_dir: str, date_str: str) -> Dict:
    """
    从元数据文件加载统计信息

    Args:
        output_dir: 输出目录
        date_str: 日期字符串

    Returns:
        统计信息字典
    """
    date_dir = Path(output_dir) / date_str
    metadata_file = date_dir / '_metadata.json'

    if not metadata_file.exists():
        return {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0, 'errors': []}

    with open(metadata_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 构建错误列表
    errors = []
    if data.get('failed_scrapes', 0) > 0:
        # 从全局元数据中读取失败详情
        global_metadata = Path(output_dir) / '_metadata.json'
        if global_metadata.exists():
            with open(global_metadata, 'r', encoding='utf-8') as f:
                global_data = json.load(f)
                for url, info in global_data.get('crawled_urls', {}).items():
                    if info.get('status') == 'failed':
                        errors.append({
                            'url': url,
                            'error': info.get('error', 'Unknown')
                        })

    return {
        'total': data.get('total_articles', 0),
        'success': data.get('successful_scrapes', 0),
        'failed': data.get('failed_scrapes', 0),
        'skipped': 0,
        'errors': errors
    }


def save_report_to_file(report: str, output_dir: str):
    """
    保存报告到文件

    Args:
        report: Markdown 格式的报告
        output_dir: 输出目录
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = output_path / f"report_{timestamp}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"📄 报告已保存: {report_file}")


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description='生成微信爬虫汇总报告')
    parser.add_argument('--date', required=True, help='目标日期 (YYYY-MM-DD)')
    parser.add_argument('--output-dir', default='./output/微信批量爬取', help='输出目录')
    parser.add_argument('--save', action='store_true', help='保存报告到文件')
    parser.add_argument('--start-time', help='开始时间 (ISO 格式)')

    args = parser.parse_args()

    # 解析开始时间
    start_time = datetime.now()
    if args.start_time:
        try:
            start_time = datetime.fromisoformat(args.start_time)
        except ValueError:
            print(f"⚠️  无效的开始时间格式: {args.start_time}")
            start_time = datetime.now()

    print("📊 生成汇总报告...")
    print(f"📅 日期: {args.date}")
    print(f"📁 输出目录: {args.output_dir}")

    # 从元数据加载统计信息
    stats = load_statistics_from_metadata(args.output_dir, args.date)
    stats['start_time'] = start_time
    stats['end_time'] = datetime.now()

    # 生成报告
    report = generate_summary(stats, args.output_dir)

    # 打印到控制台
    print("\n" + report)

    # 可选:保存到文件
    if args.save:
        save_report_to_file(report, args.output_dir)

    return 0


if __name__ == '__main__':
    sys.exit(main())
