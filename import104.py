"""解析你自己在瀏覽器開啟並存下的 104 頁面，轉成 job-radar 的職缺格式。

這支**不連網、不打 104**。它只讀你本機的檔案——來源是你以真人身分正常瀏覽後另存的頁面，
不涉及任何存取控制的規避。

用法：
    # 1. 在瀏覽器開 104 搜尋結果或公司職缺頁，捲到底把職缺載完
    # 2. Cmd+S 另存為「網頁，僅 HTML」。一個檔＝那一整頁的所有職缺，不必一筆一筆存
    # 3. 多頁就多存幾個檔，然後一次丟進來（可給多個檔或整個資料夾）：
    #    python3 import104.py ~/Downloads/104-*.html
    #    python3 import104.py ~/Downloads/104pages/ --company "iKala 愛卡拉"

輸出：與 jobs_final.json 相同的欄位，跨檔自動去重（以職缺網址為鍵），可直接併進報告資料層。

範圍說明：搜尋結果頁只帶職稱／公司／地點／薪資／日期，**沒有 JD 全文**；
要做技能需求分析才需要另外存個別職缺頁，且只需存你真的要投的那幾個。

解析採三段回退（JSON-LD → 內嵌狀態 → DOM 錨點），每個檔會印出實際命中哪一段。

⚠️ 已知限制：目前只用合成的測試檔驗證過 JSON-LD 與 DOM 錨點兩段，**尚未對真實的 104 頁面跑過**。
哪一段會實際命中要你存一頁下來才知道；全部落空代表選擇器要調，把檔案給我看一眼即可。
"""
import argparse
import html as H
import json
import pathlib
import re
import sys


def readFile(path):
    for enc in ("utf-8", "utf-8-sig", "big5", "cp950"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def clean(s, limit=0):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"\s+", " ", H.unescape(s)).strip()
    return s[:limit] if limit else s


def absUrl(u):
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return "https://www.104.com.tw" + u
    return u


# ── 策略 1：schema.org JobPosting（最乾淨，求職站多半為 SEO 而輸出） ──
def fromJsonLd(doc):
    rows = []
    for block in re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            doc, re.S | re.I):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        for node in (data if isinstance(data, list) else [data]):
            if not isinstance(node, dict):
                continue
            graph = node.get("@graph")
            for item in (graph if isinstance(graph, list) else [node]):
                if not isinstance(item, dict) or item.get("@type") != "JobPosting":
                    continue
                org = item.get("hiringOrganization") or {}
                loc = item.get("jobLocation") or {}
                if isinstance(loc, list):
                    loc = loc[0] if loc else {}
                addr = (loc or {}).get("address") or {}
                rows.append({
                    "title": clean(item.get("title")),
                    "company": clean(org.get("name") if isinstance(org, dict) else org),
                    "location": clean(addr.get("addressLocality")
                                      or addr.get("addressRegion") or ""),
                    "posted": (item.get("datePosted") or "")[:10],
                    "updated": (item.get("dateModified")
                                or item.get("datePosted") or "")[:10],
                    "url": absUrl(item.get("url") or ""),
                    "req": clean(item.get("description"), 1800),
                })
    return rows


# ── 策略 2：Nuxt / Next 內嵌狀態 ──
def fromEmbeddedState(doc):
    rows = []
    pats = [r"window\.__NUXT__\s*=\s*(\{.*?\});?\s*</script>",
            r'<script id="__NEXT_DATA__"[^>]*>(\{.*?\})</script>']
    for pat in pats:
        m = re.search(pat, doc, re.S)
        if not m:
            continue
        try:
            state = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue

        found = []

        def walk(node):
            if isinstance(node, dict):
                # 104 職缺物件慣用鍵：jobName / custName / jobNo
                if node.get("jobName") or (node.get("jobNo") and node.get("custName")):
                    found.append(node)
                    return
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(state)
        for j in found:
            rows.append({
                "title": clean(j.get("jobName") or j.get("name")),
                "company": clean(j.get("custName") or j.get("companyName")),
                "location": clean(j.get("jobAddrNoDesc") or j.get("area") or ""),
                "posted": clean(j.get("appearDate") or ""),
                "updated": clean(j.get("appearDate") or j.get("updateDate") or ""),
                "salary": clean(j.get("salaryDesc") or j.get("salary") or ""),
                "url": absUrl(j.get("link", {}).get("job")
                              if isinstance(j.get("link"), dict) else j.get("jobUrl", "")),
                "req": clean(j.get("description") or j.get("descSnippet") or "", 1800),
            })
        if rows:
            break
    return rows


# ── 策略 3：DOM 錨點（版面改動時最耐命） ──
def fromAnchors(doc):
    rows, seen = [], set()
    for m in re.finditer(
            r'<a[^>]+href="((?://www\.104\.com\.tw)?/job/[^"?#]+)[^"]*"[^>]*>(.*?)</a>',
            doc, re.S):
        href, inner = m.group(1), clean(m.group(2))
        if not inner or len(inner) < 2 or href in seen:
            continue
        seen.add(href)
        window = doc[max(0, m.start() - 400): m.end() + 1400]
        comp = re.search(r'href="(?://www\.104\.com\.tw)?/company/[^"]+"[^>]*>(.*?)</a>',
                         window, re.S)
        sal = re.search(r"(月薪|年薪|時薪|待遇面議)[^<]{0,40}", clean(window))
        loc = re.search(r"((?:台北|臺北|新北|桃園|台中|臺中|台南|臺南|高雄|新竹|"
                        r"基隆|嘉義|彰化|雲林|宜蘭|花蓮|台東|臺東|屏東|南投|苗栗)[^\s<]{0,4})",
                        clean(window))
        rows.append({
            "title": inner,
            "company": clean(comp.group(1)) if comp else "",
            "location": loc.group(1) if loc else "",
            "posted": "", "updated": "",
            "salary": sal.group(0) if sal else "",
            "url": absUrl(href),
            "req": "",
        })
    return rows


STRATEGIES = [("schema.org JobPosting", fromJsonLd),
              ("內嵌前端狀態（__NUXT__／__NEXT_DATA__）", fromEmbeddedState),
              ("DOM 錨點回退", fromAnchors)]


def main():
    ap = argparse.ArgumentParser(description="解析本機存下的 104 頁面")
    ap.add_argument("paths", nargs="+", help="另存的 .html 檔（可多個），或存放它們的資料夾")
    ap.add_argument("--company", default="", help="覆寫公司名（公司職缺頁常缺這欄）")
    ap.add_argument("--out", default="jobs_104.json")
    args = ap.parse_args()

    files = []
    for raw in args.paths:
        path = pathlib.Path(raw).expanduser()
        if path.is_dir():
            files += sorted(path.glob("*.htm*"))
        elif path.exists():
            files.append(path)
        else:
            print(f"⚠️  找不到：{raw}", file=sys.stderr)
    if not files:
        print("❌ 沒有可讀的檔案。", file=sys.stderr)
        return 1

    rows, seen, usedAny = [], set(), []
    for path in files:
        doc = readFile(str(path))
        if "Just a moment" in doc[:4000] or "cf-browser-verification" in doc[:8000]:
            print(f"⚠️  {path.name}：存到的是 Cloudflare 驗證頁，不是職缺頁。"
                  "請等頁面完全載入、看得到職缺清單之後再另存。", file=sys.stderr)
            continue

        pageRows, used = [], None
        for name, fn in STRATEGIES:
            try:
                pageRows = fn(doc)
            except Exception as exc:  # 單一策略失敗不該中斷其他策略
                print(f"   [{path.name}／{name}] 解析例外：{exc}", file=sys.stderr)
                pageRows = []
            if pageRows:
                used = name
                break

        added = 0
        for r in pageRows:
            key = r.get("url") or f"{r.get('company')}|{r.get('title')}"
            if key in seen:
                continue
            seen.add(key)
            rows.append(r)
            added += 1
        dup = len(pageRows) - added
        print(f"   {path.name}：{added} 筆"
              + (f"（去重掉 {dup} 筆重複）" if dup else "")
              + (f" · 策略「{used}」" if used else " · 未命中"))
        if used:
            usedAny.append(used)

    if not rows:
        print("❌ 三段策略都沒有命中職缺。\n"
              "   最可能的原因：(1) 頁面存檔時職缺尚未載入完（104 是捲動載入，"
              "請先捲到底）；(2) 104 改版。\n"
              "   把檔案給我看一眼即可修這支腳本——要改的是解析規則，不是取得方式。",
              file=sys.stderr)
        return 1

    for r in rows:
        r["channel"] = "104（本機匯入）"
        r.setdefault("salary", "")
        if args.company:
            r["company"] = args.company
        r["seniority"] = ""

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    withDate = sum(1 for r in rows if r.get("updated"))
    print(f"✅ 讀入 {len(files)} 個檔案，命中策略：{'／'.join(dict.fromkeys(usedAny))}")
    print(f"   合併去重後 {len(rows)} 筆，其中 {withDate} 筆有日期、"
          f"{sum(1 for r in rows if r.get('req'))} 筆有內文")
    print(f"   已寫入 {args.out}")
    for r in rows[:5]:
        print(f"   - {r['company'] or '(未帶公司)'} | {r['title']} | "
              f"{r['location']} | {r['updated'] or '無日期'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
