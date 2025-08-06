
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Node:
    """Represents a chapter or section in the book."""
    title: str
    path: str
    weight: int
    children: List["Node"] = field(default_factory=list)

def find_asset(book_dir, names):
    for n in names:
        p = os.path.join(book_dir, n)
        if os.path.exists(p):
            return p
    return None

def adjust_heading_levels(content: str, base_level: int) -> str:
    lines = content.split('\n')
    adjusted_lines = []
    has_headings = False
    inside_code_block = False
    for line in lines:
        if line.strip().startswith('```'):
            inside_code_block = not inside_code_block
            adjusted_lines.append(line)
            continue
        if inside_code_block:
            adjusted_lines.append(line)
            continue
        if line.strip().startswith('#'):
            has_headings = True
            original_level = len(line) - len(line.lstrip('#'))
            if base_level == 1:
                new_level = original_level
            else:
                new_level = original_level + base_level - 1
            new_level = min(new_level, 6)
            heading_text = line.lstrip('#').strip()
            adjusted_lines.append('#' * new_level + ' ' + heading_text)
        else:
            adjusted_lines.append(line)
    if not has_headings:
        return content
    return '\n'.join(adjusted_lines)


def build_tree(directory: str, include_drafts: bool = False, parse_front_matter=None, should_include=None) -> Optional[Node]:
    index_path = None
    for name in ("_index.md", "index.md"):
        candidate = os.path.join(directory, name)
        if os.path.exists(candidate):
            index_path = candidate
            break
    if not index_path or not parse_front_matter or not should_include:
        return None
    metadata = parse_front_matter(index_path)
    title, weight, draft, publish, export_pdf = metadata
    if not should_include(index_path, metadata, include_drafts):
        return None
    title = title or os.path.basename(directory)
    node = Node(title=title, path=index_path, weight=weight)
    for entry in sorted(os.listdir(directory)):
        subdir = os.path.join(directory, entry)
        if os.path.isdir(subdir):
            child = build_tree(subdir, include_drafts, parse_front_matter, should_include)
            if child:
                node.children.append(child)
    node.children.sort(key=lambda n: n.weight)
    return node

def flatten_tree(node: Node, result: List[Node]) -> None:
    result.append(node)
    for child in node.children:
        flatten_tree(child, result)

def write_hierarchical_content(tmp, node: Node, book_dir: str, temp_dir: str, temp_pngs: list, level: int = 1, cache_dir: str = None, process_images_in_content=None, adjust_heading_levels_func=None) -> None:
    heading_level = min(level, 4)
    heading = '#' * heading_level
    tmp.write(f'{heading} {node.title}\n\n')
    with open(node.path, "r", encoding="utf-8") as f:
        content = f.read()
        if process_images_in_content:
            content = process_images_in_content(content, book_dir, temp_dir, temp_pngs, node.path, cache_dir)
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
        content = re.sub(r'^\s*---\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^# .*\n', '', content, count=1)
        if adjust_heading_levels_func:
            content = adjust_heading_levels_func(content, heading_level)
        else:
            content = adjust_heading_levels(content, heading_level)
        tmp.write(content + "\n\n")
    for child in node.children:
        write_hierarchical_content(tmp, child, book_dir, temp_dir, temp_pngs, level + 1, cache_dir, process_images_in_content, adjust_heading_levels_func)
    if level == 1:
        tmp.write('\\newpage\n\n')
