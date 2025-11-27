#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
下载 highlight.js 静态资源到本地 assets 目录
"""

import os
import urllib.request
import urllib.error
from pathlib import Path


def download_file(url: str, output_path: Path) -> bool:
    """
    下载文件到指定路径
    
    Args:
        url: 要下载的 URL
        output_path: 输出文件路径
        
    Returns:
        bool: 下载是否成功
    """
    try:
        print(f"正在下载: {url}")
        print(f"保存到: {output_path}")
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 下载文件
        urllib.request.urlretrieve(url, output_path)
        
        # 检查文件大小
        file_size = output_path.stat().st_size
        print(f"✓ 下载成功 ({file_size} 字节)\n")
        return True
        
    except urllib.error.URLError as e:
        print(f"✗ 下载失败: {e}\n")
        return False
    except Exception as e:
        print(f"✗ 发生错误: {e}\n")
        return False


def main():
    """主函数"""
    # 获取脚本所在目录的父目录（项目根目录）
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    assets_dir = project_root / "view" / "assets"
    
    # 定义要下载的资源
    resources = [
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css",
            "filename": "github.min.css"
        },
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js",
            "filename": "highlight.min.js"
        },
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js",
            "filename": "python.min.js"
        },
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js",
            "filename": "java.min.js"
        },
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/javascript.min.js",
            "filename": "javascript.min.js"
        },
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/xml.min.js",
            "filename": "xml.min.js"
        },
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/css.min.js",
            "filename": "css.min.js"
        },
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/bash.min.js",
            "filename": "bash.min.js"
        },
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/sql.min.js",
            "filename": "sql.min.js"
        }
    ]
    
    print("=" * 60)
    print("开始下载 highlight.js 静态资源")
    print("=" * 60)
    print(f"目标目录: {assets_dir}\n")
    
    # 确保 assets 目录存在
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # 下载所有资源
    success_count = 0
    fail_count = 0
    
    for resource in resources:
        output_path = assets_dir / resource["filename"]
        if download_file(resource["url"], output_path):
            success_count += 1
        else:
            fail_count += 1
    
    # 输出统计信息
    print("=" * 60)
    print(f"下载完成: 成功 {success_count} 个, 失败 {fail_count} 个")
    print("=" * 60)
    
    if fail_count > 0:
        print("\n警告: 部分文件下载失败，请检查网络连接后重试。")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

