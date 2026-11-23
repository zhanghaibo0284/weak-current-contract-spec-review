# -*- coding: utf-8 -*-
"""配置版本化：shadow 只观察、released 已发布、current 指针原子切换与回滚。

目录结构：
    versions/current.json
    versions/shadow/<version>/config.json + proposal.json
    versions/released/<version>/config.json + release.json

约束：只增不改；旧版本目录永不原地修改；指针切换用 os.replace 原子替换。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from canonical import canonical_json, sha256_hex
from evolve import apply_proposal

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def config_checksum(config: dict) -> str:
    return sha256_hex(canonical_json(config))


def _root(root) -> Path:
    return Path(root) / "versions"


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_version(version: str) -> None:
    if not VERSION_RE.match(str(version)):
        raise ValueError("版本号必须为 X.Y.Z: %r" % version)


def _check_date(release_date: str) -> None:
    if not DATE_RE.match(str(release_date)):
        raise ValueError("发布日期必须为 YYYY-MM-DD: %r" % release_date)


def _approvers(value) -> list[str]:
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        items = []
    return [str(item).strip() for item in items if str(item).strip()]


def read_current(root) -> dict:
    path = _root(root) / "current.json"
    if not path.is_file():
        return {"current": None, "history": []}
    doc = _read_json(path)
    doc.setdefault("current", None)
    doc.setdefault("history", [])
    return doc


def _write_current(root, current: str, history: list[dict]) -> dict:
    doc = {"current": current, "history": history}
    _write_atomic(_root(root) / "current.json", _dump(doc))
    return doc


def list_versions(root) -> dict:
    base = _root(root)
    def names(kind: str) -> list[str]:
        folder = base / kind
        if not folder.is_dir():
            return []
        return sorted(p.name for p in folder.iterdir() if p.is_dir())
    return {"shadow": names("shadow"), "released": names("released")}


def stage_shadow(root, config: dict, proposal: dict) -> Path:
    """把提案应用到 shadow 目录；不触碰 current 指针。"""
    new_version = str(proposal.get("new_version", ""))
    _check_version(new_version)
    shadow_root = _root(root) / "shadow"
    target = apply_proposal(config, proposal, str(shadow_root))
    return target.parent


def release(root, version: str, approved_by, release_date: str, metrics: dict | None = None) -> dict:
    """把 shadow 版本发布为 released，并原子切换 current 指针。"""
    _check_version(version)
    _check_date(release_date)
    approvers = _approvers(approved_by)
    if not approvers:
        raise ValueError("发布需要至少一名人工审批人")

    shadow_dir = _root(root) / "shadow" / version
    shadow_cfg = shadow_dir / "config.json"
    if not shadow_cfg.is_file():
        raise ValueError("shadow 版本不存在: " + version)

    config = _read_json(shadow_cfg)
    digest = config_checksum(config)

    released_dir = _root(root) / "released" / version
    if released_dir.exists():
        raise ValueError("版本已发布，禁止覆盖: " + version)
    released_dir.mkdir(parents=True, exist_ok=True)
    release_cfg = released_dir / "config.json"
    _write_atomic(release_cfg, canonical_json(config) + "\n")

    record = {
        "version": version,
        "config_checksum": digest,
        "released_by": approvers,
        "release_date": release_date,
        "source": "shadow",
        "metrics": metrics or {},
    }
    _write_atomic(released_dir / "release.json", _dump(record))

    doc = read_current(root)
    history = list(doc["history"])
    history.append(
        {
            "version": version,
            "config_checksum": digest,
            "released_by": approvers,
            "release_date": release_date,
            "action": "release",
        }
    )
    return _write_current(root, version, history)


def rollback(root, version: str, approved_by, release_date: str) -> dict:
    """把 current 指针切回已发布版本；不改任何版本目录。"""
    _check_version(version)
    _check_date(release_date)
    approvers = _approvers(approved_by)
    if not approvers:
        raise ValueError("回滚需要至少一名人工审批人")

    released_cfg = _root(root) / "released" / version / "config.json"
    if not released_cfg.is_file():
        raise ValueError("已发布版本不存在: " + version)

    digest = config_checksum(_read_json(released_cfg))
    doc = read_current(root)
    if doc.get("current") == version:
        raise ValueError("当前指针已指向该版本: " + version)

    history = list(doc["history"])
    history.append(
        {
            "version": version,
            "config_checksum": digest,
            "released_by": approvers,
            "release_date": release_date,
            "action": "rollback",
        }
    )
    return _write_current(root, version, history)


def status(root) -> dict:
    doc = read_current(root)
    listed = list_versions(root)
    return {
        "current": doc.get("current"),
        "history": doc.get("history", []),
        "shadow": listed["shadow"],
        "released": listed["released"],
    }


def remove_shadow(root, version: str) -> None:
    """清理 shadow（仅用于回测失败后作废提案）；released 永不删除。"""
    _check_version(version)
    folder = _root(root) / "shadow" / version
    if folder.is_dir():
        shutil.rmtree(folder)
