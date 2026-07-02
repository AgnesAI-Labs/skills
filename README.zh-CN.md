# Agnes AI Skills

<p align="center">
  <a href="./README.md"><img alt="Language: English" src="https://img.shields.io/badge/LANGUAGE-ENGLISH-0969DA?style=for-the-badge&labelColor=555555"></a>
  <a href="./README.zh-CN.md"><img alt="Language: Simplified Chinese" src="https://img.shields.io/badge/LANGUAGE-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-1F883D?style=for-the-badge&labelColor=555555"></a>
</p>

Agnes AI 模型接入 Skill 官方仓库。

本仓库提供可复用的 Codex skill，用于通过 OpenAI 兼容 API 网关接入 Agnes AI 文本、图像、视频和 Agent 模型。

## 可用 Skill

| Skill | 用途 |
| --- | --- |
| [`agnes-ai-models`](./agnes-ai-models) | 接入 Agnes AI 文本、图像、视频和 Agent 工作流。 |

## 从 GitHub 安装

Codex 用户可以通过指定 skill 目录从本 GitHub 仓库安装：

```bash
python /path/to/install-skill-from-github.py \
  --repo AgnesAI-Labs/skills \
  --path agnes-ai-models
```

如果你的 Codex 环境支持 URL 安装，也可以使用：

```bash
python /path/to/install-skill-from-github.py \
  --url https://github.com/AgnesAI-Labs/skills/tree/main/agnes-ai-models
```

安装后需要重启 Codex，新的 skill 才会被识别。

## 模型覆盖

| 模型 | 类型 | 主要用途 |
| --- | --- | --- |
| `agnes-2.0-flash` | 文本与视觉语言 | 对话、代码、推理、流式输出、工具调用和图像理解 |
| `agnes-image-2.0-flash` | 图像生成 | 快速文生图和图生图 |
| `agnes-image-2.1-flash` | 图像生成 | 更高质量图像生成与编辑 |
| `agnes-video-v2.0` | 视频生成 | 文生视频、图生视频和视频结果轮询 |

## 智能体软件兼容

本仓库按 Codex Skill 格式打包，但 skill 内容也可以给 OpenClaw、Hermes、Manus 以及自定义智能体软件使用。

对于非 Codex 智能体，可以把 [`agnes-ai-models`](./agnes-ai-models) 目录作为接入说明使用：

- 阅读 [`SKILL.md`](./agnes-ai-models/SKILL.md) 获取主要接入流程。
- 使用 [`references/model_catalog.md`](./agnes-ai-models/references/model_catalog.md) 获取模型名称、端点、RPM 说明和 Token Plan 说明。
- 使用 [`references/troubleshooting.md`](./agnes-ai-models/references/troubleshooting.md) 排查常见 API 错误。
- 使用 [`references/agent_compatibility.md`](./agnes-ai-models/references/agent_compatibility.md) 查看 OpenClaw、Hermes、Manus 和通用智能体配置建议。

Agnes AI 使用 OpenAI 兼容 API 网关。大多数支持自定义 OpenAI-compatible provider 的智能体框架，都可以通过设置 Agnes Base URL、API Key 和模型名称来使用 Agnes 模型。

## 使用要求

使用前，每位用户都需要：

1. 注册 Agnes Platform 账号：https://platform.agnes-ai.com/
2. 在平台内申请 Agnes API Key。
3. 在本地把 API Key 保存为环境变量：

```bash
export AGNES_API_KEY="your_api_key_here"
```

不要提交 API Key、Bearer token、`.env` 文件、包含密钥的截图或任何私有客户数据。

## 快速开始

将 `agnes-ai-models` skill 复制或安装到 Codex skills 目录，或在其他支持外部说明的智能体软件中引用该 GitHub skill 目录。然后让智能体使用它处理 Agnes AI API 接入任务。

示例提示词：

```text
Use the Agnes AI Models skill to create a Python example for agnes-2.0-flash.
```

## Skill 覆盖内容

- OpenAI 兼容 Chat Completions
- 流式输出
- `agnes-image-2.0-flash` 和 `agnes-image-2.1-flash` 图像生成
- `agnes-video-v2.0` 视频生成与 `video_id` 轮询
- Tool calling 风格 Agent 工作流
- 常见 API 错误与排查清单
- Token Plan 与 RPM 参考说明

## 官方链接

- 官网：https://agnes-ai.com/
- 文档：https://agnes-ai.com/doc/overview
- 平台：https://platform.agnes-ai.com/
- API Base URL：`https://apihub.agnes-ai.com/v1`
