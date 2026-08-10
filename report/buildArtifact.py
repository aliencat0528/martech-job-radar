"""報告層：把 jobs_final.json ＋ reputation.json ＋ companies.yaml 組成 artifact HTML。

全部資料驅動——**沒有任何一個數字是手抄的**。要改公司清單或四維基準改 `companies.yaml`，
要改版面改 `template.html`，這支只負責把兩者接起來。

（本檔於 2026-08-05 從 session scratchpad 搬進 repo：留在暫存區等於下一期無法重現同一份報告。）

用法：
    .venv/bin/python report/buildArtifact.py --date 2026-08-05
"""
import argparse
import html
import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent


def e(s):
    return html.escape(s or "")


def normCompany(name):
    s = re.sub(r"[\s　]+", "", name or "")
    s = re.sub(r"(股份有限公司|有限公司|公司|Inc\.?|Ltd\.?|Corp\.?|Co\.?)$", "", s, flags=re.I)
    return s.lower()


def matchCompany(rowCompany, yamlName):
    """上游用 trend-agent 的公司名（如「漸強實驗室 Crescendo Lab Ltd.」），
    本專案用 companies.yaml 的正式名——兩邊對得起來才算同一家。"""
    a, b = normCompany(rowCompany), normCompany(yamlName)
    if not a or not b:
        return False
    return a == b or a.startswith(b) or b.startswith(a)


CATORDER = ["數據分析", "數據科學／工程", "技術顧問 TSE", "產品／設計", "軟體工程",
            "商務／行銷／客戶成功", "其他（HR／法務／財會／IT）"]


def cat(t):
    t = (t or "").lower()
    if any(k in t for k in ["data analyst", "campaign analyst", "analytics", "數據分析",
                            "資料分析", "data operations"]):
        return "數據分析"
    if any(k in t for k in ["machine learning", "research scientist", "ai engineer",
                            "generative ai", "data engineer", "data product"]):
        return "數據科學／工程"
    if any(k in t for k in ["solution engineer", "technical support"]):
        return "技術顧問 TSE"
    if any(k in t for k in ["product manager", "product designer", "產品經理",
                            "product owner", "product operation"]):
        return "產品／設計"
    if any(k in t for k in ["engineer", "devops", "sre", "qa", "工程師"]):
        return "軟體工程"
    if any(k in t for k in ["sales", "account", "customer success", "marketing", "campaign",
                            "business dev", "partnership", "業務", "行銷", "客戶成功",
                            "商務", "拓展", "顧問", "merchant success"]):
        return "商務／行銷／客戶成功"
    return "其他（HR／法務／財會／IT）"


def openScore(rows, company):
    """『文化開放』完全由行為算出，不是形容詞（← 報告 §02 的評分規則）。

    四項行為證據各 1 分，基底 1 分：使用開放平台刊登、公開薪資帶、
    提供實習或遠端、JD 具體（平均長度 > 300 字）。
    """
    if not rows:
        return 1
    score = 1
    if any(r.get("channels") for r in rows):
        score += 1
    if any(r.get("salary") for r in rows):
        score += 1
    if any(k in (r.get("title") or "").lower() or k in (r.get("title") or "")
           for r in rows for k in ["intern", "實習", "遠端", "remote"]):
        score += 1
    avgLen = sum(len(r.get("req") or "") for r in rows) / len(rows)
    if avgLen > 300:
        score += 1
    return min(score, 5)


PURITY_LABEL = {"service": "代理／顧問", "adjacent": "相近非純"}


def repScoreOf(repEntry):
    return repEntry.get("repScore") if repEntry else None


def meter(v):
    return ('<span class="meter" aria-label="%d / 5">' % v
            + "".join(f'<span class="m{"on" if i < v else "off"}"></span>' for i in range(5))
            + "</span>")


def companyRows(config, jobs, rep):
    out = []
    measured = [repScoreOf(rep.get(c["name"])) for c in config["companies"]]
    measured = [m for m in measured if m is not None]
    median = sorted(measured)[len(measured) // 2] if measured else 3

    for c in config["companies"]:
        mine = [r for r in jobs if matchCompany(r.get("company"), c["name"])]
        twOnly = [r for r in mine
                  if any(k in (r.get("location") or "")
                         for k in ["Taiwan", "Taipei", "台北", "臺北", "新北", "台中",
                                   "臺中", "高雄", "嘉義", "桃園", "新竹", "台灣", "海外"])]
        repEntry = rep.get(c["name"])
        repVal = repScoreOf(repEntry)
        repUnknown = repVal is None
        openVal = openScore(mine, c)

        # hot／growth 沒查到證據就留空（← JR-004）。這裡**刻意不給預設值**——
        # 舊版 `c.get("hot", 2)` 會讓沒研究過的公司帶著憑空的 2 分進榜，
        # 那正是 JR-001 推翻過三家的那種「看起來有分、其實沒有依據」。
        hot = c.get("hot")
        growth = c.get("growth")
        scored = hot is not None and growth is not None
        purity = c.get("purity", "core")
        # 只排序 core（← JR-004）；未評分者也不排。兩者都照列，只是 # 欄顯示「—」
        ranked = scored and purity == "core"
        total = (int(hot) + (median if repUnknown else repVal) + int(growth) + openVal
                 if scored else None)

        if repEntry and repEntry.get("reviewCount"):
            conf = "高" if repEntry["reviewCount"] >= 50 else "中"
        elif mine:
            conf = "中"
        else:
            conf = "低"

        chan = []
        for label, url in [("Yourator", f"https://www.yourator.co/companies/"
                            f"{(c.get('channels') or {}).get('yourator')}"),
                           ("Cake", f"https://www.cake.me/companies/"
                            f"{(c.get('channels') or {}).get('cake')}/jobs?locale=zh-TW"),
                           ("官網 Greenhouse", f"https://job-boards.greenhouse.io/"
                            f"{(c.get('channels') or {}).get('greenhouse')}")]:
            key = {"Yourator": "yourator", "Cake": "cake",
                   "官網 Greenhouse": "greenhouse"}[label]
            if (c.get("channels") or {}).get(key):
                chan.append(f'<a href="{url}" target="_blank" rel="noopener">{label}</a>')
        if c.get("careers"):
            chan.append(f'<a href="{c["careers"]}" target="_blank" rel="noopener">官網徵才</a>')
        if c.get("manualOnly"):
            chan.append('<span class="sub" style="display:inline">104（未取得）</span>')

        jobsCell = (f'{len(twOnly)}<span class="sub"> 台灣</span>' if mine
                    else '<span class="sub" style="display:inline">未取得</span>')
        repCell = ('<span class="sub" style="display:inline">—</span>' if repUnknown
                   else meter(repVal))
        note = c.get("note", "")
        if repEntry and repEntry.get("companyScore") is not None:
            note += (f"　面試趣：公司評價 {repEntry['companyScore']}／5"
                     f"（{repEntry['reviewCount']} 篇）、年薪約 "
                     f"{repEntry.get('annualSalaryWan')} 萬。")

        dash = '<span class="sub" style="display:inline">—</span>'
        badge = ("" if purity == "core"
                 else f'<span class="ptag p-{purity}">{PURITY_LABEL[purity]}</span>')
        cat = "｜".join(x for x in [c.get("category"), c.get("segment")] if x)

        out.append(f"""<tr data-hot="{hot if scored else -1}" data-rep="{-1 if repUnknown else repVal}"
 data-growth="{growth if scored else -1}" data-open="{openVal}"
 data-total="{total if scored else -1}" data-purity="{purity}"
 data-ranked="{1 if ranked else 0}"
 data-jobs="{len(twOnly) if mine else -1}">
 <td class="rank"></td>
 <td><div class="cname">{e(c['name'])}{badge}</div><div class="ccat">{e(cat)}</div></td>
 <td class="num">{jobsCell}</td>
 <td>{meter(hot) if scored else dash}</td><td>{repCell}</td>
 <td>{meter(growth) if scored else dash}</td><td>{meter(openVal)}</td>
 <td class="num tot">{total if scored else dash}</td>
 <td class="conf c-{ {'高': 'hi', '中': 'mid', '低': 'lo'}[conf] }">{conf}</td>
 <td class="chan">{'、'.join(chan) or '<span class="sub" style="display:inline">無公開管道</span>'}</td>
 <td class="cnote">{e(note)}</td>
</tr>""")
    return "\n".join(out)


def repTable(config, rep):
    rows = []
    order = sorted(rep.items(),
                   key=lambda kv: -(kv[1].get("companyScore") or 0))
    codeOf = {c["name"]: (c.get("channels") or {}).get("interviewCode")
              for c in config["companies"]}
    for name, d in order:
        code = codeOf.get(name, "")
        link = f'<a href="https://interview.tw/c/{code}/info" target="_blank" rel="noopener">{e(name)}</a>'
        if d.get("companyScore") is None:
            rows.append(f'<tr><td>{link}</td>'
                        f'<td class="num sub" colspan="7">心得數不足，面試趣未產生評分'
                        f'——本頁口碑一欄標「—」，四維總分以已測公司中位數代入</td></tr>')
            continue
        rows.append(f"""<tr>
 <td>{link}</td>
 <td class="num"><strong>{d['companyScore']}</strong></td><td class="num">{d.get('repScore')}</td>
 <td class="num">{d.get('interviewScore')}</td><td class="num">{d.get('interviewDifficulty')}</td>
 <td class="num">{d.get('reviewCount')}</td><td class="num">{d.get('annualSalaryWan')} 萬</td>
 <td class="sm">{d.get('dailyHours')} 小時・{e(d.get('overtime') or '')}</td>
</tr>""")
    return "\n".join(rows)


def jobTable(jobs, companyName, onlyTW=False, showPosted=False):
    sel = [r for r in jobs if matchCompany(r.get("company"), companyName)]
    if onlyTW:
        sel = [r for r in sel if "Taiwan" in (r.get("location") or "")]
    groups = {}
    for r in sorted(sel, key=lambda x: (x.get("updated") or ""), reverse=True):
        groups.setdefault(cat(r.get("title")), []).append(r)

    out = []
    for g in CATORDER:
        if g not in groups:
            continue
        out.append(f'<tr class="grp"><td colspan="5">{g}'
                   f'<span class="gcount">{len(groups[g])}</span></td></tr>')
        for r in groups[g]:
            posted = (f'<div class="sub">刊登 {r["posted"]}</div>'
                      if showPosted and r.get("posted") else "")
            sal = r.get("salary") or '<span class="sub">未公開</span>'
            loc = (r.get("location") or "").replace("台北市, 台灣", "台北").replace(", 台灣", "")
            chans = "＋".join(r.get("channels") or [r.get("channel", "")])
            out.append(f"""<tr>
 <td class="jt"><a href="{r.get('url')}" target="_blank" rel="noopener">{e((r.get('title') or '').strip())}</a></td>
 <td class="sm">{e(loc[:40])}</td>
 <td class="sm">{e(chans)}</td>
 <td class="sm">{sal}</td>
 <td class="sm when">{e(r.get('updated') or '—')}{posted}</td>
</tr>""")
    return "\n".join(out)


def coBreakdown(config):
    """頁首的覆蓋家數。三層拆開寫，不只給一個總數——
    「35 家」看起來比「20 家」漂亮，但其中 4 家是代理商、4 家職能只是相近，
    合成一個數字會讓覆蓋看起來比實際好（← JR-004）。"""
    cs = config["companies"]
    n = {k: sum(1 for c in cs if c.get("purity", "core") == k)
         for k in ("core", "service", "adjacent")}
    return (f"{len(cs)} 家（自有產品 {n['core']}、代理／顧問 {n['service']}、"
            f"相近非純 {n['adjacent']}）")


def main():
    ap = argparse.ArgumentParser(description="產生求職情報 artifact HTML")
    ap.add_argument("--date", required=True)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    config = yaml.safe_load(open(ROOT / "companies.yaml", encoding="utf-8"))
    jobs = json.load(open(ROOT / "data" / args.date / "jobs_final.json", encoding="utf-8"))
    repPath = ROOT / "data" / "reputation" / f"{args.date}.json"
    rep = json.load(open(repPath, encoding="utf-8")) if repPath.exists() else {}

    tpl = open(ROOT / "report" / "template.html", encoding="utf-8").read()
    out = (tpl
           .replace("<!--CO_COUNT-->", str(len(config["companies"])))
           .replace("<!--CO_BREAKDOWN-->", coBreakdown(config))
           .replace("<!--COMPANY_ROWS-->", companyRows(config, jobs, rep))
           .replace("<!--REP_TABLE-->", repTable(config, rep))
           .replace("<!--APPIER_TW-->", jobTable(jobs, "Appier", onlyTW=True, showPosted=True))
           .replace("<!--SHOPLINE-->", jobTable(jobs, "SHOPLINE 商線科技"))
           .replace("<!--CRESC-->", jobTable(jobs, "漸強實驗室 Crescendo Lab"))
           .replace("<!--OMNI-->", jobTable(jobs, "Omnichat 全通路科技"))
           .replace("<!--AWOO-->", jobTable(jobs, "awoo 阿物科技"))
           # 只呼叫一次：matchCompany 用前綴比對，「adGeek／Atelli 艾得利」已經同時吃到
           # company 欄寫「adGeek」的那批。呼叫兩次會讓同一筆職缺在頁面上出現兩列。
           .replace("<!--ADGEEK-->", jobTable(jobs, "adGeek／Atelli 艾得利"))
           .replace("<!--MISC-->", jobTable(jobs, "91APP") + jobTable(jobs, "Ocard 瑞乘數位")
                    + jobTable(jobs, "The Trade Desk（台北）")))

    outPath = pathlib.Path(args.out or (ROOT / "report" / f"artifact-{args.date}.html"))
    outPath.write_text(out, encoding="utf-8")

    leftover = re.findall(r"<!--[A-Z_]+-->", out)
    print(f"✅ 已產生 {outPath}（{len(out)} 字元）")
    print(f"   職缺 {len(jobs)} 筆、口碑 {len(rep)} 家、公司 {len(config['companies'])} 家")
    if leftover:
        print(f"⚠️  仍有未填的佔位符：{leftover}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
