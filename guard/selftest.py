# -*- coding: utf-8 -*-
"""原型自检：重复调用一致性、编号稳定性、校验器拦截、进化门禁。

运行：python selftest.py
输出：每条 PASS/FAIL，末行汇总；退出码 0=全通过。
"""

from __future__ import annotations

import copy
import itertools
import json
import random
import tempfile
from pathlib import Path

from canonical import (
    canonical_json,
    issue_id,
    input_hash,
    norm_text,
    output_hash,
    params_hash,
    sha256_hex,
    stable_issues,
)
from evolve import apply_proposal, gate, validate_proposal
from golden import load_and_validate, score_suite
from versions import read_current, release, rollback, stage_shadow
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

    # E1b 分级：B 类拒绝、审批人支持列表
    b_class = copy.deepcopy(good)
    b_class["changes"] = {"dimensions.DIM-01": "改名"}
    check("E1b B 类键被拒绝", validate_proposal(b_class) != [])

    multi = copy.deepcopy(good)
    multi["approved_by"] = ["PM-张三", "LG-李四"]
    check("E1b 审批人列表通过", validate_proposal(multi) == [])

    empty = copy.deepcopy(good)
    empty["approved_by"] = ["  "]
    check("E1b 空审批人被拒绝", validate_proposal(empty) != [])

    # T6 黄金集：结构、完美回放、漏报、误报、重复评分一致
    golden_dir = Path(__file__).resolve().parent.parent / "evolve" / "golden"
    cases, golden_errors = load_and_validate(golden_dir)
    check("T6 黄金集用例结构合法", bool(cases) and not golden_errors,
          "%d 例%s" % (len(cases), "" if not golden_errors else "；" + golden_errors[0]))

    perfect = {c["case_id"]: copy.deepcopy(c["expected"]) for c in cases}
    score1 = score_suite(cases, perfect)
    agg1 = score1["aggregate"]
    check("T6 完美回放召回=1", agg1["recall"] == 1.0)
    check("T6 完美回放误报=0", agg1["false_positive_rate"] == 0.0)
    check("T6 完美回放等级一致=1", agg1["severity_agreement"] == 1.0)
    score2 = score_suite(cases, perfect)
    check("T6 两次评分结果一致", canonical_json(score1) == canonical_json(score2))

    partial = {
        cid: (rows[:-1] if len(rows) > 1 else [])
        for cid, rows in perfect.items()
    }
    check("T6 漏报导致召回下降",
          score_suite(cases, partial)["aggregate"]["recall"] < 1.0)

    known = {row["编号"] for c in cases for row in c["expected"]}
    fp_id = next(
        "RISK-%s01" % letter
        for letter in "ABCDEFGHIJKLMNOPQRST"
        if "RISK-%s01" % letter not in known
    )
    noisy = {cid: rows + [{"编号": fp_id, "结论": "存在风险", "风险等级": "低"}]
             for cid, rows in perfect.items()}
    check("T6 误报导致误报率上升",
          score_suite(cases, noisy)["aggregate"]["false_positive_rate"] > 0)

    # E4 版本化：shadow 不动线上、release 原子切换、rollback 可恢复
    with tempfile.TemporaryDirectory() as td:
        cfg = {"thresholds": {"quantity_deviation_pct": 5}, "output_fields": []}
        prop1 = {
            "base_version": "1.3.0",
            "new_version": "1.3.1",
            "changes": {"thresholds.quantity_deviation_pct": 6},
            "evidence_runs": 40,
            "approved_by": ["PM-张三"],
        }
        stage_shadow(td, cfg, prop1)
        check("E4 shadow 不改线上指针", read_current(td)["current"] is None)

        release(td, "1.3.1", ["PM-张三"], "2026-11-23", {"baseline": {}, "candidate": {}})
        check("E4 release 原子切换指针", read_current(td)["current"] == "1.3.1")

        released_cfg = read_current(td)
        check("E4 release 写入历史",
              len(released_cfg["history"]) == 1
              and released_cfg["history"][0]["config_checksum"]
              != sha256_hex(canonical_json(cfg)))

        cfg2 = json.loads(
            (Path(td) / "versions" / "released" / "1.3.1" / "config.json").read_text(encoding="utf-8")
        )
        prop2 = {
            "base_version": "1.3.1",
            "new_version": "1.3.2",
            "changes": {"thresholds.quantity_deviation_pct": 7},
            "evidence_runs": 40,
            "approved_by": ["PM-张三"],
        }
        stage_shadow(td, cfg2, prop2)
        release(td, "1.3.2", ["PM-张三"], "2026-11-24", {})
        rollback(td, "1.3.1", ["PM-张三"], "2026-11-25")
        doc = read_current(td)
        check("E4 rollback 恢复旧指针",
              doc["current"] == "1.3.1"
              and doc["history"][-1]["action"] == "rollback"
              and len(doc["history"]) == 3)
        check("E4 旧版本目录保留",
              (Path(td) / "versions" / "released" / "1.3.1" / "config.json").is_file()
              and (Path(td) / "versions" / "released" / "1.3.2" / "config.json").is_file())

    print()
    print("汇总: %d 项检查, %d 失败" % (CHECKS, len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
