#!/usr/bin/env python3
"""
前置检查脚本
验证配置完整性和依赖可用性
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Tuple, List


def check_dependencies() -> Tuple[bool, List[str]]:
    """
    检查 Python 依赖

    Returns:
        (是否全部安装, 缺失的依赖列表)
    """
    required = {
        'feedparser': 'feedparser',
        'bs4': 'beautifulsoup4',
        'html2text': 'html2text'
    }

    missing = []

    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    return len(missing) == 0, missing


def validate_config(config_path: str) -> Tuple[bool, str]:
    """
    验证配置完整性

    检查项:
    1. 必需字段存在
    2. Decision Boundaries 约束
    3. 输出目录可写
    4. RSS 连通性 (可选)

    Args:
        config_path: metadata.json 路径

    Returns:
        (是否有效, 错误消息)
    """
    # 1. 读取配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            config = data.get('configuration', {})
    except Exception as e:
        return False, f"配置文件读取失败: {e}"

    # 2. 检查必需字段
    required_fields = [
        'rss_feed_url',
        'output_base_dir',
        'max_workers',
        'delay_range',
        'retry_limit',
        'timeout'
    ]

    missing_fields = [f for f in required_fields if f not in config]
    if missing_fields:
        return False, f"缺少必需字段: {', '.join(missing_fields)}"

    # 3. Decision Boundaries 检查
    errors = []

    # max_workers ≤ 3
    if config['max_workers'] > 3:
        errors.append(f"❌ max_workers ({config['max_workers']}) 超过 Decision Boundary (≤3)")
        config['max_workers'] = 3  # 自动修正

    # delay_range 在 5-15 秒
    delay_min, delay_max = config['delay_range']
    if delay_min < 5 or delay_max > 15:
        errors.append(f"❌ delay_range ({config['delay_range']}) 超过 Decision Boundary (5-15秒)")
        config['delay_range'] = [max(5, delay_min), min(15, delay_max)]  # 自动修正

    # retry_limit ≤ 3
    if config['retry_limit'] > 3:
        errors.append(f"❌ retry_limit ({config['retry_limit']}) 超过 Decision Boundary (≤3)")
        config['retry_limit'] = 3  # 自动修正

    if errors:
        print("⚠️  Decision Boundaries 警告:")
        for error in errors:
            print(f"   {error}")
        print("✅ 已自动修正为合规值")

        # 保存修正后的配置
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                data['configuration'] = config
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 配置已更新: {config_path}")
        except Exception as e:
            return False, f"配置更新失败: {e}"

    # 4. 检查输出目录写权限
    output_dir = Path(config['output_base_dir'])
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / '.write_test'
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        return False, f"输出目录不可写: {e}"

    # 5. 测试 RSS 连通性 (可选)
    try:
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-m', '5', '-w', '%{http_code}', config['rss_feed_url']],
            capture_output=True,
            text=True,
            timeout=10
        )
        http_code = result.stdout.strip()

        if http_code == '000':
            print(f"⚠️  RSS 服务不可达: {config['rss_feed_url']}")
            print("   提示: 请检查网络连接或稍后重试")
        elif http_code.startswith('2'):
            print(f"✅ RSS 连接正常 (HTTP {http_code})")
        else:
            print(f"⚠️  RSS 返回异常状态码: HTTP {http_code}")
    except Exception as e:
        print(f"⚠️  RSS 连通性测试失败: {e}")
        print("   提示: 这不是致命错误,爬虫可能仍能正常工作")

    return True, "配置验证通过"


def check_rss_url_format(url: str) -> Tuple[bool, str]:
    """
    检查 RSS URL 格式

    Args:
        url: RSS URL

    Returns:
        (是否有效, 错误消息)
    """
    if not url.startswith(('http://', 'https://')):
        return False, "RSS URL 必须以 http:// 或 https:// 开头"

    return True, ""


def main():
    """主入口"""
    print("🔍 微信爬虫前置检查")
    print("=" * 50)

    # 1. 检查依赖
    print("\n1️⃣  检查 Python 依赖...")
    deps_ok, missing = check_dependencies()

    if deps_ok:
        print("✅ 所有依赖已安装")
    else:
        print(f"❌ 缺少依赖: {', '.join(missing)}")
        print(f"   安装命令: pip install {' '.join(missing)}")
        return 1

    # 2. 检查配置
    print("\n2️⃣  验证配置文件...")

    # 查找配置文件
    config_path = None
    possible_paths = [
        '.claude/skills/wechat-batch-crawl/metadata.json',
        '../metadata.json'
    ]

    for path in possible_paths:
        if Path(path).exists():
            config_path = path
            break

    if not config_path:
        # 尝试从当前目录查找
        cwd = Path.cwd()
        metadata_file = cwd / 'metadata.json'
        if metadata_file.exists():
            config_path = str(metadata_file)

    if not config_path:
        print("❌ 找不到 metadata.json 配置文件")
        print("   提示: 请在 .claude/skills/wechat-batch-crawl/ 目录下运行此脚本")
        return 1

    print(f"📄 配置文件: {config_path}")

    config_ok, msg = validate_config(config_path)

    if not config_ok:
        print(f"❌ 配置验证失败: {msg}")
        return 1

    print(f"✅ {msg}")

    # 3. 检查 curl 命令
    print("\n3️⃣  检查 curl 命令...")
    try:
        result = subprocess.run(['curl', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line}")
        else:
            print("❌ curl 命令不可用")
            return 1
    except FileNotFoundError:
        print("❌ 未找到 curl 命令")
        print("   提示: 请安装 curl (macOS/Linux 自带, Windows 需单独安装)")
        return 1

    # 4. 总结
    print("\n" + "=" * 50)
    print("✅ 所有检查通过!可以开始爬取")
    print("\n下一步:")
    print("  python resources/wechat_batch_scraper.py --date today")

    return 0


if __name__ == '__main__':
    sys.exit(main())
