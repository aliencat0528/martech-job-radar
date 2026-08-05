"""Cake（原 CakeResume）職缺抓取：解析頁面內嵌的 __NEXT_DATA__（前端開放 JSON）。

Cake 是三個職缺管道中資料最結構化的一個——薪資是數字不是字串、更新時間是 ISO 時間戳，
能排序、能算中位、能跨期比。而且 Omnichat／awoo／Ocard **只在 Cake**，沒有它就少三家。

只用開放給前端的 JSON，不繞任何防護；請求間隔 >=1 秒。
"""
import json
import re
import time

import requests

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
REQUEST_INTERVAL_SEC = 1.2
MAX_PAGES = 3  # 每頁 10 筆；三頁足以涵蓋台灣 MarTech 的任何一家


def fetchPage(slug, page):
    """回傳 (結果 dict, 錯誤字串)。結果含 total 與 jobs。"""
    url = f"https://www.cake.me/companies/{slug}/jobs?locale=zh-TW"
    if page > 1:
        url += f"&page={page}"
    resp = requests.get(url, headers=UA, timeout=25)
    if resp.status_code != 200:
        return None, f"http {resp.status_code}"
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        resp.text, re.S)
    if not match:
        return None, "no __NEXT_DATA__（Cake 可能改版）"

    state = json.loads(match.group(1))["props"]["pageProps"]["initialState"]
    search = state.get("companyJobSearch", {})
    # pageMap 存的是 id 字串陣列，職缺物件在 entityByPathId——不要直接讀 pageMap
    entities = search.get("entityByPathId", {}) or {}
    view = (search.get("viewsByFilterKey", {}) or {}).get(search.get("activeFilterKey"), {})

    jobs = []
    for ent in entities.values():
        salary = ent.get("salary") or {}
        salaryDesc = ""
        if salary.get("min") or salary.get("max"):
            unit = "月" if salary.get("type") == "per_month" else "年"
            salaryDesc = f"NT${salary.get('min')}–{salary.get('max')}／{unit}"
        jobs.append({
            "channel": "Cake（原 CakeResume）",
            "title": (ent.get("title") or "").strip(),
            "company": "",  # 由呼叫端以主檔的正式名稱填入
            "location": "、".join(ent.get("locations") or []),
            "posted": "",
            "updated": (ent.get("contentUpdatedAt") or "")[:10],
            "salary": salaryDesc,
            "url": f"https://www.cake.me/companies/{slug}/jobs/{ent.get('path')}",
            "seniority": f"{ent.get('seniorityLevel') or ''} / {ent.get('minWorkExpYear') or 0}年",
            "req": (ent.get("description") or "")[:1500],
        })
    return {"total": (view.get("pagination") or {}).get("total_entries"), "jobs": jobs}, None


def fetchCompany(slug, companyName, logger=print):
    """抓一家公司的全部職缺（自動分頁）。回傳 (jobs, errors)。"""
    allJobs, errors, seenUrls = [], [], set()
    total = None
    for page in range(1, MAX_PAGES + 1):
        try:
            result, err = fetchPage(slug, page)
        except Exception as exc:
            errors.append(f"cake {slug} p{page}: {exc}")
            break
        time.sleep(REQUEST_INTERVAL_SEC)
        if err:
            if page == 1:
                errors.append(f"cake {slug}: {err}")
            break
        total = result["total"]
        fresh = [j for j in result["jobs"] if j["url"] not in seenUrls]
        for job in fresh:
            job["company"] = companyName
            seenUrls.add(job["url"])
        allJobs += fresh
        if not fresh or len(allJobs) >= (total or 0):
            break
    logger(f"  Cake [{companyName}] {len(allJobs)} 筆"
           + (f"（平台顯示 {total}）" if total not in (None, len(allJobs)) else ""))
    return allJobs, errors


def fetchAll(config, logger=print):
    """依 companies.yaml 的 channels.cake 逐家抓取。回傳 (jobs, errors)。"""
    jobs, errors = [], []
    for company in config["companies"]:
        slug = (company.get("channels") or {}).get("cake")
        if not slug:
            continue
        got, errs = fetchCompany(slug, company["name"], logger)
        jobs += got
        errors += errs
    return jobs, errors
