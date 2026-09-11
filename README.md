# GPT6省token工具v1.0

一个极简 Codex Skill：只使用 GPT-6 Astra 与 GPT-5.6 Sol。

- Astra：理解需求、规划、架构决策、任务拆分、最终验收。
- Sol：仓库读取、编码、前端实现、调试、测试、重构等执行工作。
- Astra 与 Sol 默认均使用 `medium` 推理强度，可分别选择。
- 不使用 Terra 或 Luna。
- 安装时启用 `[features.context_management] experimental_mode = true`。

## 一条命令安装

需要已安装 Git、Codex 和 Python 3.11+。以下命令会临时下载仓库并安装 Skill；默认 Astra 与 Sol 均为 `medium`：

```bash
install_dir="$(mktemp -d)" && git clone --depth 1 https://github.com/arctics2008/gpt6-token-saver-v1-0.git "$install_dir/repo" && python3 "$install_dir/repo/install.py" --astra medium --sol medium
```

可将两个 `medium` 分别改为 `low`、`medium`、`high`、`xhigh`、`max` 或 `ultra`。实际支持范围取决于目标电脑上的 Codex 版本和账号。

安装脚本会：

- 安装到 `~/.agents/skills/gpt6-token-saver-v1-0/`；
- 设置新任务默认模型为 `gpt-6-astra`；
- 设置子代理默认模型为 `gpt-5.6-sol`；
- 分别写入 Astra 与 Sol 的推理强度；
- 启用子代理及实验性 context management；
- 修改前备份现有 `config.toml`，并保留无关配置。

重新打开 Codex，在新任务中调用：

```text
使用 $gpt6-token-saver-v1-0，帮我处理以下任务：……
```

Skill 是工作流指令，不能把 Codex 的全局模型列表变成硬白名单。若当前主任务不是 Astra，或 Sol 无法使用，它会停止并说明原因，不静默改用其他模型。

更多细节见 [安装说明](./安装说明.md)，默认配置见 [config.example.toml](./config.example.toml)。
