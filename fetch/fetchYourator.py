"""Yourator 公司職缺抓取（補上游沒追蹤的公司）。

**為什麼這支存在，明明 trend-agent 已經有一支 Yourator fetcher？**

因為歸屬判準一（← D-018）是**逐家公司**成立的，不是逐個平台。trend-agent 的 Yourator
只查它自己 tier1 名單裡的 10 家；本專案追蹤 20 家，其中 SHOPLINE、adGeek 不在上游名單上，
上游只會從產業關鍵詞搜尋裡順帶撈到零星幾筆。

2026-08-05 實測代價：只讀上游時 SHOPLINE 僅得 Cake 的 23 筆，
**遺漏 Yourator 的 30 筆**——其中包含 Data Analyst ×2、Data Product Manager 等
本報告最核心的資料職。這會讓「SHOPLINE 是全台資料職開口最多的公司」這條結論失去依據。

重疊的部分交給 `mergeChannels.py` 去重，不會重複計算。
只用前端開放的 JSON，不繞任何防護；請求間隔 >=1 秒。
"""
import re
import time

import requests

SEARCH_URL = "https://www.yourator.co/api/v4/companies/{slug}/jobs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}
REQUEST_INTERVAL_SEC = 1.0
MAX_PAGES = 4


def normalizeJob(raw, companyName):
    path = raw.get("path", "")
    content = re.sub(r"<[^>]+>", " ", raw.get("content") or "")
    return {
        "channel": "Yourator" + (f"（導向 {raw['externalSource']}）"
                                 if raw.get("externalSource") else ""),
        "company": companyName,
        "title": raw.get("name", ""),
        "location": raw.get("location", "") or "",
        "posted": "",
        # Yourator 只給相對時間（「兩週內更新」），不是日期——這是平台差異不是資料缺漏
        "updated": raw.get("lastActiveAt", "") or "",
        "salary": raw.get("salary", "") or "",
        "url": f"https://www.yourator.co{path}" if path.startswith("/") else path,
        "seniority": raw.get("category", "") or "",
        "req": re.sub(r"\s+", " ", content).strip()[:1800],
    }


def fetchCompany(slug, companyName, logger=print):
    jobs, errors = [], []
    page = 1
    while page <= MAX_PAGES:
        try:
            resp = requests.get(SEARCH_URL.format(slug=slug), params={"page": page},
                                headers=HEADERS, timeout=20)
        except Exception as exc:
            errors.append(f"yourator {slug} p{page}: {exc}")
            break
        time.sleep(REQUEST_INTERVAL_SEC)
        if resp.status_code != 200:
            if page == 1:
                errors.append(f"yourator {slug}: http {resp.status_code}")
            break
        payload = resp.json().get("payload", {})
        batch = payload.get("jobs", [])
        jobs += [normalizeJob(j, companyName) for j in batch]
        if page >= payload.get("totalPages", 1) or not batch:
            break
        page += 1
    logger(f"  Yourator [{companyName}] {len(jobs)} 筆")
    return jobs, errors


def fetchAll(config, logger=print):
    """依 companies.yaml 的 channels.yourator 逐家抓取。回傳 (jobs, errors)。"""
    jobs, errors = [], []
    for company in config["companies"]:
        slug = (company.get("channels") or {}).get("yourator")
        if not slug:
            continue
        got, errs = fetchCompany(slug, company["name"], logger)
        jobs += got
        errors += errs
    return jobs, errors
