#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""weak-current-contract-spec-review 结构一致性校验器。

用途：
    改动规则 / 模板 / 配置后运行，确认没有破坏编号、枚举、引用与清单一致性。

用法：
    python verify_skill.py                 # 全量校验
    python verify_skill.py --checksum      # 只输出 {{RULESET_CHECKSUM}}
    python verify_skill.py --ledger F.md   # 额外校验覆盖台账文件

退出码：0=全部通过；1=存在失败项。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# 规则集定义：文件、前缀、期望条数与连续编号规则
RULE_SETS = {
    "RISK": {
        "file": "rules/checkitems-risk.md",
        "prefix": None,  # 单字母类别 A~T
        "letters": {
            "A": 6, "B": 6, "C": 6, "D": 6, "E": 6,
            "F": 5, "G": 5, "H": 6, "I": 6, "J": 5,
            "K": 6, "L": 5, "M": 6, "N": 5, "O": 5,
            "P": 5, "Q": 4, "R": 5, "S": 4, "T": 6,
        },
        "total": 108,
    },
    "QTY": {
        "file": "rules/checkitems-quantity.md",
        "prefix": "R",
        "total": 16,
    },
    "PARAM": {
        "file": "rules/checkitems-parameter.md",
        "prefix": "P",
        "total": 63,
    },
}

CORE_FIELDS = [
    ("f1", "问题编号"),
    ("f2", "对应条款或材料位置"),
    ("f3", "问题描述"),
    ("f4", "判定依据"),
    ("f5", "风险等级"),
    ("f6", "影响分析"),
    ("f7", "整改建议"),
]

SEVERITY_ENUM = {"高", "中（待核验）", "低", "不适用"}

ROW_RE = re.compile(r"^\|\s*([A-Z]{1,2})(\d{2})\s*\|")
QUALIFIED_RE = re.compile(r"(RISK|QTY|PARAM)-([A-Z]{1,2})(\d{2})")
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
SKILL_PATH_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|")
# 仅匹配「指向本技能旧章节」的引用动词，避免误伤规格书自身的「第 9 章」
CHAPTER_RE = re.compile(r"(?:按|见|套用|并入|落入|执行|实现|调用|依据|参照)\s*第\s*\d+(?:\.\d+)?\s*章")

results: list[tuple[str, bool, str]] = []


def ok(name: str, detail: str = "") -> None:
    results.append((name, True, detail))


def fail(name: str, detail: str) -> None:
    results.append((name, False, detail))


def warn(name: str, detail: str) -> None:
    results.append((f"{name}（告警）", True, detail))


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def load_json(rel: str):
    return json.loads(read_text(rel))


def parse_rule_ids(rel: str) -> list[str]:
    ids = []
    for line in read_text(rel).splitlines():
        m = ROW_RE.match(line)
        if m:
            ids.append(f"{m.group(1)}{m.group(2)}")
    return ids


# ---------------------------------------------------------------- 1. 文件完整性
REQUIRED_FILES = [
    "SKILL.md", "README.md", "PORTING.md", "MANIFEST.md",
    "rules/capability.md", "rules/inputs.md", "rules/parsing.md",
    "rules/workflow.md", "rules/dimensions.md", "rules/severity.md",
    "rules/cross-checks.md", "rules/adjudication.md", "rules/indexes.md",
    "rules/configuration.md", "rules/limitations.md",
    "rules/checkitems-risk.md", "rules/checkitems-quantity.md",
    "rules/checkitems-parameter.md", "rules/standards-index.md",
    "rules/glossary.md", "rules/config.json", "rules/rule-record.schema.json",
    "templates/output-schema.json", "templates/issue-list-template.md",
    "templates/issue-record.yaml", "templates/auxiliary-tables.md",
    "templates/review-report.md", "templates/coverage-ledger.md",
    "templates/coverage-schema.json", "templates/rfi-list.md",
    "templates/cost-model.md",
]


def check_files() -> None:
    missing = [f for f in REQUIRED_FILES if not (ROOT / f).is_file()]
    if missing:
        fail("文件存在性", "缺失：" + ", ".join(missing))
    else:
        ok("文件存在性", f"{len(REQUIRED_FILES)} 个必备文件齐全")

    # SKILL 文件索引中的路径必须真实存在
    broken = []
    for line in read_text("SKILL.md").splitlines():
        m = SKILL_PATH_RE.match(line)
        if not m:
            continue
        rel = m.group(1)
        if "/" not in rel and not rel.endswith((".md", ".py", ".json", ".yaml")):
            continue
        if rel.startswith(("http://", "https://")):
            continue
        if not (ROOT / rel).exists():
            broken.append(rel)
    if broken:
        fail("SKILL 索引可达性", "索引指向不存在的文件：" + ", ".join(sorted(set(broken))))
    else:
        ok("SKILL 索引可达性")


# ---------------------------------------------------------------- 2. JSON 合法
def check_json() -> None:
    for rel in [
        "rules/config.json",
        "rules/rule-record.schema.json",
        "templates/output-schema.json",
        "templates/coverage-schema.json",
    ]:
        try:
            load_json(rel)
            ok(f"JSON 解析 {rel}")
        except Exception as exc:  # noqa: BLE001
            fail(f"JSON 解析 {rel}", str(exc))


# ---------------------------------------------------------------- 3. 规则编号
def check_rules() -> dict[str, set[str]]:
    ids_by_set: dict[str, set[str]] = {}
    for set_name, spec in RULE_SETS.items():
        rel = spec["file"]
        ids = parse_rule_ids(rel)
        ids_by_set[set_name] = set(ids)

        if len(ids) != spec["total"]:
            fail(f"{set_name} 规则条数", f"期望 {spec['total']}，实际 {len(ids)}")
        else:
            ok(f"{set_name} 规则条数", f"{len(ids)} 条")

        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            fail(f"{set_name} 编号唯一", "重复：" + ", ".join(dup))
        elif len(ids) == len(set(ids)):
            ok(f"{set_name} 编号唯一")

        # 编号连续性
        gaps = []
        if set_name == "RISK":
            for letter, count in spec["letters"].items():
                got = {i for i in ids if i.startswith(letter)}
                expected = {f"{letter}{n:02d}" for n in range(1, count + 1)}
                if got != expected:
                    gaps.append(f"{letter}: 期望 {count} 条，实际 {len(got)}")
            # 是否出现未声明的类别
            declared = set(spec["letters"])
            extra = {i[0] for i in ids} - declared
            if extra:
                gaps.append("未声明类别：" + ",".join(sorted(extra)))
        else:
            prefix = spec["prefix"]
            expected = {f"{prefix}{n:02d}" for n in range(1, spec["total"] + 1)}
            if set(ids) != expected:
                missing = sorted(expected - set(ids))
                extra = sorted(set(ids) - expected)
                if missing:
                    gaps.append("缺：" + ",".join(missing))
                if extra:
                    gaps.append("多：" + ",".join(extra))
        if gaps:
            fail(f"{set_name} 编号连续性", "；".join(gaps))
        else:
            ok(f"{set_name} 编号连续性")

    # 前缀冲突只能通过规则集区分，确认消歧文档存在
    indexes = read_text("rules/indexes.md")
    if "A.4" in indexes and "编号命名空间" in indexes:
        ok("编号消歧说明", "indexes.md 附录 A.4 存在")
    else:
        fail("编号消歧说明", "rules/indexes.md 缺少 A.4 编号命名空间章节")

    return ids_by_set


# ---------------------------------------------------------------- 4. 交叉引用
def check_cross_refs(ids_by_set: dict[str, set[str]]) -> None:
    bad = []
    for rel in ["rules/adjudication.md", "rules/cross-checks.md", "rules/indexes.md"]:
        for line_no, line in enumerate(read_text(rel).splitlines(), 1):
            for set_name, letter, num in QUALIFIED_RE.findall(line):
                rid = f"{letter}{num}"
                if rid not in ids_by_set.get(set_name, set()):
                    bad.append(f"{rel}:{line_no} → {set_name}-{rid}")
    if bad:
        fail("交叉引用可解析", "无法解析的引用：" + "; ".join(bad[:20]))
    else:
        ok("交叉引用可解析")

    # 关键引用文件必须使用带前缀形式
    for rel in ["rules/adjudication.md", "rules/cross-checks.md"]:
        text = read_text(rel)
        if not QUALIFIED_RE.search(text):
            fail(f"{rel} 编号前缀", "未使用 RISK-/QTY-/PARAM- 前缀")
        else:
            ok(f"{rel} 编号前缀")


# ---------------------------------------------------------------- 5. 枚举一致
def check_enums() -> None:
    schema = load_json("templates/output-schema.json")
    fields = schema.get("fields", [])
    got = [(f.get("key"), f.get("name")) for f in fields]
    if got == CORE_FIELDS:
        ok("7 字段契约", "字段名与顺序未变")
    else:
        fail("7 字段契约", f"实际：{got}")

    f5 = fields[4].get("enum", []) if len(fields) > 4 else []
    if set(f5) == SEVERITY_ENUM:
        ok("风险等级枚举", "高/中（待核验）/低/不适用")
    else:
        fail("风险等级枚举", f"output-schema f5 = {f5}")

    severity_md = read_text("rules/severity.md")
    if "中高风险" in severity_md or "中/高" in severity_md:
        fail("等级定义自洽", "severity.md 仍出现未定义的「中高」等级")
    else:
        ok("等级定义自洽", "仅使用已定义三级")

    # 全库扫描「升级为/至中高」这类非法定级动作，防止回退
    bad_upgrade = []
    for path in sorted(ROOT.rglob("*.md")):
        if path.name == "MANIFEST.md":
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if stripped := line.strip():
                if stripped.startswith(">"):
                    continue
                if re.search(r"升级[为至][^，。；]{0,8}中高", line):
                    bad_upgrade.append(f"{path.relative_to(ROOT)}:{line_no}")
    if bad_upgrade:
        fail("升级动作合法", "出现非法定级：" + ", ".join(bad_upgrade))
    else:
        ok("升级动作合法", "无「升级为中高」类表述")

    if "判定结论与风险等级" in severity_md:
        ok("结论/等级语义区分", "severity.md 7.4 存在")
    else:
        fail("结论/等级语义区分", "缺少 severity.md 7.4")

    skill = read_text("SKILL.md")
    if "风险等级枚举：高 / 中（待核验）/ 低 / 不适用" in skill:
        ok("SKILL 枚举声明")
    else:
        fail("SKILL 枚举声明", "SKILL.md 第 5 节枚举声明缺失或被改写")


# ---------------------------------------------------------------- 6. 边界声明
def check_limitations() -> None:
    text = read_text("rules/limitations.md")
    items = re.findall(r"^\s*\d+\.\s+", text, re.M)
    if len(items) >= 7:
        ok("边界声明条数", f"{len(items)} 条")
    else:
        fail("边界声明条数", f"期望 ≥7，实际 {len(items)}")

    for rel in ["SKILL.md", "templates/review-report.md", "templates/issue-list-template.md"]:
        if "limitations" in read_text(rel):
            ok(f"边界声明引用 {rel}")
        else:
            fail(f"边界声明引用 {rel}", "未引用 rules/limitations.md")


# ---------------------------------------------------------------- 7. 占位符闭环
def check_placeholders() -> None:
    catalog: set[str] = set()
    for line in read_text("PORTING.md").splitlines():
        if line.startswith("|"):
            m = PLACEHOLDER_RE.search(line)
            if m and "`{{" in line:
                catalog.add(m.group(1))
    if not catalog:
        fail("占位符目录", "PORTING.md 未解析到占位符")
        return
    ok("占位符目录", f"{len(catalog)} 个")

    config = load_json("rules/config.json")
    runtime = set(config.get("placeholders", {}).get("runtime_required", []))
    missing = sorted(runtime - catalog)
    if missing:
        fail("运行期占位符登记", "未在 PORTING 目录登记：" + ", ".join(missing))
    else:
        ok("运行期占位符登记", f"{len(runtime)} 个")

    used: set[str] = set()
    for path in ROOT.rglob("*"):
        if path.suffix.lower() not in {".md", ".json", ".yaml"}:
            continue
        if path.name == "verify_skill.py":
            continue
        used |= set(PLACEHOLDER_RE.findall(path.read_text(encoding="utf-8")))
    known = catalog | {"SKILL_ROOT"}
    unknown = sorted(used - known)
    if unknown:
        warn("未登记占位符", ", ".join(unknown))
    else:
        ok("占位符全部登记")


# ---------------------------------------------------------------- 8. 断链章节引用
def check_stale_chapters() -> None:
    offenders = []
    for path in sorted(ROOT.rglob("*.md")):
        if path.name == "MANIFEST.md":
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith(">"):
                continue  # 溯源说明块
            if CHAPTER_RE.search(stripped):
                offenders.append(f"{path.relative_to(ROOT)}:{line_no}")
    if offenders:
        fail("断链章节引用", "正文仍引用旧章节号：" + ", ".join(offenders))
    else:
        ok("断链章节引用", "正文无旧章节号")


# ---------------------------------------------------------------- 9. 台账校验
def check_ledger(rel: str, expected: int = 187) -> None:
    path = Path(rel)
    if not path.is_absolute():
        path = ROOT / rel
    if not path.is_file():
        fail("覆盖台账", f"文件不存在：{rel}")
        return
    text = path.read_text(encoding="utf-8")
    rids = QUALIFIED_RE.findall(text)
    ids = [f"{s}-{l}{n}" for s, l, n in rids]
    if not ids:
        fail("覆盖台账", "未解析到任何规则编号")
        return
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        fail("台账编号唯一", "重复：" + ", ".join(dup[:10]))
    elif len(ids) < expected:
        fail("台账完整性", f"期望 ≥{expected} 行，实际 {len(ids)}")
    else:
        ok("台账完整性", f"{len(ids)} 行")
    if "结论" in text and "不适用" in text:
        ok("台账结论列")
    else:
        warn("台账结论列", "未识别到结论列")


# ---------------------------------------------------------------- 10. MANIFEST
def check_manifest() -> None:
    rel = "MANIFEST.md"
    if not (ROOT / rel).is_file():
        fail("MANIFEST", "文件不存在")
        return
    text = read_text(rel)
    m = re.search(r"共\s*(\d+)\s*个文件[，,]\s*合计\s*(\d+)\s*行", text)
    if not m:
        fail("MANIFEST 统计行", "缺少「共 N 个文件，合计 M 行」")
        return
    declared_files, declared_lines = int(m.group(1)), int(m.group(2))
    actual = [
        p for p in ROOT.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".md", ".json", ".yaml"}
        and p.name != "MANIFEST.md"
    ]
    actual_files = len(actual)
    actual_lines = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in actual)
    if (declared_files, declared_lines) != (actual_files, actual_lines):
        fail("MANIFEST 统计行",
             f"声明 {declared_files} 文件/{declared_lines} 行，实际 {actual_files} 文件/{actual_lines} 行")
    else:
        ok("MANIFEST 统计行", f"{actual_files} 文件 / {actual_lines} 行")


# ---------------------------------------------------------------- 11. 校验和
def compute_checksum() -> str:
    files = sorted(
        (p for p in ROOT.rglob("*")
         if p.is_file() and p.suffix.lower() in {".md", ".json", ".yaml"}),
        key=lambda p: p.relative_to(ROOT).as_posix().encode("utf-8"),
    )
    h = hashlib.sha256()
    for p in files:
        rel = p.relative_to(ROOT).as_posix().encode("utf-8")
        h.update(rel)
        h.update(b"\0")
        h.update(p.read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser(description="结构一致性校验")
    parser.add_argument("--checksum", action="store_true", help="只输出规则集校验和")
    parser.add_argument("--ledger", help="额外校验覆盖台账 Markdown 文件")
    args = parser.parse_args()

    if args.checksum:
        print(compute_checksum())
        return 0

    check_files()
    check_json()
    ids = check_rules()
    check_cross_refs(ids)
    check_enums()
    check_limitations()
    check_placeholders()
    check_stale_chapters()
    check_manifest()
    if args.ledger:
        check_ledger(args.ledger)

    width = max(len(name) for name, _, _ in results)
    failed = 0
    for name, passed, detail in results:
        mark = "PASS" if passed else "FAIL"
        if not passed:
            failed += 1
        print(f"[{mark}] {name.ljust(width)}  {detail}")

    print("-" * 60)
    print(f"合计 {len(results)} 项，失败 {failed} 项")
    print(f"RULESET_CHECKSUM = {compute_checksum()}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
