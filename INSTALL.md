# 安装与部署指南

本仓库是一个**平台中立的 Skill 包**，可安装到 Claude Code 或 Trae。安装本质是：把仓库内容放到对应平台的技能目录，目录名保持 `weak-current-contract-spec-review`，然后用 `verify_skill.py` 校验完整性。

- 版本：v1.1.1
- 包校验值：以仓库根目录 `CHECKSUM.txt` 为准（由 `verify_skill.py --checksum` 生成）
- 文件数：36（`SKILL.md` + `rules/` 18 个 + `templates/` 9 个 + 8 个文档/脚本/校验文件）

---

## 1. 环境要求

| 项 | 要求 | 说明 |
|---|---|---|
| 操作系统 | Windows 10/11、macOS 12+、Linux | 脚本提供 PowerShell 与 Bash 两个版本 |
| 平台 | Claude Code 或 Trae | 二选一，也可同时安装 |
| Git | 2.20+ | 用于克隆与升级；手动拷贝可不需要 |
| Python | 3.8+（可选） | 仅用于运行 `verify_skill.py` 自检 |
| python-docx | 建议安装 | 解析 `.docx` 正文与表格；不装则解析质量下降 |
| 网络 | 仅安装时需要 | 审查过程全程离线，无需 API Key |

---

## 2. 依赖安装

```powershell
# Windows（建议使用国内镜像）
python -m pip install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple
```

```bash
# macOS / Linux
python3 -m pip install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> 如果使用 Anaconda，请用 `python -m pip`，不要用 `conda install` 覆盖环境。
> 没有 Python 也能正常审查，只是无法执行结构自检。

---

## 3. 安装方式一：一键脚本（推荐）

先克隆仓库到任意临时目录：

```powershell
git clone --depth 1 https://gitee.com/zhanghaibo0284/weak-current-contract-spec-review.git
cd weak-current-contract-spec-review
```

### Windows

```powershell
# 自动识别已安装的平台（检测到 ~/.claude 或 ~/.trae-cn）
powershell -ExecutionPolicy Bypass -File .\install.ps1

# 或显式指定
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target trae
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target claude
```

### macOS / Linux

```bash
chmod +x install.sh
./install.sh              # 自动识别
./install.sh --target trae
./install.sh --target claude
```

脚本行为：

1. 校验当前目录存在 `SKILL.md`；
2. 识别目标平台技能目录；
3. 若同名目录已存在，重命名为 `弱电合同审查.bak-<时间戳>` 备份；
4. 复制全部文件（排除 `.git`、`.screenshots`、`__pycache__`）；
5. 自动运行 `verify_skill.py` 并比对校验指纹；
6. 输出安装路径、文件数与校验结果。

安装完成后**重启平台**（Claude Code 需新开会话）使技能生效。

---

## 4. 安装方式二：手动安装

| 平台 | 目标目录 |
|---|---|
| Claude Code（个人） | `~/.claude/skills/weak-current-contract-spec-review/` |
| Claude Code（项目） | `<项目>/.claude/skills/weak-current-contract-spec-review/` |
| Trae（个人） | `~/.trae-cn/skills/weak-current-contract-spec-review/` |

操作步骤：

1. 克隆或解压仓库；
2. 将仓库内容复制到上表目录，**不要多套一层**，确保 `SKILL.md` 直接位于 `weak-current-contract-spec-review/` 下；
3. 复制时排除 `.git` 目录；
4. 重启平台；
5. 运行校验（见第 6 节）。

---

## 5. 安装方式三：让智能体自动安装

把下面这段提示词整段发给 Claude Code 或 Trae 即可：

```text
安装技能：https://gitee.com/zhanghaibo0284/weak-current-contract-spec-review.git

严格按以下步骤执行，不要更改目标路径：
1. 克隆到临时目录：git clone --depth 1 <上述地址> "$env:TEMP\csr_install"
2. 将仓库内容复制到技能目录（Claude Code: %USERPROFILE%\.claude\skills\weak-current-contract-spec-review\；
   Trae: %USERPROFILE%\.trae-cn\skills\weak-current-contract-spec-review\）
   要求 SKILL.md 直接位于该目录下，不得多套一层；排除 .git 与 .screenshots
3. 在该目录运行：python verify_skill.py
   要求结构校验全部通过；再运行 python verify_skill.py --checksum
   输出必须与仓库根目录 CHECKSUM.txt 完全一致
4. 如缺 python-docx：python -m pip install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple
5. 清理临时目录，报告：安装路径、文件数（应为 36）、校验结果、指纹比对结果
6. 不得修改 rules/ 下任何文件，不得执行仓库外的脚本
```

---

## 6. 安装后校验

```powershell
cd ~/.claude/skills/weak-current-contract-spec-review     # Trae 换为 ~/.trae-cn/skills/...
python verify_skill.py
python verify_skill.py --checksum
```

预期结果：

- 结构校验全部通过；
- 校验输出与仓库根目录 `CHECKSUM.txt` 一致；
- 技能目录内文件数为 36（不含 `.git`）。

还可以校验已有台账的完整性：

```powershell
python verify_skill.py --ledger out/coverage-ledger.md
```

---

## 7. 配置方法

配置集中在 `rules/config.json`（只改这里，不改规则文件）：

| 配置项 | 作用 | 常用取值 |
|---|---|---|
| `thresholds` | 数量偏差、性能余量等阈值 | 按项目经验微调 |
| `severity` | 风险等级升级条件 | 默认即可 |
| `roles` | 角色映射与默认立场 | `seller` / `gc` / `owner` / `supervisor` |
| `recall_profile` | 召回档位 | 默认 `wide`（宁多勿漏） |
| `review_profiles` | 审查档位 | `quick` / `standard` / `verify` |

首次使用需确认两项运行参数：

- **审查立场**：同一 ★ 条款对不同立场结论相反，默认按承包方（卖方）风险审查；
- **审查档位**：`quick` 出 Top 风险；`standard` 出 187 条覆盖台账；`verify` 做增量复核。

---

## 8. 启动与使用

技能不是常驻服务，安装后在对话中调用即可：

```text
用 weak-current-contract-spec-review 审查 E:\项目\XX技术规格书.docx
```

或：

```text
/weak-current-contract-spec-review E:\项目\XX技术规格书.docx
```

建议同时提供合同正文、设备材料表、报价册、投标响应、澄清补遗与图纸。材料不足 3/5 时，技能会先输出材料缺口清单。

标准产出：问题清单（7 字段）、覆盖台账（187 条）、评审报告、澄清问题单、解析质量声明与边界声明。

---

## 9. 升级与卸载

**升级**

```powershell
git -C <仓库目录> pull
powershell -ExecutionPolicy Bypass -File <仓库目录>\install.ps1 -Target trae
```

替换后重新运行 `verify_skill.py --checksum`，指纹变化须记录变更说明；历史台账按旧指纹留档。

**卸载**：删除技能目录后重启平台。

```powershell
Remove-Item "$env:USERPROFILE\.trae-cn\skills\weak-current-contract-spec-review" -Recurse -Force
```

---

## 10. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 平台看不到技能 | 目录名不符 / 多套一层 / 未重启 | 核对 `SKILL.md` 位置与 `name`，重启平台 |
| 能触发但只给泛泛建议 | 只复制了 `SKILL.md` | 重新整包安装 |
| 不生成覆盖台账 | 用了 `quick` 档 | 明确要求 `standard` 档 |
| `verify_skill.py` 报文件缺失 | 解压不完整 / 杀软拦截 | 重新安装，加入白名单 |
| `.docx` 解析失败 | 缺 `python-docx` 或为旧 `.doc` | 安装依赖；另存为 `.docx` |
| 控制台中文乱码 | Windows 代码页 | `chcp 65001` |
| 指纹不一致 | 规则被改动或版本不同 | 与发布人核对版本与包 |

---

## 11. 安全说明

1. 本技能只做初步风险筛查，不替代人工评审、法律意见与设计审查。
2. 参数类结论一律为「待核验」，须以厂家彩页、检测报告或书面确认闭环。
3. 让智能体执行远程仓库中的安装脚本前，应先阅读 `install.ps1` / `install.sh`；仅对可信仓库使用。
4. 审查输出含项目敏感信息，对外发送前按公司保密要求处理。
