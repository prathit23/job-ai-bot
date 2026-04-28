from __future__ import annotations

import shutil
import uuid
from pathlib import Path


TEST_TMP_ROOT = Path(__file__).resolve().parent.parent / "data" / "test_tmp"


def ensure_test_tmp_root() -> Path:
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    return TEST_TMP_ROOT


def workspace_tmp_dir() -> Path:
    root = ensure_test_tmp_root()
    path = root / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def cleanup_workspace_tmp(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
