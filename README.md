# 客户沟通助手

版本：1.0.0。Skill 名称：`customer-conversation-assistant`。

给 Codex 提供客户聊天、文件或截图，整理客户情况、主要顾虑、当前进展、下一步待办，并准备可直接使用的回复。适用于销售、咨询、项目合作和售后等跨行业客户沟通。

## 安装

1. 从 [v1.0.0 下载页](https://github.com/ssqaq/customer-conversation-assistant/releases/tag/v1.0.0) 下载 `customer-conversation-assistant-1.0.0.zip` 并解压。
2. 将完整的 `customer-conversation-assistant` 文件夹放入 Codex 用户级 Skill 目录：
   - Windows：`%USERPROFILE%\.codex\skills\`
   - macOS / Linux：`~/.codex/skills/`
   - 自定义了 `CODEX_HOME` 时：`$CODEX_HOME/skills/`
3. 重启 Codex，在新对话中调用。

也可以下载本仓库，使用其中的 `customer-conversation-assistant/` 文件夹安装。该文件夹只有三个 Skill 文件，不需要安装脚本或服务。

## 调用

```text
$customer-conversation-assistant 分析这些客户聊天，告诉我客户在意什么、下一步怎么跟进，并帮我写一段回复。

这里放客户聊天记录。
```

也可以要求提取待办、分析客户顾虑、处理售后争议、准备久未联系的开场白，或分别整理多个客户。

## 保存规则

- 默认只在对话中分析，不主动生成客户档案。
- 明确要求“保存这份分析”时，保存单份报告。
- 明确要求“建档”时，建立客户独立目录，保存 `profile.md`、`tasks.md`、`history.md`。
- 明确要求“更新档案”时，读取已关联档案，保存完整旧快照，再更新有依据的内容。
- 用户指定目录优先；默认报告在当前工作区 `outputs/`，客户档案在 `outputs/customers/`。
- 保留原始姓名、联系方式及相关业务信息，不强制脱敏。

## 使用范围

需要使用者提供当前环境能够读取的材料。此 Skill 不自带微信自动读取、WorkBuddy 连接或 OCR 服务，不承诺跨会话自动记忆。回复草稿默认交给使用者，不自动发送给客户。

本版本完成了本地格式校验、跨行业虚构记录分析、档案保存和更新、固定快照恢复及受控真实进程中断测试。真实微信、WorkBuddy、截图 OCR 与不同模型环境尚未实测。

## 文件

```text
customer-conversation-assistant/
  SKILL.md
  references/workflows.md
  agents/openai.yaml
```

本仓库保存 Skill 和使用说明；发布页 ZIP 仅包含三个 Skill 文件，不包含客户聊天、客户档案或评审过程记录。
