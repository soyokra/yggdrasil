#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Markdown 转 HTML 文档站点生成器
将 src 目录下的 Markdown 文件转换为 HTML 页面
"""

import os
import shutil
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

import markdown
from markdown.extensions import codehilite, toc, fenced_code
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape


class DocSiteBuilder:
    """文档站点生成器"""
    
    def __init__(self, docs_dir: str = "src", view_dir: str = "docs", config_path: str = "config.json"):
        # 将相对路径转换为绝对路径
        self.docs_dir = Path(docs_dir).resolve()
        self.view_dir = Path(view_dir).resolve()
        self.template_dir = self.view_dir
        self.assets_dir = self.view_dir / "assets"
        self.html_dir = self.view_dir / "html"
        
        # 加载配置文件
        self.config = self._load_config(config_path)
        
        # 验证目录是否存在
        if not self.docs_dir.exists():
            raise FileNotFoundError(f"文档目录不存在: {self.docs_dir}")
        
        # 初始化目录
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化 Jinja2 环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # 初始化 Markdown 转换器
        self.md = markdown.Markdown(
            extensions=[
                'codehilite',
                'toc',
                'fenced_code',
                'tables',
                'nl2br',
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'hljs',
                    'use_pygments': True,
                }
            }
        )
        
        # 存储导航树结构
        self.nav_tree = []
        # 存储所有文件的路径映射 (docs相对路径 -> view相对路径)
        self.path_mapping = {}
        # 存储转换后的 HTML 内容
        self.html_contents = {}
        # 存储允许的顶级目录（从配置中读取）
        self.allowed_top_dirs = set(self.config.get('top', []))
        
    def build(self):
        """构建整个站点"""
        print("开始构建文档站点...")
        
        # 清理 docs 目录（保留模板和 assets）
        self._clean_view_dir()
        
        # 记录根目录 README.md 的路径映射（用于链接处理，但不显示在导航栏）
        readme_path = self.docs_dir / "README.md"
        if readme_path.exists():
            self.path_mapping["README.md"] = "index.html"
        
        # 构建文件路径映射和导航树
        print("扫描文档目录...")
        self.nav_tree = self._build_nav_tree()
        
        # 转换所有 Markdown 文件（包括根目录的 README.md）
        print("转换 Markdown 文件...")
        self._convert_all_markdown()
        
        # 如果根目录没有 README.md，生成默认首页内容
        if not readme_path.exists():
            print("生成默认首页内容...")
            default_content = "<h1>欢迎</h1><p>这是文档站点的首页。</p>"
            self.html_contents["index.html"] = default_content
        
        # 复制所有图片文件
        print("复制图片文件...")
        self._copy_all_images()
        
        # 生成所有 HTML 页面（包括首页）
        print("生成 HTML 页面...")
        self._generate_all_pages()
        
        print("构建完成！")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.is_absolute():
            # 如果是相对路径，相对于脚本所在目录
            script_dir = Path(__file__).parent
            config_file = script_dir / config_path
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"已加载配置文件: {config_file}")
                    return config
            except Exception as e:
                print(f"警告: 加载配置文件失败: {e}，使用默认配置")
                return {}
        else:
            print(f"警告: 配置文件不存在: {config_file}，使用默认配置")
            return {}
    
    def _clean_view_dir(self):
        """清理 docs 目录，保留模板和 assets"""
        # 清理根目录下的 HTML 文件（除了 index.html）
        for item in self.view_dir.iterdir():
            if item.is_file() and item.suffix == '.html' and item.name != 'index.html':
                if item.name not in ['template.html']:
                    item.unlink()
            elif item.is_dir():
                # 清理所有目录（除了 assets 和 html，html 目录会单独清理）
                if item.name not in ['assets', 'html']:
                    shutil.rmtree(item)
        
        # 完全清空 html 目录（防止已删除的 md 文件对应的 html 还在）
        if self.html_dir.exists():
            print("清空 html 目录...")
            shutil.rmtree(self.html_dir)
        self.html_dir.mkdir(parents=True, exist_ok=True)
    
    def _build_nav_tree(self) -> List[Dict]:
        """构建导航树结构"""
        nav_items = []
        
        # 获取配置中指定的顶级目录顺序
        top_dirs = self.config.get('top', [])
        
        # 如果没有配置，使用所有目录（保持向后兼容）
        if not top_dirs:
            # 遍历所有目录，按字母顺序排序
            for item in sorted(self.docs_dir.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    nav_item = self._build_nav_item(item, self.docs_dir)
                    if nav_item:
                        nav_items.append(nav_item)
            return nav_items
        
        # 收集所有顶级目录
        all_dirs = {}
        for item in self.docs_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                all_dirs[item.name] = item
        
        # 根据配置排序和过滤顶级目录
        processed_dirs = set()
        
        # 先处理配置中指定的目录（按配置顺序）
        for dir_name in top_dirs:
            if dir_name in all_dirs:
                item = all_dirs[dir_name]
                nav_item = self._build_nav_item(item, self.docs_dir)
                if nav_item:
                    nav_items.append(nav_item)
                    processed_dirs.add(dir_name)
            else:
                print(f"警告: 配置中指定的目录 '{dir_name}' 在 src 目录中不存在")
        
        # 如果配置中没有指定所有目录，输出提示
        if len(processed_dirs) < len(all_dirs):
            skipped_dirs = set(all_dirs.keys()) - processed_dirs
            if skipped_dirs:
                print(f"提示: 以下目录未包含在配置中，将被跳过: {', '.join(sorted(skipped_dirs))}")
        
        return nav_items
    
    def _build_nav_item(self, dir_path: Path, base_path: Path) -> Optional[Dict]:
        """构建目录导航项"""
        rel_path = dir_path.relative_to(base_path)
        readme_path = dir_path / "README.md"
        
        # 构建子项
        children = []
        
        # 处理子目录
        for item in sorted(dir_path.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                child_item = self._build_nav_item(item, base_path)
                if child_item:
                    children.append(child_item)
            elif item.is_file() and item.suffix == '.md' and item.name != 'README.md':
                child_item = self._build_file_nav_item(item, base_path)
                if child_item:
                    children.append(child_item)
        
        # 确定路径
        if readme_path.exists():
            html_path = self._get_html_path(readme_path, base_path)
            has_readme = True
        else:
            # 创建一个虚拟的路径（在 html 目录下）
            html_path = f"html/{rel_path}/index.html".replace('\\', '/')
            has_readme = False
        
        # 记录路径映射
        if readme_path.exists():
            docs_rel = str(readme_path.relative_to(self.docs_dir)).replace('\\', '/')
            self.path_mapping[docs_rel] = html_path
        
        nav_item = {
            'name': dir_path.name,
            'type': 'directory',
            'path': html_path,
            'has_readme': has_readme,
            'children': children
        }
        
        return nav_item
    
    def _build_file_nav_item(self, file_path: Path, base_path: Path) -> Optional[Dict]:
        """构建文件导航项"""
        if file_path.name == 'template.html':
            return None
            
        html_path = self._get_html_path(file_path, base_path)
        docs_rel = str(file_path.relative_to(self.docs_dir)).replace('\\', '/')
        
        # 记录路径映射
        self.path_mapping[docs_rel] = html_path
        
        return {
            'name': self._get_display_name(file_path.stem),
            'type': 'file',
            'path': html_path
        }
    
    def _get_html_path(self, md_path: Path, base_path: Path) -> str:
        """获取对应的 HTML 路径"""
        rel_path = md_path.relative_to(base_path)
        
        if md_path.name == "README.md":
            # README.md -> index.html
            parent_dir = rel_path.parent
            if str(parent_dir) == '.':
                # 根目录的 README.md -> index.html (在 docs 根目录)
                return "index.html"
            else:
                # 子目录的 README.md -> html/parent/index.html
                return f"html/{parent_dir}/index.html".replace('\\', '/')
        else:
            # other.md -> other.html
            parent_dir = rel_path.parent
            html_name = rel_path.stem + ".html"
            if str(parent_dir) == '.':
                # 根目录的文件 -> html/filename.html
                return f"html/{html_name}"
            else:
                # 子目录的文件 -> html/parent/filename.html
                return f"html/{parent_dir}/{html_name}".replace('\\', '/')
    
    def _get_display_name(self, name: str) -> str:
        """获取显示名称"""
        # 移除常见的后缀
        return name.replace('_', ' ').replace('-', ' ').title()
    
    def _convert_all_markdown(self):
        """转换所有 Markdown 文件"""
        # 如果没有配置允许的目录，处理所有文件
        if not self.allowed_top_dirs:
            allowed_prefixes = None
        else:
            # 只处理配置中允许的顶级目录下的文件
            allowed_prefixes = [str(self.docs_dir / top_dir) for top_dir in self.allowed_top_dirs]
        
        for md_file in self.docs_dir.rglob("*.md"):
            if md_file.name == 'template.html':
                continue
            
            # 如果有限制，检查文件是否在允许的目录下
            if allowed_prefixes:
                file_str = str(md_file)
                is_allowed = False
                # 根目录的 README.md 始终允许
                if md_file.name == "README.md" and md_file.parent == self.docs_dir:
                    is_allowed = True
                else:
                    is_allowed = any(file_str.startswith(prefix) for prefix in allowed_prefixes)
                if not is_allowed:
                    continue
            
            rel_path = str(md_file.relative_to(self.docs_dir)).replace('\\', '/')
            if rel_path in self.path_mapping:
                html_path = self.path_mapping[rel_path]
                self._convert_markdown_file(md_file, html_path)
        
        # 确保根目录的 README.md 被转换（如果存在且不在 path_mapping 中）
        readme_path = self.docs_dir / "README.md"
        if readme_path.exists() and "README.md" in self.path_mapping:
            html_path = self.path_mapping["README.md"]
            if html_path not in self.html_contents:
                self._convert_markdown_file(readme_path, html_path)
    
    def _normalize_list_indentation(self, md_content: str) -> str:
        """规范化列表缩进：将列表项的 2 个空格缩进转换为 4 个空格
        
        Python Markdown 库要求嵌套列表使用 4 个空格缩进才能正确识别嵌套结构。
        此方法将 2 个空格的列表缩进转换为 4 个空格，以支持常见的 2 空格缩进风格。
        
        算法：将每个 2 空格缩进级别转换为 4 空格缩进级别。
        例如：0空格 -> 0空格, 2空格 -> 4空格, 4空格 -> 8空格, 6空格 -> 12空格
        """
        lines = md_content.split('\n')
        normalized_lines = []
        in_code_block = False
        
        for line in lines:
            stripped = line.lstrip()
            
            # 检测代码块开始和结束
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                normalized_lines.append(line)
                continue
            
            # 在代码块内，保持原样
            if in_code_block:
                normalized_lines.append(line)
                continue
            
            # 检测缩进代码块（4 个空格开头），保持原样
            if line.startswith('    ') and not stripped.startswith(('- ', '* ', '+ ')):
                normalized_lines.append(line)
                continue
            
            # 处理列表项
            # 匹配列表项：可选的前导空格 + 列表标记（-、*、+） + 空格
            list_item_match = re.match(r'^(\s*)([-*+])\s+(.*)$', line)
            if list_item_match:
                leading_spaces = list_item_match.group(1)
                list_marker = list_item_match.group(2)
                content = list_item_match.group(3)
                
                # 计算缩进级别（以 2 空格为单位）
                leading_len = len(leading_spaces)
                
                # 将每个 2 空格缩进级别转换为 4 空格
                # 例如：0空格 -> 0空格, 2空格 -> 4空格, 4空格 -> 8空格, 6空格 -> 12空格
                if leading_len % 2 == 0:
                    # 是 2 的倍数，转换为 4 的倍数
                    indent_level = leading_len // 2
                    normalized_leading = '    ' * indent_level
                    normalized_lines.append(normalized_leading + list_marker + ' ' + content)
                else:
                    # 不是 2 的倍数，保持原样（可能是 tab 或其他）
                    normalized_lines.append(line)
            else:
                # 非列表项，保持原样
                normalized_lines.append(line)
        
        return '\n'.join(normalized_lines)
    
    def _convert_markdown_file(self, md_path: Path, html_rel_path: str):
        """转换单个 Markdown 文件"""
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 规范化列表缩进（将 2 空格转换为 4 空格）
        md_content = self._normalize_list_indentation(md_content)
        
        # 转换为 HTML
        html_content = self.md.convert(md_content)
        self.md.reset()
        
        # 处理链接
        html_content = self._process_links(html_content, html_rel_path)
        
        # 处理图片路径
        html_content = self._process_images(html_content, html_rel_path, md_path)
        
        # 存储 HTML 内容
        self.html_contents[html_rel_path] = html_content
    
    def _process_links(self, html_content: str, current_html_path: str) -> str:
        """处理 HTML 中的链接"""
        soup = BeautifulSoup(html_content, 'html.parser')
        # 处理路径：index.html -> . , html/spring/index.html -> html/spring
        if current_html_path == "index.html":
            current_dir = Path(".")
        elif current_html_path.startswith("html/"):
            # 移除 html/ 前缀，只保留目录部分
            current_dir = Path(current_html_path).parent
        else:
            current_dir = Path(current_html_path).parent
        
        # 处理所有链接
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if not href or href.startswith('http') or href.startswith('#'):
                continue
            
            # 转换为 HTML 相对路径
            new_href = self._convert_link_path(href, current_html_path)
            if new_href:
                link['href'] = new_href
        
        return str(soup)
    
    def _convert_link_path(self, link_path: str, current_html_path: str) -> Optional[str]:
        """转换链接路径"""
        # 移除锚点
        if '#' in link_path:
            link_path, anchor = link_path.split('#', 1)
        else:
            anchor = None
        
        # 如果是空路径，跳过
        if not link_path or link_path == '.':
            return None
        
        # 如果是 Markdown 链接
        if link_path.endswith('.md'):
            # 确定当前 HTML 文件所在的 src 目录路径
            if current_html_path == "index.html":
                docs_current_dir = self.docs_dir
            elif current_html_path.startswith("html/"):
                # html/spring/index.html -> src/spring
                rel_path = current_html_path[5:]  # 移除 "html/"
                if rel_path.endswith("index.html"):
                    rel_path = str(Path(rel_path).parent)
                else:
                    rel_path = str(Path(rel_path).parent)
                if rel_path == '.':
                    docs_current_dir = self.docs_dir
                else:
                    docs_current_dir = self.docs_dir / rel_path
            else:
                docs_current_dir = self.docs_dir
            
            # 构建完整的链接路径
            try:
                full_link_path = (docs_current_dir / link_path).resolve()
                
                # 检查路径是否在 src 目录内
                try:
                    rel_to_docs = str(full_link_path.relative_to(self.docs_dir)).replace('\\', '/')
                    if rel_to_docs in self.path_mapping:
                        html_path = self.path_mapping[rel_to_docs]
                    elif full_link_path.exists() and full_link_path.suffix == '.md':
                        # 如果是新的 markdown 文件，生成路径
                        html_path = self._get_html_path(full_link_path, self.docs_dir)
                    else:
                        return None
                except ValueError:
                    return None
            except Exception:
                return None
            
            if not html_path:
                return None
            
            # 计算相对路径
            target_path = Path(html_path)
            from_path = Path(current_html_path)
            relative_path = self._get_relative_path(from_path, target_path)
            
            if anchor:
                return f"{relative_path}#{anchor}"
            return relative_path
        
        # 其他情况保持原样
        if anchor:
            return f"{link_path}#{anchor}"
        return link_path
    
    def _get_relative_path(self, from_path: Path, to_path: Path) -> str:
        """计算两个路径之间的相对路径"""
        from_dir = from_path.parent if from_path.name != '.' else from_path
        
        # 如果目标在同一目录
        if from_dir == to_path.parent:
            return to_path.name
        
        # 计算相对路径
        try:
            # 处理 index.html 的特殊情况
            if to_path.name == 'index.html' and to_path.parent == from_dir:
                return './'
            
            rel_path = os.path.relpath(str(to_path), str(from_dir))
            return str(rel_path).replace('\\', '/')
        except ValueError:
            # 跨磁盘的情况，返回绝对路径形式的相对路径
            parts = to_path.parts
            if len(parts) > 0:
                return '/' + '/'.join(parts)
            return str(to_path)
    
    def _process_images(self, html_content: str, current_html_path: str, md_path: Path) -> str:
        """处理图片路径"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if not src or src.startswith('http'):
                continue
            
            # 计算图片在 src 目录中的路径
            img_path = (md_path.parent / src).resolve()
            try:
                # 检查图片是否在 src 目录内
                rel_to_docs = img_path.relative_to(self.docs_dir.resolve())
                # 图片现在在 html 目录下，路径为 html/...
                html_img_path = f"html/{rel_to_docs}".replace('\\', '/')
                
                # 计算相对路径（从当前 HTML 文件到图片文件）
                from_path = Path(current_html_path)
                target_path = Path(html_img_path)
                relative_path = self._get_relative_path(from_path, target_path)
                
                img['src'] = relative_path
            except ValueError:
                # 图片不在 src 目录内，保持原路径
                pass
        
        return str(soup)
    
    def _copy_all_images(self):
        """复制所有图片文件和其他非 Markdown 文件到 html 目录"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.drawio.png'}
        
        # 如果没有配置允许的目录，处理所有文件
        if not self.allowed_top_dirs:
            allowed_prefixes = None
        else:
            # 只处理配置中允许的顶级目录下的文件
            allowed_prefixes = [str(self.docs_dir / top_dir) for top_dir in self.allowed_top_dirs]
        
        for file_path in self.docs_dir.rglob("*"):
            # 跳过目录
            if file_path.is_dir():
                continue
            
            # 跳过 Markdown 文件和模板文件
            if file_path.suffix.lower() == '.md' or file_path.name == 'template.html':
                continue
            
            # 如果有限制，检查文件是否在允许的目录下
            if allowed_prefixes:
                file_str = str(file_path)
                is_allowed = any(file_str.startswith(prefix) for prefix in allowed_prefixes)
                if not is_allowed:
                    continue
            
            # 复制图片文件和其他文件
            rel_path = str(file_path.relative_to(self.docs_dir)).replace('\\', '/')
            # 文件放到 html 目录下，保持相同的目录结构
            view_file_path = self.html_dir / rel_path
            
            # 创建目标目录
            view_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(file_path, view_file_path)
    
    def _generate_all_pages(self):
        """生成所有 HTML 页面"""
        template = self.jinja_env.get_template('template.html')
        
        # 生成所有已转换的 Markdown 页面
        for html_path, content in self.html_contents.items():
            self._generate_page(template, html_path, content)
        
        # 为没有 README.md 的目录生成空白页面
        self._generate_empty_directory_pages(template)
    
    def _generate_empty_directory_pages(self, template):
        """为没有 README.md 的目录生成空白页面"""
        def process_nav_items(items):
            for item in items:
                if item['type'] == 'directory' and not item['has_readme']:
                    html_path = item['path']
                    # 生成空白页面
                    blank_content = f"<h1>{item['name']}</h1><p>此目录暂无内容。</p>"
                    self._generate_page(template, html_path, blank_content)
                
                # 递归处理子项
                if 'children' in item and item['children']:
                    process_nav_items(item['children'])
        
        process_nav_items(self.nav_tree)
    
    def _generate_page(self, template, html_path: str, content: str):
        """生成单个 HTML 页面"""
        # 确定文件路径
        if html_path == "index.html":
            # index.html 在 docs 根目录
            view_file_path = self.view_dir / html_path
            depth = 0
        else:
            # 其他页面在 docs/html 目录下
            view_file_path = self.view_dir / html_path
            # 计算深度：html/spring/actuator.html -> depth = 2 (html + spring)
            if html_path.startswith("html/"):
                # 移除 html/ 前缀来计算深度
                relative_path = html_path[5:]  # 移除 "html/"
                if relative_path:
                    relative_path_obj = Path(relative_path)
                    if str(relative_path_obj.parent) == '.':
                        # html/filename.html -> depth = 1
                        depth = 1
                    else:
                        # html/spring/actuator.html -> depth = 2 (html + spring)
                        depth = len(relative_path_obj.parent.parts) + 1
                else:
                    depth = 1
            else:
                depth = 0
        
        view_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 计算基础路径（用于引用 assets）
        base_path = "../" * depth if depth > 0 else "./"
        
        # 生成导航树 HTML
        nav_tree_html = self._render_nav_tree(self.nav_tree, html_path, base_path)
        
        # 生成页面标题
        title = Path(html_path).stem
        if title == 'index':
            # 尝试从父目录获取标题
            parent_dir = Path(html_path).parent
            if str(parent_dir) != '.':
                title = parent_dir.name
            else:
                title = '首页'
        else:
            title = self._get_display_name(title)
        
        # 渲染模板
        html_output = template.render(
            title=title,
            content=content,
            nav_tree=nav_tree_html,
            base_path=base_path
        )
        
        # 写入文件
        with open(view_file_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
    
    def _render_nav_tree(self, nav_items: List[Dict], current_path: str, base_path: str, level: int = 0) -> str:
        """渲染导航树为 HTML"""
        html_parts = []
        
        for item in nav_items:
            if item['type'] == 'directory':
                has_children = len(item['children']) > 0
                nav_path = item['path']
                is_active = current_path == nav_path or current_path.startswith(Path(nav_path).parent.as_posix() + '/')
                
                icon_class = "nav-link-icon" + (" expanded" if has_children and is_active else "")
                link_class = "nav-link" + (" has-children" if has_children else "") + (" active" if is_active else "")
                
                html_parts.append(f'<li class="nav-item">')
                html_parts.append(f'<div class="{link_class}">')
                if has_children:
                    html_parts.append(f'<span class="{icon_class}" data-toggle="collapse"></span>')
                else:
                    html_parts.append('<span class="nav-link-icon" style="width: 20px; margin-right: 4px;"></span>')
                html_parts.append(f'<a href="{base_path}{nav_path}" class="nav-link-text" data-path="{nav_path}">{item["name"]}</a>')
                html_parts.append('</div>')
                
                if has_children:
                    html_parts.append(f'<ul class="nav-children{" expanded" if is_active else ""}">')
                    html_parts.append(self._render_nav_tree(item['children'], current_path, base_path, level + 1))
                    html_parts.append('</ul>')
                
                html_parts.append('</li>')
            else:
                nav_path = item['path']
                is_active = current_path == nav_path
                link_class = "nav-link" + (" active" if is_active else "")
                
                html_parts.append(f'<li class="nav-item">')
                html_parts.append(f'<div class="{link_class}">')
                html_parts.append('<span class="nav-link-icon" style="width: 20px; margin-right: 4px;"></span>')
                html_parts.append(f'<a href="{base_path}{nav_path}" class="nav-link-text" data-path="{nav_path}">{item["name"]}</a>')
                html_parts.append('</div>')
                html_parts.append('</li>')
        
        return '\n'.join(html_parts)
    
    def _generate_index(self):
        """生成首页"""
        readme_path = self.docs_dir / "README.md"
        
        if readme_path.exists():
            # 转换 README.md
            with open(readme_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            html_content = self.md.convert(md_content)
            self.md.reset()
        else:
            # 生成默认首页
            html_content = "<h1>欢迎</h1><p>这是文档站点的首页。</p>"
        
        # 处理链接和图片
        html_content = self._process_links(html_content, "index.html")
        html_content = self._process_images(html_content, "index.html", readme_path if readme_path.exists() else self.docs_dir / "README.md")
        
        # 生成页面
        template = self.jinja_env.get_template('template.html')
        self._generate_page(template, "index.html", html_content)


def get_project_root() -> Path:
    """获取项目根目录（python 的父目录）"""
    script_path = Path(__file__).resolve()
    # 脚本在 python/build_site.py，项目根目录是 python 的父目录
    return script_path.parent.parent


def main():
    """主函数"""
    # 获取项目根目录
    project_root = get_project_root()
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    # 构建路径
    docs_dir = project_root / "src"
    view_dir = project_root / "docs"
    
    builder = DocSiteBuilder(str(docs_dir), str(view_dir))
    builder.build()


if __name__ == "__main__":
    main()

