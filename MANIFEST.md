# MANIFEST · 完整目录结构与逐文件内容索引

> 本文件记录目录完整性、文件职责与内容来源，由 `verify_skill.py` 校验一致性。
> 校验项：文件存在性、规则条数与编号唯一性、枚举一致性、交叉引用可解析、占位符闭环、统计行一致。
> 任一文件增删或改写后，请运行 `python verify_skill.py` 并同步更新本文件。

## 1. 完整目录结构

```text
weak-current-contract-spec-review/
├── SKILL.md
├── README.md
├── INSTALL.md
├── PORTING.md
├── MANIFEST.md
├── CHECKSUM.txt
├── .gitignore
├── verify_skill.py
├── guard/
│   ├── canonical.py
│   ├── evolve.py
│   ├── selftest.py
│   └── validate.py
├── rules/
│   ├── adjudication.md
│   ├── capability.md
│   ├── checkitems-parameter.md
│   ├── checkitems-quantity.md
│   ├── checkitems-risk.md
│   ├── config.json
│   ├── configuration.md
│   ├── cross-checks.md
│   ├── dimensions.md
│   ├── glossary.md
│   ├── indexes.md
│   ├── inputs.md
│   ├── limitations.md
│   ├── parsing.md
│   ├── rule-record.schema.json
│   ├── severity.md
│   ├── standards-index.md
│   └── workflow.md
└── templates/
    ├── auxiliary-tables.md
    ├── cost-model.md
    ├── coverage-ledger.md
    ├── coverage-schema.json
    ├── issue-list-template.md
    ├── issue-record.yaml
    ├── output-schema.json
    ├── review-report.md
    ├── rfi-list.md
    └── run-manifest.schema.json
```

共 32 个文件，合计 2930 行（不含 MANIFEST.md 自身）。

## 2. 逐文件内容索引

| 路径 | 行数 | 字节 | 校验和（SHA-256 前 12 位） | 职责 | 来源 |
|---|---|---|---|---|---|
| `PORTING.md` | 94 | 8403 | `93def1a883a1` | 占位符目录、按平台形态的替换要点、校验和算法、回测建议 | 重新组织 + 本次补充 |
| `README.md` | 201 | 8712 | `3fe004e27b8f` | 目录说明 / 安装部署 / 快速上手 | 重新组织 |
| `INSTALL.md` | 105 | 4176 | `d2b9c30d565e` | 安装指南：文件清单、目标路径、安装提示词、校验与失败判据 | 新增 |
| `SKILL.md` | 192 | 13954 | `e114abb1cb07` | 标准 skill 唯一入口：触发/目标/流程/输出/硬约束 + 健壮性自检 | 重新组织 |
| `verify_skill.py` | — | — | — | 结构一致性校验器与校验和生成器 | 新增 |
| `templates/run-manifest.schema.json` | 66 | 1926 | `dd1c71786cfe` | 运行清单契约：输入/参数/规则/产物四类指纹 | 新增 |
| `guard/canonical.py` | 124 | 4049 | `8001a2b5dbd4` | 确定性内核：归一化、稳定排序、稳定编号、三类指纹 | 新增 |
| `guard/validate.py` | 92 | 3630 | `71949ecc21c8` | 一致性校验 C1~C5：字段/台账/互证/指纹 | 新增 |
| `guard/evolve.py` | 151 | 5962 | `7d6b901360fd` | 进化提案校验、五道门、原子落盘 | 新增 |
| `guard/selftest.py` | 198 | 6918 | `13f9c28d539d` | 确定性与进化门禁回归自检（19 项） | 新增 |
| `rules/adjudication.md` | 79 | 9771 | `a4c18c98f8ef` | 六类异常判定、3 个综合判定范式、召回优先词表 | 原 `SKILL.md` 第 9 章 |
| `rules/capability.md` | 91 | 7523 | `51e7c53d5de9` | 能力定位、适用/不适用场景、接入约定 | 原 `SKILL.md` 第 1~4 章与 12.3 节 |
| `rules/checkitems-parameter.md` | 145 | 38266 | `f80dd5f769c5` | 设备参数核实项 63 条（P01~P63 / 14 组） | 原 `SKILL.md` 第 8.3 节 |
| `rules/checkitems-quantity.md` | 31 | 9605 | `c739febd3fe4` | 数量配比核查项 16 条（R01~R16） | 原 `SKILL.md` 第 8.2 节 |
| `rules/checkitems-risk.md` | 228 | 65788 | `cfd7fd17903b` | 合同风险检查项 108 条（20 类 A~T） | 原 `SKILL.md` 第 8.1 节 |
| `rules/config.json` | 195 | 5932 | `aac4e1a9da8e` | 机器可读配置：阈值/词表/档位/状态/校验和规范 | 重新组织 + 本次扩展 |
| `rules/configuration.md` | 61 | 3792 | `ff07effc4e88` | 可配置项清单与规则外置结构（人读版） | 原 `SKILL.md` 第 12 章 |
| `rules/cross-checks.md` | 25 | 2279 | `3bd3e9040158` | 7 组贯穿性交叉检查，引用带规则集前缀 | 原 `SKILL.md` 第 8.4 节 |
| `rules/dimensions.md` | 60 | 7136 | `0f8f264af5f0` | 12 个审查维度与类别—维度映射 | 原 `SKILL.md` 第 6 章 |
| `rules/glossary.md` | 86 | 5157 | `6974e1168c3a` | 弱电/轨道/合同术语表 | 新增 |
| `rules/indexes.md` | 107 | 6788 | `31b85c5be9cc` | 角色映射、编号索引、证据来源对照、编号命名空间 A.4 | 原 `SKILL.md` 附录 A/B + 本次补充 |
| `rules/inputs.md` | 47 | 3467 | `5c7fb4f7ac08` | 材料齐备性检查与齐备度门槛（阻断规则） | 原 `SKILL.md` 第 5 章 + 本次补充 |
| `rules/limitations.md` | 20 | 1921 | `2b90056fdb04` | 边界与声明 7 条，须随输出呈现 | 原 `SKILL.md` 第 13 章 |
| `rules/parsing.md` | 98 | 5498 | `6401e23373d9` | 解析契约、异常码 E-01~E-08、降级与解析质量声明 | 新增 |
| `rules/rule-record.schema.json` | 87 | 1911 | `4534f4001236` | 单条规则的数据结构 | 重新组织 |
| `rules/severity.md` | 56 | 4269 | `ac2c0f6c5038` | 三级定义、待核验语义、升级规则、结论/等级消歧 | 原 `SKILL.md` 第 7 章 + 本次修正 |
| `rules/standards-index.md` | 84 | 4227 | `b5ad0ed4075f` | 常用标准规范基线与现行性核对方法 | 新增 |
| `rules/workflow.md` | 128 | 9146 | `9ead2d1a6fb7` | 六步流程、判定分支、角色、复核闭环、异常处理、状态机 | 原 `SKILL.md` 第 10 章 + 本次补充 |
| `templates/auxiliary-tables.md` | 25 | 967 | `e56ac50435c6` | 项目基线表、数量核对表 | 原 `SKILL.md` 第 11.2 节 |
| `templates/cost-model.md` | 64 | 3521 | `1f1f3f276f56` | 影响分析量化公式库 | 新增 |
| `templates/coverage-ledger.md` | 91 | 4478 | `d392b74b55e0` | 187 条逐项结论台账（G1 强制交付物） | 新增 |
| `templates/coverage-schema.json` | 143 | 4584 | `83a3a7168f4d` | 覆盖台账字段契约与条件约束 | 新增 |
| `templates/issue-list-template.md` | 65 | 5031 | `65d2fb603e9e` | 7 字段主模板、清单表头、填写示例、扩展字段、常见错误 | 原 `SKILL.md` 第 11.1 节 + 本次补齐 |
| `templates/issue-record.yaml` | 13 | 1407 | `44b586662bc9` | 单条问题记录样例 | 原 `SKILL.md` 第 11 章 |
| `templates/output-schema.json` | 131 | 4641 | `4868cae25a70` | 7 字段输出契约 + 7 个可选扩展字段 + 等级使用约束 | 重新组织 + 本次扩展 |
| `templates/review-report.md` | 33 | 2220 | `f15f3ca86cba` | 评审报告 10 节骨架、页码提示语、边界声明占位 | 原 `SKILL.md` 第 11.2 节 |
| `templates/rfi-list.md` | 79 | 4028 | `dfac11608235` | 材料缺口清单、澄清问题单、版本差异登记表 | 新增 |

## 3. 逐文件内容大纲（主要文件）

### `SKILL.md`

- ## 1. 文件索引
- ## 2. 触发条件（含 2.1 不触发条件）
- ## 3. 审查目标
- ## 4. 执行流程
- ## 5. 输出约束（含覆盖台账与扩展字段）
- ## 6. 硬约束
- ## 7. 快速调用顺序
- ## 8. 不变式
- ## 9. 健壮性与自检

### `rules/workflow.md`

- ## 10. 审查流程
- ### 10.1 六步标准流程
- ### 10.2 单项判定逻辑
- ### 10.3 角色与分工
- ### 10.4 复核与闭环
- ### 10.5 异常处理与降级（E-01~E-07）
- ### 10.6 状态机与增量复核

### `rules/severity.md`

- ### 7.1 等级定义与处置要求
- ### 7.2 待核验语义
- ### 7.3 升级规则（仅允许已定义等级）
- ### 7.4 判定结论与风险等级的关系（消歧）

### `rules/parsing.md`

- 输入格式矩阵 / 定位锚点规范 / 异常码与处置 / 表格读取规则 / 解析质量声明 / 禁止行为

### `templates/coverage-ledger.md`

- 生成规则 / 表头 / 分区模板 / 完整性自检 / 表头元信息

### 其余文件

| 文件 | 主要章节 |
|---|---|
| `rules/adjudication.md` | 9.1 六类异常、9.2 三个案例、9.3 话术词表（带规则集前缀） |
| `rules/capability.md` | 1 能力概览、2 适用场景、3 触发条件、4 审查目标、12.3 接入约定 |
| `rules/checkitems-risk.md` | 8.1 合同风险 108 条（A~T 共 20 类） |
| `rules/checkitems-quantity.md` | 8.2 数量配比 16 条 |
| `rules/checkitems-parameter.md` | 8.3 参数核实 63 条（G01~G14 共 14 组） |
| `rules/cross-checks.md` | 8.4 交叉匹配 7 组 |
| `rules/dimensions.md` | 6.1 核心维度、6.2 扩展维度、6.3 映射 |
| `rules/indexes.md` | A.1 角色映射、A.2 风险编号、A.3 参数组、A.4 命名空间、附录 B |
| `rules/inputs.md` | 5.1 必需材料、5.2 补充材料、5.3 质量与基线、5.4 齐备度门槛 |
| `rules/standards-index.md` | 方法、各专业基线、维护约定 |
| `rules/glossary.md` | 系统架构 / 冗余 / 数量 / 网络 / 机房 / 合同流程 |
| `rules/configuration.md` | 12.1 可配置项、12.2 外置结构、12.3 接入约定 |
| `templates/issue-list-template.md` | 7 字段、表头、示例、扩展字段、常见错误 |
| `templates/rfi-list.md` | 材料缺口清单、RFI、版本差异、交付节奏 |
| `templates/cost-model.md` | 变量、公式表、输出写法、禁止行为 |

## 4. 内容完整性校验

| 校验项 | 期望 | 实测 | 结果 |
|---|---|---|---|
| 合同风险检查项（RISK） | 108 | 108 | PASS |
| 数量配比核查项（QTY） | 16 | 16 | PASS |
| 设备参数核实项（PARAM） | 63 | 63 | PASS |
| 覆盖台账应审条数 | 187 | 187 | PASS |
| 审查维度 DIM | 12 | 12 | PASS |
| 角色 | 8 | 8 | PASS |
| 输出核心字段 | 7 | 7 | PASS |
| 扩展字段（可选） | 7 | 7 | PASS |
| 交叉检查组 | 7 | 7 | PASS |
| 边界声明条款 | 7 | 7 | PASS |
| 异常码 E-01~E-08 | 8 | 8 | PASS |
| 占位符登记 | 31 | 31 | PASS |

**总体：全部通过（以 `python verify_skill.py` 输出为准）**

## 5. 溯源

- 拆分来源：`../弱电项目合同审查Skill/SKILL.md`（v1.0.0，单文件版，保留未改动）。
- 规则内容以原文件为准；主入口、配置、模板、移植说明为重新组织，判定口径未改。
- 结构校验：本目录内 `verify_skill.py`（替代早期外部脚本，随包可复现）。
- 本次修订目标：消除编号同号歧义、补齐空模板、统一等级枚举、增加异常处置与可验证台账。

## 6. 原章节号 → 新文件路径对照（仅用于历史溯源）

> 本表只用于解释历史文档中的旧章节号；当前正文已全部改为路径引用，新文档不应再使用旧章节号。

| 原单文件章节 | 新位置 |
|---|---|
| 第 1~4 章 能力概览 / 适用场景 / 触发条件 / 审查目标 | `rules/capability.md`（入口摘要见 `SKILL.md` 第 2、3 节） |
| 第 5 章 输入材料要求 | `rules/inputs.md` |
| 第 6 章 审查维度体系 | `rules/dimensions.md` |
| 第 7 章 风险分级标准 | `rules/severity.md` |
| 第 8.1 节 合同风险检查项 108 条 | `rules/checkitems-risk.md` |
| 第 8.2 节 数量配比核查项 16 条 | `rules/checkitems-quantity.md` |
| 第 8.3 节 参数核实检查项 63 条 | `rules/checkitems-parameter.md` |
| 第 8.4 节 交叉匹配与联动检查 | `rules/cross-checks.md` |
| 第 9 章 常见问题判定依据 | `rules/adjudication.md` |
| 第 10 章 审查流程 | `rules/workflow.md`（概览见 `SKILL.md` 第 4 节） |
| 第 11.1 节 问题清单主模板 | `templates/issue-list-template.md` + `templates/issue-record.yaml` |
| 第 11.2 节 辅助模板 | `templates/auxiliary-tables.md` + `templates/review-report.md` |
| 第 12 章 配置化与平台中立约定 | `rules/configuration.md`（人读）+ `rules/config.json`（机器读） |
| 第 13 章 边界与声明 | `rules/limitations.md` |
| 附录 A / 附录 B | `rules/indexes.md` |
| 输出契约 | `templates/output-schema.json` |
| 移植占位符 | `PORTING.md` 第 1 节 |
