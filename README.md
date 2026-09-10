# 客户沟通助手

版本：1.2.0。Skill 名称：`customer-conversation-assistant`。

给 Codex 提供客户聊天、文件或截图，整理客户情况、主要顾虑、当前进展、下一步待办，并准备可直接使用的回复。适用于销售、咨询、项目合作和售后等跨行业客户沟通。

1.2.0 增加输出模式锁定、截图和微信合并转发的归属规则，并升级 GitHub Actions。1.1.1 的“高情商”规则仍保留：先接住具体问题，再讲事实和下一步，不靠夸赞、长篇安慰或额外承诺显得客气。

## 安装

1. 从 [v1.2.0 下载页](https://github.com/ssqaq/customer-conversation-assistant/releases/tag/v1.2.0) 下载 `customer-conversation-assistant-1.2.0.zip` 并解压。
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

```text
$customer-conversation-assistant 帮我回这个客户，自然一点，有分寸，不要套话；保留事实和条件，只给能发出去的正文。

$customer-conversation-assistant 把下面这段客户回复改得少点AI味，别改价格、日期和承诺。
```

一般文章润色和无客户背景的通用文案不套用客户分析模板，也不应靠普通文章触发客户沟通 Skill。自然表达规则来源见 [来源与取舍](docs/SOURCES.md)。

“高情商回复”在这里指：回应具体处境，讲清能确认的事实，给出有依据的下一步。它不等于夸赞、长篇安慰或编造优惠、退款和交期。规则回归记录见 [1.1.1 回复验证](docs/REPLY-VALIDATION-1.1.1.md)。

## 保存规则

- 默认只在对话中分析，不主动生成客户档案。
- 明确要求“保存这份分析”时，保存单份报告。
- 明确要求“建档”时，建立客户独立目录，保存 `profile.md`、`tasks.md`、`history.md`。
- 明确要求“更新档案”时，读取已关联档案，保存完整旧快照，再更新有依据的内容。
- 用户指定目录优先；默认报告在当前工作区 `outputs/`，客户档案在 `outputs/customers/`。
- 保留原始姓名、联系方式及相关业务信息，不强制脱敏。

## 使用范围

需要使用者提供当前环境能够读取的材料。此 Skill 不自带微信自动读取、WorkBuddy 连接或 OCR 服务，不承诺跨会话自动记忆。回复草稿默认交给使用者，不自动发送给客户。

1.0.0 已完成基础分析、档案保存更新、固定快照恢复及受控进程中断测试。1.1.0完成29项打包与发布自动测试，以及10个虚构客户回复场景检查；这些是单次验证端的结果，不是多模型或 CI 自动生成的质量分数。1.1.1 增加高情商边界和触发回归，1.2.0 增加输出模式、截图和合并转发回归设计，详见 [回复验证记录](docs/REPLY-VALIDATION.md)、[1.1.1 回复验证](docs/REPLY-VALIDATION-1.1.1.md) 与 [1.2.0 验证计划](docs/REPLY-VALIDATION-1.2.0.md)。真实微信、WorkBuddy、截图 OCR 和多模型效果仍需按新计划实测。

## 文件

```text
customer-conversation-assistant/
  SKILL.md
  references/workflows.md
  agents/openai.yaml
```

本仓库保存 Skill 和使用说明；发布页 ZIP 仅包含三个 Skill 文件，不包含客户聊天、客户档案或评审过程记录。

## 自动校验与发布

main 和 PR 自动在 Windows、Linux 校验格式、引用、版本并测试打包。推送版本标签后，两平台构建包一致、GitHub draft 附件下载回查通过，才正式发布；失败不会自动放出正式包。已发布版本不覆盖。

构建脚本和测试只存在于仓库外围，不进入 Skill ZIP。[查看运行记录](https://github.com/ssqaq/customer-conversation-assistant/actions/workflows/release.yml)，操作方法见 [发布说明](docs/RELEASING.md)。仓库公开后不要把真实客户聊天、档案、电话、付款信息或截图发到 issue、PR、讨论区或文档；本地按用户明确要求保留原始资料的规则不变。
