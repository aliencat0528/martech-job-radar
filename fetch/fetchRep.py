"""面試趣公司口碑抓取：公司評價、面試評價、難度、心得數、年薪中位、工時。

這是**唯一能穿透 104 缺口的來源**——員工評價跟公司有沒有在刊職缺無關，
所以 iKala、CYBERBIZ、TenMax 在三個職缺管道全掛零時，這裡照樣有幾百篇心得（← JR-001）。

數字全部寫在頁面的 meta description 裡，一次 request 就拿得到，無 bot 防護。
公司代碼（如 Appier 的 XTDv）無法自動取得——搜尋頁是前端渲染——
因此一次性人工建檔於 `companies.yaml` 的 `channels.interviewCode`。
"""
import re
import time

import requests

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
REQUEST_INTERVAL_SEC = 1.0

# meta description 形如：
# 「<公司名>評價 3.7/5，每日平均工時 8.6 小時、偶爾加班，年薪約 96 萬；
#   面試評價 3.6/5、難度 3.1/5，497 篇真實心得，完整公司評價馬上看！」
PAT_COMPANY = re.compile(r"評價\s*([\d.]+)\s*/\s*5")
PAT_HOURS = re.compile(r"每日平均工時\s*([\d.]+)\s*小時、([^，。]{2,8})")
PAT_SALARY = re.compile(r"年薪約\s*([\d.]+)\s*萬")
PAT_INTERVIEW = re.compile(r"面試評價\s*([\d.]+)\s*/\s*5、難度\s*([\d.]+)\s*/\s*5")
PAT_REVIEWS = re.compile(r"([\d,]+)\s*篇真實心得")


def parseMeta(html):
    """從頁面抽出結構化欄位。抽不到的欄位回 None，不猜。"""
    match = re.search(r'"description"\s*:\s*"([^"]{20,400})', html)
    desc = match.group(1) if match else ""
    if not desc:
        return None

    out = {"raw": desc[:220]}
    m = PAT_COMPANY.search(desc)
    out["companyScore"] = float(m.group(1)) if m else None
    m = PAT_INTERVIEW.search(desc)
    out["interviewScore"] = float(m.group(1)) if m else None
    out["interviewDifficulty"] = float(m.group(2)) if m else None
    m = PAT_REVIEWS.search(desc)
    out["reviewCount"] = int(m.group(1).replace(",", "")) if m else None
    m = PAT_SALARY.search(desc)
    out["annualSalaryWan"] = float(m.group(1)) if m else None
    m = PAT_HOURS.search(desc)
    out["dailyHours"] = float(m.group(1)) if m else None
    out["overtime"] = m.group(2) if m else None
    return out


def repScore(companyScore, reviewCount, bands, minReviews):
    """公司評價 → 1–5 分格。心得數不足回 None（標「—」不給分，← JR-001）。"""
    if companyScore is None or (reviewCount or 0) < minReviews:
        return None
    for threshold, score in bands:
        if companyScore >= threshold:
            return score
    return 1


def fetchOne(code, logger=print):
    url = f"https://interview.tw/c/{code}/info"
    resp = requests.get(url, headers=UA, timeout=20)
    if resp.status_code != 200:
        return None, f"http {resp.status_code}"
    data = parseMeta(resp.text)
    if not data:
        return None, "meta description 抽不到（面試趣可能改版）"
    data["url"] = url
    return data, None


def fetchAll(config, logger=print):
    """依 companies.yaml 逐家抓取。回傳 ({公司名: 資料}, errors)。"""
    bands = [(float(a), int(b)) for a, b in config.get("repScoreBands", [])]
    minReviews = int(config.get("repMinReviews", 50))
    out, errors = {}, []

    for company in config["companies"]:
        code = (company.get("channels") or {}).get("interviewCode")
        if not code:
            continue
        try:
            data, err = fetchOne(code, logger)
        except Exception as exc:
            errors.append(f"interview {company['name']}: {exc}")
            logger(f"  面試趣 [{company['name']}] 失敗：{exc}")
            time.sleep(REQUEST_INTERVAL_SEC)
            continue
        time.sleep(REQUEST_INTERVAL_SEC)
        if err:
            errors.append(f"interview {company['name']}: {err}")
            logger(f"  面試趣 [{company['name']}] {err}")
            continue

        data["repScore"] = repScore(data["companyScore"], data["reviewCount"],
                                    bands, minReviews)
        out[company["name"]] = data
        score = data["repScore"]
        logger(f"  面試趣 [{company['name']}] 公司評價 {data['companyScore']}"
               f"／{data['reviewCount']} 篇 → "
               + (f"{score} 格" if score is not None else "樣本不足，標「—」"))
    return out, errors
