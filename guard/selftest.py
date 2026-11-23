# -*- coding: utf-8 -*-
"""原型自检：重复调用一致性、编号稳定性、校验器拦截、进化门禁。

运行：python selftest.py
输出：每条 PASS/FAIL，末行汇总；退出码 0=全通过。
"""

from __future__ import annotations

import copy
import itertools
import random
import tempfile
from pathlib import Path

from canonical import (
    issue_id,
    input_hash,
    norm_text,
    output_hash,
    params_hash,
    stable_issues,
)
from evolve import apply_proposal, gate, validate_proposal
from validate import (
    manifest_core,
    validate_cross_products,
    validate_ledger,
    validate_records,
    verify_output_hash,
)

FAILS: list[str] = []
CHECKS = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    print(("PASS " if cond else "FAIL ") + name + ((" | " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)


BLOCKS = [
    "★ 卖方须无条件配合买方人工智能建设，相关费用包含在合同总价中。",
    "软件交付时以买方名称注册登记，卖方须交付所有密码。",
    "设备在质保期过后开始最终验收。",
]
TABLES = [
    [["段场", "通信基站", "备件"], ["安顺", "14", "3"], ["古镇口", "9", "1"]],
    [["设备", "数量"], ["定位标签", "76+8"]],
]
MATERIALS = ["第五册 技术规格书", "设备材料表"]
PARAMS = {
    "stance": "seller",
    "profile": "standard",
    "recall": "wide",
    "review_date": "2026-11-23",
    "rule_version": "1.1.3",
    "locale": "zh-CN",
}


def sample_records() -> list[dict]:
    return [
        {
            "问题编号": issue_id("RISK-002", "B00001"),
            "对应条款或材料位置": "B00001",
            "问题描述": "AI 配合无范围与费用上限",
            "判定依据": "命中 RISK-B06 扩展义务",
            "风险等级": "高",
            "影响分析": "工作量不可估算",
            "整改建议": "设置封顶工作量并书面确认",
        },
        {
            "问题编号": issue_id("RISK-020", "B00002"),
            "对应条款或材料位置": "B00002",
            "问题描述": "全部密码交付买方",
            "判定依据": "命中 RISK-F03 交付物范围",
            "风险等级": "中（待核验）",
            "影响分析": "质保期后运维受限",
            "整改建议": "保留只读运维账号",
        },
    ]


def sample_ledger() -> list[dict]:
    return [
        {"编号": "RISK-B06", "结论": "存在风险"},
        {"编号": "RISK-F03", "结论": "待核验"},
        {"编号": "QTY-R14", "结论": "符合"},
    ]


def main() -> int:
    # T1 重复调用一致性：5 次 + 输入容器顺序扰动
    hashes = []
    for _ in range(5):
        h = output_hash(sample_records(), sample_ledger(), manifest_core("in", "pa", "rs"))
        hashes.append(h)
    check("T1 同一输入 5 次输出哈希一致", len(set(hashes)) == 1, hashes[0][:12])

    shuffled = list(MATERIALS)
    random.Random(0).shuffle(shuffled)
    check(
        "T1b 材料清单顺序扰动不影响输入指纹",
        input_hash(BLOCKS, TABLES, MATERIALS) == input_hash(BLOCKS, TABLES, shuffled),
    )

    # D6 编号稳定性：空白/全角空格差异不影响编号
    a = issue_id("RISK-002", "B00001")
    b = issue_id("RISK-002", "  B00001\u3000")
    check("D6 证据坐标归一化后编号稳定", a == b, a)

    # D4 稳定排序：打乱输入顺序后输出顺序一致
    recs = sample_records()
    perms = list(itertools.permutations(recs))
    orders = {tuple(r["问题编号"] for r in stable_issues(list(p))) for p in perms}
    check("D4 输入乱序后输出排序唯一", len(orders) == 1)

    # C1 字段校验：正常通过、缺字段被拦
    check("C1 合法记录通过", validate_records(recs) == [])
    broken = copy.deepcopy(recs)
    broken[0]["整改建议"] = ""
    check("C1 空整改建议被拦截", any("整改建议" in e for e in validate_records(broken)))
    dup = copy.deepcopy(recs)
    dup[1]["问题编号"] = dup[0]["问题编号"]
    check("C1 编号重复被拦截", any("重复" in e for e in validate_records(dup)))

    # C2 台账完整性：缺行被拦
    expected = {"RISK-B06", "RISK-F03", "QTY-R14"}
    check("C2 完整台账通过", validate_ledger(sample_ledger(), expected) == [])
    missing = sample_ledger()[:-1]
    check(
        "C2 缺行被拦截",
        any("缺行" in e for e in validate_ledger(missing, expected)),
    )

    # C4/C5 互证与指纹
    core = manifest_core("in", "pa", "rs")
    claimed = output_hash(recs, sample_ledger(), core)
    check("C4 问题清单与台账可互证", validate_cross_products(recs, sample_ledger()) == [])
    check("C5 指纹一致通过", verify_output_hash(recs, sample_ledger(), core, claimed) == [])
    check(
        "C5 篡改后指纹不一致被拦截",
        verify_output_hash(recs, sample_ledger(), core, "0" * 64) != [],
    )

    # E1/E2 进化门禁：非法提案必须拒绝
    good = {
        "base_version": "1.1.3",
        "new_version": "1.1.4",
        "changes": {"thresholds.quantity_deviation_pct": 6},
        "evidence_runs": 40,
        "approved_by": "PM-张三",
    }
    check("E1 合法提案通过", validate_proposal(good) == [])

    immutable = copy.deepcopy(good)
    immutable["changes"] = {"output_fields": ["问题编号"]}
    check("E1 修改契约字段被拒绝", validate_proposal(immutable) != [])

    out_of_range = copy.deepcopy(good)
    out_of_range["changes"] = {"thresholds.quantity_deviation_pct": 50}
    check("E1 参数越界被拒绝", validate_proposal(out_of_range) != [])

    no_evidence = copy.deepcopy(good)
    no_evidence["evidence_runs"] = 3
    check("E1 证据不足被拒绝", validate_proposal(no_evidence) != [])

    check(
        "E2 召回下降被门禁拦截",
        gate({"recall": 0.90, "false_positive_rate": 0.10},
             {"recall": 0.88, "false_positive_rate": 0.10, "coverage": 187, "runtime_ratio": 1.0},
             5) != [],
    )
    check(
        "E2 全部门通过",
        gate({"recall": 0.90, "false_positive_rate": 0.10},
             {"recall": 0.91, "false_positive_rate": 0.11, "coverage": 187, "runtime_ratio": 1.05},
             5) == [],
    )

    # E3 原子落盘：只写新版本目录
    with tempfile.TemporaryDirectory() as td:
        cfg = {"thresholds": {"quantity_deviation_pct": 5}, "output_fields": []}
        target = apply_proposal(cfg, good, td)
        written = target.read_text(encoding="utf-8")
        check("E3 新版本独立落盘", target.exists() and "6" in written and cfg["thresholds"]["quantity_deviation_pct"] == 5)

    print()
    print("汇总: %d 项检查, %d 失败" % (CHECKS, len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
