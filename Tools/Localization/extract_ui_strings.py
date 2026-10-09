#!/usr/bin/env python3
"""提取 SwiftUI 源码中所有用户可见字符串,供汉化使用。

用法:
    python3 Tools/Localization/extract_ui_strings.py [--tsv 输出文件]

输出: 每条记录为 "字符串<TAB>出现次数<TAB>文件:行号,文件:行号..."
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

# 项目根目录(脚本位于 Tools/Localization/ 下)
REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "PiCode"

# SwiftUI 中参数为 LocalizedStringKey 的调用,其字面量会被自动本地化
LOCALIZED_CALLS = (
    "Text",
    "Label",
    "Button",
    "Toggle",
    "Picker",
    "Section",
    "TextField",
    "SecureField",
    "Stepper",
    "Link",
    "Menu",
    "MenuItem",
    "NavigationLink",
    "CommandMenu",
    "CommandGroup",
    "GroupBox",
    "SettingsRow",
    "SettingsSection",
    "RailButton",
)

# 以 `name: "字面量"` 形式传参即被本地化
LOCALIZED_ARG_LABELS = (
    "title",
    "label",
    "subtitle",
    "placeholder",
    "prompt",
    "help",
    "message",
    "description",
    "confirmationTitle",
    "detail",
    "caption",
    "summary",
)

# 修饰符:第一个字符串参数被本地化
LOCALIZED_MODIFIERS = (
    "help",
    "accessibilityLabel",
    "navigationTitle",
    "navigationSubtitle",
    "confirmationDialog",
    "alert",
)

# 字符串字面量:不含插值 \( 的普通引号串
LITERAL = r'"((?:[^"\\]|\\.)*)"'


def build_patterns() -> list[re.Pattern[str]]:
    patterns: list[re.Pattern[str]] = []

    call_names = "|".join(LOCALIZED_CALLS)
    patterns.append(re.compile(rf"\b(?:{call_names})\(\s*{LITERAL}"))

    arg_names = "|".join(LOCALIZED_ARG_LABELS)
    patterns.append(re.compile(rf"\b(?:{arg_names}):\s*{LITERAL}"))

    modifier_names = "|".join(LOCALIZED_MODIFIERS)
    patterns.append(re.compile(rf"\.(?:{modifier_names})\(\s*{LITERAL}"))

    return patterns


# 明显不是自然语言的字符串:SF Symbol 名、标识符、格式串等
def looks_translatable(text: str) -> bool:
    if not text:
        return False
    # 纯符号 / 单字符
    if len(text) < 2:
        return False
    # 不含任何 ASCII 字母(如纯中文、纯符号)
    if not re.search(r"[A-Za-z]", text):
        return False
    # SF Symbol 名称风格:小写点分标识符,如 setting-2 / arrow.up.circle
    if re.fullmatch(r"[a-z0-9]+(?:[.\-][a-z0-9]+)+", text):
        return False
    # 纯小写单词(多为标识符或命令名)
    return not re.fullmatch(r"[a-z0-9_]+", text)


def unescape(swift_literal: str) -> str:
    """还原 Swift 字符串转义,得到真正的本地化 key。"""
    return swift_literal.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def scan_file(path: Path, patterns: list[re.Pattern[str]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = defaultdict(list)
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"[警告] 跳过 {path}:{exc}", file=sys.stderr)
        return found

    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.lstrip()
        # 跳过注释行,避免把文档示例当成 UI 文案
        if stripped.startswith("//"):
            continue
        for pattern in patterns:
            for match in pattern.finditer(line):
                key = unescape(match.group(1))
                if looks_translatable(key):
                    found[key].append(f"{path.relative_to(REPO_ROOT)}:{line_number}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="提取待汉化的用户可见字符串")
    parser.add_argument("--tsv", help="把结果写入该 TSV 文件")
    args = parser.parse_args()

    patterns = build_patterns()
    aggregate: dict[str, list[str]] = defaultdict(list)

    for path in sorted(SOURCE_ROOT.rglob("*.swift")):
        for key, locations in scan_file(path, patterns).items():
            aggregate[key].extend(locations)

    rows = sorted(aggregate.items(), key=lambda item: (-len(item[1]), item[0]))
    total_occurrences = sum(len(locations) for _, locations in rows)

    print(f"唯一字符串: {len(rows)} 条,出现次数: {total_occurrences} 次", file=sys.stderr)

    output_lines = [f"{key}\t{len(locations)}\t{','.join(locations)}" for key, locations in rows]

    if args.tsv:
        Path(args.tsv).write_text("\n".join(output_lines) + "\n", encoding="utf-8")
        print(f"已写入 {args.tsv}", file=sys.stderr)
    else:
        for line in output_lines:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
