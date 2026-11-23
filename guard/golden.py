# -*- coding: utf-8 -*-
"""黄金集（T6）：加载、校验与评分。纯函数，不读时钟、不联网、不写状态。"""

from __future__ import annotations

import json
import re
from pathlib import Path

from canonical import canonical_json, norm_text, sha256_hex

CASE_ID_RE = re.compile(r"^G-\d{3}$")
RULE_REF_RE = re.compile(r"^(RISK-[A-T]\d{2}|QTY-R\d{2}|PARAM-P\d{2})$")
CONCLUSIONS = {"符合", "存在风险", "待核验", "不适用"}
SEVERITIES = {"高", "中（待核验）", "低", "不适用"}
PARAM_KEYS = ["stance", "profile", "recall", "review_date", "rule_version", "locale"]


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_index(golden_dir) -> dict:
    """读取索引；索引缺失或结构非法时抛 ValueError。"""
    path = Path(golden_dir) / "index.json"
    if not path.is_file():
        raise ValueError("缺少黄金集索引: " + str(path))
    index = _read_json(path)
    if not isinstance(index.get("cases"), list) or not index["cases"]:
        raise ValueError("黄金集索引 cases 必须为非空数组")
    return index


def validate_case(case: dict) -> list[str]:
    """单例结构校验：必备字段、编号命名空间、枚举合法。"""
    errors = []
    if not isinstance(case, dict):
        return ["用例必须为对象"]
    for key in ("case_id", "title", "materials", "params", "expected"):
        if key not in case:
            errors.append("缺少字段: " + key)
    if errors:
        return errors

    if not CASE_ID_RE.match(str(case["case_id"])):
        errors.append("case_id 必须形如 G-001: %r" % case["case_id"])
    if not str(case["title"]).strip():
        errors.append("title 不能为空")
    if not isinstance(case["materials"], list) or not case["materials"]:
        errors.append("materials 必须为非空数组")

    params = case.get("params")
    if not isinstance(params, dict):
        errors.append("params 必须为对象")
    else:
        missing = [k for k in PARAM_KEYS if not str(params.get(k, "")).strip()]
        if missing:
            errors.append("params 缺少参数: " + ",".join(missing))

    rows = case.get("expected")
    if not isinstance(rows, list) or not rows:
        errors.append("expected 必须为非空数组")
        return errors

    seen = set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append("expected[%d] 必须为对象" % i)
            continue
        rid = norm_text(str(row.get("编号", "")))
        if rid in seen:
            errors.append("expected[%d] 编号重复: %s" % (i, rid))
        seen.add(rid)
        if not RULE_REF_RE.match(rid):
            errors.append("expected[%d] 编号非法: %r" % (i, rid))
        if row.get("结论") not in CONCLUSIONS:
            errors.append("expected[%d] 结论非法: %r" % (i, row.get("结论")))
        if row.get("风险等级") not in SEVERITIES:
            errors.append("expected[%d] 风险等级非法: %r" % (i, row.get("风险等级")))
    return errors


def load_cases(golden_dir) -> list[dict]:
    """按索引加载用例；索引与磁盘文件必须一一对应，否则抛 ValueError。"""
    base = Path(golden_dir)
    index = load_index(base)
    case_dir = base / "cases"
    files = sorted(p.name for p in case_dir.glob("*.json"))
    listed = sorted(Path(e.get("file", "")).name for e in index["cases"])
    if files != listed:
        raise ValueError(
            "黄金集索引与用例文件不一致: 磁盘=%s 索引=%s" % (",".join(files), ",".join(listed))
        )

    cases = []
    ids = set()
    for entry in index["cases"]:
        case = _read_json(base / entry["file"])
        if case.get("case_id") != entry.get("case_id"):
            raise ValueError("索引 case_id 与文件不一致: " + str(entry.get("file")))
        if case["case_id"] in ids:
            raise ValueError("黄金集 case_id 重复: " + case["case_id"])
        ids.add(case["case_id"])
        cases.append(case)
    return sorted(cases, key=lambda c: c["case_id"])


def load_and_validate(golden_dir) -> tuple[list[dict], list[str]]:
    """加载并逐例校验；返回 (用例, 错误列表)。"""
    cases = load_cases(golden_dir)
    errors = []
    for case in cases:
        for err in validate_case(case):
            errors.append("%s: %s" % (case.get("case_id", "?"), err))
    return cases, errors


def score_case(expected_rows, actual_rows) -> dict:
    """单例评分：召回、误报率、等级一致率、覆盖率，全部按编号集合计算。"""
    exp = {norm_text(str(r.get("编号", ""))): r for r in expected_rows}
    act = {norm_text(str(r.get("编号", ""))): r for r in actual_rows}
    hits = sorted(set(exp) & set(act))
    missed = sorted(set(exp) - set(act))
    false_positives = sorted(set(act) - set(exp))

    recall = len(hits) / len(exp) if exp else 1.0
    fpr = len(false_positives) / len(act) if act else 0.0
    if hits:
        agree = sum(
            1
            for rid in hits
            if norm_text(str(exp[rid].get("风险等级", "")))
            == norm_text(str(act[rid].get("风险等级", "")))
        )
        severity_agreement = agree / len(hits)
    else:
        severity_agreement = 1.0 if not exp else 0.0
    coverage_ratio = len(act) / len(exp) if exp else 1.0

    return {
        "expected": len(exp),
        "actual": len(act),
        "hits": len(hits),
        "missed": missed,
        "false_positives": false_positives,
        "recall": round(recall, 6),
        "false_positive_rate": round(fpr, 6),
        "severity_agreement": round(severity_agreement, 6),
        "coverage_ratio": round(coverage_ratio, 6),
    }


def score_suite(cases: list[dict], actual_by_case: dict) -> dict:
    """整集评分：逐例结果 + 最差值聚合（召回/等级/覆盖取 min，误报取 max）。"""
    per_case = []
    for case in cases:
        cid = case["case_id"]
        result = score_case(case["expected"], actual_by_case.get(cid, []))
        result["case_id"] = cid
        per_case.append(result)
    per_case.sort(key=lambda r: r["case_id"])

    aggregate = {
        "cases": len(per_case),
        "recall": min((r["recall"] for r in per_case), default=1.0),
        "false_positive_rate": max((r["false_positive_rate"] for r in per_case), default=0.0),
        "severity_agreement": min((r["severity_agreement"] for r in per_case), default=1.0),
        "coverage_ratio": min((r["coverage_ratio"] for r in per_case), default=1.0),
    }
    return {"aggregate": aggregate, "cases": per_case}


def suite_digest(cases: list[dict]) -> str:
    """黄金集指纹：用例排序后规范化序列化，用于回测可追溯。"""
    ordered = sorted(cases, key=lambda c: c["case_id"])
    return sha256_hex(canonical_json(ordered))
