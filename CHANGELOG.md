# Changelog

格式依循 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)。

> 本檔於 v1.1.1 補建，v1.0.0 與 v1.1.0 的條目由 README 版本歷史與 git log 回填。

## [1.1.1] - 2026-08-10

### Fixed
- **`report/buildArtifact.py` 的 adGeek 職缺在頁面上重複兩次**：`<!--ADGEEK-->` 原本呼叫
  `jobTable()` 兩次（`adGeek／Atelli 艾得利` 與 `adGeek`），但 `matchCompany()` 是前綴比對，
  第一次呼叫已經把兩種公司名的資料都吃進去了。改為只呼叫一次。
  2026-08-05 那期兩個名稱各有資料所以沒被發現，本期資料全部集中在其中一個名稱才顯形

### Added
- `docs/ARCHITECTURE.md`：四層架構圖、模組職責、去重鍵與跨期比較的前提、與上游的邊界
- 本檔（`CHANGELOG.md`）

### Changed
- 報告更新到 **第 2 期（2026-08-10）**：35 家、265 筆職缺。`report/template.html` 的
  §01 判斷、§04 統計、§05 趨勢引用、§07 覆蓋限制全數改寫
- README 的資料來源限制：104 未取得的公司從 5 家更正為 **7 家**（名單擴充後新增
  美庫爾 Merkle、達摩媒體），家數以 `mergeChannels.py` 印出的清單為準

### Notes
- 本期是第一次有可比的上一期，但主檔在 08/06 從 20 家擴到 35 家，
  196 → 265 的差額幾乎全來自名單。跨期判讀限定在「上期就已在名單裡的公司」子集（196 → 190）

## [1.1.0] - 2026-08-06

### Added
- `companies.yaml` 新增 `purity` 三層（`core` 自有產品／`service` 代理顧問／`adjacent` 相近非純）
  與 MarTech Landscape 六大類固定 `category`，三層全收但**報告只排序 `core`**（← JR-004）
- `mergeChannels.py` 新增 taxonomy 守門：`category`／`purity` 寫錯值會在單一入口出聲
- `docs/candidates.md`：查過但還沒建檔的候選公司

### Changed
- 公司名單 20 → 35 家，補收美庫爾 Merkle、OakMega、意藍資訊、LnData、meepShop 等
- **未評分的公司不再拿預設分進榜**（← JR-005）：`hot`／`growth` 留空者照列但不排名，
  `#` 欄標「—」。舊行為 `c.get("hot", 2)` 會讓沒研究過的公司帶著憑空的 2 分擠掉前段班

## [1.0.0] - 2026-08-05

### Added
- `companies.yaml` 公司主檔（20 家公司、9 家面試趣代碼）
- 抓取層：`fetch/fetchCake.py`、`fetch/fetchYourator.py`、`fetch/fetchRep.py`，
  加上唯讀取用 `martech-trend-agent` 快照
- `import104.py`：104 人工匯入，解析使用者自己另存的本機頁面，三段回退、不連網
- `mergeChannels.py`：單一入口守門（欄位契約＋跨管道去重＋新鮮度檢查）
- `report/buildArtifact.py` ＋ `report/template.html`：資料驅動的報告生成器，無手抄數字
- 2026-08-05 的 196 筆基準快照

### Fixed
- 去重鍵從「公司＋職稱」改為平台職缺編號——SHOPLINE 兩個不同團隊、同名的
  `Data Analyst` 原本會被併成一筆
- 上游快照新鮮度守門：上游 repo 的工作區停在不含最新快照的分支時，
  本工具會安靜地用到舊資料且無錯誤訊息

### Removed
- 104 自動抓取——端點有 Cloudflare bot 防護，不做規避，改走人工匯入
