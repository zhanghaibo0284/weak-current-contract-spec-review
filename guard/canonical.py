# -*- coding: utf-8 -*-
"""确定性内核（DET）：归一化、稳定排序、稳定编号、指纹。

设计原则：
- 纯函数：不读时钟、不用随机数、不联网、不读写运行状态；
- 所有对外哈希只依赖入参内容，与调用次数、机器、路径无关；
- 序列化统一 UTF-8 + LF + 键升序 + 紧凑分隔符。
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

SEVERITY_RANK = {"高": 0, "中（待核验）": 1, "低": 2, "不适用": 3}

CORE_FIELDS = [
    "问题编号",
    "对应条款或材料位置",
    "问题描述",
    "判定依据",
    "风险等级",
    "影响分析",
    "整改建议",
]

REQUIRED_PARAMS = ["stance", "profile", "recall", "review_date", "rule_version", "locale"]

_WS_RE = re.compile(r"[\s\u00a0\u200b\u200c\u200d\ufeff]+")


def norm_text(value: str) -> str:
    """文本归一化：NFC + 全空白折叠。只做等价变换，不改变语义。"""
    s = unicodedata.normalize("NFC", value or "")
    return _WS_RE.sub(" ", s).strip()


def canonical_json(obj) -> str:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_hex(data) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_blocks(blocks: list[str]) -> list[dict]:
    """正文块按出现顺序赋稳定坐标 B00001...；坐标只依赖顺序，不依赖页码。"""
    return [
        {"block_id": "B%05d" % (i + 1), "text": norm_text(b)}
        for i, b in enumerate(blocks)
    ]


def canonical_tables(tables: list[list[list[str]]]) -> list[dict]:
    """表格统一为网格；合并单元格由解析层先行展开，本层不做推断。"""
    out = []
    for i, rows in enumerate(tables):
        grid = [[norm_text(c) for c in row] for row in rows]
        out.append(
            {
                "table_id": "T%03d" % (i + 1),
                "rows": len(grid),
                "cols": max((len(r) for r in grid), default=0),
                "grid": grid,
            }
        )
    return out


def input_hash(blocks, tables, materials) -> str:
    """输入指纹：正文 + 表格 + 材料清单，与文件路径、机器无关。"""
    payload = {
        "blocks": canonical_blocks(blocks),
        "tables": canonical_tables(tables),
        "materials": sorted(norm_text(m) for m in materials),
    }
    return sha256_hex(canonical_json(payload))


def params_hash(params: dict) -> str:
    """参数轴指纹；缺参数直接失败，禁止用默认时间/默认立场静默补全。"""
    missing = [k for k in REQUIRED_PARAMS if not str(params.get(k, "")).strip()]
    if missing:
        raise ValueError("缺少必需参数: " + ", ".join(missing))
    axis = {k: params[k] for k in sorted(params)}
    return sha256_hex(canonical_json(axis))


def issue_id(rule_id: str, evidence: str) -> str:
    """问题编号由「规则编号 + 证据坐标」派生，与命中顺序、并发数无关。"""
    return "ISSUE-%s-%s" % (rule_id, sha256_hex(norm_text(evidence))[:8])


def stable_issues(records: list[dict]) -> list[dict]:
    """稳定排序：等级 → 位置 → 编号。同分再按证据文本兜底，保证全序。"""
    def key(r):
        return (
            SEVERITY_RANK.get(r.get("风险等级", ""), 9),
            norm_text(r.get("对应条款或材料位置", "")),
            norm_text(r.get("问题编号", "")),
            sha256_hex(norm_text(r.get("问题描述", ""))),
        )

    return sorted(records, key=key)


def output_hash(records, ledger, manifest_core) -> str:
    """产物指纹：覆盖清单与问题清单同排序后参与哈希。"""
    payload = {
        "records": stable_issues(records),
        "ledger": sorted(ledger, key=lambda x: norm_text(x.get("编号", ""))),
        "manifest": manifest_core,
    }
    return sha256_hex(canonical_json(payload))
