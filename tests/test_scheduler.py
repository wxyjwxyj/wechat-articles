"""scheduler.py 核心逻辑测试。"""
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


# 把 scripts/ 加入 path，方便 import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def make_schedule(runs):
    """写临时 schedule.yaml，返回路径。"""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    yaml.dump({"runs": runs}, f)
    f.close()
    return Path(f.name)


def make_ran_dir():
    """创建临时 .ran 目录，返回路径。"""
    d = tempfile.mkdtemp()
    return Path(d)


# ── 导入被测模块 ──────────────────────────────────────────────
from scheduler import load_schedule, find_matching_run, already_ran, mark_ran


class TestLoadSchedule:
    def test_loads_runs(self):
        p = make_schedule([{"time": "09:30", "steps": ["wechat"]}])
        runs = load_schedule(p)
        assert len(runs) == 1
        assert runs[0]["time"] == "09:30"
        assert runs[0]["steps"] == ["wechat"]
        os.unlink(p)

    def test_empty_runs(self):
        p = make_schedule([])
        runs = load_schedule(p)
        assert runs == []
        os.unlink(p)


class TestFindMatchingRun:
    def test_exact_match(self):
        runs = [{"time": "09:30", "steps": ["wechat"]}]
        now = datetime(2026, 4, 22, 9, 30)
        result = find_matching_run(runs, now, tolerance_minutes=2)
        assert result is not None
        assert result["time"] == "09:30"

    def test_within_tolerance(self):
        runs = [{"time": "09:30", "steps": ["wechat"]}]
        now = datetime(2026, 4, 22, 9, 31)
        result = find_matching_run(runs, now, tolerance_minutes=2)
        assert result is not None

    def test_outside_tolerance(self):
        runs = [{"time": "09:30", "steps": ["wechat"]}]
        now = datetime(2026, 4, 22, 9, 33)
        result = find_matching_run(runs, now, tolerance_minutes=2)
        assert result is None

    def test_no_match(self):
        runs = [{"time": "09:30", "steps": ["wechat"]}]
        now = datetime(2026, 4, 22, 14, 0)
        result = find_matching_run(runs, now, tolerance_minutes=2)
        assert result is None

    def test_multiple_runs_picks_closest(self):
        runs = [
            {"time": "09:30", "steps": ["wechat"]},
            {"time": "09:31", "steps": ["bundle"]},
        ]
        now = datetime(2026, 4, 22, 9, 31)
        result = find_matching_run(runs, now, tolerance_minutes=2)
        assert result["time"] == "09:31"


class TestAlreadyRan:
    def test_not_ran(self):
        ran_dir = make_ran_dir()
        assert not already_ran("09:30", datetime(2026, 4, 22, 9, 30), ran_dir)

    def test_already_ran(self):
        ran_dir = make_ran_dir()
        mark_ran("09:30", datetime(2026, 4, 22, 9, 30), ran_dir)
        assert already_ran("09:30", datetime(2026, 4, 22, 9, 30), ran_dir)

    def test_different_day_not_ran(self):
        ran_dir = make_ran_dir()
        mark_ran("09:30", datetime(2026, 4, 21, 9, 30), ran_dir)
        assert not already_ran("09:30", datetime(2026, 4, 22, 9, 30), ran_dir)


class TestMarkRan:
    def test_creates_marker_file(self):
        ran_dir = make_ran_dir()
        mark_ran("09:30", datetime(2026, 4, 22, 9, 30), ran_dir)
        marker = ran_dir / "2026-04-22_09-30"
        assert marker.exists()
