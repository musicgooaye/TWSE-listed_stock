# TWSE Listed Companies

台灣證券交易所上市、上櫃、興櫃公司清單自動爬蟲

## 概述

每月自動爬取台灣證交所的上市、上櫃、興櫃公司清單，排除認購(售)權證，輸出為 CSV 格式。

## 更新頻率

- **自動更新**：每月 1 日凌晨 0 點（UTC）執行
- **手動更新**：可在 GitHub Actions 分頁手動觸發

## 數據來源

| 市場 | URL |
|------|-----|
| 上市 | https://isin.twse.com.tw/isin/C_public.jsp?strMode=2 |
| 上櫃 | https://isin.twse.com.tw/isin/C_public.jsp?strMode=4 |
| 興櫃 | https://isin.twse.com.tw/isin/C_public.jsp?strMode=5 |

## 過濾條件

- **排除**：認購(售)權證
- **保留**：股票、ETF、債券等商品

## 輸出格式

### 檔案位置
