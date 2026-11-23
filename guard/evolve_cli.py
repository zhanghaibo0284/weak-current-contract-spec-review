# -*- coding: utf-8 -*-
"""进化流水线命令行：validate / score / shadow / release / rollback / status。

用法（在技能根目录执行）：
    python guard/evolve_cli.py status
    python guard/evolve_cli.py validate --proposal proposal.json
    python guard/evolve_cli.py score --actual actual.json
    python guard/evolve_cli.py shadow --proposal proposal.json
    python guard/evolve_cli.py release --version 1.3.1 --approved-by PM-张三 \
        --release-date 2026-11-23 --metrics metrics.json
    python guard/evolve_cli.py rollback --version 1.3.0 --approved-by PM-张三 \
        --release-date 2026-11-24

退出码：0=成功；1=校验或门禁失败；2=参数/IO 错误。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from evolve import gate, validate_proposal  # noqa: E402
from golden import load_and_validate, score_suite, suite_digest  # noqa: E402
from versions import release, rollback, stage_shadow, status  # noqa: E402

DEFAULT_ROOT = HERE.parent


def _read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2))


def cmd_status(args) -> int:
    _print(status(args.root))
    return 0


def cmd_validate(args) -> int:
    proposal = _read_json(args.proposal)
    errors = validate_proposal(proposal)
    if errors:
        _print({"ok": False, "errors": errors})
        return 1
    _print({"ok": True, "errors": []})
    return 0


def cmd_score(args) -> int:
    golden_dir = Path(args.root) / "evolve" / "golden"
    cases, errors = load_and_validate(golden_dir)
    if errors:
        _print({"ok": False, "errors": errors})
        return 1
    payload = _read_json(args.actual)
    actual = payload.get("cases", payload) if isinstance(payload, dict) else {}
    result = score_suite(cases, actual)
    result["ok"] = True
    result["suite_digest"] = suite_digest(cases)
    _print(result)
    return 0


def cmd_shadow(args) -> int:
    proposal = _read_json(args.proposal)
    errors = validate_proposal(proposal)
    if errors:
        _print({"ok": False, "errors": errors})
        return 1
    config = _read_json(str(Path(args.root) / "rules" / "config.json"))
    target = stage_shadow(args.root, config, proposal)
    _print({"ok": True, "shadow": str(target)})
    return 0


def cmd_release(args) -> int:
    metrics = _read_json(args.metrics) if args.metrics else {}
    baseline = metrics.get("baseline", {})
    candidate = metrics.get("candidate", {})
    if not baseline or not candidate:
        _print({"ok": False, "errors": ["metrics 必须包含 baseline 与 candidate"]})
        return 1
    gate_errors = gate(baseline, candidate, int(candidate.get("determinism_runs", 0)))
    if gate_errors:
        _print({"ok": False, "errors": gate_errors})
        return 1
    doc = release(args.root, args.version, args.approved_by, args.release_date, metrics)
    _print({"ok": True, "current": doc["current"], "history": len(doc["history"])})
    return 0


def cmd_rollback(args) -> int:
    doc = rollback(args.root, args.version, args.approved_by, args.release_date)
    _print({"ok": True, "current": doc["current"], "history": len(doc["history"])})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EVO 进化流水线")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="技能根目录（默认脚本上级）")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="查看当前指针、历史、shadow/released 版本")

    p_validate = sub.add_parser("validate", help="静态校验提案")
    p_validate.add_argument("--proposal", required=True)

    p_score = sub.add_parser("score", help="黄金集评分")
    p_score.add_argument("--actual", required=True)

    p_shadow = sub.add_parser("shadow", help="生成 shadow 版本")
    p_shadow.add_argument("--proposal", required=True)

    p_release = sub.add_parser("release", help="发布 shadow 版本并切换指针")
    p_release.add_argument("--version", required=True)
    p_release.add_argument("--approved-by", required=True)
    p_release.add_argument("--release-date", required=True)
    p_release.add_argument("--metrics", help="门禁指标文件")

    p_rollback = sub.add_parser("rollback", help="回滚到已发布版本")
    p_rollback.add_argument("--version", required=True)
    p_rollback.add_argument("--approved-by", required=True)
    p_rollback.add_argument("--release-date", required=True)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "status": cmd_status,
        "validate": cmd_validate,
        "score": cmd_score,
        "shadow": cmd_shadow,
        "release": cmd_release,
        "rollback": cmd_rollback,
    }
    try:
        return handlers[args.command](args)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        _print({"ok": False, "errors": [str(exc)]})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
