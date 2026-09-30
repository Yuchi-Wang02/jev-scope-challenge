# jev-scope-challenge 深度审计报告（2026-09-30）

> 本报告由 Claude Code 的多智能体审计流程生成（AI 执行、未经人工复核），它本身也是知道结果的回顾性分析。报告只增加文档，不修改任何冻结文件、结果或分数。

- **审计对象**：GitHub `Yuchi-Wang02/jev-scope-challenge`，审计基线为 HEAD `022950f`（“Publish completed rule-direction diagnostic and pause exploration”）。
- **审计方式**：只读审计。在副本上完整跑了 CI（64 条命令全部 exit 0，315 个单元测试通过，build 类命令不产生 git diff）；对 17 个研究单元分别从原始 jsonl/csv 独立复算；另做 6 个横向维度的专项核查（文档、git/GitHub 服务器取证、许可与隐私、工程、外部文献与新颖性、统计）和 3 个视角的研究价值评估；再对候选问题做对抗核查（major 候选从证据、披露、影响三个视角各核一次，minor 候选做证据核查），最后补查了 7 个缺口。审计没有调用付费 API，没有下载模型权重，也没有在 GitHub 上做任何写操作。
- **写法约定**：证据写成仓库相对路径加行号，英文原文保留英文。每个问题都标明披露状态：**已披露**（仓库自己写过）、**已披露但被低估或埋没**、**未披露**。

---

## 0. 一页结论（TL;DR）

1. **做了什么**：两天内共 114 次提交（2026-09-29 07:40 到 09-30 10:49，-0400），在约 20 个研究目录里做了 17 个可审计的单元。这些单元把“现有小模型能否不经新训练成为可靠的软件决策组件”这个长期问题拆成一串小型、事先冻结的诊断，主线依次是取消范围、Kev 同底座对照、证据充分性、证据归属、候选完整性、公开数据（ShARC/QA4PC）和规则方向（if/only-if）。Jev 共调用约 1,200 次，付费总额不到 0.03 美元；本地 GPU 时间以分钟计。
2. **可复现性和透明度很好，属同类少见**：CI 全绿；所有被核对的头条数字都能从原始记录独立复算出来；**没有发现报告数字与原始数据矛盾，也没有分母错误、标签泄露或评分 bug**。GitHub 服务器端记录显示，16/16 个推理研究的冻结提交都在首次模型调用之前 5–25 秒公开推送，历史未被改写。
3. **没有 critical 级问题**。核实成立的 **major 问题有 5 个**：
   - (M1) 原生路径的 BF16 logits 大量精确并列，并列按候选位置打破，这一规则既没声明也没计数；
   - (M2) 最直接的先例 SemIf（冻结 Qwen3.5-4B 原生 logits 对标 Jev）没有被当作最近邻工作来定位；
   - (M3) Kev 研究的主布局 L0 并非 Kev 检查点的原生训练格式，恰好是最不原生的一种，而仓库把它称作 conventional；
   - (M4) 系列层面从没总结“同输入 6 组 Jev 对 Qwen 比较中 Jev 5 胜 1 平 0 负”，首屏反而以唯一的平局开头；
   - (M5) Qwen3.5 的头条在顶层没有写明所用配置，7 个 Jev 对 Qwen 头条里没有一个用了模型卡默认的 thinking 模式和推荐的预算。
   另有约 110 条 minor、约 90 条 info。
4. **科学分量远小于工程分量**：每个研究的独立单位通常只有约 12 个（parent、tree 或词汇族），检测 20pp 差异的功效只有 3–6%。Holm 校正后没有任何一项单独的 Jev 对 Qwen 比较显著。已知语法程序在所有合成任务上都拿满分（12/12、48/48、72/72、24/24、216/216、108/108），所以这些任务回答不了“是否需要模型”。人工评审几乎是空的：约 828 项待评，非作者只完成 96 项。
5. **最有价值的四个发现**：
   - (a) “证据不足或目标有歧义时仍给出确定答案”在多个研究里反复出现：Qwen 加推理后 12/12；Kev pointer 在决定性删除上只对 3/36；14/18 个缺失字段被填上了值；Jev 对歧义目标给出 VALID=0.97；规则方向上错误承诺 24/60。
   - (b) 请求归属和字段读取可以分开：目标行 99/100 读对，但外来行有 85/100 被当作证据；加一个确定性 ID 门，结果从 2/24 升到 23/24。
   - (c) 读出和接口本身会决定结论：挪动一个分隔符就翻转了 7.3% 的决策；严格格式门把 24/24 的正确内容判成 11/24；有限选择读出坍缩成常数 Yes。
   - (d) 仓库有数据却没用的 **Jev 置信度信号**：在规则方向研究里，用置信度区分对错的 AUROC 为 0.974（Qwen 为 0.802）。
6. **长期问题仍然开放**：在所有测过的冻结 4B 配置里，没有一个追平 Jev（方向性结论，存在混杂）；但也没有证据证明需要 Jev，因为程序已满分，Jev 与 copy-last 等平凡基线在树层面也无法区分。
7. **评分**：工程与透明度 8/10；科学证据强度 3–4/10；**研究价值综合 5/10**（学术、工业、策略三个视角分别为 4、5.5、5.5）。按现状可以发 arXiv 技术报告或数据审计短文，离主会论文还远。
8. **建议**：停止继续加小型诊断。先做零成本的补全：选择性预测分析、聚类统计、文献定位、在头条旁并列平凡基线、写明配置。然后把规则方向（C20）扩展成一项预注册、带人类基线和多模型的核心实验。优先解决人工评审人力。上述条件满足后，再在程序无法满分的自然语言材料上做一次确认性研究。

---

## 1. 项目是什么

### 1.1 被比较的对象

| 名称 | 是什么 | 在本仓库中的用法 |
|---|---|---|
| **Jev** | TypeSafe 托管的专用决策模型 `jev-1.13.0`，“System One model”，非生成式；Choice API 返回所选项、各选项概率和 confidence；输入按 $0.042/百万 token 计费，输出免费；2026-09-15 开放早期访问 | 实时调用，保留原始概率 |
| **Kev** | `jaredpalmer/kev`，“Small Jev-like decision models you can train and run yourself”；rank-16 LoRA 加 pointer head。本仓库用的是历史检查点 `kev-4b@c4bfa11`（Qwen3-4B-Base 底座，源码 `29d71c7`） | N0 = Base 原生 logits；N1 = Base+Kev LoRA、原生 logits；K1 = Kev pointer head |
| **Qwen3-4B / Qwen3.5-4B** | 冻结的开源模型，不做新训练 | 早期用 Qwen3-4B（关闭 thinking，首 token 字母 logits）；后期用 Qwen3.5-4B（有限选择 prefill、贪心生成、语义标签、thinking 等多种接口） |
| **已知语法程序** | 为每个构造语法专门写的正则/解析器加规则执行器，零模型调用 | 各研究的强零模型对照 |
| **平凡基线** | always-keep/defer/maybe、常数标签、copy-last（复制最后一条历史回答） | 各研究的弱对照 |

### 1.2 长期问题与作者自设的门槛
- README.md:39-40：“The longer-term question is whether existing small models can become reliable software decision components without new training. That question remains open.”
- STAGE_LOG.md:665-666 给出的研究顺序：inspectable phenomenon → separately reviewed new-material test → fair controls and inference costs → mechanism/intervention 或 bounded negative result。**到目前为止，没有一个现象进入第二步。**
- 论文门槛（research/candidate-completeness/NEXT_RESEARCH_GATES.md:86-92）三选一：validated diagnostic、带强基线的 transferable intervention、carefully established replacement boundary。作者自评（STAGE_LOG.md:670-671）：“have not yet met the gate for a general replacement or novel-method paper”。

### 1.3 系列演化脉络
- **原名**：“You Might Not Need Jev”（PROTOCOL.md:3 仍保留）。这是一个偏向小模型的假设。它在 `db233ba`（09-29 23:40）中被悄悄从 README 删掉，CHANGELOG 没有说明，也从没给出结论。
- 各阶段：
  1. **取消范围**：Jev 对冻结 Qwen3-4B，12/12 对 8/12。
  2. **同底座 Kev（N0/N1/K1）与布局边界**：想弄清差距来自参数适配、表示还是读出。
  3. **证据充分性**：evidence-gap（决定性与非决定性删除），evidence-guards（门控），fact-execution（事实抽取加执行器）。
  4. **证据归属**：line/joint 试点失败，事后回放可见 ID 门，request-ownership（同前缀 ID 目标切换）。
  5. **回到实时 Jev**：payment-ownership（tau2 退款目的地），candidate-completeness（候选覆盖），decision-sufficiency（谓词与身份的可执行规格，零调用）。
  6. **Qwen3.5 基础设施与公开数据**：baseline-readiness、generation-calibration、action-backends，ShARC 评审包与 dev 源标签筛查，finite-choice，EXtrA/QA4PC 审计，QA4PC 阶段归因与六向答案接口。
  7. **规则方向（if / only if / iff）**：两个后端都是 84/108，并犯同样的 24 个错；按用户指示暂停。
- 主线的变化：从“模型能不能判断”，变成“模型在抽取环节提供的价值是否大于它带来的错误”，再变成“可靠性取决于规格、契约和接口，还是取决于模型”。

---

## 2. 目前做了什么

### 2.1 时间线（UTC；F=冻结提交，C=首次模型调用，R=结果提交）

| 研究 | F | C | R | F→R | 修订/停止 |
|---|---|---|---|---|---|
| 原始取消范围 | 2c08d9b 09-29 11:41:45（0850edf 11:40:56 早 49 秒） | 11:42:16 | 0f83402 11:47:11 | 5.4 分 | 调用前做了 1 次 CRLF 哈希修订；GitHub 仓库 11:47:25 才创建，prereg 标签在 09-30 05:11 才推送 |
| next-study（Kev） | 9999005 12:51:04；v0.2 c9deeb4 12:56:47 | 无时间戳 | a0104a6 13:10:53 | 19.8 分 | v0.1 在 K1 parity 门处停止，v0.2 为看结果后修订（已披露） |
| layout-boundary | 124ffa6 13:38:19 | 13:38:34 | 8acce50 13:49:52 | 11.6 分 | 0 |
| evidence-gap | 4809a5b 14:08:03 | 14:08:20 | 4347039 14:25:02 | 17.0 分 | 冻结前修复（未用模型） |
| evidence-guards（事后，无调用） | 48e8d95 14:33:52 | — | 30c5d29 14:44:19 | 10.4 分 | 设计本身即事后 |
| fact-execution | 548e00f 15:50:27 | 15:50:43 | 2900349 16:00:43 | 10.3 分 | 0 |
| line-evidence 试点 | 66513e5 22:16:25 | 22:17:19 | 87a500e 22:21:24 | 5.0 分 | 筛选失败 |
| joint-routing 试点 | 2eae43d 23:06:52 | 09-30 02:07:34 | 6de8be4 02:22:11 | 195 分 | 两项筛选均失败；ID 门回放 4fb4ba3 02:38 |
| request-ownership | d714de2 02:49:47 | 03:05:57 | 56a9882 03:14:19 | 24.5 分 | 0（通过） |
| payment-ownership | 0569f8d 04:55:09 | 04:55:17 | 8e31b7d 05:05:33 | 10.4 分 | smoke 停止后做 1 次看结果修订（v0.2）；两份评审 05:44–06:40 |
| candidate-completeness | 680fb6f 06:46:39 | 06:50:06 | 67583ee 07:06:06 | 19.4 分 | 追加 Qwen 冻结 c327d59 |
| 推理对照 | db2837c 07:11:29；v2 4527534 07:15:17 | 07:11:52 | 8d0bf35 07:40:06 | 28.6 分 | 采样偏差修复为 greedy |
| decision-sufficiency | a9d82d6 07:55:40（单次提交） | — | — | — | 无模型 |
| Qwen3.5 冒烟/校准/动作 | 9ec62b8 08:19 → 2ee64ac 08:30；e907e7c 08:40 → 1a92746 08:50；6f26707 09:20 → 1c5f9ea 09:26 | — | — | 约 10 分 | 3 次技术修订 |
| ShARC 评审准备 | 队列冻结 26e698b 09-30 00:10；公开包 8eb67cf 09:10 | 无 | — | — | 0 份评审，0 次调用 |
| source-label-screen | e90f051 10:51:48 | 10:52:16 | 74a22f0 11:50:20 | 58.5 分 | 2 次停止，2 次看结果后读出修复 |
| finite-choice | 47d77bd 12:09:56 | 12:10:21 | 628c508 12:15:19 | 5.4 分 | 设计即看结果后 |
| EXtrA/QA4PC 审计 | a9ba706 12:27；d7b2ec2 12:44 | — | — | — | 零调用 |
| QA4PC 阶段归因 | 543899f 12:59:37；续跑 cebac57 13:16:31 | 12:59:57 | d9bc5ad 13:26:24 | 26.8 分 | Qwen smoke 停止后做看结果门槛修订 |
| QA4PC 答案接口 | eba5ba4 13:46:42 | 13:47:01 | af2a269 13:56:40 | 10.0 分 | 0；源审计 d838b52 14:19 |
| rule-direction | 5bd9675 14:36:08 | 14:36:35 | 022950f 14:49:15 | 13.1 分 | 0；暂停 |

- 相邻提交间隔中位数 9.7 分钟，有 34 次提交在当地时间 00:00–07:00。
- 103/114 次提交在本地提交后 2–38 秒内推送。79 次推送全部是 fast-forward，没有 force-push。

### 2.2 研究清单总表（17 个单元）

| # | 研究（目录） | 问题 | 数据/规模 | 模型 | 主结果 | 状态 |
|---|---|---|---|---|---|---|
| 1 | 原始取消范围（根目录） | 同词不同义时能否判对目标服务的 CANCEL/KEEP | 48 条合成消息，12 个四变体 parent（3 族）；96 决策 × 2 轮 | Jev；Qwen3-4B 首 token logits | 完整案例 Jev 12/12，Qwen 8/12；程序 12/12 | 已完成，冻结 |
| 2 | next-study | 同底座下 LoRA 与 pointer 各自的作用 | 24 parent（实为 6 个逻辑模板）×4 视图×3 顺序 | N0/N1/K1 | 测试集 85/111/98 /144；完整 parent 0/1/0；缺失误承诺 36/29/35 /36 | v0.1 停止，v0.2 完成 |
| 3 | layout-boundary | 排序是不是由输入布局造成的 | 同一语料 × L0/L1/L2 | N0/N1/K1 | K1 98→119→127；N1 111→121→121；L1→L2 只翻转 K1 的 21/288 | 完成 |
| 4 | evidence-gap | 能否区分决定性与非决定性删除 | 12 个 dev parent × 6 视图 × 3 顺序 = 216 | N0/N1/K1 | K1 非决定性 31/36，决定性 3/36，配对 1/36；FC 55–68/72 | 完成（dev only） |
| 5 | evidence-guards + 成本页 | 门控能否去掉无依据承诺，代价是什么 | 复用 648 条 + fact-execution 数据 | 同上 + 程序 | K1+policy gate 172/216，FC 0，残余错误动作 26；纯代码 216/216 | 事后分析 |
| 6 | fact-execution | 只抽取类型化事实再交给执行器，是否更可靠 | 72 文本；168 字段 | N0/N1/K1 | N1 31→44/72；14/18 缺失字段被断言为值；事实向量完全正确 33/72 | 完成 |
| 7 | line/joint 试点 + ID 门审计 | 逐行分类或互斥路由能否降低错误承诺 | 同 72 文本；548/514 次前向 | N1 | line 29/72；joint 34/72（两项筛选失败）；外来行 60/66 被误路由；ID 门回放 70/72 | 失败并公开 |
| 8 | request-ownership | 可见 ID 门能否修正归属错误 | 24 场景 / 48 视图；500 次前向 | N1 | joint 2/24 → gated 23/24，FC 7/12→0/12；直接判决 2/24；程序 24/24 | 预设方向性判据通过 |
| 9 | payment-ownership | 外来订单记录会不会误导 Jev 判断退款目的地 | tau2 零售库 12 个用户、48 输入、192 次主调用 | Jev | 6 个单元格全部 48/48；smoke 5/6（歧义目标 VALID 0.97） | 关闭（STOP_NO_FOLLOWUP） |
| 10 | candidate-completeness + 推理对照 | 候选覆盖声明改变时，是否只在应改判时改判 | 12 parent × 6 输入 = 72，两种映射 | Jev；Qwen3-4B 原生；512 token greedy 思考 | Jev 63 与 67（/72，两种映射），FC 0/12，不必要延迟 9 与 5；Qwen 34 与 30，FC 12/12；推理 58 与 59，FC 仍为 12/12；程序 72/72 | 关闭 |
| 11 | decision-sufficiency | “谓词确定”与“身份确定”能否拆开写成接口规格 | 20 个示例，730+180 个枚举合约 | 无 | 7/20 例两种接口输出不同；审计 0 处不一致 | 规格原型 |
| 12 | Qwen3.5 基础设施 | 普通对照模型能否可审计地加载、生成和解析 | 6+48+8 次生成 | Qwen3.5-4B；Jev 8 次 | thinking 严格有效 11/24（13 个 JSON 围栏，内容全对）；动作复制 8/8 | 基础设施 |
| 13 | ShARC 外部验证准备 | 人工参考先于推理的配对比较 | 3,334 对清单；30 对/60 项评审包 | 无 | 0 份评审，0 次调用 | 暂停 |
| 14 | ShARC 源标签筛查 + finite-choice | 一个历史回答变化时，决策是否跟着变 | 12 棵 dev 树，24 输入 × 2 顺序 | Jev；Qwen3.5 direct/thinking/prefill | Jev 18/24；Qwen direct 11–12；thinking 5–6（37/48 截断）；copy-last 14；prefill 13 与 10（/24；order1 等于常数 Yes） | 关闭 |
| 15 | EXtrA/QA4PC 审计 + 阶段归因 | 已有数据能否作为支架；错误来自读事实还是组合 | EXtrA 100 对；QA4PC 437 场景；阶段研究 12 树/24 场景 | Jev；Qwen3.5 prefill | EXtrA 确定性上限 198/200；QA4PC 429/429 可复现；Jev G 20/24（两种映射相同），Qwen D 13 与 19（/24）等 | 关闭 |
| 16 | QA4PC 答案接口 | 差距有多少来自输出接口 | 新 12 树/24 场景 × 6 映射 | Jev；Qwen3.5 三条路线 | 101/85/89/87 /144；字母桥 162/162 logits 相同；源审计标记 8/24 | 关闭 |
| 17 | rule-direction | 连接词在 if/only if/iff 间变化时，决策是否跟着变 | 12 词汇族 × 3 关系 × 3 事实 = 108 × 2 | Jev；Qwen3.5 greedy 语义标签 | 两个后端都是 84/108，24 个错误相同（216/216 输出一致）；always-maybe 60；程序 108 | 完成，暂停 |

### 2.3 各研究详述

#### 2.3.1 原始研究：Cancel the Right Thing
- **做了什么**：手写 48 条消息，组成 12 个四变体 parent，分三族：S 对象范围、Q 引用示例与实际请求、T 作废与当前请求。同一 parent 内四条文本的词多重集相同（core.py:59-60 有断言）。每条文本在两种字母映射下各问一次，共跑两轮。Jev 用原生 Choice 概率，Qwen3-4B（1cfa9a72，BF16，关闭 thinking）读 A/B 两个首 token 的 logits。对照是 always-keep、关键词规则和已知语法解析器。
- **结果**：完整案例 Jev 12/12、Qwen 8/12、程序 12/12；逐决策 96 对 83；Qwen 错误取消 10/48、漏取消 3/48；映射分歧 1/48；两轮之间 0 分歧；Brier 0.000106 对 0.134289；案例层 bootstrap [-0.583, -0.083]；Jev 花费 $0.003762（results/REPORT.md:3-56）。
- **作者自述局限**：只有 48 条合成输入，没有人工标签；程序能全部解出；读出和托管方式不同；bootstrap 只是重加权敏感性分析；冻结只在本地完成，没有外部时间戳（REPRODUCIBILITY.md:115-118）。
- **审计复算**：全部一致，包括 384 行 decisions.csv 和 26 行错误表。补充几点：Qwen 的 13 个错误**全部在 S 族**（S 族 19/32，flip 对 3/16，S03/S04 共 16 个决策全部输出 CANCEL，与关键词规则逐条相同）；7 条错判文本的金标都没有歧义；客户端请求 192/192 严格对等，但 Jev 服务端每次多约 270 个输入 token、生成 31 个输出 token；Jev 概率只精确到 0.01。见 F02、F59、G-O1~O4。

#### 2.3.2 next-study：同底座 N0/N1/K1
- **做了什么**：生成 24 个 parent，每个有 full/hold/flip/missing 四个视图，按 3 种循环候选顺序各跑一次。v0.1 在 K1 的工程 parity 门处停止（delta 0.0091），改用 math-only SDPA 后发 v0.2，864 条科学前向。
- **结果**：测试集 N0 85、N1 111、K1 98（/144）；预设主指标“完整 parent”为 0/1/0；缺失视图误承诺 36/29/35（/36）；顺序敏感的输入数 15/5/2。
- **作者自述局限**：12 个测试 parent，没有人工审核；v0.2 是看过 v0.1 分数后的修订；K1 同时改变了表示和读出；已知语法解析器是事后写的。
- **审计复算**：主要数字一致。v0.1 与 v0.2 的 N0/N1 logits 576/576 逐位相同，修订没有改变任何已看到的结果（正面，F143）。**但**：24 个 parent 实际只对应 6 个逻辑模板，dev/cal/test 在逻辑上重复（F15）；N1 唯一的完整 parent（owner_scope-6）靠 BF16 并列按位置打破才成立，严格处理后是 0/12（F01）；根目录只引用次要指标 85/111/98（F67）；L0 不是 Kev 的原生格式（M3）；K1 训练数据里完全没有 INSUFFICIENT 这一类（G-K3）。

#### 2.3.3 layout-boundary：输入布局边界
- **做了什么**：用同一语料比较三种布局：L0（证据放 state、策略放 question）、L1（策略+证据放 state、固定通用问句）、L2（策略放 state、证据+问句放 question）。对原生路径来说 L1 与 L2 逐 token 相同，所以唯一变量只作用于 pointer。
- **结果**：K1 98→119→127，N1 111→121→121，N0 85→106→106。L1→L2 翻转了 K1 的 21/288 个决策；锚点复跑和 parity 检查的差都是 0。
- **作者自述局限**：设计是看过结果后做的；新布局可能在训练分布之外；不做显著性声明；“不是 pointer 全面胜利”。
- **审计复算**：一致。差中差（K1 从 L0 到 L2 的增益减去 N1 的增益）在测试面板上是 +19，CI [4, 34]，是本单元最稳健的量。“Different winner”只在 L2×测试面板这一格成立：9 格中 N1 领先 6 格；L2 测试面板上 K1−N1=+6，CI [−3, +15]（F16）。parity 检查在单问题编码下在数学上是恒等式（F46）。“2,016 new forwards”里有 864 次是锚点复跑（F72）。L0 恰恰是最不原生的布局（M3）。

#### 2.3.4 evidence-gap：决定性与非决定性删除
- **做了什么**：新写了一个有限策略语料，4 个机制族，每个 parent 6 个视图。只对 development 集评分（72 文本 × 3 顺序 × 3 臂），另外试了 null-subtraction 和两顺序平均两种读出。216 条保留文本一次也没评。
- **结果**：K1 raw 非决定性 31/36、决定性 3/36、配对 1/36；FC：N0 55、N1 68、K1 66（/72）；null-subtraction 让 N1 总分从 96 升到 111，但 FC 升到 72/72 满额（指标陷阱）。
- **作者自述局限**：只有 12 个 parent，没有人工标注；null-subtraction 是未经验证的消融；dev 与保留集的呈现方式不同。
- **审计复算**：一致；保留集隔离也核实成立（0 命中）。补充：“preserved answers 31/36”其实是 nondecisive 视图本身的正确数，预注册的“保持且正确”只有 25/36（F74）；决定性 3/36 实际上是 1 个 parent 重复了 3 次（F75）；两类删除的线索结构不对称，nondecisive 删掉的总是反向线索（F17）；N0 有 33/216 个精确并列，raw 分数在 90–119 之间（F01）；null 提示下 N1/K1 36/36 选 INSUFFICIENT，这一点没有报告（F77）；后续研究发现的命名捷径没有回写到本单元（F78）；K1 被固定在对它最不利的 L0 布局上（G-K4）。

#### 2.3.5 evidence-guards 与成本敏感性页
- **做了什么**：纯离线的事后分析，比较 13 种方法：raw、最大概率阈值、margin 阈值、schema gate、policy determinacy gate、always-INSUFFICIENT，外加纯代码参照。成本页（docs/risk_tradeoff.html）用有理数算出 direct、whole-state facts、line reader、always-defer、grammar 五种方案的最优区间。
- **结果**：K1+policy gate 172/216，FC 0，false INSUFFICIENT 18，determined 上仍有 26 个错误动作，完整 parent 2/12；schema gate 使 false I 翻倍到 36；max-prob 0.99 阈值仍有 14/72 个无依据承诺；纯代码 216/216。
- **作者自述局限**：事后分析，不是预注册；policy gate 是强程序先验；不做显著性检验。
- **审计复算**：39 个面板 × 10 项指标 0 处不一致。policy 正确数 = raw 正确数 + raw unsupported，按构造等于 oracle（F79）。即使按 gold 挑最优阈值，也只能到 109–120/216，“分数阈值替代不了策略 gate”这一结论稳健。schema 与 policy 的差异只来自 6 条文本（F80）；tradeoff 图里没有画纯代码点（F81）；成本页“line 在任何 r 下都不最优”只在 canonical 顺序（facts_0）下成立（F82，已恢复为成立）。

#### 2.3.6 fact-execution：事实抽取 + 执行器
- **做了什么**：在 72 条 dev 文本上，比较“直接决策”和“逐字段抽取四态事实（TRUE/FALSE/MISSING/CONFLICT）再交给有限策略执行器”。
- **结果**：N1 31→44/72；真实缺失字段被断言为值 N1 14/18、K1 16/18；事实向量完全正确 33/72；执行器 0 缺陷；N0 的读出退化（canonical 顺序下 135/168 为 CONFLICT）。
- **作者自述局限**：事后开发诊断，没有人工标注；已知语法代码 72/72；架构并不新（Binder）。
- **审计复算**：一致。补充：N1 在决定性缺失上断言的 11 个值**全部照抄了同字段外来记录的值**，应理解为绑定错误，不是凭空捏造（F18）；提升里有 +8 来自 conflict 视图，去掉 conflict 视图后 N1 净增 +5，K1 为 0（F19）；“primary”臂是看结果后才指定的（F83）；N0 有 15/72 个精确并列，范围 32–44（F01）；reverse 顺序下提示中状态名与字母错位（F84）。

#### 2.3.7 line/joint 试点与可见 ID 门审计
- **做了什么**：line 方法逐“目标字段 × 证据行”三选一；joint 方法每行在 6/8 个选项中互斥路由，并设置调用数匹配和 token 数匹配两个直接对照；事后用 ID 相等门重放已保存的路由。
- **结果**：line 29/72，FC 6/24，determined 11/48（筛选要求 ≥34）；joint 34/72，FC 11/24（两项筛选都失败）；目标行 160/162 路由正确，外来行 60/66 被当作目标证据；ID 门回放 70/72；oracle 同时修正“其他请求”和“其他字段”两类错误后可到 68/72。
- **作者自述局限**：同一批已检视的文本；预算不匹配；只跑了 N1；ID 门是事后设计的；存在 request-/other- 命名捷径。
- **审计复算**：全部一致。补充：joint 的 228 行只有 52 个不同 prompt，66 条外来行只有 12 个不同 prompt（其中 11 个误路由）（F21）；joint 34 对 31 的“小幅增益”完全来自 flip/conflict 视图，在这两类视图中误路由恰好无害；去掉它们后 joint 10/48，direct 23/48（F20）；line 中 4 条“极性相反”都来自同一个并列 prompt（F01）；只测了一种选项顺序（F65）。

#### 2.3.8 request-ownership：同前缀 ID 目标切换
- **做了什么**：24 个父场景，只切换被询问的请求 ID（两个 ID 同为 `request-` 前缀，一半只差 1 个字符）。比较 joint_full、joint_gated、direct_full、direct_filtered 和已知语法程序。
- **结果**：完整配对 2/24 → 23/24（21 胜 0 负），FC 7/12 → 0/12；目标行 99/100 读对，外来行 85/100 被接收；直接判决即使过滤了外来行也只有 2/24；程序 24/24。
- **作者自述局限**：构造场景；方向性判据不代表统计显著；门控只做词法 ID 校验；已知语法程序严格优于混合管线。
- **审计复算**：8 种方法的主表全部一致。21:0 的符号检验约为 4.8e-7，在构造分布内效应非常明确。补充：一条与内容无关的规则（目标行数少于外来行数则判 INSUFFICIENT，否则看首行归属）就能拿到 18/24 对、0 个错误承诺（F22）；方向性判据在构造上几乎必然通过（F88）；ID 门能覆盖的行，正则本身已经能完整解析，遇到无法解析的文本时直接放行（fail-open）（F64）。

#### 2.3.9 payment-ownership：退款目的地
- **做了什么**：从 tau2-bench 固定提交的零售库里确定性地选出 12 个用户，构造 48 个输入，对比 full（两笔订单都可见）与 related（oracle 删除非目标订单）两种条件，各跑两种映射；主网格前先跑 6 个 smoke。
- **结果**：6 个单元格全部 48/48，wrong-VALID 0/24；smoke 5/6，其中目标歧义的用例 VALID=0.97；共 198 次请求，$0.0103；两份评审在标签上 96/96 一致，但商品名指代的 48 项存在范围异议。
- **作者自述局限**：静态诊断；主数据没有 NOT_ESTABLISHED；门槛修订是看过 smoke 后做的；评审之一是作者本人。
- **审计复算**：一致；源用户选择可以从 db.json 复现。补充：真正测“外来订单诱导”的 lure 子集只有 12 个输入、6 个 parent，P(VALID)≤0.06（F90）；按严格读法重新计分，Jev 24/48，与 always-NOT_ESTABLISHED 持平（F92）；作者那份评审的 96 个时间戳落在 10.6 秒内（F14）；另一位（非作者）评审者的姓名与原件被公开，但没有同意记录（F125）。

#### 2.3.10 candidate-completeness 与 512 token 推理对照
- **做了什么**：同一可见记录下只改一句覆盖声明（complete / relevant_omission / irrelevant_omission），交叉两种请求风格（显式 ID 与商品名）。
- **结果**：Jev 63/72 与 67/72，FC 0/12，不必要延迟 9/60 与 5/60，错误全在“显式 ID + 相关遗漏”这一格；Qwen 原生 34 与 30（/72），FC 12/12；512 token greedy 思考 58 与 59，FC 仍为 12/12，69/144 被截断；程序 72/72。
- **作者自述局限**：12 个 parent；零人工审阅；措辞存在另一种读法；推理对照是看结果后加的；greedy 不符合模型卡推荐。
- **审计复算**：一致。补充：Jev 出错的那一格最大概率中位数只有 0.59，接近五五开（F23）；Qwen 两种接口下 NOT_ESTABLISHED 都是 0/144，映射 1 下 72/72 全判 VALID，等于常数（F95）；被停用的采样 smoke 得 5/6，正是模型卡推荐的配置，这一点没报告（F58）；目标订单在列表中的位置与标签完全共线（F97）；反序映射下 INVALID 始终在 B 位（F96）。

#### 2.3.11 decision-sufficiency：可执行规格实验室
- **做了什么**：零模型调用。定义结构化合约，给出 predicate_only 和 unique_target_required 两种接口，写了 20 个示例、5 个非法输入，并用第二套枚举器做 910 个合约的审计。
- **结果**：7/20 个示例在两种接口下输出不同；730 个有效合约、180 个被拒；1900 个投影一致；192 个合约两种接口不同。
- **作者自述局限**：零经验证据；没有新颖性（certain answers 属已有工作）；两套实现都由 AI 辅助编写。
- **审计复算**：一致。在更宽的 10,731 个合约上 0 处不一致。补充：早期 12 个 NOT_ESTABLISHED 输入在 predicate_only 下同样无法确定，所以早期结论与接口选择无关（F170）；180 个被拒合约全部来自同一条规则（F100）；NOT_ESTABLISHED 这一个标签混了三种状态（F102）。

#### 2.3.12 Qwen3.5 基础设施（baseline-readiness / generation-calibration / action-backends）
- **做了什么**：盘点候选对照模型；做 Qwen3.5-4B 技术冒烟（首次因旧版 PEFT 在 import 阶段失败，修订后重跑）；用 12 道合成初级题做生成校准；做四动作集成冒烟。
- **结果**：direct 严格有效 24/24、内容正确 22/24；thinking 严格有效只有 11/24，其余 13 个都是 Markdown JSON 围栏，围栏内的对象全部正确；动作冒烟 Jev 8/8、Qwen 8/8；本地没有 ≥8B 的通用指令模型。
- **作者自述局限**：只是运行时和接口证据，不是能力证据；上限远低于厂商推荐的 32,768；C13 的 greedy 与模型卡推荐不符（已加注）。
- **审计复算**：一致。补充：presence penalty 1.5 跨过 `</think>` 作用到最终答案 token，可能是围栏出现的原因之一，也会不对称地压低某些选项（F103/F104）；“冻结先于权重下载”无法核实（F174）。

#### 2.3.13 ShARC 外部验证准备
- **做了什么**：审计数据源结构；从 train 集找出一答翻转的配对清单（3,334 对）；按冻结规则抽 30 对（24 对主样本 + 6 对备用），拆成 60 条盲评单项并发布 CC BY-SA 3.0 的评审包；写了对账、定稿、计划编译器、运行器、分析器等代码。
- **结果**：0 份人工评审，0 次模型调用。
- **作者自述局限**：公开 train 集可能已被模型见过；只有程序性盲法；没有不变对；参照已有工作撤回新颖性主张。
- **审计复算**：结构统计、配对清单、选择哈希、包哈希全部可以复现。补充：3,037/3,037 个动作改变的配对都是**最后一轮**回答翻转，按源标签 copy-last 能解出全部 No/Yes 主样本对（F24）；包里 30 对样本可以直接按文本配出来，所谓“不透明 ID”可以反查回源行（F25、F106）；比较草案仍用已知会大面积截断的 2048 token 上限（F57）。

#### 2.3.14 ShARC 源标签筛查与 finite-choice 对照
- **做了什么**：12 棵 dev 树 × 2 输入 × 2 顺序，比较 Jev、Qwen3.5 direct（256 token）和 thinking（2048 token）；之后又做了单次 prefill 字母读出。
- **结果**：Jev 18/24（两种顺序都是）；Qwen direct 11 与 12（/24，两种顺序）；thinking 5 与 6，37/48 被截断；copy-last 14/24；prefill 13 与 10；Jev API 有 2/48 个响应违反自身契约。
- **作者自述局限**：只看源标签一致率，没有人工审核；读出做过自适应修复；不量化种子方差。
- **审计复算**：一致；样本选择可复现。补充：树级检验 Jev 对 Qwen direct p=0.29/0.45，对 copy-last p=0.75；prefill 在 order1 下 23/24 输出 Yes，得分与 constant_Yes 完全相同（F26）；在 Yes/No 翻转层，copy-last 4/4、Jev 2/4、Qwen 1/4（F111）；源证据审查写于 Jev 逐项输出公开约 18 分钟之后（F112）；Qwen 收到的是按键名排序的 JSON（F110）。

#### 2.3.15 EXtrA / QA4PC 审计与阶段归因
- **做了什么**：审计 EXtrA 的可见字段；用强 Kleene 三值逻辑复算 QA4PC 的组合标签；在 12 树/24 场景上设四个臂，D 直接判断、G 附上人工图、F 逐条事实加代码组合、L 给定事实只做执行；Qwen 在 smoke 停止后做看结果修订再续跑。
- **结果**：EXtrA 的确定性上限 198/200（2 对可见输入相同但标签不同）；QA4PC 429/429 自洽，1 棵树缺变量 Q1。（以下每对数字为两种映射下的得分，分母均为 24）Jev D 19、19，G 20、20，F 19、20，L 24、24；Qwen D 13、19，G 14、16，F 12、14，L 19、22；F 用了 2.33 倍调用却没有稳定收益。
- **作者自述局限**：24 场景只能描述；Qwen 完整比较依赖一次看结果修订；参考标签来自上游。
- **审计复算**：一致；262 个 Jev 作业哈希全部可以重建。补充：Qwen 在映射 0 下，事实层对 gold 为 no 的召回是 0/26，一致率 22/56 **低于恒答 no 的 26/56**（F27）；12 棵树中 6 棵是单变量公式（F28）；Jev 的 G 错误有一半来自参考可疑的树 61bf03cf（F115）；10 个精确并列（F01）。

#### 2.3.16 QA4PC 六向答案接口
- **做了什么**：在新的 12 树/24 场景上跑全部 6 种映射，比较 Jev 原生、Qwen 有限字母、Qwen 生成字母、Qwen 生成语义标签四条路线，共 648 个作业；之后做了 AI 辅助的全案源审计。
- **结果**：101/85/89/87（/144）；finite 与生成字母的 162/162 首步 logits 相同，差异全部来自 5 个并列；语义标签 324/324 格式合法，但一致率没有提高；源审计标记 8/24 个参考可疑。
- **作者自述局限**：源审计是 AI 辅助且知道结果的；语义路线是捆绑干预；单个 4B 模型。
- **审计复算**：一致。补充：所有路线里最大的错误格都是 no→maybe，与指令中的 “Do not treat missing facts as false” 以及 QA4PC 的封闭世界标注约定冲突（F116）；源审计只讨论了 Jev 被标记的错误，没提 Jev 在可疑标签上附和源标签而得分，其中对 semantic 路线的领先有 8/14 来自被标记的场景（F13）；Jev 跨映射 ICC 0.968，144 个决策的有效样本约 24.7（F136）。

#### 2.3.17 rule-direction：if / only if / iff
- **做了什么**：12 个虚构词汇族 × 3 种关系 × 3 种事实状态 = 108 个输入，参考答案由四世界穷举得到；Jev 走 Choice API，Qwen3.5 用 greedy 生成语义标签。
- **结果**：两者在两种映射下都是 84/108；24 个错误完全相同，都落在 “only if + P 真” 和 “if + P 假” 两格；216/216 条输出一致；always-maybe 60/108；程序 108/108。
- **作者自述局限**：12 个族只是 3 种逻辑模式的换词复制；零人工审阅；语用读法可能不同。
- **审计复算**：一致；冻结在调用前约 23 秒推送。补充：两个错误格正是否定前件和肯定后件（DA/AC），也就是 conditional perfection，但仓库既没用这些术语也没引文献（F11、F54）；一个忽略连接词、只看事实极性作答的启发式同样得 84/108，并与两个模型逐条相同（F118）；Jev 的置信度 AUROC 为 0.974，按 0.9 阈值可以把 48 个错误中的 18 个送去升级，且不误伤正确项（F10）；这种“错误”的 if→iff 读法恰好是 QA4PC 人工参考在 rule_scope 场景中采用的约定（F138）；顶层没有写明 Qwen 的配置（M5）。

### 2.4 跨研究的主线发现

1. **证据不足或身份不明时仍然给出确定答案**。这是唯一在多个研究中复现的现象：候选覆盖研究里 Qwen 不论原生还是思考都是 12/12 误承诺；Kev pointer 在决定性删除上只对 3/36；fact-execution 中 14/18 个缺失字段被填值；payment 中歧义目标得到 VALID=0.97；规则方向研究中 24/60。不过 fact-execution 的 11/11 断言都照抄了外来记录，说明其中一部分其实是**绑定错误**，不是“不会弃权”（N1/K1 在“完全无证据”提示下 36/36 会弃权）。
2. **读实体与读字段是两回事**：单行的字段和极性读取接近完美（99/100），请求归属却基本不做（85/100 外来行被接收，ID 差 5 个字符也一样）。确定性 ID 门能消除这类错误，但它能起作用的范围，程序本身就能完整解析。
3. **读出、接口、格式会左右结论**：只移动一个分隔符就翻转 7.3% 的 pointer 决策；严格 JSON 门把正确内容判成失败（24/24 → 11/24）；有限选择 prefill 坍缩为常数 Yes；映射 0 下 Qwen 的 no/maybe 系统性坍缩；BF16 精确并列按位置打破会改变头条数字。
4. **在已知语法上，程序总能解决，模型只会增加错误**。这把长期问题变成了“在程序覆盖不到的语言上，模型抽取带来的价值是否超过它带来的错误”。这个问题在仓库里几乎没有被测过。
5. **Jev 在方向上领先，但证据很弱，而且与平凡基线分不开**：同输入的 6 组正面比较中 Jev 5 胜 1 平 0 负（按 Qwen 最好的一路，差距为 +0.135、+0.090、+0.271、+0.208、+0.083、0）。每项只有约 12 个聚类，而且比较条件混杂（托管 API 对本地、读出接口不同）。在 ShARC 上 Jev 与 copy-last 在树层面无法区分（p=0.75）。Jev 的置信度在规则方向和候选覆盖上能较好地识别自身错误（AUROC 0.974/0.964），在 QA4PC 上只有 0.675。
6. **人工评审和参考标签是整个系列的瓶颈**：约 19 个推理研究中只有 1 个做过人工评审，那一次就在 48/96 项上提出了范围异议；QA4PC 约三分之一的源标签可疑（8/24）。AI 代理的产出速度远快于人工验证。

---

## 3. 审计结果

### 3.1 可复现性

**整体 CI**：在副本上执行 `.github/workflows/check.yml` 的全部 64 条命令，全部 exit 0；315 个单元测试通过（Python 3.11，CI 用 3.10；逐文件单独运行、三种随机顺序都通过）；build 类命令不产生 git diff。main 上最新的 CI（#103）和 Pages 部署（#66）都成功，线上 20 个页面与 docs/ 逐字节一致。

**各单元独立复算（节选；复算都不导入仓库的分析代码）**

| 单元 | 数字 | 报告值 | 复算值 | 一致 |
|---|---|---|---|---|
| 原始 | 完整案例 Jev/Qwen | 12/12, 8/12 | 12/12, 8/12（两轮） | ✔ |
| 原始 | 错误取消 / 漏取消 | 10/48, 3/48 | 10/48, 3/48 | ✔ |
| 原始 | Brier / NLL（Qwen） | 0.134289 / 2.046177 | 同 | ✔ |
| 原始 | bootstrap 95% | [-0.583, -0.083] | 同（按族聚类为 [-1, 0]） | ✔ |
| 原始 | Jev 花费 | $0.003762 | $0.003761646 | ✔ |
| next-study | N0/N1/K1 测试正确 | 85/111/98 | 85/111/98 | ✔ |
| next-study | 缺失视图误承诺 | 36/29/35 | 36/29/35 | ✔ |
| next-study | 温度 / K1 raw coverage | 1/0.75/2；0.715 | 同 | ✔ |
| layout | K1 L0/L1/L2 | 98/119/127 | 同 | ✔ |
| layout | L1→L2 K1 翻转 | 21/288 | 21，其中 16 纠正 5 退化 | ✔ |
| layout | 锚点 / parity 最大差 | 0.0 | 0.0 | ✔ |
| evidence-gap | K1 决定性/非决定性/配对 | 3/31/1 | 3/31/1 | ✔ |
| evidence-gap | null-subtraction N1 | 111, FC 72 | 111, 72 | ✔ |
| evidence-gap | 保留集未评分 | 0 命中 | 0 命中 | ✔ |
| guards | 39 面板 × 10 指标 | — | 0 处不一致 | ✔ |
| guards | 成本页区间 | 3/16, 2, 37/14, 17/6 | 同 | ✔ |
| fact-exec | N1 direct/facts | 31/44 | 31/44 | ✔ |
| fact-exec | 缺失被断言 N1/K1 | 14/18, 16/18 | 同 | ✔ |
| line | 29/72, FC 6/24, det 11/48 | 同 | 同，与 decisions 0 处不一致 | ✔ |
| joint | 34/72；目标 160/162；外来 6/66 | 同 | 同 | ✔ |
| ID 门回放 | 70/72（38 纠正 / 2 回退） | 同 | 同 | ✔ |
| request-ownership | 8 种方法主表 | 2/23/2/2/3/3/24/0 | 同 | ✔ |
| request-ownership | 目标行 / 外来行 | 99/100, 85/100 | 同 | ✔ |
| payment | 6 单元格 | 48/48 | 48/48，0 条解码不一致 | ✔ |
| payment | token / 花费 | 245,241 / $0.0103 | 同 | ✔ |
| candidate | Jev / Qwen / 推理 | 63,67 / 34,30 / 58,59 | 同 | ✔ |
| candidate | 截断 | 69/144 | 69 | ✔ |
| decision-suff. | 730/180/192/1900 | 同 | 同（更宽的 10,731 片段 0 不一致） | ✔ |
| Qwen3.5 校准 | thinking 严格有效 | 11/24 | 11（13 个围栏内容全对） | ✔ |
| ShARC 准备 | 3,334 / 3,037 / 599 | 同 | 同；selection 与 pack sha 可重建 | ✔ |
| source-label | Jev / direct / thinking | 18 / 11,12 / 5,6 | 同 | ✔ |
| finite-choice | prefill（两种顺序，/24） | 13、10 | 13、10，1 个并列 | ✔ |
| QA4PC 审计 | 429/429 | 同 | 同 | ✔ |
| QA4PC 阶段 | Jev G / Qwen D（两种映射，/24） | 20、20；13、19 | 同；262 个作业哈希可重建 | ✔ |
| QA4PC 接口 | 四条路线 /144 | 101/85/89/87 | 同；648 个动作 0 不一致 | ✔ |
| rule-direction | 两后端两映射 | 84/108 | 84/108；216/216 输出相同 | ✔ |

说明：单元报告中标为 `matches_report=false` 的条目（BF16 并列、逻辑模板计数、prompt 去重、树级检验、结构性基线、presence penalty 暴露等）都是**报告里没有做的新增分析**，不是与已报告数字的矛盾。**审计没有发现任何一个已报告数字与原始数据矛盾。**

**需要注意的可复现性边界**：
- 离线复核很强，但重新跑推理比较脆弱：Qwen3.5 环境没有锁定，runner 对私有 generation API 做精确断言，只在一台 Windows 机器上跑过（F12）。
- QA4PC 三项研究和 implementation-audit 不在 CI 中，分析器依赖未提交的 `.local` 私有计划（F48）。
- 在默认模式下（不带 `--verify`）运行 `analyze.py` 会覆盖根 README（F35）。
- 有 5 个公开回放页面没有 CI 逐字节校验（G-P2）。

### 3.2 已验证的问题清单

> **没有 critical 级问题**：所有问题都不推翻已报告的数字，也没有安全或法律上的重大风险。严重性是对抗核查（major 三个视角、minor 一个视角）后的最终值（不少条从 major 降到了 minor）。编号 F 来自主问题库，G- 为补查阶段新增。

#### 3.2.1 Major（5 条）

**M1 / F01 原生路径 BF16 logits 大量精确并列，并列按候选位置打破，规则未声明，数量未报告**
- 证据：next-study/study.py:277 `.logits[0,-1].float()`，argmax 取第一个最大值（evidence-gap/gap_run.py:175-186，analyze_study.py:78）；N0/N1 的 logits 全部落在 0.125 网格上。evidence-gap N0 有 33/216 个并列，raw 分数在 90–119 之间（报告 102）；next-study N1 唯一的完整 parent owner_scope-6 的 logits 为 [23.625, 23.75, 23.75]，严格处理后是 0/12；fact-execution N0 direct_0 有 15/72 个并列，范围 32–44（报告 39）；line 中 route_lookup-2 的 [24.125, 24.125, 23.5] 是 4 条“极性相反”的唯一来源。
- 解释：预测由候选位置决定，N0 行数字、N1 的唯一完整 parent 和“极性错误”这个诊断都依赖这条没声明的规则。后来的研究（finite-choice/PROTOCOL.md:30）又改成“并列即无效”，前后标准不一致。K1 和 Jev 没有并列，相对排序大体不变。
- 披露：早期单元（next-study、evidence-gap、fact-execution、layout）**未披露**；QA4PC 和 finite-choice 研究有披露。
- 建议：各单元报告并列数，以及“并列=无效/最好/最坏”三种处理下的区间；今后用 FP32 计算 lm_head，并预注册并列规则。

**M2 / F32（恢复）+ G-A 最直接的先例 SemIf 没有被定位为最近邻工作**
- 证据：全仓库只有 3 处提到 SemIf，PROTOCOL.md:114-115 “Native readout already has open implementations such as SemIf”，THIRD_PARTY_NOTICES.md:112，analyze.py:318；NOVELTY_MATRIX.md 和 research/next-study/related_work.md（“Closest sources”）里都没有它。SemIf 用冻结 Qwen3.5-4B 的原生 logits 与 Jev 比较，在 TypeSafe 公开子集上约 0.845 对 0.883，还有 direct logits 与 JSON 的速度对比（5.21 倍）。这些数字来自外部 README 摘要，有一定不确定性。
- 解释：它回答的正是本系列原名 “You Might Not Need Jev” 的核心问题，模型和读出方式都相同，而且规模更大。finite-choice-readout 几乎就是它的做法，却没有引用。读者会高估本系列的增量。
- 披露：未披露（仓库只是整体上否认方法新颖）。
- 建议：在 NOVELTY_MATRIX 中新增“最近先例”一节，逐项对照 SemIf、Kev README 中的 Jev 对比、Laya、jev-benchmarks 和 TypeSafe 公开评测，并说明本系列的差异（实时原始概率、成对扰动诊断、纯代码对照、负结果留存）。

**M3 / G-K1 Kev 研究的主布局 L0 与检查点的原生训练格式相反，仓库却称之为 conventional**
- 证据：
  - 上游 `29d71c7` 的 kev/composition.py:284 和 contrastive.py:230 都写 `state = {"policy": ..., "case": ...}`。
  - 检查点训练集 decision-v7（其 manifest sha a8f50e48… 等于 checkpoint_metadata.json 里的 suite_sha256；train.jsonl sha 7ed5254b… 也对得上）中，2576/2576 条策略记录都把策略放在 state，question 最多 10 个词，**没有一条**把策略放进 instruction。
  - L0 把 43–48 词的完整策略放进 question；选项只有描述，没有 key（kev/api.py:55-56 的原生格式是 “key: 描述”）。
  - layout-boundary/README.md:57-58 只写 “The alternative field assignments may be outside training distribution”；evidence-gap/PROTOCOL.md:48 写 “Use L0's conventional contract”。
- 解释：N1 111 > K1 98 这一对比，K1 用的正是训练中出现 0 次的字段分配；同一套权重换成最接近原生的 L1 就是 119。L0/L1/L2 都不是原生格式，所以“pointer 不如原生读出”不能归到 Kev 本身。仓库的提示方向正好反了：它提示新布局可能在分布外，暗示 L0 在分布内。此外 evidence-gap 又把 K1 固定在这个最不利的布局上。
- 披露：未披露。
- 建议：写明 Kev 原生策略格式（`policy: P\ncase: E`、短问句、`key: 描述` 选项），不再把 L0 叫 conventional，把相关结论降级为“在非原生输入分配下”；如果恢复实验，加一个经 `api.to_record` 渲染的原生格式组。

**M4 / G-S1 系列层面没有概括“Jev 5 胜 1 平 0 负”，首屏以唯一的平局开头，并省略 QA4PC 中 Jev 领先的数字**
- 证据：README.md:12-15 以 “Jev and Qwen3.5-4B both score84/108 … making the same24 errors” 作为首屏主结论；README.md:19-23 的 QA4PC 接口段只写 “do not improve mean source agreement”，没写 Jev 101/144 对 Qwen 85/89/87；README.md:32-34 没写 Jev G 20、20 对 Qwen 14、16（两种映射，/24）。grep 顶层文档，承认 Jev 领先的只有 C1（RESEARCH_CLAIMS.md:29）一句。RESEARCH_CLAIMS 总述写于 db233ba（09-29 23:40），当时只有 1 组 Jev 对 Qwen 比较。
- 解释：首次阅读的人只会看到“两个模型犯同样的错”，看不到最主要的跨研究事实：在所有测过的冻结 4B 配置里，没有一个追平 Jev，Jev 的映射稳定性也普遍更好。单项研究里都报了数字，但系列层面的叙事在方向上低估了 Jev。这个模式应当带上限定写出来（样本小、条件混杂、研究之间不完全独立）。
- 披露：未披露。
- 建议：在 README 首屏和 RESEARCH_CLAIMS 加一张跨研究汇总表（研究、聚类数、Jev、Qwen 最好一路、最强平凡基线），配一句带限定的方向性陈述。

**M5 / G-Q1 Qwen3.5 头条在顶层没有写明所用配置；7 个 Jev 对 Qwen 头条中，0 个用的是模型卡默认的 thinking 模式和推荐预算**
- 证据：rule-direction/plan.py:58-63 `enable_thinking=False, 'max_new_tokens':32`，加上 qa4pc-answer-interface/generation_config.py:7-9 `do_sample=False`；Qwen3.5-4B 模型卡第 712 行 “operate in thinking mode by default”、第 837 行给出 non-thinking 推荐采样参数、第 1147 行推荐 32,768 token。唯一的 thinking 臂（ShARC）上限 2048，37/48 被截断。README、RESEARCH_INDEX 和 C15–C17/C20 都没有写 greedy/no-thinking/32 token。baseline-readiness/README.md:30-31 和 STAGE_LOG.md:655 已经要求区分 capability reference 与 budget-constrained，后续研究没有照做。
- 解释：“两个模型犯同样的错”“Jev 领先”都只能理解为“Jev 对 Qwen 的某个预算受限、非默认的接口”。研究内部文档写了配置，但顶层用的是模型层面的措辞。
- 披露：已披露但被埋没（只在研究内部写了）。
- 建议：给所有 Qwen 头条统一加配置标签（例如 “thinking off, greedy, ≤32 tokens: budget-constrained component”）；在 CLAIMS 的“可能的过度陈述”表里加一行。

#### 3.2.2 Minor（按类别）

**(a) 统计与样本结构**

| 编号 | 问题 | 关键证据 | 披露 | 建议 |
|---|---|---|---|---|
| F02 | 原始研究 12/12 对 8/12 的差距全部来自 S 族（对象范围） | REPORT.md:32-35；REPRODUCIBILITY.md:96；C1/INDEX 只写总数 | 埋没 | 头条按族拆分，以族为聚类单位 |
| F59 + G-O1 | 唯一给出的区间（12 单元 bootstrap）不含 0，精确 McNemar p=0.125；flip/hold 配对终点在协议中承诺报告，但没进 REPORT | REPORT.md:56；PROTOCOL.md:65-66；grep flip REPORT/README = 0 | 未披露 | 并列精确检验；给出按族的 flip/hold 表（S 族 3/16） |
| F04 | 12 个聚类下检测 20pp 的功效只有 3–6%，“没有改善”只能说明证据不足 | C16、README.md:21；只有 evidence-gap/NEXT_STEPS.md:28-29 提到功效 | 埋没 | 改写为“未检测到（功效约 5%）”；需要时做 TOST |
| F15 | next-study 的 24 个 parent 只是 6 个逻辑模板，三个 split 共享同一批模板 | study.py:84,113-114；PROTOCOL.md:9 “entity names are disjoint” | 埋没 | 按模板计独立单位 |
| F21 | line/joint 的行级计数来自逐字相同的 prompt（66 条外来行只有 12 个不同 prompt） | JOINT_RESULTS.md:5-7,32 | 埋没 | 并列报告不同 prompt 的计数 |
| F75 | evidence-gap K1 的 3/36 实际是 1/12 个 parent | README.md:24-26 | 埋没（info 级） | 头条给出 parent 级计数 |
| F90 | payment 真正检验诱导的 lure 子集只有 12 个输入、6 个 parent | RESULTS_V02.md:12 | 埋没 | 单独报告这一行 |
| F92 | 按严格读法，Jev 24/48 = always-NE，仓库明确拒绝报告这个敏感性分数 | REVIEW_DISPOSITION.md:59-61 | 埋没 | 附一张标明的敏感性表 |
| F98 | 推理对照中 32/144 条的全词表 top token 是 “The” 而不是字母 | REASONING_RESULTS.md:52 | 未披露 | 按截断分层报告概率质量 |
| G-O3 | Jev 概率只到 0.01，却与全精度 Qwen 并列比较 Brier/NLL | jev_formal.jsonl 中 167/192 条为 0/1 | 未披露 | 注明分辨率并给出区间 |

**(b) 方法学与构造混杂**

| 编号 | 问题 | 关键证据 | 披露 | 建议 |
|---|---|---|---|---|
| F10 | 所有 Jev 结论只按 argmax 计分，没评估厂商主打的“置信度加阈值升级”；rule-direction AUROC 0.974，0.9 阈值挡住 18/48 个错误（但仍有 30/198 个自动执行的错误），QA4PC 只有 0.675 | rule-direction/RESULTS.md:75-76 | 埋没 | 补一份事后的选择性预测分析，双口径标题 |
| F11 | rule-direction 两个“错误格”就是 DA/AC 和 conditional perfection，在语用上有争议 | RESULTS.md:1, 89-91；plan.py:21-25 | 埋没 | 用标准术语，加人类基线 |
| F118 | 忽略连接词的基线 84/108 与两模型逐条相同，“对照通过”高估了能力 | README.md:6-7；72/72 连接词不变 | 埋没 | 并列这一基线 |
| F138 | rule-direction 判为错误的 if→iff 读法，恰好是 QA4PC rule_scope 场景人工参考的约定 | source_audit.json 81a3824686 | 埋没 | 冻结前声明目标语义 |
| F16 | “Same weights. Different winner”只在 L2×测试面板成立，L1 下原排序保持 | RESEARCH_NOTE.md:7-9 | 埋没 | 头条改为“pointer 对布局更敏感” |
| F71 | 布局对比不对称：pointer 有 3 种不同输入，原生只有 2 种 | layout_study.py:234-239 | 埋没 | 注明 L2 只对 pointer 是新输入 |
| F46 | 单问题编码下 packed 与 causal 的 parity 检查在数学上是恒等式 | vendor/kev/model.py:71 | 埋没 | 说明几乎恒真 |
| F17 | evidence-gap 两类删除的线索极性不对称 | gap_data.py:163,168,170-172 | 埋没 | 报告错误方向分解 |
| F18 | 决定性缺失视图都带有同字段相反值的外来记录：“invented observation”实际是绑定错误（11/11 照抄） | RESULTS.md:3；VISIBLE_ID_GATE_AUDIT.md:58-59 | 埋没 | 改称 misbound |
| F74 | “preserved answers 31/36”其实是正确数，预注册的主指标 25/36 没写进文档 | README.md:24；gap_analyze.py:38 | 未披露 | 改措辞，同时报告 29/36 和 25/36 |
| F76 | evidence-gap 的证据块标题与 full/flip gold 确定性绑定 | gap_data.py:152,175 | 未披露 | 下一版独立随机化 |
| F19 | fact-execution 31→44 主要来自 conflict 视图，其中 6 个纠正属于错误被掩盖 | ALL_COUNTS；CONFLICT 精确率 9/26 | 埋没 | 按视图分解 |
| F83 | fact-execution 的 primary 臂 N1 是看结果后才指定的；三臂方向不一（−15/+13/+3） | 548e00f:PROTOCOL.md:68 | 未披露 | 摘要写出三臂 |
| F84 | reverse 顺序下，提示中状态名的顺序与字母错位 | interface.py:54 | 未披露 | 选项文本带上状态名 |
| F20 | joint 34 对 31 的“增益”来自 flip/conflict 视图（在其中误路由无害） | summary.json by_variant | 未披露（协议要求报告但没报） | 按视图报告，删掉“gain” |
| F22 | request-ownership 中与内容无关的结构线索能拿到 18/24 | prepare.py:61-79,101 | 埋没 | 在数据卡中报告，平衡行数 |
| F64 | ID 门的覆盖范围等于完整语法解析，遇到 UNKNOWN 放行 | scope_gate.py:11-18 | 埋没 | 标注覆盖率与 fail-open |
| F65 | line/joint 只测了一种选项顺序，OTHER_REQUEST 恒在 A 位 | line_run.py:71 | 埋没 | 在局限中写明 |
| F23 | candidate 中 Jev 唯一出错的格子最大概率中位数只有 0.59 | responses.jsonl | 未披露 | 报告概率分布 |
| F95 | Qwen 两种接口下 NOT_ESTABLISHED 都是 0/144，“0/60 不必要延迟”其实是退化 | REASONING_RESULTS.md:17-18 | 埋没 | 加一列预测分布 |
| F96 | 反序映射下 INVALID 始终在 B 位 | payment study.py:20-21 | 埋没 | 用循环移位或全部 6 种排列 |
| F97 | candidate 中目标订单位置与标签完全共线 | study.py:85 | 未披露 | 交叉平衡 |
| F26 | finite-choice 读出坍缩为 Yes，order1 与 constant_Yes 同分 | report.json 混淆矩阵 | 埋没 | 报告预测分布 |
| F27 | QA4PC 阶段研究中 Qwen 映射 0 下 no 召回 0/26，事实层 22/56 低于恒答 no 的 26/56 | continuation_report.json | 埋没 | 给出逐类召回和常数基线 |
| F28 | QA4PC 阶段研究 12 棵树中 6 棵是单变量公式 | cohort.json | 未披露 | 按公式复杂度分层 |
| F115 | Jev 一半的 G 错误来自参考可疑的树 61bf03cf | 源文件政策原文 | 埋没 | 做逐项来源标注 |
| F116 | 预注册的混淆矩阵和候选概率质量没写进 RESULTS；no→maybe 是主导错误 | DESIGN.md:89-91 | 埋没 | 补表 |
| F13 | QA4PC 源审计只从一个方向讨论标记（对 semantic 路线的领先有 8/14 来自被标记场景） | SOURCE_AUDIT.md:57-60 | 未披露 | 给出对称的敏感性表 |
| F24 | ShARC 配对 100% 是最后一轮翻转，copy-last 能解出全部 No/Yes 主样本对 | recompute：3037 last | 埋没 | 以“模型减 copy_last”为主对比 |
| F25 | ShARC 盲评包里的配对可以直接从文本还原，页面文案却说 “Paired items hidden” | review.html:84 | 未披露 | 如实披露或拆给不同评审人 |
| F57 | ShARC 比较草案仍用已知会截断的 2048 token 上限 | COMPARISON_DRAFT.md:34 | 埋没 | 冻结前修订 |
| F110 | ShARC 中 Jev 与 Qwen 收到的状态序列化顺序不同 | comparison_plan.py:52-53 | 未披露 | 两端统一 |
| F60 | 原始研究 round 1 对 Qwen 只是确定性复算；Jev 两轮之间 6/96 的概率有变化，没报告 | run.py:185-214 | 未披露 | 注明 |
| F67 | next-study 预注册的主指标处于地板，根目录只引用次要指标 | PROTOCOL.md:26 | 埋没 | 根目录同时给出主指标和常数参照 |
| F70 | next-study 实体名带有 target/other 角色词 | study.py:83 | 未披露 | 用中性名称 |
| F73 | layout 盲审材料中，2/3 家族的缺失类可以只靠证据条数识别 | blind_review.csv | 未披露 | 平衡条数 |
| F80 | schema gate 与 policy gate 的差异只来自 6 条文本 | gates.jsonl | 埋没 | 写明 |
| F86 | “144 AI-generated rewrite pairs”实际是 18 个模板渲染出来的，全是正例 | data_tools.py:22-31 | 未披露 | 改称 template-generated |
| F88 | request-ownership 的方向性判据几乎必然通过 | EXECUTION_PROTOCOL.md:153-155 | 未披露 | 降为次要表述 |
| F103/F104 + G-Q2 | presence penalty 跨过 `</think>` 作用于最终答案 token：可能导致 JSON 围栏；在 ShARC 中 4/11 条对选项形成不对称惩罚 | generation-calibration/interface.py:52 | 未披露 | 在 `</think>` 后清零惩罚 |
| F33 | 长期问题中的 “reliable”“competitive total cost” 没有操作化 | NEXT_RESEARCH_GATES.md:86-87 | 埋没 | 写一页 SLO |
| F34 | 能执行的研究都落在程序必然满分的合成区，能打破这一点的研究都卡在评审上；QA4PC test 从未被规划为确认集 | STAGE_LOG.md:671-672 | 埋没 | 评估 QA4PC test 的可行性 |
| F63 | Jev 是托管闭源 API，可能漂移或退役，没有预案 | PROTOCOL.md:50 | 未披露 | 设锚点重测条款 |
| F58（恢复） | 被停用的采样 smoke 得 5/6，其中包含唯一一次正确弃权（发生在截断后强制闭合）；它恰好就是模型卡推荐的配置 | reasoning_responses.jsonl；GENERATION_CONFIG_NOTE.md | 未披露 | 补一行说明 |
| F82（恢复） | 成本页“line 在任何 r 下都不最优”只在 canonical 顺序下成立，换成 facts_1 时 line 在 (8/5, 11/6) 区间唯一最优 | build_risk_tradeoff.py:119-120 | 未披露 | 写明比较所用顺序并做敏感性分析 |
| F05（部分恢复） | 顶层没把 candidate（Qwen 映射 1 就是常数 VALID）、finite、QA4PC、rule-direction 的常数基线并列出来 | README.md:98-101 | 埋没 | 在总表加一列平凡基线 |
| G-O2 | 原始研究声称 “sees the same state…”，但 Jev 每次多约 270 个输入 token、输出 31 个 token | PROTOCOL.md:46 | 未披露 | 写明对等只在客户端层面成立 |
| G-O4 | candidate 的 policy 要求 “select NOT_ESTABLISHED”，但这个标签名从未对应到任何字母 | study.py:31 | 未披露 | 在 criteria 中给出标签名 |
| G-K2 | 三种布局都不是 Kev 原生格式（缺字段标签、选项没有 key） | api.py:55-56,69,72 | 未披露 | 补原生格式组 |
| G-K3 | K1 缺失视图 35/36 测的是训练中不存在的类别 | decision-v7 标签统计 | 未披露 | 在 claims 中注明 |
| G-K4 | layout 研究已显示 L0 对 K1 最不利，evidence-gap 之后仍把 K1 固定在 L0 | evidence-gap/PROTOCOL.md:48-50 | 未披露 | 在结果旁注明 |

**(c) 流程与预注册**

| 编号 | 问题 | 关键证据 | 披露 | 建议 |
|---|---|---|---|---|
| F06 | 分岔花园：同一批 72 条文本被十余个分析复用，约 30 种配置 | README.md:51-53；grep multiplicity = 0 | 埋没 | 做一张全系列对比登记表 |
| F07 | 停止规则和评审门槛多次在几分钟内被修订绕过（6 次停止全部被接续）；rule-direction 疑似违反 14 分钟前刚写下的对照路线要求 | EXECUTION_V02.md:6,26-27；CURRENT_RESOURCES.md:38-39 | 埋没 | 做停止/修订登记表 |
| F08 | 人工评审是几乎所有后续计划的唯一闸门，却没有招募方案：约 828 项待评，外部参与为零 | evidence-gap/review/README.md:4 | 埋没 | 统一评审待办，写明招募方案 |
| F14 | payment 的两份评审都有批量生成痕迹（作者那份 96 条在 10.6 秒内保存） | submissions CSV | 埋没 | 如实写出录入流程 |
| F89 | 第二份评审提出的 scope 异议，是否独立于作者已公开的异议，无法确认 | 0cbf005 比 receipt 早约 22 分钟公开 | 埋没 | 降级表述 |
| F139 / F107 / F47 | “独立评审”允许作者本人算一份；裁决人没有独立性要求；入口页把两份评审称为 “two reviewers” | REVIEW_AUDIT.md:17；review_finalize.py | 部分 | 至少两名非作者评审 |
| F30 | “AI-assisted” 低估了代理的自主程度 | README.md:351；PROTOCOL.md:4-5 | 埋没 | 在 README/CITATION 中声明 |
| F44 | 原始研究的冻结没有外部时间戳；prereg 标签事后才推送，并触发两次红色 CI | 仓库 created_at 11:47:25Z | 部分披露 | 注明；以后用 OpenTimestamps 或 OSF |
| F56 | 多个单元的分析和评分代码不在冻结范围内 | rule-direction/plan.py pins() | 未披露 | 注明；以后一并冻结 |
| F66 | line 试点冻结后 54 秒就开始运行，协议要求的审阅无法核验 | LINE_EVIDENCE_PROTOCOL.md:101-102 | 未披露 | 留出审阅窗口 |
| F112 | ShARC 源审查写于 Jev 逐项输出公开约 18 分钟之后，“had already identified”夸大了独立性 | INTERPRETATION.md:26 | 埋没 | 改用中性措辞 |
| G-S2 | 原系列名 “You Might Not Need Jev” 被悄悄撤下，从未给出结论 | db233ba；CHANGELOG 未提 | 未披露 | 记录改名并给出结论 |

**(d) 可复现性与工程**

| 编号 | 问题 | 披露 | 建议 |
|---|---|---|---|
| F12 | Qwen3.5 环境没有锁定（requirements-qwen.txt 固定的 4.55.4 无法加载 qwen3_5）；只在一台 Windows 机器上跑过 | 埋没 | 提供带哈希的锁文件或 Docker |
| F31 | 没有共享库：39 处 sys.path.insert 链式导入，9 个 Jev 客户端各不相同 | 埋没 | 抽出 jevlab 包 |
| F35 | 不带 `--verify` 运行冻结的 analyze.py 会覆盖根 README 和中文 README，并删掉许可归属 | 未披露 | 警告或加包装脚本 |
| F36 | replicate.py 能产出复现数据，但没有给复现结果计分的工具 | 未披露 | 加 score_replication.py |
| F48 | REPRODUCIBILITY 自称 “complete series”，实际漏了 7 个研究 | 埋没 | 按三类列清 |
| F128 | 最新研究的评分代码和 Qwen3.5 runner 没有单元测试（非测试代码覆盖率 61%） | 未披露 | 加合成夹具测试 |
| F131 | CLI 约定不统一，部分脚本默认写文件，CI 末尾没有 diff 检查 | 未披露 | 统一约定，加 `git diff --exit-code` |
| F127 | Markdown 中的数字没有机器校验，把 84/108 改成 85/108 后 verifier 仍全部通过 | 未披露 | 用占位符生成 |

**(e) 呈现与文档**

| 编号 | 问题 | 建议 |
|---|---|---|
| F29 | README 358 行，从未定义 Jev，倒序堆叠，各段用相对时间命名 | 首屏 800 词以内，放总表和术语表 |
| F38 / F52 / G-P1 | Pages 首页 “Latest” 落后 5 个阶段；已被取代的 payment_ownership.html 仍在线，写着 “review pending”，还有 3 个 404 链接；模板页被公开发布 | 首页改成系列目录，修链接 |
| F39 | “暂停”只写在 STAGE_LOG:26 | README 顶部加状态 |
| F40 | 大量数字与前一个词粘连，如 “score84/108”“All444”（包括冻结的 PROTOCOL） | 修复并加 lint |
| F41 / F42 / F53 / G-S3 | CITATION.cff 停在 09-29；THIRD_PARTY_NOTICES 把 Qwen3.5 标为只做过 smoke；多处 “latest/current” 措辞过时；顶层综述早于后续 5 组比较 | 统一更新 |
| F54 / F133 / F132 / F134 | 漏引 Holliday EMNLP 2024、Geis & Zwicky、Horn、AbstentionBench、QuestBench、“My Answer is C”、PriDe、Logic-LM、LINC；C16 实际检验了 TypeSafe 官方推荐的工作流，却没这样定位 | 补文献 |
| F72 | “2,016 new forwards” 中有 864 次是锚点复跑 | 改为 1,152 次新前向 + 864 次回归 |
| F78 | evidence-gap 文档没回链后续发现的命名捷径 | 加注 |
| F85 / F87 / F99 | “Missing→value”一列掩盖了 N0 的 17/18 CONFLICT；fact-execution 的 README 是长段落堆叠；C12 丢掉了“措辞待裁定”的限定 | 分别修正 |
| F93 / F94 / F100 / F111 / F122 | payment 商品名指代中 10/24 其实是显式 ID；“view”一词多义；180 个拒绝来自同一规则；source-label 没按选择组报告；顶层时间顺序混乱 | 分别修正 |

**(f) 许可、隐私与安全**

| 编号 | 问题 | 建议 |
|---|---|---|
| F123 | 根目录许可总述漏掉了 CC BY-SA 3.0 的 ShARC 衍生文件（selection.json、plan.json、qwen.jsonl、docs/source_label_screen.html 等），没有按路径列出的许可地图 | 加许可表 |
| F124 | payment 的两个评审 ZIP 再分发了 tau2 衍生记录，却没附 Sierra 的 MIT 声明（candidate 的评审包附了） | 补附 |
| F125 | 第二评审者的姓名、原始 CSV 和转述的自述被公开，没有同意记录 | 补同意或匿名化 |
| F50 | rule-direction 把合成数据声明为 MIT，与仓库的 CC BY 4.0 政策矛盾 | 统一 |
| F51 | QA4PC 的条款未决；其文本承袭自 ShARC（CC BY-SA 3.0），可以部分澄清 | 注明承袭关系 |
| F43 | traceback 和默认路径暴露了本地用户名和凭据存放位置；两次早期提交用了个人邮箱 | 替换为占位符 |
| F126 | 凭据扫描器与脱敏正则不一致，不扫 ZIP 和 git 历史（实测 0 泄露） | 统一正则，加 gitleaks |

#### 3.2.3 Info（摘要）
- **负面或提示类**：F45（verify 放宽容差的改动挂在标题无关的提交下）、F49（多处计数被硬编码，验证时自己比自己）、F55（84/108 由格配比决定）、F68（K1 的高置信错误只出现在 summary.json）、F69（next-study 审核表 id 带视图名）、F77（null 提示下 36/36 弃权没报告）、F79（policy gate 等于 oracle，是算术恒等）、F81（tradeoff 图没画 code 点）、F91（payment 的 STOP 表述）、F102（NOT_ESTABLISHED 一个标签混了三种状态）、F105、F106（ID 可以反查）、F108、F109、F114（QA4PC 分析器修改披露不全）、F117、F119（Qwen journal 中的 first_letter 字段对语义臂没有意义）、F120（中文 README 没有入站链接）、F129、F130（docstring 只有 9%）、F135（Jev 基座可能与 Qwen 同源，只是第三方推测）、F136（/144 的精度错觉，ICC 0.97）、G-O5（只展示错误取消，不展示漏取消）、G-O6（指令对三个族的提示强度不对称）、G-P2（5 个页面没有 CI 字节校验）、G-A6（ShARC 那条 choice≠argmax 异常中，confidence 与 B 一致，说明异常出在 choice 字段）。
- **正面**：F143（v0.1 与 v0.2 的 logits 逐位相同）、F165（候选范围异议几乎不改变任何参考标签）、F170（早期结论与接口选择无关）、F180（两次读出修复对 18/24 基本没有影响）、F184（QA4PC 门槛修订做法恰当）、F192（服务器端证据比仓库自称的更强）、F193–F195（复算一致、测试扎实、没有凭据泄露）、F198（对刚上线的闭源 API 做独立冻结实测，有存档价值）、F199（抽查的 7 篇 2026 年引用全部真实）、F200（跨数据集合并的探索性信号）。
- **其余** F140–F205 属于记录性观察，详见审计数据。

### 3.3 被否决、存疑或经复核修正的发现

为保证公正，下列候选问题经对抗核查后被否决或降级，有 3 条在补查阶段恢复。

| 编号 | 原主张 | 最终裁决与理由 |
|---|---|---|
| F03 | 各头条在聚类层面都不显著，仓库一个区间都没给 | **基本否决**：数字属实，但仓库多处明确声明不做显著性主张（README.md:228-229，source-label-screen/RESULTS.md:100 等），而且 REPORT.md:56 给了区间。**保留的部分**：唯一给出的区间与精确检验冲突（并入 F59） |
| F05 | 顶层从不并列平凡基线 | **部分恢复**：原始研究和 ShARC 在顶层并列了 copy-last/always-keep；candidate、finite、QA4PC、rule-direction 没有，按 minor 保留 |
| F09 | “更强对照模型”门槛不可满足；缺 8B 只是资源决策 | **否决**：CURRENT_RESOURCES.md:41-47 给出了两条可执行路线；仓库从未说过硬件不可行；托管 API 成本无数据支撑 |
| F32 | 长期问题已有 Kev/Laya/SemIf 等直接先例，仓库没有据此定位 | 核查阶段曾否决（Kev、Laya 已被定位）；**补查后针对 SemIf 恢复为 major（M2）**。Kev、Laya 是训练过的替代品，不属于“冻结、不训练”这一问题的先例 |
| F37 | Jev 的 confidence 与概率不一致 | **推翻**：confidence 等于 (k·p_max−1)/(k−1) 这一确定性变换，最大偏差 0.015，来自四舍五入。只保留“概率分辨率为 0.01”这一点（G-O3） |
| F58 | 被停用的采样 smoke 5/6 没报告 | 核查阶段以“方向与 C13 相同”为由否决；**补查后恢复为 minor**：分数确实没报告，但那次正确弃权发生在截断之后，不应夸大 |
| F61 | 若干“先于执行”的说法只有本地时间戳支撑 | **否决**：candidate 的三次冻结都有 GitHub Actions 服务器时间，而且早于运行；next-study 已声明是 local freeze |
| F62 | 3 次 CI 失败没有记录 | **否决**：STAGE_LOG.md:587、CHANGELOG.md:249-250、CURRENT_RESOURCES.md:54-58 都有记录，只是没写提交哈希 |
| F82 | 成本页的结论依赖 canonical 顺序 | 核查阶段以“line 本身只有 canonical 结果”为由否决；**补查后恢复为 minor**：主张没有限定，也没做敏感性说明 |
| F101 | 查询范围不匹配时排除了早期显式 ID 输入 | **否决**：对于可见的精确 ID，可以如实编码为 query=order_id，决策信息没有丢失 |
| F113 | thinking 的 2048 上限由 1 小时预算决定，完成率和一致率混在一起 | **否决**：INTERPRETATION.md:14-21 已明确区分两者；2048 沿用自校准阶段 |
| F121 | CHANGELOG 中 run.py 的盲点是悬空引用 | **否决**：上一条目（replicate.py 的特性）间接描述了这些盲点 |
| F137 | 多份文档宣称的“下一步”互相冲突，STAGE_LOG 漏掉 09-29 的计划 | **否决**：几处表述针对的范围不同，并不冲突；09-29 的待办在 RESEARCH_INDEX:123-132 中有记录 |

另有两处审计过程中的更正：
- 统计维度称“Jev 在 6 个数据集上一致占优 +0.13~+0.18”，应更正为 **5 胜 1 平 0 负**（rule-direction 差值为 0）。finite-choice 与 ShARC 用的是同一批输入，不能算独立数据集。
- 有说法认为 rule-direction 复用了 generation-calibration 的 presence penalty，这不成立：它复用的是 greedy、无惩罚的后端。

### 3.4 各维度评价

| 维度 | 评价 | 分数（/10） |
|---|---|---|
| **方法学** | 对照纪律好：每个研究都有已知语法程序和平凡基线；成对扰动设计精巧。缺点：构造混杂较多（线索不对称、结构捷径、非原生格式）；合成任务在结构上无法回答“是否需要模型”；Qwen 配置普遍不是推荐配置 | 5 |
| **统计** | 所有核对过的数字都没错。但独立单位约 12 个，功效约 3–6%；只有一个区间且偏乐观；没有聚类检验、功效分析和多重比较控制；否定性结论不能当作等价证据 | 3.5 |
| **流程与预注册** | 冻结先于推理有服务器时间佐证（16/16），冻结哈希完整，失败都保留了。但冻结在系列层面约束力弱：6 次停止都在几分钟内被修订接续；分析代码不在冻结范围；分岔花园没有登记；原始研究没有外部时间戳 | 6 |
| **许可与隐私** | 没有凭据泄露，上游文件与 bundle 逐字节核对一致。缺按路径的许可地图，两个 ZIP 少 MIT 声明，第二评审者的公开没有同意记录 | 6.5 |
| **工程质量** | 315 个测试有实质内容（105 个含篡改或负对照），离线 verify 真的从原始数据重算。但没有共享库、环境没锁、CLI 不统一、最新研究缺测试、默认模式会覆盖 README | 6.5 |
| **文档与呈现** | 局限写得极其诚实。但 README 冗长倒序、Jev 没有定义、顶层综述过时、跨研究汇总缺失、首屏以平局开头、数字粘连、Pages 首页过时 | 4.5 |

---

## 4. 研究价值评估

### 4.1 三个视角

| 视角 | 评分 | 核心判断 |
|---|---|---|
| **学术审稿人**（NLP/ML 评测） | **4/10** | 工程与透明度可作示范，科学规模很小。20 条分散主张，每条约 12 个单位，没有人工参考；C20 的核心现象就是已知的 DA/AC 与 conditional perfection 却没有引用；最接近的先例 SemIf 没有定位。按现状主会会以 limited novelty、insufficient scale、missing related work 为由拒稿 |
| **工业实践者**（决策组件落地） | **5.5/10** | 可以直接采纳的架构原则：能写代码就写代码；实体绑定用主键比较；证据充分性由检索契约或规则引擎承担；冻结序列化并做压力测试；调用端校验托管 API 的不变量（Jev 在 48 个响应里有 2 个违反自身契约）；方案一定要和 always-defer 与规则代码比较。单次 Jev 决策约 467 个输入 token，约 $0.00002，约 0.15 秒。但没有评估置信度阈值（0.9 阈值下自动执行的决策仍有 15% 是错的），对照模型最大只到 4B，也没有操作化 SLO，所以不能用来做选型 |
| **研究策略顾问** | **5.5/10** | 工艺值 8 分，科学产出值 3–4 分。AI 代理的产出能力远大于人工判断能力，每多做一个 12 单元的小诊断，边际信息接近零。应当收敛为一条主线（无依据承诺 + 置信度/程序门控能否拦截），以 C20 扩展实验为核心，并用付费外包解决评审问题 |

### 4.2 优势
1. 可审计性罕见：约 1,200 条 Jev 原始概率，原始 logits、失败账本和停止记录全部公开，独立复算全部一致。
2. 冻结可信度有第三方佐证（GitHub 服务器时间），没有 force-push。
3. 失败和负结果如实发布（line/joint 两项筛选失败、do_sample 事故、payment smoke 5/6）。
4. 有几条定位清晰的诊断：归属与读取可以分离（21:0，p≈5e-7）；执行正确不等于事实正确；指标陷阱；格式门把接口问题伪装成能力问题。
5. 数据审计有独立价值：EXtrA 的 198/200 上限、QA4PC 缺变量的树、ShARC 字段说明与实际不符、3,334 对清单。
6. 时效性：在生态出现的两周窗口内，对一个新上线的闭源决策 API 做了独立的冻结实测。

### 4.3 弱点
1. 统计功效几乎为零，有效样本常常只是 3–6 个模板族。
2. 合成区由程序主导，“是否需要模型”在结构上无法检验。
3. 人工参考几乎为零；唯一一次人工评审就提出了实质异议。
4. 被测系统的主要卖点（置信度与选择性执行）没有测。
5. 文献定位有关键缺口（SemIf、DA/AC、AbstentionBench、QuestBench 等）。
6. 若干头条受构造混杂或读出退化影响（BF16 并列、非原生格式、常数坍缩、视图构造）。
7. 外部效度风险：Jev 可能漂移，基座未公开。

### 4.4 新颖性与最接近的先前工作

| 主张 | 最接近的先例 | 本仓库的增量 | 新颖性 |
|---|---|---|---|
| C1 取消范围 | Laya Feishu 诊断（带 Jev 成对输出）、SemIf 自写决策、CheckList | 同词四变体 + 程序对照 | 低 |
| C2 N0/N1/K1 与布局 | Kev README 与 probe、FormatSpread | 固定历史版本的复现与布局消融（但格式不是原生的） | 低 |
| C3–C5 证据充分性与 facts+执行 | Sufficient Context、QuestBench、AbstentionBench、Binder、Logic-LM、LINC | 成对删除设计；缺失字段 11/11 照抄外来值 | 低到中 |
| C6–C10 归属 | Feng & Steinhardt（绑定）、Legible Failures | 行级分离观测 | 低到中 |
| C11–C13 候选完整性与弃权 | Ling et al.、AbstentionBench、Liu et al. AAAI-26 | 4B greedy 设置下的小规模复现 | 低 |
| C14–C18 接口与映射 | SemIf（direct logits 对 JSON）、PriDe、“My Answer is C”、Let Me Speak Freely、Verma 2020 | 字母桥 162/162 的干净识别 | 低 |
| C16 分解执行 | QA4PC/LDPC；TypeSafe 官方 “narrow questions + defer to code” | 对厂商推荐工作流的独立检验（仓库没这样定位） | 低到中，有实践价值 |
| C19 源标签审计 | Northcutt 2021、Verma 2020 | QA4PC 约三分之一标签可疑 | 低 |
| C20 规则方向 | Holliday et al. EMNLP 2024；Geis & Zwicky 1971；Horn 2000；LogicBench | 在“专用校准决策 API + 明确古典语义指令”条件下仍出现，与 4B 逐项相同，并有置信度差异 | 目前低；补人类基线和多模型后可到中 |

### 4.5 综合评分
**研究价值 5/10**。当前可发表性：arXiv 技术报告或数据审计短文可行；补全后可投 workshop；TMLR 要等到完成一项有功效、有人工标签的确认研究；主会目前不现实。

---

## 5. 前景与计划

### 5.1 仓库自述的计划、门槛与当前状态
- **门槛（G1–G7）**：G1 两名独立人工评审加裁决；G2 更强的普通对照模型（区分 capability reference 与 budget-constrained）；G3 在新材料上确认（已检视的 cohort 不能当确认集）；G4 公平的接口、辅助与成本核算；G5 必须超过已知语法程序；G6 HF 发布排在数据、许可和评审就绪之后；G7 先冻结，只跑一次，不做 prompt 搜索。
- **已准备但未执行**：ShARC 评审后比较（Jev 96 次调用 + Qwen 192 次生成，卡在 0/60 份评审）；QA4PC 24 场景回顾评审；72 条候选覆盖评审与新面板；payment 范围异议裁决；更强对照模型的获取；rule-direction 新表示对比；evidence-gap 216 条保留集；144 对改写的语言迁移；next-study 第二阶段 H0/H1 训练；决策审计工具包；HF 数据集。
- **暂停状态**：STAGE_LOG.md:26-28 “User stop instruction: finish this round and pause… Future work above remains proposed, not queued for execution.” README 没有写明暂停。
- **未决事项**：评审队列约 828 项（非作者只完成 96 项）；没有 ≥8B 的对照模型（本机 16GB，Qwen3-8B BF16 需要 15.26 GiB）；QA4PC 许可未决；没有统一的待办和优先级；Jev 版本漂移没有预案。
- **关键路径**：所有计划最终都卡在两个外部决策上，一是**评审人力**，二是**对照模型预算**。工程侧早已不是瓶颈。

### 5.2 审计建议的路线图

**立即（1–2 周，不做新推理）**

| 行动 | 理由 | 成功标准 |
|---|---|---|
| 1. 选择性预测补充分析：各研究的 AUROC、risk-coverage、0.9/0.5 阈值下的自动化率与残余错误、Brier/ECE、按族或树的聚类 CI；Qwen 用候选概率，同口径 | 仓库已有但没用的最强信号，直接对应 Jev 的产品定位 | 每个研究三列：自动化率、残余错误、升级率，并写明“置信度挡不住哪类错误”（例如 DA 格中 22/24 的置信度 ≥0.9） |
| 2. 补统计：每个头条旁加上按 parent/tree 的精确配对检验与功效说明；做 6 组比较的随机效应合并（标为探索性）；做停止、修订和数据复用的登记表 | 否定结论需要写明功效；为确认研究估计效应量 | README 和 CLAIMS 每个头条都有 p/CI 和基线行 |
| 3. 补文献与定位：SemIf、Kev README、Laya、jev-benchmarks、TypeSafe 官方评测、Holliday 2024、Geis & Zwicky、Horn、AbstentionBench、QuestBench、“My Answer is C”、PriDe、Logic-LM、LINC；C20 改用 DA/AC 术语 | 成本最低、对审稿印象影响最大 | NOVELTY_MATRIX 新增“最近先例”一节 |
| 4. 重写入口：README 首屏控制在 800 词内（定义 Jev/Kev/Qwen、写明暂停状态、跨研究总表、最强平凡基线、Qwen 配置标签）；修数字粘连、Pages 首页、失效链接、CITATION、NOTICES 和许可地图；补第二位评审者的公开同意；给 HEAD 打 release 并挂 Zenodo DOI | 目前外部读者两分钟内看不懂项目 | 格式 lint 和 Pages 链接检查纳入 CI 并通过 |
| 5. 写一页 SLO：错误动作、错误承诺、过度弃权的上限与代价比，每次决策的总成本口径，必须击败的对照集合；同时写好止损条件 | 不操作化，长期问题就永远是 “remains open” | 这页文档在任何新推理前公开提交 |

**短期（1–2 月）**

| 行动 | 理由 | 成功标准 |
|---|---|---|
| 6. 解决评审瓶颈：只保留 QA4PC 24×2 和 C20 扩展的语义审阅两个队列，其余归档；招募 ≥2 名有报酬的非作者评审员；人类基线走众包（条件句推理不需要专业知识）；作者不算独立评审；裁决人盲于模型输出 | 所有确认性计划都卡在这里 | 6 周内拿到 2 份完整评审，报告 κ；众包基线 ≥60 人 |
| 7. 预注册 C20 扩展实验（OSF 外部时间戳）：≥5 种条件表达的改写族；≥60 个独立政策内容；显式方向说明作为干预臂；推荐采样且预算充足的 thinking 臂；更强的普通模型（托管 8B 以上或前沿 API）；当前 Kev-4B、Laya、SemIf 作为“开源 Jev 替代”臂；同一指令下的人类基线；主终点为 DA/AC 格的错误承诺率，另报置信度阈值下的残余错误；按功效定样本量（≥100 个独立单位）；只跑一次 | 最便宜、最干净的试验台，有现成的文献对照；能区分“模型缺陷”与“语用读法” | 冻结先于数据生成；执行中 0 次修订；无论结果如何都全部发布 |
| 8. 在已关闭的 cohort 上预注册一次“同价位强模型”对照（rule-direction 108、candidate 72、ShARC 24），标为 development，不改旧分数 | 区分“小模型不行”和“这个配置不行”的最便宜办法 | 给出 SLO 口径下的对比表（含单次成本和 p50/p95 延迟） |
| 9. 发布 arXiv 技术报告和博客，把约 1,200 条 Jev 原始记录整理成带数据卡的 HF/Zenodo 数据集 | 生态变化以周计，时效价值会衰减 | 报告只有 1–2 个核心主张；数据集附许可地图 |

**中期（3–6 月）**

| 行动 | 理由 | 成功标准 |
|---|---|---|
| 10. 在程序覆盖不到的自然语言材料上做一次确认：优先评估 QA4PC test 中约 133 棵只属于 test 的树（先核查与 ShARC 的重叠和许可）或经审校的真实政策文本；主终点只设一个，“证据不足时的错误承诺”；比较纯规则（遇到未知句法显式拒绝）、模型抽取 + ID 门 + 执行器、Jev + 置信度阈值、强开源模型；Holm 校正，用混合效应或 GEE，覆盖全部 6 种映射 | 这是作者自设研究顺序中从未走到的第二步，也是回答长期问题的唯一途径 | 已知语法程序在该数据上无法满分；主终点有效应量和 CI；人工参考 κ≥0.6 |
| 11. 投 workshop（Insights from Negative Results、TrustNLP、GEM 等，具体届次需自行核实）；出现第二个真实任务后再抽共享库和审计工具包 | 同行评审对负结果友好；共享库只在有复用需求时才值得做 | 收到审稿意见；新研究不再 sys.path 导入冻结脚本 |

**长期（6 月以上）**

| 行动 | 理由 | 成功标准 |
|---|---|---|
| 12. 二选一收束：(a) 若确认研究显示存在稳健的错误承诺，而置信度或程序门控能低成本拦截，就整合投 TMLR；(b) 若差距在公平接口和预算下消失，或已被开源替代品解决，就写成有界负结果并结项。只有在未见数据上出现可重复的机制差距，才考虑 H0/H1 训练 | 训练类研究成本高，前提都还没满足 | 一个有统计支撑、有人类参照的核心主张被接收，或有一份边界清晰的结项报告 |
| 13. 托管决策 API 漂移监测：固定锚点子集，定期重测 Jev/Kev/Laya/强开源模型的 argmax、置信度、契约违规率、时延和价格 | Jev 刚上线两周，可能漂移 | 至少连续 3 个版本周期有可比数据 |

**应停止或转向的条件**
- **立即停止**：不要再在已检视的合成 cohort（72 条开发文本、24 个 ShARC 输入、72 个候选输入、108 个规则输入）上加 prompt、读出、映射或上限变体，也不要再开 12 单元规模的新诊断。
- **评审止损**：6 周内拿不到 ≥2 份非作者完整评审，就放弃自建标签路线，改用自带人工标签的公开数据（QA4PC test、ConditionalQA），并以技术报告结项。
- **主线止损**：在功效充足的确认实验中，出现以下任一情况就转向或结项：Jev 与最强开源配置的差距落在预设的 ±10pp 等价界内；显式方向说明或简单程序门控已把错误承诺降到 SLO 以下（问题就变成规格问题）；人类基线在 DA/AC 格与模型同样“出错”，且裁决认为参考语义有争议（转向“政策语言规范化”方向）。
- **资源止损**：Jev 的锚点子集出现漂移时，把它当新系统处理；单项确认实验的花费超过事先写定的上限，就停止扩样。
- **产出止损**：3 个月内既没有 arXiv 报告，也没有外部评审或复现参与，就把精力转到写作和投稿，不再做实验。

### 5.3 把约 20 个小研究收敛成 1–2 个成果

**成果 A：技术报告或 workshop 论文（8–12 页）**
暂定题目：*Typed Decision APIs Commit Under Missing Evidence and Inherit Conditional Fallacies: An Independent, Preregistered Audit of Jev and Small Open Models*

1. **引言**：类型化决策 API 的生态（Jev/Kev/Laya/SemIf）；长期问题；贡献分三点：跨研究的无依据承诺现象、argmax 与置信度双口径、C20 受控实验加人类基线。
2. **相关工作**：SemIf、Kev、Laya、TypeSafe 官方评测；DA/AC 与 conditional perfection（Geis & Zwicky、Horn、Holliday 2024）；弃权（AbstentionBench、QuestBench、Sufficient Context）；接口与选项偏差（PriDe、“My Answer is C”）；LLM + 求解器（Binder、Logic-LM、LINC）。
3. **评测工艺**：冻结 → 推送 → 推理的外部时间戳；原始日志；零模型对照；平凡基线；聚类统计（这一节可以写成独立的方法学贡献）。
4. **回顾性证据（探索性）**：6 组 Jev 对 Qwen 正面比较（5 胜 1 平 0 负，写明聚类 CI 和混杂）；跨研究的无依据承诺表；置信度 AUROC（0.974 / 0.964 / 0.675）。
5. **核心实验（预注册）**：C20 扩展。改写族 × 显式方向干预 × 模型（Jev、强开源、Qwen3.5 推荐 thinking、Kev/Laya/SemIf） × 人类基线；主终点为 DA/AC 错误承诺率，次要终点为置信度阈值下的残余错误。
6. **归属与接口的补充发现**：行级分离与 ID 门（request-ownership），同时写明程序已满分、门的覆盖范围等于解析；接口陷阱（分隔符、格式门、常数坍缩、BF16 并列）。
7. **局限**：合成模板、源标签、单机、Jev 可能漂移、AI 代理自主程度的声明。
8. **结论与部署建议**：模型只做窄抽取；归属、方向和充分性由程序与契约负责；置信度阈值能挡住一部分错误但挡不住方向误读。
- 附录：约 18 个研究的一页摘要与失败、修订登记表。

**成果 B：数据与工具**
- HF/Zenodo 数据集：约 1,200 条 Jev 原始概率，配 Qwen/Kev 对照记录，附数据卡和按路径的许可地图。
- 数据勘误短文或 issue：EXtrA 中可见输入相同但标签不同的 2 对、QA4PC 缺变量的树、ShARC 字段说明与数据不符。
- 最小的决策审计工具（映射校验、实际生效的生成配置断言、并列与坍缩检测、API 不变量校验、只尝试一次的 journal），前提是有第二个真实任务。

---

## 6. 附录

### 6.1 独立复算明细（补充）
- **Jev 对 Qwen 6 组正面比较**（按 Qwen 最好一路计的正确率差）：取消范围 +0.135；candidate +0.090（按原生读出为 +0.458）；ShARC +0.271；QA4PC 阶段 G +0.208；QA4PC 接口 +0.083；rule-direction 0。
- **聚类精确检验**：原始研究 McNemar b=4、c=0，p=0.125（按族聚类的 bootstrap 为 [-1, 0]，30% 的重抽样差值为 0）；ShARC Jev 对 Qwen direct，树级 p=0.148/0.219，Jev 对 copy-last p=0.75；QA4PC 接口 p=0.25–0.37；candidate p=0.0156（但此时 Qwen 在映射 1 下就是常数）；Holm 校正后最小 p=0.109。
- **功效**：n=12、20pp 时精确 McNemar 功效为 2.6–5.8%；80% 功效需要 47–91 个独立 parent；10pp 差异约需 249 个。
- **Jev 置信度**：rule-direction AUROC 0.974（Qwen 首 token 0.802）；0.9 阈值下自动执行 198 条，其中 30 条错误，升级 18/48 个错误，误升级 0/168；candidate AUROC 0.964；QA4PC 0.675（43 个不一致中 9 个 confidence ≥0.9）。confidence 等于 (k·p_max−1)/(k−1)，偏差 ≤0.015。
- **BF16 并列**：evidence-gap N0 33/216；next-study N0 17、N1 5；fact-execution N0 direct_0 15/72；QA4PC 阶段 10；接口 5；request-ownership 20/500（不影响终点）；candidate 2；finite 1。
- **Qwen 读出坍缩**：finite order1 为 23/24 Yes；candidate 原生映射 1 为 72/72 VALID；QA4PC 阶段映射 0 下 no 召回 0/26。
- **成本**：rule-direction 中 Jev 每次决策约 467 个输入 token，约 $0.00002，约 0.15 秒；原始研究 Jev 共 $0.003762；payment $0.0103；candidate $0.0095；ShARC $0.00127。

### 6.2 关键文件索引
- **入口与综述**：README.md、RESEARCH_INDEX.md、RESEARCH_CLAIMS.md（C1–C20）、NOVELTY_MATRIX.md、STAGE_LOG.md（门槛与暂停，:26-28、:661-675）、CHANGELOG.md、REPRODUCIBILITY.md、THIRD_PARTY_NOTICES.md、CITATION.cff、.github/workflows/check.yml。
- **原始研究**：PROTOCOL.md、core.py、run.py、analyze.py（默认模式会覆盖 README）、replicate.py、verify_evidence.py、data/cases.jsonl、results/REPORT.md、results/summary.json、provenance/。
- **各研究（research/…）**：next-study/（study.py、vendor/kev/model.py、RESEARCH_NOTE.md、PLAN.zh-CN.md）、layout-boundary/、evidence-gap/（gap_data.py、NEXT_STEPS.md）、evidence-guards/、fact-execution/（RESULTS.md、LINE_*、JOINT_*、VISIBLE_ID_GATE_AUDIT.md、scope_gate.py）、request-ownership/、payment-ownership/（RESULTS_V02.md、REVIEW_DISPOSITION.md）、candidate-completeness/（RESULTS.md、REASONING_RESULTS.md、NEXT_RESEARCH_GATES.md）、decision-sufficiency/、baseline-readiness/、generation-calibration/（interface.py，涉及 presence penalty）、action-backends/、external-validation/（TASK_CARD.md、COMPARISON_DRAFT.md、public-review/）、source-label-screen/、finite-choice-readout/、implementation-audit/、qa4pc-audit/、qa4pc-stage-attribution/、qa4pc-answer-interface/（SOURCE_AUDIT.md）、rule-direction/（plan.py、RESULTS.md）。
- **公开页面（docs/）**：index.html（原始四行挑战，“Latest” 已过时）、rule_direction.html、source_label_screen.html、candidate_coverage.html、joint_route.html、request_switch.html、risk_tradeoff.html、payment_ownership_v02.html（payment_ownership.html 已被取代）。

### 6.3 术语表
- **N0 / N1 / K1**：N0 = Qwen3-4B-Base 原生 LM head 读字母 logits；N1 = 同一底座 + 历史 Kev LoRA，仍用原生读出；K1 = N1 的骨干 + Kev pointer head（`<decide>` 与 `</opt>` 隐状态做双线性打分）。
- **L0 / L1 / L2**：Kev 研究的三种输入布局（证据/策略放在 state 还是 question）。L1 与 L2 对原生路径逐 token 相同。
- **parent / 母例 / tree**：同一构造的一组视图，是真正的独立单位。**complete parent / complete case / complete pair**：该组所有视图在所有映射或顺序下全部答对才算通过。
- **视图**：full、hold（记录倒序）、flip（关键关系翻转，答案应该变）、missing / decisive_missing（删掉决定性事实，应判 INSUFFICIENT）、nondecisive_missing（删掉无关事实，答案应保持）、conflict。
- **false commitment（FC，错误或无依据承诺）**：参考为 INSUFFICIENT / NOT_ESTABLISHED / maybe 时，却给出了确定动作。
- **needless / unnecessary deferral（不必要延迟）**：参考是确定答案时，却选择了不足或延迟。
- **mapping（映射）**：语义标签与 A/B/C 字母的对应顺序。映射敏感性指换顺序后结果是否改变。
- **source agreement（源标签一致率）**：与上游数据集标签的一致率，不等于经人工核验的正确率。
- **known-grammar program（已知语法程序）**：针对构造语法专门写的解析器加规则执行器，零模型调用。
- **copy-last**：复制最后一条历史回答作为决策的浅层对照。**always-defer/keep/maybe**：常数对照。
- **D/G/F/L**（QA4PC 阶段研究）：D 直接判断；G 附人工决策图；F 逐条事实判断再用代码组合；L 给定参考事实只做执行。
- **lure**：目的地只等于另一笔订单原支付方式的诱导输入。
- **parity 检查**：Kev packed mask 与标准因果前向的数值一致性检查。
- **ID 门（visible-ID gate）**：用正则解析每行的请求 ID，与目标不等时丢弃该行的确定性程序门。
- **DA / AC / conditional perfection**：否定前件 / 肯定后件 / 把 “if” 读成 “if and only if” 的语用加强。
- **ICC / 有效样本量**：重复测量之间的相关性；ICC 高时，144 个决策的信息量只相当于约 25 个。
- **SLO**：服务水平目标，这里指可接受的错误率、延迟与成本上限。
