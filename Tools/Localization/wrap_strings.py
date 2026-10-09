#!/usr/bin/env python3
r"""把枚举 / 计算属性里的硬编码文案接到 `L(_:)` 上。

`Text("key")` 这类 SwiftUI 字面量由 `.environment(\.locale, …)` 处理,但
`var title: String { return "New Session" }` 不是 `LocalizedStringKey`,SwiftUI
不会查找本地化。这些文案必须显式经过 `L(_:)`。

清单是手工挑选的:只收录用户可见的文案,协议字段、SF Symbol 名、命令行参数、
产品名等技术字符串不在其中。

用法:
    python3 Tools/Localization/wrap_strings.py [--check]

`--check` 只报告还没接上 `L(_:)` 的条目,不做修改。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# 文案在源码里的写法:返回值、命名参数赋值,以及组件的 String 参数。
PREFIXES = ("return ", "title: ", "detail: ", "help: ", "caption: ")

# 文件 → 该文件里需要经过 L(_:) 的文案
WRAPPINGS: dict[str, tuple[str, ...]] = {
    "PiCode/Models/TranscriptItem.swift": (
        "Queued",
        "Running",
        "Done",
        "Failed",
        "Cancelled",
        "Compact context",
        "Branch summary",
        "created",
        "modified",
        "deleted",
        "read",
    ),
    "PiCode/Models/Project.swift": (
        "New session",
        "Modified",
        "Added",
        "Deleted",
        "Renamed",
        "Copied",
        "Untracked",
        "Conflicted",
        "Type changed",
        "Not started",
        "Starting",
        "Connected",
        "Disconnected",
        "Failed",
        "Idle",
        "Working",
        "Compacting",
        "No project resources",
        "Not evaluated",
        "Needs decision",
    ),
    "PiCode/Models/RPCModels.swift": (
        "User: ",
        "Assistant: ",
        "Bash: ",
        "Branch summary",
        "Compaction summary",
    ),
    "PiCode/Models/ExtensionUI.swift": (
        "Choose an option",
        "Confirm",
        "Enter a value",
        "Edit text",
        "Extension request",
    ),
    "PiCode/Models/ProviderDiscoveryTypes.swift": (
        "Enter a valid HTTP or HTTPS endpoint.",
        "The endpoint responded, but did not return any models.",
    ),
    "PiCode/Services/PiProviderService.swift": (
        "API key",
        "API key + environment",
        "Key reference",
        "OAuth",
        "Pi could not load its credential or model configuration",
        "No credentials configured",
        "This Pi does not offer that provider",
        "Not ready",
        "The API key was empty.",
    ),
    "PiCode/Services/PiPackageService.swift": (
        "This Mac",
        "This project",
        "Pi's user settings (~/.pi/agent/settings.json)",
        "The project's .pi/settings.json",
        "Pi was not found, so packages cannot be installed or removed.",
    ),
    "PiCode/Services/PiRPCClient.swift": (
        "The Pi process is not running.",
    ),
    "PiCode/Services/RPCFrameDecoder.swift": (
        "OMP sent invalid RPC chunk metadata.",
        "OMP sent an invalid RPC chunk payload.",
        "OMP interrupted a chunked RPC response.",
        "OMP sent RPC response chunks out of sequence.",
        "OMP's chunked RPC response length did not match its metadata.",
        "OMP's reassembled RPC response was not valid JSON.",
    ),
    "PiCode/Services/PreferencesStore.swift": (
        "System",
        "Light",
        "Dark",
        "Return sends, Shift-Return adds a line",
        "Command-Return sends, Return adds a line",
    ),
    "PiCode/Harness/AgentRuntime.swift": (
        "The agent process is not running.",
    ),
    "PiCode/Harness/LocalHarnessAccountService.swift": (
        "This harness does not expose a local account-status command.",
        "Not signed in",
        "ChatGPT subscription",
        "Local Codex credentials",
        "Codex is signed in.",
        "Run `claude auth login` and choose your Claude subscription.",
        "Claude subscription",
        "Local Claude credentials",
        "Claude Code OAuth is ready.",
        "Claude Code is using its saved account.",
        "Local accounts ready",
        "No local accounts",
        "Unavailable",
        "Account status is unavailable.",
    ),
    "PiCode/Features/Composer/ComposerModelPicker.swift": (
        "Try a provider, model name, or qualified model ID.",
    ),
    "PiCode/Features/Composer/ComposerView.swift": (
        "Pi is not running…",
        "Steer Pi, or queue a follow-up…",
        "Do anything",
    ),
    "PiCode/Features/Composer/TrustViews.swift": (
        "This project is trusted",
        "This project has nothing to load",
        "Waiting for your decision",
        "This project is not trusted",
        "Trust state unknown",
        "Full access",
        "Trust project?",
        "Not trusted",
        "no project resources",
        "waiting for you",
        "not trusted",
        "PiCode asked Pi for the resources this project declares and has not had an answer yet.",
        "Pi is running with `--no-approve`, so this project's resources are ignored.",
    ),
    "PiCode/Features/Conversation/TranscriptRows.swift": (
        "Ran command",
        "Edited file",
        "Read file",
        "Ran commands",
        "Edited files",
        "Read files",
        "Thinking",
    ),
    "PiCode/Features/Session/PiSessionController.swift": (
        "Queue as steering",
        "Queue as follow-up",
    ),
    "PiCode/Features/Session/SessionView.swift": (
        "steers this turn",
        "runs after this turn",
        "The session transcript is still shown. Restart to continue working in this session.",
    ),
}


def wrap_file(path: Path, literals: tuple[str, ...], check_only: bool) -> tuple[int, list[str]]:
    """把裸文案改写成经过 `L(_:)` 的形式,返回改动数与本次触及的文案。"""
    content = path.read_text(encoding="utf-8")
    changed = 0
    touched: list[str] = []

    for literal in literals:
        bare_forms = [f'{prefix}"{literal}"' for prefix in PREFIXES]
        wrapped_forms = [f'{prefix}L("{literal}")' for prefix in PREFIXES]

        # 已经接上 L(_:) 的条目不再处理,避免重复包装。
        if any(form in content for form in wrapped_forms):
            continue

        for bare, wrapped in zip(bare_forms, wrapped_forms, strict=True):
            occurrences = content.count(bare)
            if occurrences == 0:
                continue
            touched.append(literal)
            content = content.replace(bare, wrapped)
            changed += occurrences

    if changed and not check_only:
        path.write_text(content, encoding="utf-8")
    return changed, touched


def main() -> int:
    parser = argparse.ArgumentParser(description="给硬编码文案接上 L(_:)")
    parser.add_argument("--check", action="store_true", help="只检查,不修改")
    args = parser.parse_args()

    total = 0
    for relative, literals in WRAPPINGS.items():
        path = REPO_ROOT / relative
        if not path.exists():
            print(f"[警告] 文件不存在:{relative}", file=sys.stderr)
            continue
        changed, _ = wrap_file(path, literals, args.check)
        total += changed
        action = "待处理" if args.check else "已包装"
        print(f"{action} {changed:>2} 条:{relative}")

    print(f"合计 {total} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
