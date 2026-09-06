# 1.1.0 回复方法来源

调研日期：2026-09-07。下列为当天 GitHub 实测仓库 stars，代表项目关注度，不是单个 Skill 安装量，也不证明输出质量。采用固定提交，后续上游变化不会自动进入本 Skill。

| 来源 | Stars | 许可证 | 采用内容 |
|---|---:|---|---|
| [blader/humanizer](https://github.com/blader/humanizer/tree/9862685f575c65a8247f90369951df1b3416e3d6) | 44,156 | MIT | 删空话和机械结构，保留原意，内部检查后输出最终稿 |
| [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh/tree/91f3d394db8419c20d67ebe22a96cf8fee0a404b) | 16,768 | MIT | 识别中文套话、过度排比和谄媚表达 |
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills/tree/5b2c0007766c6a1cf1d53fd8fc73e979e0821022) | 47,465 | MIT | copywriting 中客户用词、具体说明和明确下一步的方法 |
| [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins/tree/1f517b9de47e827c80cd933ed364e16838072239/customer-support/skills/draft-response) | 23,908 | Apache-2.0 | 仅参考按渠道调整语气、回应具体影响、说明坏消息与下一步的通用方法；未复制模板、代码或连接器 |

[skills.sh 的 copywriting 页面](https://skills.sh/coreyhaines31/marketingskills/copywriting) 当天显示安装数194.4K。两个 Humanizer 的安装数未核实。不把它们称为“高情商专用 Skill”；本轮没有找到足够可信的热门高情商专门项目，得体沟通采用客户支持任务的方法。

## 合并取舍

- 只融合适用规则，不安装整套第三方 Skill，不增加运行依赖。
- 中文 Humanizer 部分示例会补入原文没有的年份、数据或人物，不采用这种做法。
- 不靠故意错字、虚构经历、刻意方言或情绪来扮演真人。
- 不沿用固定删词数量、强制三项改两项、营销页结构、情商评分或AI检测通过率。
- 新规则只调整客户回复表达，不修改原始证据，不推高退款、交付或付款状态，不添加折扣和期限。
- 保留暂停联系、正式称呼、姓名电话、币种金额、型号日期和否定条件。用户只要一句或正文时遵守。

MIT 来源的版权和许可声明保留在分发包 `references/workflows.md` 末尾。客户场景示例为本 Skill 根据虚构材料编写。
