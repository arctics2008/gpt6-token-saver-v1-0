#!/usr/bin/env python3
"""Install the sibling skill and merge only the requested Codex settings. Python 3.11+."""
import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

try:
    import tomllib
except ImportError:
    sys.exit("需要 Python 3.11+；请用 python3.11 或更新版本运行本文件。")

LEVELS = ("low", "medium", "high", "xhigh", "max", "ultra")
NAME = "gpt6-token-saver-v1-0"


def merge_config(original, desired):
    """Preserve unrelated content; refuse unusual layouts rather than guess."""
    expected = copy.deepcopy(tomllib.loads(original))
    result = original
    for section, values in desired.items():
        node = expected
        if section:
            for part in section.split("."):
                node = node.setdefault(part, {})
                if not isinstance(node, dict):
                    raise ValueError("目标配置项不是 TOML 表，未修改配置。")
        node.update(values)
        headers = list(re.finditer(r"(?m)^[ \t]*(\[\[?[^\n]+?\]\]?)[ \t]*(?:#[^\n]*)?$", result))
        if section:
            matches = [h for h in headers if h.group(1) == "[" + section + "]"]
            if not matches:
                result = result.rstrip() + "\n\n[" + section + "]\n"
                start, end = len(result), len(result)
            else:
                header = matches[0]
                start = header.end()
                end = next((h.start() for h in headers if h.start() > header.start()), len(result))
        else:
            start, end = 0, headers[0].start() if headers else len(result)
        block = result[start:end]
        for key, value in values.items():
            line = key + " = " + json.dumps(value, ensure_ascii=False)
            pattern = r"(?m)^[ \t]*" + re.escape(key) + r"[ \t]*=[^\n]*$"
            if re.search(pattern, block):
                block = re.sub(pattern, lambda _: line, block)
            else:
                block = block.rstrip() + "\n" + line + "\n"
        result = result[:start] + block.rstrip() + "\n\n" + result[end:]
    if tomllib.loads(result) != expected:
        raise ValueError("配置使用了无法安全保留的写法；未写入。请按 config.example.toml 手动合并。")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--astra", choices=LEVELS, default="medium")
    parser.add_argument("--sol", choices=LEVELS, default="medium")
    parser.add_argument("--context-config", choices=("stdin",))
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))))
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".agents" / "skills")
    args = parser.parse_args()
    context = {"features": {"context_management": {"experimental_mode": True}}}
    if args.context_config and tomllib.loads(sys.stdin.read()) != context:
        parser.error("标准输入必须仅包含 [features.context_management] experimental_mode = true。")
    desired = {
        "": {"model": "gpt-6-astra", "model_reasoning_effort": args.astra},
        "agents": {"enabled": True, "default_subagent_model": "gpt-5.6-sol", "default_subagent_reasoning_effort": args.sol},
        "features.context_management": {"experimental_mode": True},
    }
    root = Path(__file__).resolve().parent
    sources = [root / NAME / "SKILL.md", root / NAME / "agents" / "openai.yaml"]
    target = args.skills_dir.expanduser().resolve() / NAME
    config = args.codex_home.expanduser().resolve() / "config.toml"
    original = config.read_text(encoding="utf-8") if config.exists() else ""
    candidate = merge_config(original, desired)
    writes = [(config, candidate)] + [(target / p.relative_to(root / NAME), p.read_text(encoding="utf-8")) for p in sources]
    # Preflight every target before any write. Existing modified skills require manual handling.
    for dest, content in writes[1:]:
        if dest.exists() and dest.read_text(encoding="utf-8") != content:
            sys.exit("发现同名 Skill 文件且内容不同，未覆盖：" + str(dest))
    if original != candidate and config.exists():
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = config.with_name("config.toml.gpt6-backup-" + stamp)
        shutil.copy2(config, backup)
        backup.chmod(0o600)
        print("配置备份：", backup)
    for dest, content in writes:
        if dest.exists() and dest.read_text(encoding="utf-8") == content:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=dest.parent, delete=False) as output:
            output.write(content)
            temporary = Path(output.name)
        try:
            temporary.replace(dest)
        finally:
            temporary.unlink(missing_ok=True)
    print("已安装：", target)
    print("已配置：Astra=" + args.astra + "，Sol=" + args.sol + "，context_management=true")
    print("重新打开 Codex；已有任务须手动选 GPT-6 Astra 和对应推理强度。")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        sys.exit("安装未完成：" + str(error))
