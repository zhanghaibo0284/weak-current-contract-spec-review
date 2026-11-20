# weak-current-contract-spec-review · 标准 Skill 目录

面向弱电 / 智能化 / 轨道交通机电集成项目的合同与技术规格书审查能力。
本目录是**平台中立的标准 skill 目录结构**：单一入口 + 外置规则 + 外置模板 + 外置配置 + 随包校验器。

---

## 目录结构（简）

```text
weak-current-contract-spec-review/
├── SKILL.md              入口：触发条件 / 审查目标 / 执行流程 / 输出约束 / 健壮性自检
├── README.md             本文件：快速上手
├── PORTING.md            跨平台导入：占位符、校验和算法、回测建议
├── MANIFEST.md           完整目录、逐文件索引、校验结果
├── verify_skill.py       结构一致性校验器（可复现）
├── rules/                规则、解析契约、标准基线、术语、配置
└── templates/            问题清单、覆盖台账、RFI、报告、成本模型
```

完整目录树、行数与校验和见 `MANIFEST.md`。

---

## 安装与部署

完整步骤见 [`INSTALL.md`](INSTALL.md)，以下为速查版。

### 环境要求

| 项 | 要求 |
|---|---|
| 平台 | Claude Code（`~/.claude/skills/`）或 Trae（`~/.trae-cn/skills/`） |
| 系统 | Windows 10/11、macOS 12+、Linux |
| Git | 2.20+（克隆与升级） |
| Python | 3.8+（可选，仅用于 `verify_skill.py` 自检） |
| python-docx | 建议安装，用于解析 `.docx` |
| 网络 | 仅安装时需要；审查过程离线，无需 API Key |

### 依赖安装

```powershell
python -m pip install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple
```

```bash
python3 -m pip install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 方式一：一键脚本

```powershell
git clone --depth 1 https://gitee.com/zhanghaibo0284/weak-current-contract-spec-review.git
cd weak-current-contract-spec-review
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target trae   # 或 -Target claude
```

```bash
git clone --depth 1 https://gitee.com/zhanghaibo0284/weak-current-contract-spec-review.git
cd weak-current-contract-spec-review
chmod +x install.sh
./install.sh --target trae        # 或 --target claude；省略则自动识别
```

脚本会校验 `SKILL.md`、备份同名旧目录、复制文件（排除 `.git`）、运行结构校验并比对 `CHECKSUM.txt`。

### 方式二：手动安装

1. 克隆或解压仓库；
2. 将内容复制到 `~/.claude/skills/weak-current-contract-spec-review/` 或 `~/.trae-cn/skills/weak-current-contract-spec-review/`；
3. 确保 `SKILL.md` 直接位于该目录下（不要多套一层），排除 `.git`；
4. 重启 Claude Code / Trae。

### 方式三：让智能体安装

```text
安装技能：https://gitee.com/zhanghaibo0284/weak-current-contract-spec-review.git
克隆后把内容放到 ~/.claude/skills/weak-current-contract-spec-review/（Trae 为 ~/.trae-cn/skills/...），
确保 SKILL.md 直接在该目录下、排除 .git，然后运行 python verify_skill.py 与
python verify_skill.py --checksum，将结果与 CHECKSUM.txt 比对后报告。
```

### 配置

配置集中在 `rules/config.json`，可调阈值、等级升级条件、角色/立场映射、审查档位与召回档位；规则文件与 7 字段契约不可改。首次使用需确认**审查立场**（`seller`/`gc`/`owner`/`supervisor`）与**审查档位**（`quick`/`standard`/`verify`）。

### 启动与使用

技能为对话内调用，无需常驻进程：

```text
用 weak-current-contract-spec-review 审查 E:\项目\XX技术规格书.docx
/weak-current-contract-spec-review E:\项目\XX技术规格书.docx
```

标准产出：问题清单（7 字段）、覆盖台账（187 条）、评审报告、澄清问题单、解析质量声明。

### 安装校验

```powershell
cd ~/.trae-cn/skills/weak-current-contract-spec-review
python verify_skill.py              # 结构校验应全部通过
python verify_skill.py --checksum   # 与仓库根目录 CHECKSUM.txt 比对
```

### 升级与卸载

```powershell
git -C <仓库目录> pull
powershell -ExecutionPolicy Bypass -File <仓库目录>\install.ps1 -Target trae
Remove-Item "$env:USERPROFILE\.trae-cn\skills\weak-current-contract-spec-review" -Recurse -Force
```

### 故障排查

| 现象 | 处理 |
|---|---|
| 平台看不到技能 | 检查目录名、是否多套一层、是否重启 |
| 只输出泛泛建议 | 确认 `rules/` 与 `templates/` 已一起安装 |
| 无覆盖台账 | 声明使用 `standard` 档 |
| `.docx` 解析失败 | 安装 `python-docx`，旧 `.doc` 另存为 `.docx` |
| 校验失败 | 重新安装，核对 `CHECKSUM.txt` |

---

## 快速开始（面向使用者）

| 场景 | 档位 | 最小输入 | 主要产出 |
|---|---|---|---|
| 投标/售前快速筛查 | `quick` | 合同正文 + 设备材料表 | Top 风险清单 + 报价敞口提示 |
| 合同交底 / 详细评审 | `standard` | 合同 + 规格书 + 清单 + 报价册 | 问题清单 + 覆盖台账 + 报告 + RFI |
| 补遗后的增量复核 | `verify` | 既有台账 + 变更文件 | 版本差异表 + 受影响条目重判 |

执行顺序：`SKILL.md` 第 7 节 → `rules/inputs.md`（材料门槛）→ `rules/workflow.md`（六步）→ `templates/`（输出）。

使用前请确认：

1. 审查立场（`seller` / `gc` / `owner` / `supervisor`）——同一 ★ 条款对不同立场结论相反。
2. 审查档位（`quick` / `standard` / `verify`）。
3. 必需材料齐备度；不足 3/5 时会先出材料缺口清单，而不是 187 条空结论。

---

## 导入步骤

1. 把整个目录复制到目标平台的 skill 挂载点，设置 `{{SKILL_ROOT}}`。
2. 以 `SKILL.md` 作为**唯一入口**载入。
3. 按 `PORTING.md` 第 1 节替换占位符，并把 `{{TEXT_SEARCH_BACKEND}}`、
   `{{TABLE_READ_BACKEND}}`、`{{STRUCTURED_OUTPUT_BACKEND}}` 映射到执行主体提供的能力。
4. 读取 `rules/config.json` 注入阈值、等级词表、角色映射、审查档位与召回档位（默认 wide）。
5. 按 `SKILL.md` 第 7 节「快速调用顺序」执行；输出按 `templates/output-schema.json`。
6. 用已知风险条款样例回测召回率；改动后用 `python verify_skill.py` 做结构校验。

---

## 输出物

| 产物 | 模板 | 是否强制 |
|---|---|---|
| 问题清单（7 字段） | `templates/issue-list-template.md` | 强制 |
| 覆盖台账（187 条逐项结论） | `templates/coverage-ledger.md` | 强制（兑现 G1） |
| 评审报告（10 节） | `templates/review-report.md` | 强制 |
| 澄清问题单 / 材料缺口清单 / 版本差异 | `templates/rfi-list.md` | 有交底或改版时必须 |
| 解析质量声明 | `rules/parsing.md` 第 5 节 | 强制（随报告） |
| 成本量化 | `templates/cost-model.md` | 需要金额/工期暴露时 |

> 边界声明（`rules/limitations.md` 的 7 条）须原文附在报告、台账表头与调用界面。

---

## 三类基础能力要求

执行主体只需具备：文本检索（关键词 / 正则 / 共现）、表格读取、结构化输出。
文档解析、报告生成、原文标注等实现方式均可替换，本目录不指定具体实现技术。
若具备外部知识检索（`{{KNOWLEDGE_BACKEND}}`），可用于标准年号与 CPU 支持列表核对；不具备时相关项一律判「待核验」。

---

## 质量校验

```powershell
python verify_skill.py              # 33 项结构校验
python verify_skill.py --checksum   # 生成 {{RULESET_CHECKSUM}}
python verify_skill.py --ledger out/coverage-ledger.md   # 校验台账完整性
```

校验覆盖：文件存在性、规则条数与编号唯一/连续、枚举一致性、交叉引用可解析、
占位符闭环、旧章节号残留、MANIFEST 统计行。

---

## 不变式

触发条件、审查目标、六步流程顺序、7 字段输出约束、硬约束、检查项编号与判定口径、
等级定义、边界声明不可改写。可调整项仅限 `rules/config.json` 中的阈值、词表、角色映射、
维度名称、审查档位与召回档位。详见 `PORTING.md` 第 3 节。

---

## 版本与来源

- 版本 1.1.1：打包与安装修订——新增 `INSTALL.md`、`install.ps1`、`install.sh`、`CHECKSUM.txt`，补充 README 安装说明；规则文件与 7 字段契约未变。
- 版本 1.1.0，能力编号 CAP-CSR-001（在 1.0.0 基础上做向后兼容修订，7 字段与规则编号未变）。
- 1.1.0 主要变化：新增覆盖台账与校验器、补齐空模板、统一等级枚举、增加异常码与状态机、
  明确编号命名空间；均为增量，不破坏既有台账。
- 由单文件 `SKILL.md` v1.0.0 重构：规则、限制、流程、案例内容以原文为准。
- 原单文件保留在 `../弱电项目合同审查Skill/SKILL.md`，作为溯源基线。
