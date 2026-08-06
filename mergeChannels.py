"""把各管道的職缺合併成單一 jobs_final.json，並回報覆蓋狀況。

設計重點在於：**手動匯入的 104 資料不能靠「記得」才進來，也不能過期而不自知。**
所以這支做三件事——固定路徑掃描、欄位契約驗證、新鮮度守門——並把結果印成一張
覆蓋報表，缺什麼、舊了多久，一眼看得到。

用法：
    python3 mergeChannels.py --date 2026-08-05

預設讀取（路徑固定，不需要每次指定）：
    data/auto/<日期>/*.json      ← 機械層抓的（Greenhouse／Yourator／Cake／面試趣）
    data/manual/104/<日期>/*.json ← import104.py 的輸出，你手動放進來的
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys

import yaml

# 所有管道都必須符合的欄位契約——少一個就擋下，不讓格式不合的資料默默混進報告
SCHEMA = {"channel", "company", "title", "location", "posted", "updated",
          "salary", "url", "seniority", "req"}

DEFAULT_MANUAL_MAX_AGE_DAYS = 21


def validateTaxonomy(cfg, logger=print):
    """守住 `category`／`purity` 的固定值（← JR-004）。

    這兩欄改成固定值的**唯一理由**是要能彙總（哪一類在招人、只排序哪一層）。
    一旦有人手滑寫了自由字串，彙總會安靜地少算一家而不是報錯——
    所以在單一入口這裡擋，跟欄位契約同一個位置、同一種脾氣。
    """
    cats, levels = set(cfg.get("categories") or []), set(cfg.get("purityLevels") or [])
    bad = []
    for c in cfg["companies"]:
        if cats and c.get("category") not in cats:
            bad.append(f"{c['name']}：category「{c.get('category')}」不在 {sorted(cats)}")
        if levels and c.get("purity") not in levels:
            bad.append(f"{c['name']}：purity「{c.get('purity')}」不在 {sorted(levels)}")
    for msg in bad:
        logger(f"   ⚠️  {msg}")
    return bad


def loadConfig(path="companies.yaml"):
    """新鮮度上限與「只在 104」的公司清單都來自主檔，不寫死在程式裡。"""
    cfg = yaml.safe_load(open(path, encoding="utf-8"))
    validateTaxonomy(cfg)
    return (cfg,
            int(cfg.get("manualMaxAgeDays", DEFAULT_MANUAL_MAX_AGE_DAYS)),
            [c["name"] for c in cfg["companies"] if c.get("manualOnly")])


def normCompany(name):
    """公司名正規化：去掉法人後綴與空白，讓跨管道的同一家對得起來。"""
    s = re.sub(r"[\s　]+", "", name or "")
    s = re.sub(r"(股份有限公司|有限公司|公司|Inc\.?|Ltd\.?|Corp\.?|Co\.?)$", "", s, flags=re.I)
    return s.lower()


def normTitle(title):
    """職稱正規化：只去掉平台自己加的編號與狀態標籤。

    刻意**不動圓括號**——`(Ad Cloud Platform)`／`(Playable Ads)`／`(BotBonnie)` 是不同團隊
    的不同職缺，砍掉會把它們誤併成一筆（實測會多吃掉 14 筆真實職缺）。
    """
    s = title or ""
    s = re.sub(r"【[^】]{0,40}】", "", s)          # 【CMS0501】平台職缺編號
    s = re.sub(r"^\s*\[[^\]]{0,20}\]\s*", "", s)  # [UPD]、[Open] 等狀態標籤
    s = re.sub(r"[\s　·・/／\-–—_]+", "", s)
    return s.lower()


PAT_JOBCODE = re.compile(r"【([A-Za-z0-9]{4,12})】")


def dedupeKey(row):
    """跨管道去重鍵。不用 url——同一個缺在不同平台的 url 本來就不同。

    有平台職缺編號（如 SHOPLINE 的【TPD0803】）時**優先用編號**：
    2026-08-05 實測 19 筆 SHOPLINE 職缺在 Yourator 與 Cake 兩邊編號一致，
    證明它是可靠識別碼。反過來，只靠職稱會把編號不同、職稱相同的兩個真實職缺
    （`【SGMO0801】Data Analyst` 與 `【TPD0803】Data Analyst`，分屬不同團隊）誤併成一筆。
    """
    company = normCompany(row.get("company"))
    code = PAT_JOBCODE.search(row.get("title") or "")
    if code:
        return f"{company}|#{code.group(1).lower()}"
    return f"{company}|{normTitle(row.get('title'))}"


def loadDir(path, label):
    """讀一個目錄下所有 json，驗證欄位契約。回傳 (rows, 問題清單)。"""
    rows, problems = [], []
    if not path.exists():
        return rows, [f"{label}：目錄不存在（{path}）"]
    files = sorted(path.glob("*.json"))
    if not files:
        return rows, [f"{label}：目錄存在但沒有 json（{path}）"]
    for f in files:
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception as exc:
            problems.append(f"{label}／{f.name}：讀取失敗 {exc}")
            continue
        if not isinstance(data, list):
            problems.append(f"{label}／{f.name}：頂層不是陣列，略過")
            continue
        for i, r in enumerate(data):
            missing = SCHEMA - set(r)
            if missing:
                # 補空字串而不是丟掉——缺欄位是格式問題，不是資料錯誤
                for k in missing:
                    r[k] = ""
                if i == 0:
                    problems.append(f"{label}／{f.name}：補了缺少的欄位 {sorted(missing)}")
            r["_src"] = f.name
        rows += data
    return rows, problems


def ageDays(path):
    """從目錄名（YYYY-MM-DD）算資料幾天前的。無法解析回 None。"""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    if not m:
        return None
    return (dt.date.today() - dt.date.fromisoformat(m.group(1))).days


def main():
    ap = argparse.ArgumentParser(description="合併各管道職缺並回報覆蓋狀況")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--root", default="data")
    ap.add_argument("--config", default="companies.yaml")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    try:
        _cfg, maxAge, manualOnly = loadConfig(args.config)
    except Exception as exc:
        print(f"❌ 讀不到主檔 {args.config}：{exc}", file=sys.stderr)
        return 1

    root = pathlib.Path(args.root)
    autoDir = root / "auto" / args.date
    manualRoot = root / "manual" / "104"

    allRows, problems, notes = [], [], []

    autoRows, p = loadDir(autoDir, "機械層")
    problems += p
    allRows += autoRows

    # 手動 104：找不到當期就退而求其次用最近一期，但一定要標示出來
    manualRows = []
    if manualRoot.exists():
        dated = sorted([d for d in manualRoot.iterdir() if d.is_dir()], reverse=True)
        exact = manualRoot / args.date
        chosen = exact if exact.exists() else (dated[0] if dated else None)
        if chosen is None:
            notes.append("⚠️  104：從未匯入過任何資料")
        else:
            manualRows, p = loadDir(chosen, "104 手動匯入")
            problems += p
            age = ageDays(chosen)
            if chosen != exact:
                notes.append(f"⚠️  104：本期（{args.date}）沒有匯入，改用 {chosen.name} 的舊資料"
                             + (f"（{age} 天前）" if age is not None else ""))
            if age is not None and age > maxAge:
                notes.append(f"⚠️  104 資料已 {age} 天未更新（上限 {maxAge} 天）"
                             "——報告中該來源的職缺應標為「可能已下架」")
            allRows += manualRows
    else:
        notes.append(f"⚠️  104：手動匯入目錄不存在（{manualRoot}）")

    if not allRows:
        print("❌ 沒有任何資料可合併。", file=sys.stderr)
        for n in problems + notes:
            print("   " + n, file=sys.stderr)
        return 1

    # ── 去重：同一個缺可能同時出現在多個管道 ──
    merged, seen = [], {}
    for r in allRows:
        key = dedupeKey(r)
        if key in seen:
            prev = merged[seen[key]]
            # 保留資訊較多的那筆，並把兩邊的管道都記下來
            prevChans = prev.get("channels") or [prev.get("channel", "")]
            if r.get("channel") and r["channel"] not in prevChans:
                prevChans.append(r["channel"])
            prev["channels"] = prevChans
            for field in ("posted", "updated", "salary", "req", "location"):
                if not prev.get(field) and r.get(field):
                    prev[field] = r[field]
            continue
        r["channels"] = [r.get("channel", "")]
        seen[key] = len(merged)
        merged.append(r)

    outPath = pathlib.Path(args.out or (root / args.date / "jobs_final.json"))
    outPath.parent.mkdir(parents=True, exist_ok=True)
    json.dump(merged, open(outPath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ── 覆蓋報表 ──
    byChannel, byCompany = {}, {}
    for r in merged:
        for c in r.get("channels", []):
            byChannel[c] = byChannel.get(c, 0) + 1
        byCompany[r.get("company", "")] = byCompany.get(r.get("company", ""), 0) + 1

    print(f"✅ 合併完成：{len(allRows)} 筆 → 去重後 {len(merged)} 筆")
    print(f"   輸出：{outPath}")
    print("\n各管道貢獻：")
    for c, n in sorted(byChannel.items(), key=lambda x: -x[1]):
        print(f"   {n:4d}  {c or '(未標管道)'}")

    has104 = any("104" in c for c in byChannel)
    print(f"\n104 手動匯入：{'✅ 已納入 ' + str(len(manualRows)) + ' 筆' if has104 else '❌ 本期沒有'}")
    if not has104:
        print("   受影響的公司（只能靠 104 覆蓋，本期將顯示為無職缺資料）：")
        for c in manualOnly:
            print(f"     · {c}")
        print("   → 這幾家在報告中必須標為「未取得」，不可標為「無職缺」")

    if problems or notes:
        print("\n需要注意：")
        for n in notes + problems:
            print("   " + n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
