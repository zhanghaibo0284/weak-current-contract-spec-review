# 跨平台导入：变量与占位符对照

本目录不含任何平台专有语法：文件格式为 Markdown / JSON / YAML / 纯文本；占位符统一使用
`{{NAME}}` 双花括号（通用模板记号，不是任何平台的 DSL）。导入目标平台时按下表批量替换即可。
若目标平台使用不同的占位符写法（例如 `${NAME}`、`{NAME}`、`<NAME>`），先整体替换记号风格，
再逐项填值；**不要改动字段名、编号与判定口径**。

---

## 1. 占位符总表

| 占位符 | 含义 | 默认值 / 示例 | 替换时机 | 出现位置 |
|---|---|---|---|---|
| `{{SKILL_ROOT}}` | 本目录在目标平台的挂载根路径 | `.`（本目录） | 导入时（必填） | `README.md`、`SKILL.md` 文件索引 |
| `{{RULES_DIR}}` | 规则目录相对路径 | `rules/` | 导入时 | `SKILL.md`、`rules/config.json` |
| `{{TEMPLATES_DIR}}` | 模板目录相对路径 | `templates/` | 导入时 | `SKILL.md`、`rules/config.json` |
| `{{CONFIG_PATH}}` | 配置文件路径 | `rules/config.json` | 导入时 | `SKILL.md` 第 7 节 |
| `{{RULESET_VERSION}}` | 规则集版本 | `1.0.0` | 导入时 | 报告概览、`rules/config.json` |
| `{{RULESET_CHECKSUM}}` | 规则集校验和（用于审计留痕） | 运行前计算 | 运行时（必填） | 报告概览 |
| `{{PROJECT_NAME}}` | 项目名称 | 从材料读取 | 运行时（必填） | `templates/review-report.md` 标题 |
| `{{REVIEW_BATCH}}` | 审查批次前缀，用于问题编号 | `CSR` | 运行时 | `templates/issue-record.yaml` |
| `{{MATERIAL_MANIFEST}}` | 本批材料清单（文件名/版本/日期/页码基准） | 从输入材料生成 | 运行时（必填） | 报告概览、`rules/inputs.md` |
| `{{PROJECT_BASELINE}}` | 项目基线（车站数 N / 冗余层级 R / 点数 P / 链路数 L / 并发 C / 计量口径） | 建基线阶段生成 | 运行时（必填） | `templates/auxiliary-tables.md` |
| `{{OUTPUT_PATH}}` | 报告与台账的落盘位置 | 由目标平台决定 | 运行时（必填） | `rules/workflow.md` 步骤 6 |
| `{{OUTPUT_FORMAT}}` | 输出载体 | `markdown` / `json` / `table` | 导入时 | `templates/output-schema.json` |
| `{{THRESHOLDS}}` | 阈值组（数量偏差、参数余量、页码估算） | 见 `rules/config.json` | 导入时 | `rules/config.json` |
| `{{SEVERITY_LABELS}}` | 风险等级词表 | 高 / 中（待核验）/ 低 / 不适用 | 导入时 | `rules/config.json`、`rules/severity.md` |
| `{{ROLE_MAP}}` | 8 类角色与实际岗位映射 | PM/TE/CM/PR/QA/LG/OM/FI | 导入时 | `rules/config.json`、`rules/workflow.md` 10.3 |
| `{{DIMENSION_MAP}}` | 12 维度与组织内部审查分类的映射 | DIM-01 ~ DIM-12 | 导入时 | `rules/config.json` |
| `{{SENSITIVITY}}` | 召回档位 | `wide`（召回优先） | 导入时 | `rules/config.json` |
| `{{TEXT_SEARCH_BACKEND}}` | 文本检索能力入口（关键词 / 正则 / 共现 / 上下文窗口） | 由执行主体提供 | 导入时（必填） | 流程步骤 2~4 |
| `{{TABLE_READ_BACKEND}}` | 表格读取能力入口 | 由执行主体提供 | 导入时（必填） | `rules/inputs.md`、数量核对 |
| `{{STRUCTURED_OUTPUT_BACKEND}}` | 结构化输出能力入口 | 由执行主体提供 | 导入时（必填） | 流程步骤 6 |
| `{{DOC_PARSER}}` | 文档解析实现（Word / PDF / Excel） | 由执行主体提供 | 导入时（按需） | `rules/inputs.md` |
| `{{ANNOTATION_BACKEND}}` | Word 原文分色标注实现（可选能力） | 无则跳过，不影响输出 | 导入时（可选） | 报告第 7 节 |
| `{{PAGE_HINT}}` | 页码提示语 | 见 `templates/review-report.md` | 导入时 | 报告 / 台账 / 调用界面 |
| `{{BOUNDARY_NOTICE}}` | 边界声明全文（`rules/limitations.md`） | 原样附上 | 运行时（必填） | 报告尾部、台账表头、调用界面 |
| `{{EXECUTOR_ID}}` | 执行主体标识（台账留痕用） | 可留空 | 运行时 | 报告概览 |
| `{{REVIEW_PROFILE}}` | 审查档位 | `standard` / `quick` / `verify` | 运行时 | `rules/config.json`、报告概览 |
| `{{STANCE}}` | 审查立场 | `seller` / `gc` / `owner` / `supervisor` | 运行时 | `rules/config.json`、报告概览 |
| `{{LEDGER_PATH}}` | 覆盖台账落盘位置 | 由目标平台决定 | 运行时 | `templates/coverage-ledger.md` |
| `{{RFI_PATH}}` | 澄清问题单落盘位置 | 由目标平台决定 | 运行时 | `templates/rfi-list.md` |
| `{{KNOWLEDGE_BACKEND}}` | 外部知识检索能力（标准年号、CPU 支持列表等） | 无则相关项一律判「待核验」 | 导入时（按需） | 交叉检查 1、`rules/standards-index.md` |

> 说明：`{{RULESET_VERSION}}`、`{{SEVERITY_LABELS}}`、`{{ROLE_MAP}}`、`{{THRESHOLDS}}` 等
> 均有默认值，导入时可直接沿用 `rules/config.json`；标为「必填」的多为运行时业务变量。

### 1.1 `{{RULESET_CHECKSUM}}` 计算规范

为避免「校验和不可复现」，统一如下（实现见 `verify_skill.py --checksum`）：

1. 取本目录全部 `.md` / `.json` / `.yaml` 文件（含 `MANIFEST.md`），排除 `.git`、`__pycache__`、`samples/out/`。
2. 按**相对路径的 UTF-8 字节序升序**排序。
3. 对每个文件依次 `hash.update(相对路径.replace("\\","/").encode())`、`hash.update(b"\0")`、`hash.update(原始字节)`。
4. 算法 SHA-256，输出小写 64 位十六进制；报告可截断为前 12 位，但须标注「截断」。
5. 规则内容任何改动都会改变校验和；仅改报告模板也计入（属于契约变更）。

> 若目标平台无法计算，必须留空并显式写「校验和未计算」，不得编造值。

---

## 2. 按平台形态的替换要点（中性描述，不绑定任何具体产品）

| 平台形态 | 需要处理的差异 | 处理方式 |
|---|---|---|
| 以「单一提示词 + 附件」载入能力的平台 | 一次只能读一个入口文件 | 以 `SKILL.md` 为入口；按第 1 节文件索引把 `rules/`、`templates/` 内容按需拼入上下文，或挂载为可检索附件 |
| 支持目录挂载的技能平台 | 目录可直接挂载 | 设置 `{{SKILL_ROOT}}`；确认 `rules/`、`templates/` 相对路径可解析 |
| 以函数/工具编排执行的能力体 | 检索、读表、输出由外部工具提供 | 把 `{{TEXT_SEARCH_BACKEND}}` 等映射为具体工具名；流程顺序与分支逻辑不变 |
| 以配置文件驱动的平台 | 阈值、词表需注入平台配置 | 读取 `rules/config.json`，映射 `{{THRESHOLDS}}`、`{{SEVERITY_LABELS}}`、`{{ROLE_MAP}}` |
| 占位符记号不同的平台 | `{{NAME}}` 不被识别 | 全目录批量替换记号风格后再填值；字段名与编号不得改动 |
| 无文件写入能力的平台 | 无法落盘报告 | 把 `{{OUTPUT_PATH}}` 替换为「直接返回结构化结果」，7 字段契约不变 |
| 仅支持纯文本上下文的平台 | JSON/YAML 附件需转换 | `rules/config.json` 与 `templates/output-schema.json` 可转为等价表格描述，字段语义不变 |

---

## 3. 不可替换项（改动即视为改变技能定义）

- `SKILL.md` 第 2 节触发条件、第 3 节审查目标 G1~G6、第 4 节六步流程顺序与顺序约束、
  第 5 节 7 字段输出约束、第 6 节硬约束；
- `rules/checkitems-risk.md`（A01~T06，108 条）、`rules/checkitems-quantity.md`（R01~R16，16 条）、
  `rules/checkitems-parameter.md`（P01~P63，63 条）中的编号、异常判定信号与处置建议；
- `rules/severity.md` 的等级定义、待核验语义与升级规则；`rules/limitations.md` 的 7 条声明；
- `rules/cross-checks.md` 的 7 组交叉关系；`rules/adjudication.md` 的六类异常与 3 个判定范式；
- `templates/output-schema.json` 的 7 个字段名与语义（可扩展，不可删减、不可改名）。

---

## 4. 移植后校验清单

1. 核对 187 条检查项编号无缺失、无重复（108 / 16 / 63）。
2. 核对 12 个维度 DIM-01~DIM-12、8 类角色、4 类规则集仍在 `rules/config.json` 中。
3. 用样例材料跑一遍六步流程，确认每条问题均含 7 字段且附 `{{BOUNDARY_NOTICE}}`。
4. 用已知风险条款回测召回率：宁可误报不可漏报，不得因否定句式剔除命中项。
5. 核对 `rules/limitations.md` 已在报告、台账表头与调用界面显著呈现。
