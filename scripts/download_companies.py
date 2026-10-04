#!/usr/bin/env python3
"""
下載台灣證交所上市、上櫃、興櫃公司清單
排除認購(售)權證
資料來源：https://isin.twse.com.tw/isin/C_public.jsp
"""

import requests
import pandas as pd
import os
from datetime import datetime
from bs4 import BeautifulSoup

# 數據來源配置
SOURCES = {
    '上市': 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2',
    '上櫃': 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=4',
    '興櫃': 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=5',
}

# 排除的商品類型（認購售權證）
EXCLUDE_KEYWORDS = ['認購', '認售', '權證']

def fetch_companies_from_url(url, market_name):
    """
    從指定 URL 爬取公司清單

    Args:
        url: 目標 URL
        market_name: 市場名稱（上市/上櫃/興櫃）

    Returns:
        DataFrame 包含 code, name, market, type, listing_date
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # 尋找所有表格（網站結構已改變，不再使用 classalltb）
        tables = soup.find_all('table')
        if not tables:
            print(f"⚠️ 無法找到表格：{market_name}")
            return pd.DataFrame()

        companies = []

        # 遍歷所有表格，第一個通常是空的或是標題表
        for table_idx, table in enumerate(tables):
            rows = table.find_all('tr')

            # 跳過標題行（通常是第一行包含"代號"、"名稱"等文字）
            data_rows = rows[1:] if len(rows) > 1 else rows

            for row in data_rows:
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue

                # 新的網站結構：
                # [0] 有價證券代號及名稱 (e.g., "1101 台泥")
                # [1] 國際證券辨識號碼(ISIN Code) (e.g., "TW0001101004")
                # [2] 上市日 (e.g., "1962/02/09")
                # [3] 產業別 (e.g., "水泥工業")
                # [4] CFI Code (e.g., "ESVUFR")

                code_name = cols[0].text.strip()
                isin_code = cols[1].text.strip()
                listing_date = cols[2].text.strip()
                industry = cols[3].text.strip()
                cfi_code = cols[4].text.strip()

                # 從"代號 名稱"中分割
                parts = code_name.split(maxsplit=1)
                if len(parts) < 2:
                    continue

                code = parts[0]
                name = parts[1]

                # 檢查是否為權證（排除）
                if any(keyword in industry or keyword in cfi_code for keyword in EXCLUDE_KEYWORDS):
                    continue

                # 檢查是否為有效的股票代號（避免表格邊界或空行）
                if not code or len(code) > 10 or not code.isdigit():
                    continue

                # 檢查 ISIN Code 是否有效
                if not isin_code or not isin_code.startswith('TW'):
                    continue

                companies.append({
                    'code': code,
                    'name': name,
                    'market': market_name,
                    'type': industry,
                    'listing_date': listing_date,
                })

        if companies:
            print(f"✓ 成功爬取 {market_name}：{len(companies)} 筆")
        else:
            print(f"⚠️ 無法找到有效的公司數據：{market_name}")

        return pd.DataFrame(companies)

    except Exception as e:
        print(f"✗ 爬取失敗 ({market_name})：{e}")
        return pd.DataFrame()

def main():
    print("開始下載台灣證交所公司清單...")
    print("-" * 50)
    
    all_companies = []
    
    # 爬取三個市場的公司
    for market, url in SOURCES.items():
        df = fetch_companies_from_url(url, market)
        if not df.empty:
            all_companies.append(df)
    
    if not all_companies:
        print("\n✗ 無法下載任何數據")
        exit(1)
    
    # 合併所有數據
    result_df = pd.concat(all_companies, ignore_index=True)
    result_df = result_df.drop_duplicates(subset=['code'], keep='first')
    result_df = result_df.sort_values('code').reset_index(drop=True)
    
    # 建立 data 資料夾
    os.makedirs('data', exist_ok=True)
    
    # 生成檔案名稱（包含年月）
    today = datetime.now()
    filename = f"data/twse_companies_{today.strftime('%Y-%m')}.csv"
    
    # 保存為 CSV
    result_df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print("-" * 50)
    print(f"✓ 更新完成！")
    print(f"✓ 總公司數：{len(result_df)}")
    print(f"✓ 輸出檔案：{filename}")
    print(f"  - 上市：{len(result_df[result_df['market'] == '上市'])}")
    print(f"  - 上櫃：{len(result_df[result_df['market'] == '上櫃'])}")
    print(f"  - 興櫃：{len(result_df[result_df['market'] == '興櫃'])}")

if __name__ == '__main__':
    main()
