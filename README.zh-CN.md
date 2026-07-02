# Agnes AI Skills

Agnes AI 模型接入 Skill 官方仓库。

本仓库提供可复用的 Codex skill，用于通过 OpenAI 兼容 API 网关接入 Agnes AI 文本、图像、视频和 Agent 模型。

## 可用 Skill

| Skill | 用途 |
| --- | --- |
| [`agnes-ai-models`](./agnes-ai-models) | 接入 Agnes AI 文本、图像、视频和 Agent 工作流。 |

## 模型覆盖

| 模型 | 类型 | 主要用途 |
| --- | --- | --- |
| `agnes-2.0-flash` | 文本与视觉语言 | 对话、代码、推理、流式输出、工具调用和图像理解 |
| `agnes-image-2.0-flash` | 图像生成 | 快速文生图和图生图 |
| `agnes-image-2.1-flash` | 图像生成 | 更高质量图像生成与编辑 |
| `agnes-video-v2.0` | 视频生成 | 文生视频、图生视频和视频结果轮询 |

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

将 `agnes-ai-models` skill 复制或安装到 Codex skills 目录，然后让 Codex 使用该 skill 处理 Agnes AI API 接入任务。

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

## 语言

- [English](./README.md)
- [简体中文](./README.zh-CN.md)
