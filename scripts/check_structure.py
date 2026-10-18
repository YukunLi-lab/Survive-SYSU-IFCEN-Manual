#!/usr/bin/env python3
"""检查本手册的目录、正文入口和本地链接；仅依赖 Python 3.10+ 标准库。

运行：python scripts/check_structure.py
可选：python scripts/check_structure.py --root /path/to/repository
外部网址不联网检查。标题片段采用 GitHub 常用规则；支持显式 HTML id/name。
"""

from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import re
import struct
import sys
from urllib.parse import unquote, urlsplit


BODY_DIRS = ("xu", "li-zhi-pian", "fang-tan-ji", "sheng-cun-ji-qiao", "fu-lu")
EXCLUDED = {".git", "_book", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}
BINARY_SUFFIXES = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".tif",
    ".tiff", ".avif", ".svg", ".zip", ".gz", ".7z", ".rar", ".epub", ".mobi",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".exe", ".dll", ".pyc",
    ".mp3", ".mp4", ".wav", ".woff", ".woff2", ".ttf", ".otf",
}
FIGURES_DIR = Path("assets/figures")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def valid_png_header(path: Path) -> bool:
    """验证 PNG 签名、首个 IHDR 块与正数宽高；不需要第三方图像库。"""
    try:
        with path.open("rb") as source:
            header = source.read(33)
    except OSError:
        return False
    if len(header) != 33 or header[:8] != PNG_SIGNATURE:
        return False
    if header[8:12] != b"\x00\x00\x00\r" or header[12:16] != b"IHDR":
        return False
    width, height = struct.unpack(">II", header[16:24])
    return width > 0 and height > 0


def hide_code(text: str) -> str:
    """以空白覆盖代码与注释，保留换行，以便报告正确的行号。"""
    def blank(value: str) -> str:
        return re.sub(r"[^\n]", " ", value)

    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            lines.append(blank(line))
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
        elif marker:
            fence = (marker[1][0], len(marker[1]))
            lines.append(blank(line))
        else:
            lines.append(line)
    clean = "".join(lines)
    clean = re.sub(r"<!--.*?-->", lambda match: blank(match[0]), clean, flags=re.S)
    clean = re.sub(r"(?<!`)(`+)(?!`)(.*?)(?<!`)\1(?!`)", lambda match: blank(match[0]), clean, flags=re.S)
    return clean


def reference_id(label: str) -> str:
    return " ".join(label.split()).casefold()


def balanced_end(text: str, start: int, opening: str, closing: str) -> int | None:
    depth = 0
    index = start
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == opening:
            depth += 1
        elif text[index] == closing:
            depth -= 1
            if not depth:
                return index
        index += 1
    return None


def link_destination(value: str) -> str:
    value = value.strip()
    if value.startswith("<") and ">" in value:
        return value[1:value.index(">")]
    # Markdown 目的地址不能含未转义空格；后面的可选文字是链接标题。
    match = re.match(r"(?:\\.|[^\s])+", value)
    return match[0] if match else ""


def markdown_links(clean: str) -> list[tuple[int, str]]:
    """返回行号、目的地址；支持内联、引用式、图片和 HTML href/src。"""
    definitions = {}
    content = clean
    definition_pattern = re.compile(r"^ {0,3}\[([^\]\n]+)\]:[ \t]*(<[^>\n]*>|\S+)[^\n]*$", re.M)
    for match in definition_pattern.finditer(clean):
        definitions[reference_id(match[1])] = link_destination(match[2])
    content = definition_pattern.sub(lambda match: " " * len(match[0]), content)
    links = []
    index = 0
    while index < len(content):
        if content[index] == "\\":
            index += 2
            continue
        if content[index] != "[":
            index += 1
            continue
        end = balanced_end(content, index, "[", "]")
        if end is None:
            index += 1
            continue
        label = content[index + 1:end]
        after = end + 1
        destination = None
        if after < len(content) and content[after] == "(":
            close = balanced_end(content, after, "(", ")")
            if close is not None:
                destination = link_destination(content[after + 1:close])
                after = close + 1
        elif after < len(content) and content[after] == "[":
            close = content.find("]", after + 1)
            if close != -1:
                identifier = content[after + 1:close] or label
                destination = definitions.get(reference_id(identifier))
                after = close + 1
        else:
            destination = definitions.get(reference_id(label))
        if destination is not None:
            links.append((content.count("\n", 0, index) + 1, destination))
        index = max(index + 1, after)
    for match in re.finditer(r"<(?:a|img|source)\b[^>]*?\b(?:href|src)\s*=\s*(['\"])(.*?)\1[^>]*>", content, re.I | re.S):
        links.append((content.count("\n", 0, match.start()) + 1, html.unescape(match[2])))
    return links


def heading_slug(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]*>", "", text)
    text = html.unescape(text).strip().lower()
    text = re.sub(r"[^\w\-\s]", "", text)
    return re.sub(r"\s", "-", text)


def document_anchors(text: str) -> set[str]:
    # 内联代码仍然属于标题文字，只移除包围它的反引号。
    no_inline = re.sub(r"`([^`\n]+)`", r"\1", text)
    clean = hide_code(no_inline)
    anchors = set()
    for match in re.finditer(r"<[^>]+\b(?:id|name)\s*=\s*(['\"])(.*?)\1[^>]*>", clean, re.I):
        anchors.add(html.unescape(match[2]))
    generated = set()
    lines = clean.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        title = match[1] if match else None
        if title is None and index + 1 < len(lines) and line.strip() and re.match(r"^ {0,3}(?:=+|-+)\s*$", lines[index + 1]):
            title = line.strip()
        if title is not None:
            base = heading_slug(title)
            slug = base
            number = 0
            while slug in generated:
                number += 1
                slug = f"{base}-{number}"
            generated.add(slug)
            anchors.add(slug)
    return anchors


class Checker:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.problems: list[str] = []
        self.documents: dict[Path, str] = {}
        self.files: list[Path] = []
        self.directories: list[Path] = []

    def label(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def fail(self, message: str) -> None:
        if message not in self.problems:
            self.problems.append(message)

    def scan(self) -> None:
        for directory, dirs, files in os.walk(self.root, followlinks=False):
            base = Path(directory)
            dirs[:] = sorted(name for name in dirs if name not in EXCLUDED)
            for name in list(dirs):
                path = base / name
                if path.is_symlink():
                    self.fail(f"{self.label(path)}：请用普通文件夹代替符号链接。")
                    dirs.remove(name)
                    continue
                self.directories.append(path)
                if name.casefold() == "download":
                    self.fail(f"{self.label(path)}：存在旧 download 残留，请移除。")
            for name in sorted(files):
                path = base / name
                self.files.append(path)
                relative = self.label(path)
                if path.is_symlink():
                    self.fail(f"{relative}：请用普通文本文件代替符号链接。")
                    continue
                if name.casefold() in {"gitbook.yaml", "download"} or re.fullmatch(r"README \(\d+\)\.md", name, re.I):
                    self.fail(f"{relative}：存在旧文件残留，请按正文位置整理或移除。")
                if path.suffix.casefold() == ".png" and path.relative_to(self.root).parent == FIGURES_DIR:
                    if not valid_png_header(path):
                        self.fail(f"{relative}：数据图须为具有有效 PNG 签名、IHDR 和正数尺寸的文件。")
                    continue
                if path.suffix.casefold() in BINARY_SUFFIXES:
                    self.fail(f"{relative}：仅允许 assets/figures/ 中的 PNG 数据图，请移除其他图片、PDF、压缩包等附件。")
                try:
                    value = path.read_text(encoding="utf-8-sig")
                    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
                        raise ValueError("包含二进制控制字符")
                except (OSError, UnicodeError, ValueError):
                    self.fail(f"{relative}：无法作为 UTF-8 纯文本读取，请检查文件编码或二进制内容。")
                    continue
                if path.suffix.casefold() == ".md":
                    self.documents[path] = value

    def exact_path(self, source: Path, destination: str, line: int) -> tuple[Path, str] | None:
        address = html.unescape(re.sub(r"\\([\\`*{}\[\]()#+.!_<> -])", r"\1", destination.strip()))
        if not address:
            self.fail(f"{self.label(source)} 第 {line} 行：链接地址为空，请补充目的文件或标题。")
            return None
        try:
            parts = urlsplit(address)
        except ValueError:
            self.fail(f"{self.label(source)} 第 {line} 行：链接地址格式不正确：{destination}")
            return None
        if parts.scheme or parts.netloc or address.startswith("//"):
            return None
        relative = unquote(parts.path)
        fragment = unquote(parts.fragment)
        location = f"{self.label(source)} 第 {line} 行"
        if any(ord(char) < 32 for char in relative):
            self.fail(f"{location}：链接路径包含不可见控制字符：{destination}")
            return None
        if "\\" in relative:
            self.fail(f"{location}：链接路径请使用 /，不要使用反斜线：{destination}")
            return None
        candidate = self.root / relative.lstrip("/") if relative.startswith("/") else source.parent / relative if relative else source
        candidate = Path(os.path.abspath(candidate))
        try:
            components = candidate.relative_to(self.root).parts
        except ValueError:
            self.fail(f"{location}：链接超出了仓库目录：{destination}")
            return None
        actual = self.root
        for component in components:
            try:
                names = {item.name: item for item in actual.iterdir()}
            except OSError:
                names = {}
            if component not in names:
                similar = [name for name in names if name.casefold() == component.casefold()]
                if similar:
                    self.fail(f"{location}：链接的大小写与文件名不一致，{component} 应为 {similar[0]}：{destination}")
                else:
                    self.fail(f"{location}：找不到链接目标：{destination}")
                return None
            actual = names[component]
        if actual.is_dir():
            actual = actual / "README.md"
            if not actual.is_file():
                self.fail(f"{location}：目标文件夹缺少 README.md 入口：{destination}")
                return None
        if actual.is_symlink() or not actual.is_file():
            self.fail(f"{location}：目标不是可读取的普通文件：{destination}")
            return None
        if actual not in self.files:
            self.fail(f"{location}：链接指向被排除的目录，不能作为手册内容：{destination}")
            return None
        return actual, fragment

    def check_config(self) -> None:
        config = self.root / ".gitbook.yaml"
        if not config.is_file():
            self.fail("根目录缺少 .gitbook.yaml，请加入 GitBook 入口设置。")
            return
        try:
            text = config.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            return  # scan 已报告无法读取。
        found = {}
        in_structure = False
        for number, line in enumerate(text.splitlines(), 1):
            line = re.sub(r"\s+#.*$", "", line).rstrip()
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            match = re.fullmatch(r"( {0,2})(root|structure|readme|summary):\s*(.*?)", line)
            if not match:
                self.fail(f".gitbook.yaml 第 {number} 行：此检查器只支持 root 和 structure 下的 readme/summary 简单设置。")
                continue
            indent, key, value = match.groups()
            value = value.strip("\"'")
            expected_indent = "  " if key in {"readme", "summary"} else ""
            if indent != expected_indent or (key in {"readme", "summary"} and not in_structure):
                self.fail(f".gitbook.yaml 第 {number} 行：readme 和 summary 应放在 structure 下，并缩进两个空格。")
                continue
            if key in found:
                self.fail(f".gitbook.yaml 第 {number} 行：{key} 设置重复。")
            found[key] = value
            if key in {"root", "structure"}:
                in_structure = key == "structure"
        for key, expected in {"root": "./", "structure": "", "readme": "README.md", "summary": "SUMMARY.md"}.items():
            if found.get(key) != expected:
                self.fail(f".gitbook.yaml：{key} 应设置为 {expected or '包含 readme、summary 的分组'}。")

    def check_book(self) -> None:
        if not (self.root / ".gitignore").is_file():
            self.fail("根目录缺少 .gitignore，请加入生成文件的忽略规则。")
        readme = self.root / "README.md"
        title = re.search(r"^#\s+(.+?)\s*#*\s*$", hide_code(self.documents.get(readme, "")), re.M)
        if not title or title[1] != "中山大学中法核生存手册":
            self.fail("README.md：一级标题应为“中山大学中法核生存手册”。")
        for name in BODY_DIRS:
            directory = self.root / name
            if not directory.is_dir():
                self.fail(f"缺少正文文件夹 {name}/。")
                continue
            for folder in [directory] + [item for item in self.directories if directory in item.parents]:
                if folder / "README.md" not in self.documents:
                    self.fail(f"{self.label(folder)}/：缺少 README.md，请添加该部分的导读入口。")
        summary = self.root / "SUMMARY.md"
        if summary not in self.documents:
            self.fail("根目录缺少可读取的 SUMMARY.md，请加入手册目录。")
            return
        clean = hide_code(self.documents[summary])
        entries = markdown_links(clean)
        linked_lines = {line for line, _ in entries}
        for number, line in enumerate(clean.splitlines(), 1):
            if re.match(r"^\s*(?:[-+*]|\d+[.)])\s+", line) and number not in linked_lines:
                self.fail(f"SUMMARY.md 第 {number} 行：目录条目缺少可读取的正文链接，请使用 [标题](路径.md) 格式。")
        included = set()
        for line, address in entries:
            result = self.exact_path(summary, address, line)
            if result is None:
                if re.match(r"(?:[A-Za-z][A-Za-z0-9+.-]*:|//)", address):
                    self.fail(f"SUMMARY.md 第 {line} 行：目录条目应指向仓库内的 Markdown 正文：{address}")
                continue
            path, fragment = result
            if path not in self.documents:
                self.fail(f"SUMMARY.md 第 {line} 行：目录条目不是可读取的 Markdown：{address}")
            if fragment:
                self.fail(f"SUMMARY.md 第 {line} 行：请将整篇正文作为目录条目，移除标题片段：{address}")
            if path in included:
                self.fail(f"SUMMARY.md 第 {line} 行：同一篇正文重复入目录：{self.label(path)}")
            included.add(path)
        for path in self.documents:
            relative = path.relative_to(self.root)
            if path == readme or relative.parts[0] in BODY_DIRS:
                if path not in included:
                    self.fail(f"{self.label(path)}：正文尚未加入 SUMMARY.md，请补充目录条目。")
        if not entries:
            self.fail("SUMMARY.md：未找到目录链接，请使用 [标题](路径.md) 格式。")

    def check_links(self) -> int:
        count = 0
        anchors = {path: document_anchors(value) for path, value in self.documents.items()}
        for path, value in self.documents.items():
            for line, address in markdown_links(hide_code(value)):
                count += 1
                result = self.exact_path(path, address, line)
                if result is None:
                    continue
                target, fragment = result
                if target.suffix.casefold() == ".md" and target not in self.documents:
                    self.fail(f"{self.label(path)} 第 {line} 行：链接目标无法作为 Markdown 读取：{address}")
                elif fragment and target in anchors and fragment not in anchors[target]:
                    self.fail(f"{self.label(path)} 第 {line} 行：目标正文中找不到标题片段 #{fragment}：{address}")
        return count

    def run(self) -> int:
        if not self.root.is_dir():
            print(f"检查未通过：仓库文件夹不存在：{self.root}")
            return 1
        self.scan()
        self.check_config()
        self.check_book()
        links = self.check_links()
        if self.problems:
            print(f"检查未通过，共发现 {len(self.problems)} 个问题：")
            for number, problem in enumerate(self.problems, 1):
                print(f"{number}. {problem}")
            return 1
        print(f"检查通过：{len(self.documents)} 篇 Markdown、{links} 个链接，目录、入口、文件名与文件格式要求均符合。")
        print("说明：外部网址未联网检查；本地标题片段按 GitHub 常用规则检查。")
        return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="检查中山大学中法核生存手册的文件结构与本地链接。")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="仓库根目录，默认使用脚本所在仓库")
    return Checker(parser.parse_args().root).run()


if __name__ == "__main__":
    raise SystemExit(main())
