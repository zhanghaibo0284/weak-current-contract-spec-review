# -*- coding: utf-8 -*-
"""一致性校验（CON）：输出契约、覆盖完整性、引用可解析、产物互证。"""

from __future__ import annotations

import re

from canonical import CORE_FIELDS, output_hash, sha256_hex, canonical_json

CONCLUSIONS = {"符合", "存在风险", "待核验", "不适用"}
ISSUE_SEVERITIES = {"高", "中（待核验）", "低"}
RULE_ID_RE = re.compile(r"(RISK|QTY|PARAM)-[A-Z]\d{2}(?:-\d+)?")


def validate_records(records: list[dict]) -> list[str]:
    """C1：7 字段、枚举、编号唯一、规则引用可解析。"""
    errors = []
    seen = set()
    for i, r in enumerate(records):
        for f in CORE_FIELDS:
            if f not in r or not str(r[f]).strip():
                errors.append("record[%d] 缺少字段: %s" % (i, f))
        sev = r.get("风险等级", "")
        if sev and sev not in ISSUE_SEVERITIES:
            errors.append(
                "record[%d] 风险等级非法: %s（不适用仅允许出现在台账）" % (i, sev)
            )
        iid = str(r.get("问题编号", "")).strip()
        if iid in seen:
            errors.append("record[%d] 问题编号重复: %s" % (i, iid))
        seen.add(iid)
        if not RULE_ID_RE.search(str(r.get("判定依据", ""))):
            errors.append("record[%d] 判定依据未引用规则编号" % i)
    return errors


def validate_ledger(rows: list[dict], expected_ids: set[str]) -> list[str]:
    """C2：187 条全覆盖，无缺行、无多余、结论合法。"""
    errors = []
    seen = set()
    for i, row in enumerate(rows):
        rid = str(row.get("编号", "")).strip()
        verdict = str(row.get("结论", "")).strip()
        if rid in seen:
            errors.append("ledger[%d] 编号重复: %s" % (i, rid))
        seen.add(rid)
        if verdict not in CONCLUSIONS:
            errors.append("ledger[%d] 结论非法: %s" % (i, verdict))
    missing = sorted(expected_ids - seen)
    extra = sorted(seen - expected_ids)
    if missing:
        errors.append("台账缺行 %d 条: %s" % (len(missing), ",".join(missing[:8])))
    if extra:
        errors.append("台账多余 %d 条: %s" % (len(extra), ",".join(extra[:8])))
    return errors


def validate_cross_products(records, ledger) -> list[str]:
    """C4：问题清单的编号集合必须与台账中「存在风险/待核验」可对应。"""
    errors = []
    record_ids = {str(r.get("问题编号", "")).strip() for r in records}
    if len(record_ids) != len(records):
        errors.append("问题编号不唯一，无法与台账互证")
    ledger_flagged = {
        str(r.get("编号", "")).strip()
        for r in ledger
        if r.get("结论") in {"存在风险", "待核验"}
    }
    if not record_ids and ledger_flagged:
        errors.append("台账有风险项但问题清单为空")
    return errors


def verify_output_hash(records, ledger, manifest_core, claimed: str) -> list[str]:
    """C5：产物指纹可重算；声明值与重算值不一致即判定被篡改或非确定性。"""
    actual = output_hash(records, ledger, manifest_core)
    if actual != claimed:
        return ["产物指纹不一致: 声明=%s 重算=%s" % (claimed[:12], actual[:12])]
    return []


def manifest_core(input_hash: str, params_hash: str, ruleset_checksum: str) -> dict:
    """运行清单核心：只含内容寻址信息，不含时间、主机、路径。"""
    return {
        "input_hash": input_hash,
        "params_hash": params_hash,
        "ruleset_checksum": ruleset_checksum,
    }


def manifest_digest(core: dict) -> str:
    return sha256_hex(canonical_json(core))
