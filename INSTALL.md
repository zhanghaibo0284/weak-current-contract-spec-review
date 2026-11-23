# 安装指南

本仓库是一个平台中立的 Skill 包。安装 = 把整个目录放到平台技能目录 + 校验通过，共 40 个文件。

- 版本：v1.2.0
- 校验值：以仓库根目录 `CHECKSUM.txt` 为准

---

## 1. 文件清单（必须完整复制）

```text
weak-current-contract-spec-review/
├── SKILL.md
├── README.md
├── INSTALL.md
├── PORTING.md
├── MANIFEST.md
├── CHECKSUM.txt
├── verify_skill.py
├── rules/        # 18 个：187 条规则、config.json、schema、标准基线
└── templates/    # 9 个：问题清单、覆盖台账、RFI、报告、成本模型等
```

- 合计 **40 个文件**（不含 `.git`）。
- `rules/` 与 `templates/` 必须整目录复制，缺一个都会导致规则失效或台账无法生成。
- 复制时排除：`.git`、`.screenshots`、`__pycache__`。

---

## 2. 目标路径

| 平台 | 目标目录 |
|---|---|
| Claude Code（个人） | `~/.claude/skills/weak-current-contract-spec-review/` |
| Claude Code（项目） | `<项目>/.claude/skills/weak-current-contract-spec-review/` |
| Trae（个人） | `~/.trae-cn/skills/weak-current-contract-spec-review/` |
| 其他工具 | 由其技能/指令目录决定；无技能机制时放到任意固定目录，按第 3 节提示词引用 |

> 上表仅供人工安装参考。把任务交给智能体时，应让它按自身平台约定确定目录，不要照抄此表。

要求：

1. 目录名固定为 `weak-current-contract-spec-review`，与 `SKILL.md` 的 `name` 一致；
2. `SKILL.md` 必须直接位于该目录下，**不要多套一层**；
3. 安装后重启平台（Claude Code 需新开会话）才会加载。

---

## 3. 安装（推荐交给智能体执行）

把下面整段发给任意支持文件操作的智能体即可。提示词不指定具体产品，由智能体按自身平台的约定确定安装目录：

```text
安装技能：https://gitee.com/zhanghaibo0284/weak-current-contract-spec-review.git

按以下步骤执行，不要凭印象猜测路径：
1. 克隆到临时目录：git clone --depth 1 <上述地址> "$env:TEMP\csr_install"
2. 确定目标目录：
   - 若你支持技能机制，使用你所在平台官方约定的个人技能目录，
     目录名固定为 weak-current-contract-spec-review；
   - 若不支持技能机制，安装到任意固定目录，并告知用户后续如何触发；
   - 无法确定时先询问用户，不要自行假设。
3. 将仓库内容完整复制到目标目录：
   SKILL.md 必须直接位于该目录下，不得多套一层；
   必须包含 rules/ 与 templates/ 两个完整目录；
   排除 .git、.screenshots、__pycache__
4. 确认文件总数为 40（不含 .git）
5. 进入目录运行：python verify_skill.py，失败数必须为 0；
   再运行 python verify_skill.py --checksum，输出须与 CHECKSUM.txt 完全一致
6. 清理临时目录，报告：安装路径、文件数、校验结果、指纹比对结果
7. 不得修改 rules/ 与 templates/ 中任何文件
```

手动安装时，按第 1 节清单直接复制目录，再执行第 4 节校验即可。

不支持技能机制、只能读取指令文件的智能体，将技能放到任意固定目录，并在其指令文件中注明：

```text
当用户要求审查合同/技术规格书时，读取 <安装路径>/SKILL.md，按其流程执行。
```

---

## 4. 验证与失败判据

```powershell
cd ~/.trae-cn/skills/weak-current-contract-spec-review   # Claude Code 换为 ~/.claude/skills/...
python verify_skill.py
python verify_skill.py --checksum
```

通过标准（三条同时满足）：

1. 校验失败数为 **0**；
2. 文件总数为 **39**（不含 `.git`）；
3. `--checksum` 输出与仓库根目录 `CHECKSUM.txt` 完全一致。

任一不满足即视为**安装未完成**，不要开始审查，重新完整复制后再校验。

依赖说明：

- Python 3.8+ 仅用于运行 `verify_skill.py`，不装也能审查；
- 解析 `.docx` 建议安装 `python-docx`：`python -m pip install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple`；
- 审查过程离线运行，无需 API Key。
