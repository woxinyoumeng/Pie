#!/usr/bin/env python3
"""把中文翻译表转换成 Xcode 的 String Catalog。

翻译表 `zh-Hans.json` 只维护 `"英文原文": "中文译文"` 的映射,格式细节由本脚本
负责,避免手工编辑 `Localizable.xcstrings` 时写错 JSON 结构。

用法:
    python3 Tools/Localization/build_catalog.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSLATION_TABLE = Path(__file__).resolve().parent / "zh-Hans.json"
CATALOG = REPO_ROOT / "PiCode" / "Localizable.xcstrings"

# 中文语言代码,与 PreferencesStore.AppLanguage.chinese 保持一致
CHINESE = "zh-Hans"
SOURCE_LANGUAGE = "en"


def load_translations() -> dict[str, str]:
    """读取翻译表,并校验键值都是非空字符串。"""
    try:
        raw = json.loads(TRANSLATION_TABLE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[错误] 找不到翻译表:{TRANSLATION_TABLE}", file=sys.stderr)
        raise SystemExit(1) from None
    except json.JSONDecodeError as exc:
        print(f"[错误] 翻译表不是合法 JSON:{exc}", file=sys.stderr)
        raise SystemExit(1) from None

    if not isinstance(raw, dict):
        print("[错误] 翻译表顶层必须是对象", file=sys.stderr)
        raise SystemExit(1)

    translations: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            print(f"[错误] 键和值都必须是字符串:{key!r}", file=sys.stderr)
            raise SystemExit(1)
        if not key.strip():
            print("[错误] 存在空的英文原文", file=sys.stderr)
            raise SystemExit(1)
        if not value.strip():
            print(f"[错误] {key!r} 的译文为空", file=sys.stderr)
            raise SystemExit(1)
        translations[key] = value
    return translations


def build_catalog(translations: dict[str, str]) -> dict[str, object]:
    """组装 String Catalog 结构;键按字母序排列,让 diff 保持稳定。"""
    strings: dict[str, object] = {}
    for key in sorted(translations):
        strings[key] = {
            "localizations": {
                CHINESE: {
                    "stringUnit": {
                        "state": "translated",
                        "value": translations[key],
                    }
                }
            }
        }
    return {
        "sourceLanguage": SOURCE_LANGUAGE,
        "strings": strings,
        "version": "1.0",
    }


def main() -> int:
    translations = load_translations()
    catalog = build_catalog(translations)
    CATALOG.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"已写入 {CATALOG.relative_to(REPO_ROOT)}:共 {len(translations)} 条译文")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
