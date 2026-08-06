# 候選公司名單（尚未進 `companies.yaml`）

> **這份檔案是 JR-004 的落地素材，不是報告內容。**
> `companies.yaml` 是主檔；本檔只放「已經查過、但還沒建檔」的公司，
> 每建檔一家就從這裡移除。清空即代表本輪擴充做完。
>
> **建立日期**：2026-08-06 · **觸發**：報告名單漏了美庫爾 Merkle，追查後發現主檔從無收錄準則

---

## 分類軸（JR-004 定案）

**六大類 `category`**：沿用 MarTech Landscape 的固定六類，取代原本每家一種寫法的自由字串——
自由字串讓「這一期是廣告端還是資料端在招人」算不出來。

`廣告推廣` / `內容體驗` / `社群關係` / `商務銷售` / `資料` / `管理`

**三層 `purity`**：三層全收，但**報告預設只排序 `core`**。

| 值 | 定義 | 為什麼分開排 |
|----|------|-------------|
| `core` | 自有 MarTech 產品／平台為主要營收來源 | 有產品職梯，四維可比 |
| `service` | 代理商、顧問、系統整合商，賣的是人與專案 | 熱門度與成長力的口徑和 SaaS 不同義 |
| `adjacent` | 主業非行銷科技，但職能高度重疊 | 職缺多半不是行銷科技職，混進排名會失真 |

## 查證狀態的意思

- **已查證**（2026-08-06）＝ 確認公司在台實體存在，且有可指認的招募出口（104 公司代碼／
  Yourator slug／官網徵才頁）。**不代表現在有在刊職缺**——那要等實抓。
- **待查證** ＝ 尚未驗，不得寫進報告，也不得當成「名單已完整」的依據。

查證來源：Yourator 公司標籤 API（`/api/v2/companies?term[]=<標籤>`，實查 12 個標籤）＋ 網路搜尋。

---

## 廣告推廣 Advertising & Promotion

| 公司 | purity | 依據 | 狀態 |
|------|--------|------|------|
| 美庫爾 Merkle Taiwan | service | dentsu 旗下 CXM，2021-12 在台成立；104 公司代碼 `1a2x6bicuq` | 已查證 |
| 達摩媒體 | core | 程序化廣告／DMP；104 公司代碼 `cyrv33k`，徵才中 | 已查證 |
| 就是廣告科技 | 待定 | Yourator「AdTech」標籤唯一命中，業務範圍未確認 | 公司已查證，業務待查 |
| Accucrazy 肖準行銷 | service | Yourator 廣告科技／數位行銷標籤 | 已查證 |
| 數字廣告 | 待定 | Yourator 廣告科技標籤；與 8891「數字科技」無關係待確認 | 公司已查證，歸屬待查 |
| 安布思沛 iProspect | service | dentsu 效果行銷線，與美庫爾同集團 | 待查證 |
| Criteo／Taboola／AppsFlyer 台灣 | adjacent | 國際平台在台多只設商務端（同 The Trade Desk 的形狀） | 待查證 |
| TAmedia | 待定 | 行動聯播網＋自有 DMP；**歸屬電信商有兩種說法**，查到的資料互相矛盾 | 待查證 |

## 社群關係 Social & Relationships

> 最該補的一格。漸強、AccuHit、Omnichat 都在這條賽道，只收三家會低估
> 「對話式 CRM 是台灣最熱的分類」這條結論的樣本數。

| 公司 | purity | 依據 | 狀態 |
|------|--------|------|------|
| OakMega 大橡科技 | core | Social CRM＋LINE 行銷自動化，150+ 品牌、已進日本；Yourator slug `OakMega` | 已查證 |
| 意藍資訊 eLand | core | OpView 社群口碑資料庫；**上櫃 6925**，雲端訂閱佔營收 >90%、續約率 >85% | 已查證 |
| CreatorDB | core | KOL 數據，對標 iKala KOL Radar | 公司已查證 |
| AlleyPin 翔評互動 | core | 評論口碑管理／診所 CRM | 公司已查證 |
| QSearch | core | 社群數據分析（見 OakMega 合作報導） | 待查證 |

## 資料 Data

| 公司 | purity | 依據 | 狀態 |
|------|--------|------|------|
| LnData 麟數據科技 | core | DMP＋CDP 雙引擎，自述台灣第一家第三方數據監測 | 已查證 |
| WebComm 偉康科技 | adjacent | Yourator「CDP」標籤命中；身分驗證起家的系統商 | 公司已查證 |
| 創市際 InsightXplorer | adjacent | 受眾衡量／市場研究 | 待查證 |
| 精誠資訊 Etu | adjacent | SI 型 CDP，非產品公司 | 待查證 |

## 商務銷售 Commerce & Sales

| 公司 | purity | 依據 | 狀態 |
|------|--------|------|------|
| meepShop | core | 開店 SaaS，與 SHOPLINE／91APP 同類卻漏收 | 已查證 |
| inline | core | 餐飲訂位＋會員，與 Ocard 同類 | 公司已查證 |
| 12CM 睿鼎數位 | adjacent | O2O 支付／會員 | 公司已查證 |
| iCHEF | adjacent | POS 起家，會員經營為附加模組 | 待查證 |
| Hour Loop 飛輪電商、樂播科技 Jambo Live | adjacent | 電商營運／直播，非工具商 | 公司已查證 |

## 內容體驗 Content & Experience

| 公司 | purity | 依據 | 狀態 |
|------|--------|------|------|
| 玩美移動 Perfect Corp | core | AI/AR 試妝賣給美妝品牌，NYSE 上市 | 公司已查證 |
| 三竹資訊 | adjacent | 簡訊／推播 API，上櫃 | 待查證 |
| 簡訊設計 圖文不符 | service | 內容代理 | 公司已查證 |

## 管理 Management

**台灣幾乎空白**——行銷預算、專案協作、素材管理這類工具沒有本土玩家。
這格留白**本身就是報告可以寫的一條結論**，不是資料缺漏；建檔時不要為了填滿而硬塞。

---

## 建檔時的注意事項

- `hot`／`growth` 是手填維度，**沒查到證據就留空，不要憑印象給分**——
  JR-001 已經因為主觀判斷被實測推翻過三家。
- `interviewCode` 要逐家人工搜（面試趣搜尋頁前端渲染，抓不到代碼）。
  查不到就留空，口碑欄依 JR-001 標「—」、四維總分以中位數代入。
- 只在 104 的公司要標 `manualOnly: true`，報告才會標「未取得」而不是「無職缺」。
  **美庫爾就是漏了這一步才整家消失**——連盲區都沒被記錄下來，比標「未取得」更糟。
