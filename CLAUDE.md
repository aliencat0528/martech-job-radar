> 繼承根目錄共用規則（Claude Code 已自動載入，勿重複讀取 ../CLAUDE.md）

# martech-job-radar

## 技術棧與指令

- Python 3.12＋venv（`.venv/`，不進 git）；依賴僅 requests / pyyaml
- 執行：`.venv/bin/python run.py`（選項見 README）
- Lint：`.venv/bin/python -m py_compile run.py fetch/*.py *.py`

## 與根規則的差異

- **資料快照要進 git**：`data/<日期>/jobs_final.json` 是「哪些缺消失了」的跨期比較基準，
  屬「程式產出的資料資產」——仍禁止手改，但由 pipeline 重新產生後 commit 是正常流程
  （同 `martech-trend-agent`，← D-002 的同一類處理）
- **抓取禮儀**：只用官方公開 API 或開放給前端的 JSON 端點；請求間隔 ≥1 秒；
  來源加 bot 防護（如 104 的 Cloudflare）就放棄該來源，
  **禁止加入任何繞過防護的依賴**（cloudscraper、curl_impersonate、undetected-chromedriver 等）
- **104 只走人工匯入**：`import104.py` 解析**使用者自己瀏覽器另存**的本機檔案，
  不連網、不打 104。這條線需要人在場，因此**永遠不得放進任何排程**（← D-018）
- **不重算產業趨勢**：報告 §05 直接引用 `martech-trend-agent` 當期
  `reports/analysis-<日期>.md` 的結論。趨勢結論只有一個來源，避免兩份報告互相打架

## 與 martech-trend-agent 的關係

唯讀消費者。只讀它產出的 `data/raw/<日期>/jobs.json`，**不 import 它的模組、不改它的 config**。
契約欄位：`company` / `title` / `area` / `link` / `appearDate` / `source`。
找不到快照時降級成只用本專案自抓的來源，不硬相依。

## 決策記錄

見 `prepare.md`（編號前綴 `JR-`）。
