#!/usr/bin/env python3
"""
微信公众号批量爬虫
使用 subprocess + curl 避免被识别为 502
支持智能延迟、日期过滤、自动去重
"""

import subprocess
import random
import json
import time
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict


class WeChatBatchScraper:
    """微信公众号批量爬虫"""

    def __init__(self, config_path: Optional[str] = None):
        """初始化爬虫配置"""
        self.config = self._load_config(config_path)
        self.rss_url = self.config['rss_feed_url']
        self.output_dir = Path(self.config['output_base_dir'])
        self.max_workers = self.config.get('max_workers', 3)
        self.delay_range = self.config.get('delay_range', [5, 15])
        self.retry_limit = self.config.get('retry_limit', 3)
        self.timeout = self.config.get('timeout', 30)

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 加载元数据
        self.metadata = self._load_metadata()

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """从 metadata.json 加载配置"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'metadata.json'

        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('configuration', {})

    def fetch_rss(self) -> str:
        """使用 curl 获取 RSS Feed (避免 502)"""
        cmd = [
            'curl', '-s', '-L',
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '-H', 'Accept: application/rss+xml, application/xml, text/xml, */*',
            '-H', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
            '-m', str(self.timeout),
            '--connect-timeout', '10',
            self.rss_url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout + 5
        )

        if result.returncode != 0:
            raise Exception(f"RSS 获取失败: {result.stderr}")

        return result.stdout

    def parse_rss(self, rss_content: str, target_date: str) -> List[Dict]:
        """解析 RSS Feed 并按日期过滤"""
        try:
            import feedparser
        except ImportError:
            raise ImportError("缺少依赖: pip install feedparser")

        feed = feedparser.parse(rss_content)
        target_dt = self._parse_date(target_date)

        articles = []
        for entry in feed.entries:
            # 解析发布时间
            pub_time = None
            if hasattr(entry, 'published_parsed'):
                pub_time = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed'):
                pub_time = datetime(*entry.updated_parsed[:6])

            # 按日期过滤
            if pub_time and pub_time.date() == target_dt.date():
                articles.append({
                    'title': entry.get('title', '无标题'),
                    'url': entry.get('link', ''),
                    'published': pub_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'author': entry.get('author', '未知')
                })

        return articles

    def _parse_date(self, date_filter: str) -> datetime:
        """解析日期参数"""
        today = datetime.now()

        if date_filter == 'today':
            return today
        elif date_filter == 'yesterday':
            return today - timedelta(days=1)
        else:
            # 尝试解析 YYYY-MM-DD 格式
            try:
                return datetime.strptime(date_filter, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"不支持的日期格式: {date_filter}")

    def get_adaptive_delay(self) -> float:
        """智能延迟:根据时间段调整"""
        hour = datetime.now().hour

        if 9 <= hour <= 18:    # 白天高峰
            return random.uniform(10, 15)
        elif 19 <= hour <= 23:   # 晚间
            return random.uniform(7, 12)
        else:                     # 深夜
            return random.uniform(3, 7)

    def filter_existing(self, urls: List[str], date_str: str) -> List[str]:
        """去重:过滤已爬取的文章"""
        output_path = self.output_dir / date_str

        if not output_path.exists():
            return urls

        metadata_file = output_path / '_metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                existing = set(data.get('scraped_urls', []))
                return [url for url in urls if url not in existing]

        return urls

    def scrape_article(self, url: str) -> Dict:
        """爬取单篇文章"""
        for retry in range(self.retry_limit):
            try:
                html = self._fetch_html_via_curl(url)
                article_data = self._extract_content(html)
                return {
                    'url': url,
                    'success': True,
                    'data': article_data
                }
            except Exception as e:
                if retry < self.retry_limit - 1:
                    time.sleep(self.get_adaptive_delay() * 2)
                    continue
                return {
                    'url': url,
                    'success': False,
                    'error': str(e)
                }

        return {'url': url, 'success': False, 'error': 'Max retries exceeded'}

    def _fetch_html_via_curl(self, url: str) -> str:
        """使用 curl 获取 HTML (避免 502)"""
        cmd = [
            'curl', '-s', '-L',
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9',
            '-H', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
            '-H', 'Cache-Control: no-cache',
            '-m', str(self.timeout),
            '--connect-timeout', '10',
            url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout + 5
        )

        if result.returncode != 0:
            raise Exception(f"HTTP 请求失败: {result.stderr}")

        return result.stdout

    def _extract_content(self, html: str) -> Dict:
        """从 HTML 提取内容"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("缺少依赖: pip install beautifulsoup4")

        soup = BeautifulSoup(html, 'html.parser')

        # 提取标题
        title = ''
        title_meta = soup.find('meta', property='og:title')
        if title_meta:
            title = title_meta.get('content', '')
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text()

        # 提取作者
        author = ''
        author_meta = soup.find('meta', property='og:article:author')
        if author_meta:
            author = author_meta.get('content', '')

        # 提取正文
        content_div = soup.find('div', {'id': 'js_content'}) or soup.find('div', class_='rich_media_content')
        if content_div:
            try:
                import html2text
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                content = h.handle(str(content_div))
            except ImportError:
                raise ImportError("缺少依赖: pip install html2text")
        else:
            content = '[无法提取正文]'

        # 提取发布时间
        publish_time = ''
        time_meta = soup.find('meta', property='og:article:published_time')
        if time_meta:
            publish_time = time_meta.get('content', '')

        return {
            'title': title,
            'author': author,
            'content': content,
            'publish_time': publish_time
        }

    def save_article(self, article: Dict, date_str: str, index: int) -> Path:
        """保存文章为 Markdown 文件"""
        # 创建日期目录
        date_dir = self.output_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名 (移除非法字符)
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', article['data']['title'][:50])
        filename = f"{index:03d}_{safe_title}.md"
        file_path = date_dir / filename

        # 生成 Markdown 内容
        md_content = f"""---
title: {article['data']['title']}
author: {article['data']['author']}
publish_time: {article['data']['publish_time']}
url: {article['url']}
crawl_time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---

# {article['data']['title']}

**作者**: {article['data']['author']}
**发布时间**: {article['data']['publish_time']}
**原文链接**: {article['url']}

---

{article['data']['content']}
"""

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return file_path

    def _load_metadata(self) -> Dict:
        """加载元数据"""
        metadata_file = self.output_dir / '_metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'version': '1.0',
            'crawled_urls': {},
            'statistics': {'total_crawled': 0, 'success_count': 0, 'failed_count': 0}
        }

    def _update_metadata(self, date_str: str, results: List[Dict]):
        """更新元数据"""
        date_dir = self.output_dir / date_str
        metadata_file = date_dir / '_metadata.json'

        # 初始化日期元数据
        date_metadata = {
            'date': date_str,
            'total_articles': len(results),
            'successful_scrapes': sum(1 for r in results if r['success']),
            'failed_scrapes': sum(1 for r in results if not r['success']),
            'scraped_urls': []
        }

        # 记录爬取结果
        scraped_urls = []
        for result in results:
            if result['success']:
                scraped_urls.append(result['url'])

        date_metadata['scraped_urls'] = scraped_urls

        # 保存日期元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(date_metadata, f, ensure_ascii=False, indent=2)

        # 更新全局元数据
        for result in results:
            url = result['url']
            if url not in self.metadata['crawled_urls']:
                self.metadata['crawled_urls'][url] = {
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'success' if result['success'] else 'failed'
                }
                if not result['success']:
                    self.metadata['crawled_urls'][url]['error'] = result.get('error', 'Unknown')

        self.metadata['statistics']['total_crawled'] += len(results)
        self.metadata['statistics']['success_count'] += sum(1 for r in results if r['success'])
        self.metadata['statistics']['failed_count'] += sum(1 for r in results if not r['success'])

        # 保存全局元数据
        global_metadata_file = self.output_dir / '_metadata.json'
        with open(global_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def _generate_report(self, results: List[Dict], date_str: str) -> Dict:
        """生成统计报告"""
        total = len(results)
        success = sum(1 for r in results if r['success'])
        failed = total - success

        return {
            'date': date_str,
            'total': total,
            'success': success,
            'failed': failed,
            'success_rate': f"{success/total*100:.1f}%" if total > 0 else "0%",
            'errors': [r for r in results if not r['success']]
        }

    def run(self, target_date: str, list_only: bool = False) -> Dict:
        """主执行流程"""
        print(f"🚀 开始爬取 {target_date} 的文章...")

        # 1. 获取 RSS
        try:
            rss_content = self.fetch_rss()
            print(f"✅ RSS 获取成功")
        except Exception as e:
            print(f"❌ RSS 获取失败: {e}")
            return {'error': str(e)}

        # 2. 解析并过滤日期
        articles = self.parse_rss(rss_content, target_date)
        print(f"📅 找到 {len(articles)} 篇文章")

        if not articles:
            print("⚠️  没有找到符合条件的文章")
            return {'total': 0, 'success': 0, 'failed': 0}

        # 3. 去重
        urls = [a['url'] for a in articles]
        filtered_urls = self.filter_existing(urls, target_date)
        print(f"🔄 去重后待爬取: {len(filtered_urls)} 篇")

        if list_only:
            return {
                'articles': articles,
                'count': len(articles),
                'new_count': len(filtered_urls)
            }

        if not filtered_urls:
            print("✅ 所有文章已爬取,无需重复")
            return {'total': 0, 'success': 0, 'failed': 0, 'skipped': len(articles)}

        # 4. 多线程爬取
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.scrape_article, url): url for url in filtered_urls}

            for i, future in enumerate(as_completed(futures), 1):
                try:
                    result = future.result()
                    results.append(result)

                    if result['success']:
                        # 保存文章
                        self.save_article(result, target_date, i)
                        print(f"✅ [{i}/{len(filtered_urls)}] {result['data']['title'][:40]}")
                    else:
                        print(f"❌ [{i}/{len(filtered_urls)}] {result['url'][:60]} - {result.get('error', 'Unknown')}")

                    # 智能延迟
                    if i < len(filtered_urls):
                        delay = self.get_adaptive_delay()
                        time.sleep(delay)

                except Exception as e:
                    print(f"❌ 异常: {e}")
                    results.append({'url': futures[future], 'success': False, 'error': str(e)})

        # 5. 更新元数据
        self._update_metadata(target_date, results)

        # 6. 生成报告
        report = self._generate_report(results, target_date)

        print(f"""
╔══════════════════════════════╗
║       爬取完成报告           ║
╠══════════════════════════════╣
║ 总数: {report['total']:3d}                   ║
║ 成功: {report['success']:3d}  ({report['success_rate']:5s})          ║
║ 失败: {report['failed']:3d}                    ║
╚══════════════════════════════╝
        """)

        return report


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='微信公众号批量爬虫')
    parser.add_argument('--date', default='today', help='目标日期: today/yesterday/YYYY-MM-DD')
    parser.add_argument('--list-only', action='store_true', help='仅列出文章,不爬取')
    parser.add_argument('--config', help='配置文件路径')

    args = parser.parse_args()

    try:
        scraper = WeChatBatchScraper(config_path=args.config)
        report = scraper.run(args.date, args.list_only)
        return 0 if report.get('error') is None else 1
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
