# martech-job-radar - 台灣 MarTech 求職情報彙整

把散在四個招募管道的台灣 MarTech 職缺與公司口碑收攏成一份可重複產生的求職報告，
回答三個問題：**現在有哪些缺、這些公司值不值得投、我該先投哪一個**。

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

姊妹專案 [`martech-trend-agent`](https://github.com/aliencat0528/martech-trend-agent)
回答的是「產業風向往哪吹」；本專案回答「我現在該投哪裡」。兩者共用資料、分離產出，
耦合只有兩處（見「與 martech-trend-agent 的關係」）。

## 功能特色

- **多管道彙整**：Cake（結構化薪資與確切更新時間）、面試趣（公司口碑與年薪中位）、
  104（人工匯入），加上讀取 `martech-trend-agent` 已抓好的 Greenhouse／Yourator 快照
- **單一入口守門**：所有來源都必須通過 `mergeChannels.py`——欄位契約、跨管道去重、
  新鮮度檢查；缺席或過期會**出聲**而不是安靜略過
- **跨期比較**：`data/<日期>/jobs_final.json` 進 git，下一期能算出「哪些缺消失了、
  哪些是新開的、誰的口碑掉了」
- **公司四維排序**：熱門／口碑／成長力／文化開放，其中口碑與文化開放完全由資料算出，
  換算規則寫在 `companies.yaml`，可自行改權重重排

## 快速開始

```bash
cd martech-job-radar
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py
# 預期：依序印出各來源筆數，最後
# ✅ 合併完成：N 筆 → 去重後 M 筆
#    輸出：data/YYYY-MM-DD/jobs_final.json
#    104 手動匯入：❌ 本期沒有（列出受影響的 5 家公司）
```

## 使用方式

本工具分兩層：**機械層**（Python 抓取＋整併，可自行執行）與**分析層**
（Claude 讀完資料撰寫判斷與投遞優先序，需模型在場）。

### 機械層

| 指令 | 用途 |
|------|------|
| `.venv/bin/python run.py` | 完整執行：抓取 → 整併 → 產出 `jobs_final.json` |
| `.venv/bin/python run.py --no-cake --no-rep` | 只跑部分來源（四個略過旗標可組合） |
| `.venv/bin/python mergeChannels.py --date <日期>` | 只重跑整併（改完 yaml 後用，不打網路） |
| `.venv/bin/python report/buildArtifact.py --date <日期>` | 由資料產生報告 HTML |

### 104 人工匯入

104 有 Cloudflare bot 防護，本工具**不做任何規避**。改走人工匯入——
你以真人身分正常瀏覽後另存的頁面，本工具只讀本機檔案、不連網：

```bash
# 1. 瀏覽器開 104 搜尋結果或公司職缺頁，捲到底把職缺載完
# 2. Cmd+S 另存為「網頁，僅 HTML」。一個檔＝那一整頁的所有職缺，不必一筆一筆存
# 3. 多頁就多存幾個檔，一次丟進來（可給多個檔或整個資料夾）：
.venv/bin/python import104.py ~/Downloads/104pages/ --company "iKala 愛卡拉" \
  --out data/manual/104/$(date +%F)/jobs_104.json
```

解析採三段回退（schema.org JobPosting → `__NUXT__` 內嵌狀態 → DOM 錨點），
每個檔會印出實際命中哪一段。

### 分析層

在 Claude Code 打 **`/job-radar`**——讀完資料後撰寫報告的判斷章節、更新視覺化 artifact。
見解由 Claude 親自寫，非模板。

## 專案結構

```
martech-job-radar/
├── companies.yaml       # 公司主檔：四維基準、各平台 slug、面試趣 code（唯一需手動維護的檔）
├── run.py               # 主程式：抓取 → 整併
├── fetch/
│   ├── fetchCake.py     # Cake 頁面內嵌 __NEXT_DATA__（結構化薪資＋確切更新日）
│   ├── fetchYourator.py # Yourator（補上游沒追蹤的公司，如 SHOPLINE）
│   └── fetchRep.py      # 面試趣公司評價與年薪中位
├── import104.py         # 解析本機另存的 104 頁面（不連網）
├── mergeChannels.py     # 單一入口：欄位契約、跨管道去重、新鮮度守門
├── report/
│   ├── buildArtifact.py # 由資料產生報告 HTML（無手抄數字）
│   └── template.html    # 版面與正文（與資料分離）
└── data/
    ├── auto/<日期>/     # 機械層抓的原始快照
    ├── manual/104/<日期>/ # 你匯入的 104 資料
    ├── reputation/<日期>.json # 面試趣口碑（非職缺，不進整併流）
    └── <日期>/jobs_final.json # 合併去重後的基準（進 git）
```

## 與 martech-trend-agent 的關係

**唯讀消費者，介面是檔案不是程式。** 只讀它產出的 `data/raw/<日期>/jobs.json`，
不 import 它的模組、不改它的 `config.yaml`——它怎麼重構內部都不會弄壞這裡。

| 耦合點 | 內容 | 解決什麼 |
|--------|------|---------|
| `jobs.json` 唯讀契約 | 欄位 `company` / `title` / `area` / `link` / `appearDate` / `source` | 不重寫 Greenhouse 與 Yourator 兩支已跑過四期、坑都補好的 fetcher |
| 報告 §05 引用其分析結論 | 引 `reports/analysis-<日期>.md`，不自己重算趨勢 | 趨勢結論只有一個來源，兩份報告不會互相打架 |

找不到快照時降級成只用本專案自抓的來源，**不硬相依**。

## 測試

```bash
.venv/bin/python -m py_compile run.py fetch/*.py import104.py mergeChannels.py
.venv/bin/python mergeChannels.py --date <既有快照日期>   # 不打網路，驗證整併與守門
```

## 版本歷史

### v1.0.0 (2026-08-05)

- **首版** — `companies.yaml` 主檔（20 家公司、9 家面試趣代碼）、
  Cake／Yourator／面試趣 fetcher、104 人工匯入、整併守門（欄位契約＋去重＋新鮮度）、
  資料驅動的報告生成器，以及 2026-08-05 的 **196 筆**基準快照

## 授權

MIT License

---

## 資料來源限制（判讀前必讀）

- **104 不自動抓**（Cloudflare bot 防護，本工具不做規避）：iKala、CYBERBIZ、Vpon、
  cacaFly、域動行銷五家的職缺**只存在於 104**，未人工匯入時它們在報告中應標為
  **「未取得」而不是「無職缺」**——這兩者在求職判斷上差很多
- **官網徵才頁沒有東西可爬**（2026-08-05 查證）：iKala 官網唯一出口是 104 公司頁、
  TenMax 導向 Yourator、CYBERBIZ 只有通用履歷表單、Vpon 的 careers 停更在 2025-02
- **口碑資料的樣本差異很大**：面試趣心得數從 51 篇（TenMax）到 807 篇（91APP）不等，
  50 篇以下只當參考；漸強實驗室心得數不足，口碑欄標「—」而非給分
- **年薪中位的口徑**：面試趣的數字涵蓋全公司所有職級與職能，與職缺公開薪資
  （特定職缺的談判帶）**不可直接相減**
- **公司名單本身有已知缺口**：現行 20 家是「開放平台抓得到的」長出來的，不是照準則選的。
  收錄範圍已於 JR-004 定案（三層全收、報告只排序 `core`）但**尚未落到 `companies.yaml`**——
  在那之前，代理商／顧問型公司（如美庫爾 Merkle）缺席不代表它們沒在招。
  已查證的候選見 `docs/candidates.md`

## 相關文件

- **待驗證與待操作事項（9 筆）** → `prepare.md` 文末。
  第 9 筆是**下次開發的起點**（JR-004 落地）；第 1 筆最重要：`import104.py` 從未對真實 104 頁面跑過
- 決策記錄（`JR-` 系列）→ `prepare.md`
- **候選公司名單（尚未建檔）** → `docs/candidates.md`。三層 `purity` 與六大類 `category` 的
  定義也在該檔，主檔尚未套用
- README 更新觸發條件、版本規則 → `../.claude/specs/docs.md`
- 分析層流程 → `../.claude/commands/job-radar.md`
