"""统一调度器：每5分钟被 launchd 触发，读 schedule.yaml 决定是否执行任务。"""
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml

PROJECT_DIR = Path(__file__).parent.parent
SCHEDULE_FILE = PROJECT_DIR / "schedule.yaml"
RAN_DIR = PROJECT_DIR / ".ran"
DAILY_RUN = PROJECT_DIR / "daily_run.sh"


def load_schedule(schedule_path: Path = SCHEDULE_FILE) -> list[dict]:
    """读取 schedule.yaml，返回 runs 列表。"""
    with open(schedule_path) as f:
        data = yaml.safe_load(f)
    return data.get("runs", [])


def find_matching_run(
    runs: list[dict],
    now: datetime,
    tolerance_minutes: int = 2,
) -> dict | None:
    """找到与当前时间最近且在容忍范围内的 run，返回 None 表示无匹配。"""
    best = None
    best_diff = timedelta(minutes=tolerance_minutes + 1)

    for run in runs:
        h, m = map(int, run["time"].split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        diff = abs(now - target)
        if diff <= timedelta(minutes=tolerance_minutes) and diff < best_diff:
            best = run
            best_diff = diff

    return best


def already_ran(time_str: str, now: datetime, ran_dir: Path = RAN_DIR) -> bool:
    """检查今天这个时间点是否已经跑过。"""
    marker = ran_dir / f"{now.strftime('%Y-%m-%d')}_{time_str.replace(':', '-')}"
    return marker.exists()


def mark_ran(time_str: str, now: datetime, ran_dir: Path = RAN_DIR) -> None:
    """标记今天这个时间点已跑过。"""
    ran_dir.mkdir(parents=True, exist_ok=True)
    marker = ran_dir / f"{now.strftime('%Y-%m-%d')}_{time_str.replace(':', '-')}"
    marker.touch()


def cleanup_old_markers(ran_dir: Path = RAN_DIR, keep_days: int = 3) -> None:
    """清理3天前的标记文件。"""
    if not ran_dir.exists():
        return
    cutoff = datetime.now() - timedelta(days=keep_days)
    for f in ran_dir.iterdir():
        if f.stat().st_mtime < cutoff.timestamp():
            f.unlink()


def run_steps(steps: list[str]) -> int:
    """调用 daily_run.sh --steps <step1,step2,...>，返回 exit code。"""
    steps_arg = ",".join(steps)
    cmd = ["/bin/bash", str(DAILY_RUN), "--steps", steps_arg]
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))
    return result.returncode


def main() -> None:
    now = datetime.now()
    runs = load_schedule()
    matched = find_matching_run(runs, now)

    if matched is None:
        sys.exit(0)

    time_str = matched["time"]

    if already_ran(time_str, now):
        sys.exit(0)

    mark_ran(time_str, now)
    cleanup_old_markers()

    steps = matched.get("steps", [])
    exit_code = run_steps(steps)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
