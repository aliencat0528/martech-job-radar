"""martech-job-radar 機械層主程式：抓取 → 整併。

流程：
    companies.yaml
      ├─ fetch/fetchCake.py   → Cake 職缺
      ├─ fetch/fetchRep.py    → 面試趣口碑
      └─ 讀 martech-trend-agent 最新快照（唯讀契約，找不到就降級，不硬相依）
                ↓
        data/auto/<日期>/*.json
                ↓
        mergeChannels.py（欄位契約 → 去重 → 新鮮度守門）
                ↓
        data/<日期>/jobs_final.json

分析層（判斷、投遞優先序）不在這裡——在 Claude Code 打 `/job-radar`。
"""
import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch import fetchCake, fetchRep  # noqa: E402


def readTrendSnapshot(config, logger=print):
    """讀 martech-trend-agent 最新一期的 jobs.json。

    契約只有六個欄位，缺哪個都不致命；找不到快照就回空清單並提醒，
    **不讓上游缺席變成本專案跑不動**（← D-018）。
    """
    base = pathlib.Path(config.get("trendAgentSnapshotDir", "")).expanduser()
    if not base.exists():
        logger(f"  ⚠️  找不到上游快照目錄（{base}）——降級為只用本專案自抓的來源")
        return [], None

    dated = sorted([d for d in base.iterdir() if d.is_dir()], reverse=True)
    for snapshot in dated:
        jobsFile = snapshot / "jobs.json"
        if not jobsFile.exists():
            continue
        raw = json.load(open(jobsFile, encoding="utf-8"))
        rows = [{
            "channel": f"{r.get('source', '?')}（via trend-agent {snapshot.name}）",
            "company": r.get("company", ""),
            "title": r.get("title", ""),
            "location": r.get("area", ""),
            "posted": r.get("appearDate", ""),
            "updated": r.get("appearDate", ""),
            "salary": r.get("salaryDesc", ""),
            "url": r.get("link", ""),
            "seniority": "",
            "req": (r.get("description") or "")[:1800],
        } for r in raw]
        logger(f"  上游快照 [{snapshot.name}] {len(rows)} 筆")
        return rows, snapshot.name

    logger("  ⚠️  上游目錄存在但沒有任何 jobs.json——降級為只用本專案自抓的來源")
    return [], None


def main():
    ap = argparse.ArgumentParser(description="抓取並整併各管道職缺")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--config", default="companies.yaml")
    ap.add_argument("--no-cake", action="store_true", help="略過 Cake")
    ap.add_argument("--no-rep", action="store_true", help="略過面試趣")
    ap.add_argument("--no-upstream", action="store_true", help="不讀 trend-agent 快照")
    args = ap.parse_args()

    config = yaml.safe_load(open(args.config, encoding="utf-8"))
    outDir = pathlib.Path("data/auto") / args.date
    outDir.mkdir(parents=True, exist_ok=True)
    errors = []

    if not args.no_upstream:
        print("▶ 讀取 martech-trend-agent 快照…", flush=True)
        rows, snapDate = readTrendSnapshot(config)
        if rows:
            json.dump(rows, open(outDir / "upstream.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)

    if not args.no_cake:
        print("▶ 抓取 Cake 職缺…", flush=True)
        jobs, errs = fetchCake.fetchAll(config)
        errors += errs
        json.dump(jobs, open(outDir / "cake.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    if not args.no_rep:
        print("▶ 抓取面試趣口碑…", flush=True)
        rep, errs = fetchRep.fetchAll(config)
        errors += errs
        # 口碑不是職缺——存到 data/reputation/ 而非 data/auto/，
        # 否則會被 mergeChannels 當成職缺檔掃到並抱怨「頂層不是陣列」
        repDir = pathlib.Path("data/reputation")
        repDir.mkdir(parents=True, exist_ok=True)
        json.dump(rep, open(repDir / f"{args.date}.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    print("\n▶ 整併…", flush=True)
    result = subprocess.run(
        [sys.executable, "mergeChannels.py", "--date", args.date, "--config", args.config],
        check=False)

    if errors:
        print(f"\n⚠️  {len(errors)} 個來源有問題：")
        for e in errors:
            print("   " + e)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
