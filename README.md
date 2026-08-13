# martech-job-radar - 台灣 MarTech 求職情報彙整

把散在四個招募管道的台灣 MarTech 職缺與公司口碑收攏成一份可重複產生的求職報告，
回答三個問題：**現在有哪些缺、這些公司值不值得投、我該先投哪一個**。

![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

姊妹專案 [`martech-trend-agent`](https://github.com/aliencat0528/martech-trend-agent)
回答的是「產業風向往哪吹」；本專案回答「我現在該投哪裡」。兩者共用資料、分離產出，
耦合只有兩處（見「與 martech-trend-agent 的關係」）。

## 功能特色

- **多管道彙整**：Cake（結構化薪資與確切更新時間）、面試趣（公司口碑與年薪中位）、
  104（人工匯入），加上讀取 `martech-trend-agent` 已抓好的 Greenhouse／Yourator 快照
- **單一入口守門**：所有來源都必須通過 `mergeChannels.py`——欄位契約、跨管道去重、
  新鮮度檢查；缺席或過期會**出聲**而不是安靜略過
- **跨期比較**：`data/<日期>/jobs_final.json` 進 git，能算出「哪些缺消失了、哪些是新開的」。
  判讀前要先扣兩種假訊號：**非追蹤公司**（上游搜尋輪替）與**名單本身的變動**
  （主檔擴充那期只能在共同子集內比），見 `docs/ARCHITECTURE.md`
- **公司四維排序**：熱門／口碑／成長力／文化開放，其中口碑與文化開放完全由資料算出，
  換算規則寫在 `companies.yaml`，可自行改權重重排
- **推薦職缺（報告 §00）**：三個門檻同時成立才進榜——口碑實測 repScore ≥ 3 且心得數 ≥ 50、
  成長力 ≥ 4（留空者不給預設分，因此不進榜）、職缺本身屬「數據分析」或「數據科學／工程」
  且在台灣。排序**不用四維總分**（那是公司的分數，拿來排職缺會讓常駐缺贏過新開缺），
  改為刊登新鮮度優先。門檻寫在 `report/buildArtifact.py` 頂部常數，改門檻不必動版面

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
├── companies.yaml       # 公司主檔：四維基準、purity 三層、各平台 slug、面試趣 code（唯一需手動維護的檔）
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
├── data/
│   ├── auto/<日期>/     # 機械層抓的原始快照
│   ├── manual/104/<日期>/ # 你匯入的 104 資料
│   ├── reputation/<日期>.json # 面試趣口碑（非職缺，不進整併流）
│   └── <日期>/jobs_final.json # 合併去重後的基準（進 git）
└── docs/
    ├── ARCHITECTURE.md  # 漏斗架構圖、模組職責、去重鍵、跨期比較的前提
    └── candidates.md    # 查過但還沒建檔的候選公司，建檔一家就從那裡移除
```

模組職責與資料流見 `docs/ARCHITECTURE.md`。

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

### v1.2.0 (2026-08-13)

- **報告新增 §00 推薦職缺**——三門檻（口碑實測達標／成長力達標／職缺屬數據 AI 方向且在台）
  篩選，門檻與排序邏輯在 `report/buildArtifact.py` 頂部常數。
  排序刻意**不用四維總分**：四維是公司的分數，用它排職缺會讓 2019 年掛到現在的常駐缺
  贏過本週新開的缺；改為新鮮度優先，並替刊登超過一年者標「常駐缺」
- 報告更新到第 3 期（265 筆、35 家）。**名單未變動，265 → 265 首次可直接跨期相減**，
  上一期的可比子集限制解除
- 本期查出**去重鍵的一個侷限**：同一個缺換城市（Appier Ad Cloud 由東京改台北）
  會因 URL 變動而被同時計入新增與消失。判讀差集時必須配合刊登日一起看

### v1.1.1 (2026-08-10)

- **修掉 artifact 的重複輸出**——`<!--ADGEEK-->` 呼叫 `jobTable()` 兩次，
  但 `matchCompany()` 是前綴比對，第一次就已經吃到兩種公司名，同一批職缺被列了兩遍
- 新增 `docs/ARCHITECTURE.md` 與 `CHANGELOG.md`
- 報告更新到第 2 期（265 筆、35 家）。**這是第一次有可比的上一期**，
  但主檔剛擴充過，跨期判讀限定在共同子集（196 → 190）

### v1.1.0 (2026-08-06)

- **公司名單有收錄準則了**（← JR-004）——`companies.yaml` 新增 `purity` 三層
  （`core` 自有產品／`service` 代理顧問／`adjacent` 相近非純）與 MarTech Landscape
  六大類固定 `category`，三層全收但**報告只排序 `core`**
- **補收 15 家**（20 → 35 家），包含原本整家不存在於名單的美庫爾 Merkle、OakMega、
  意藍資訊、LnData、meepShop 等
- **未評分的公司不再拿預設分進榜**（← JR-005）——`hot`／`growth` 留空者照列但不排名，
  `#` 欄標「—」。舊行為是 `c.get("hot", 2)`，會讓沒研究過的公司帶著憑空的 2 分擠掉前段班
- `mergeChannels.py` 新增 taxonomy 守門：`category`／`purity` 寫錯值會在單一入口出聲

### v1.0.0 (2026-08-05)

- **首版** — `companies.yaml` 主檔（20 家公司、9 家面試趣代碼）、
  Cake／Yourator／面試趣 fetcher、104 人工匯入、整併守門（欄位契約＋去重＋新鮮度）、
  資料驅動的報告生成器，以及 2026-08-05 的 **196 筆**基準快照

## 授權

MIT License

---

## 資料來源限制（判讀前必讀）

- **104 不自動抓**（Cloudflare bot 防護，本工具不做規避）：iKala、CYBERBIZ、Vpon、
  cacaFly、域動行銷、美庫爾 Merkle、達摩媒體**七家**的職缺只存在於 104，
  未人工匯入時它們在報告中應標為**「未取得」而不是「無職缺」**——這兩者在求職判斷上差很多。
  家數會隨主檔變動，**以 `mergeChannels.py` 每次印出的清單為準**，不要背這裡的名字
- **官網徵才頁沒有東西可爬**（2026-08-05 查證）：iKala 官網唯一出口是 104 公司頁、
  TenMax 導向 Yourator、CYBERBIZ 只有通用履歷表單、Vpon 的 careers 停更在 2025-02
- **口碑資料的樣本差異很大**：面試趣心得數從 51 篇（TenMax）到 807 篇（91APP）不等，
  50 篇以下只當參考；漸強實驗室心得數不足，口碑欄標「—」而非給分
- **年薪中位的口徑**：面試趣的數字涵蓋全公司所有職級與職能，與職缺公開薪資
  （特定職缺的談判帶）**不可直接相減**
- **「沒被排名」不等於「不值得投」**：報告只排序 `purity: core` 且四維齊備的公司
  （← JR-004／JR-005）。代理／顧問型（如美庫爾 Merkle）、相近非純型，以及 2026-08-06
  補收但 `hot`／`growth` 尚未查證的 15 家，都會照列在榜後、`#` 欄標「—」。
  名單覆蓋已補上、**排名覆蓋還沒**；還沒查完的候選見 `docs/candidates.md`

## 相關文件

- **待驗證與待操作事項（10 筆）** → `prepare.md` 文末。
  第 9 筆是新收 15 家的四維補分；第 1 筆最重要：`import104.py` 從未對真實 104 頁面跑過
- 架構圖、模組職責、跨期比較的前提 → `docs/ARCHITECTURE.md`
- 版本變更明細 → `CHANGELOG.md`
- 決策記錄（`JR-` 系列）→ `prepare.md`
- **候選公司名單（查過但還沒建檔，10 家）** → `docs/candidates.md`。
  三層 `purity` 與六大類 `category` 的定義也在該檔
- README 更新觸發條件、版本規則 → `../.claude/specs/docs.md`
- 分析層流程 → `../.claude/commands/job-radar.md`
