# -*- coding: utf-8 -*-
"""自我进化门禁（EVO）：只允许改配置轴，且必须通过确定性/回归/覆盖/耗时/审批五道门。"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from canonical import canonical_json, sha256_hex

# 不可进化：契约、流程、编号命名空间、边界声明
IMMUTABLE_KEYS = {
    "output_fields",
    "conclusions",
    "severity_labels",
    "rule_sets",
    "recall_policy.no_negative_exclusion",
    "review_profiles.standard",
    "review_profiles.verify",
    "checksum",
    "placeholders",
}

# 可进化：配置轴 + 合法区间（边界即安全护栏）
ALLOWED_KEYS = {
    "thresholds.quantity_deviation_pct": (1, 10),
    "thresholds.page_estimate_paragraphs_per_page": (20, 80),
    "thresholds.page_estimate_chars_per_page": (600, 2400),
    "recall_policy.default_sensitivity": {"wide", "standard", "narrow"},
    "review_profiles.quick.expect_minutes": (10, 120),
    "review_profiles.quick.risk_categories": None,
    "review_profiles.quick.quantity_rules": None,
    "review_profiles.quick.parameter_groups": None,
}

PROPOSAL_KEYS = {"base_version", "new_version", "changes", "evidence_runs", "approved_by"}


def _parse_version(v: str) -> tuple[int, int, int]:
    parts = v.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError("版本号必须为 X.Y.Z: %s" % v)
    return tuple(int(p) for p in parts)  # type: ignore[return-value]


def validate_proposal(proposal: dict) -> list[str]:
    """提案静态校验：结构、版本、白名单、不可变项、证据与审批。"""
    errors = []
    unknown = set(proposal) - PROPOSAL_KEYS
    if unknown:
        errors.append("提案含未知字段: " + ",".join(sorted(unknown)))
    for k in PROPOSAL_KEYS:
        if k not in proposal:
            errors.append("提案缺少字段: " + k)
    if errors:
        return errors

    try:
        if _parse_version(proposal["new_version"]) <= _parse_version(proposal["base_version"]):
            errors.append("新版本必须大于基线版本")
    except ValueError as exc:
        errors.append(str(exc))

    changes = proposal.get("changes") or {}
    if not isinstance(changes, dict) or not changes:
        errors.append("changes 必须为非空对象")
        return errors

    for key, value in changes.items():
        if key in IMMUTABLE_KEYS or any(
            key == ik or key.startswith(ik + ".") for ik in IMMUTABLE_KEYS
        ):
            errors.append("禁止修改不可变项: " + key)
            continue
        if key not in ALLOWED_KEYS:
            errors.append("键不在进化白名单: " + key)
            continue
        rule = ALLOWED_KEYS[key]
        if isinstance(rule, tuple):
            if not isinstance(value, (int, float)) or not (rule[0] <= value <= rule[1]):
                errors.append("取值越界: %s=%r，允许区间 %s" % (key, value, rule))
        elif isinstance(rule, set):
            if value not in rule:
                errors.append("取值非法: %s=%r，允许 %s" % (key, value, sorted(rule)))

    if not isinstance(proposal.get("evidence_runs"), int) or proposal["evidence_runs"] < 30:
        errors.append("证据样本不足：至少 30 次历史运行")
    if not str(proposal.get("approved_by", "")).strip():
        errors.append("缺少人工审批人")
    return errors


def gate(baseline: dict, candidate: dict, determinism_runs: int) -> list[str]:
    """五道门：确定性、召回、误报、覆盖、耗时。任何一项不过即阻断。"""
    errors = []
    if determinism_runs < 5:
        errors.append("确定性复跑次数不足 5 次")
    if candidate.get("recall", 0) < baseline.get("recall", 0):
        errors.append(
            "召回下降: %.4f -> %.4f" % (baseline.get("recall", 0), candidate.get("recall", 0))
        )
    if candidate.get("false_positive_rate", 1) > baseline.get("false_positive_rate", 1) + 0.02:
        errors.append(
            "误报率上升超 2 个百分点: %.4f -> %.4f"
            % (baseline.get("false_positive_rate", 0), candidate.get("false_positive_rate", 0))
        )
    if candidate.get("coverage") != 187:
        errors.append("覆盖不完整: %r != 187" % candidate.get("coverage"))
    if candidate.get("runtime_ratio", 99) > 1.2:
        errors.append("耗时膨胀超 20%: %.2f" % candidate.get("runtime_ratio", 99))
    return errors


def apply_proposal(config: dict, proposal: dict, versions_dir: str) -> Path:
    """原子写入新版本目录；绝不原地修改线上配置。"""
    errors = validate_proposal(proposal)
    if errors:
        raise ValueError("提案不合法: " + "; ".join(errors))

    new_cfg = copy.deepcopy(config)
    for dotted, value in proposal["changes"].items():
        node = new_cfg
        parts = dotted.split(".")
        for p in parts[:-1]:
            if p not in node or not isinstance(node[p], dict):
                raise ValueError("配置路径不存在: " + dotted)
            node = node[p]
        if parts[-1] not in node:
            raise ValueError("配置路径不存在: " + dotted)
        node[parts[-1]] = value

    out_dir = Path(versions_dir) / proposal["new_version"]
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "config.json"
    target.write_text(canonical_json(new_cfg) + "\n", encoding="utf-8", newline="\n")

    meta = {
        "base_version": proposal["base_version"],
        "new_version": proposal["new_version"],
        "changes": proposal["changes"],
        "evidence_runs": proposal["evidence_runs"],
        "approved_by": proposal["approved_by"],
        "config_checksum": sha256_hex(canonical_json(new_cfg)),
    }
    (out_dir / "proposal.json").write_text(
        json.dumps(meta, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return target
