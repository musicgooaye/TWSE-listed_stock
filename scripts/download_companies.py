#!/usr/bin/env python3
"""
下載台灣證交所上市、上櫃、興櫃公司清單
排除認購(售)權證
資料來源：https://isin.twse.com.tw/isin/C_public.jsp

修正：處理 BIG5 編碼問題
"""

import requests
import pandas as pd
import os
import time
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

# 更完整的 User-Agent 和請求頭
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def fetch_companies_from_url(url, market_name, max_retries=3):
    """
    從指定 URL 爬取公司清單，支援重試機制

    Args:
        url: 目標 URL
        market_name: 市場名稱（上市/上櫃/興櫃）
        max_retries: 最大重試次數

    Returns:
        DataFrame 包含 code, name, market, type, listing_date
    """
    for attempt in range(max_retries):
        try:
            print(f"  嘗試 {attempt + 1}/{max_retries}...", end=" ", flush=True)

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=15,
                allow_redirects=True
            )

            # 重要：嘗試檢測實際編碼
            # TWSE 網站使用 BIG5 編碼
            if response.apparent_encoding and 'big5' in response.apparent_encoding.lower():
                response.encoding = 'big5'
            elif response.encoding and 'utf' not in response.encoding.lower():
                # 如果不是 UTF，使用檢測到的編碼
                pass
            else:
                # 預設試試 BIG5
                response.encoding = 'big5'

            response.raise_for_status()
            print("✓")

            soup = BeautifulSoup(response.text, 'html.parser')

            # 尋找所有表格
            tables = soup.find_all('table')
            if not tables:
                print(f"⚠️ 無法找到表格：{market_name}")
                return pd.DataFrame()

            companies = []

            # 遍歷所有表格
            for table_idx, table in enumerate(tables):
                rows = table.find_all('tr')

                # 跳過標題行（通常是第一行）
                data_rows = rows[1:] if len(rows) > 1 else rows

                for row_idx, row in enumerate(data_rows):
                    cols = row.find_all('td')

                    # 檢查列數
                    if len(cols) < 5:
                        continue

                    try:
                        # 新的網站結構：
                        # [0] 有價證券代號及名稱 (e.g., "1101 台泥")
                        # [1] 國際證券辨識號碼(ISIN Code) (e.g., "TW0001101004")
                        # [2] 上市日 (e.g., "1962/02/09")
                        # [3] 產業別 (e.g., "水泥工業")
                        # [4] CFI Code (e.g., "ESVUFR")

                        code_name = cols[0].get_text(strip=True)
                        isin_code = cols[1].get_text(strip=True)
                        listing_date = cols[2].get_text(strip=True)
                        industry = cols[3].get_text(strip=True)
                        cfi_code = cols[4].get_text(strip=True)

                        # 跳過空行或標題行
                        if not code_name or '代號' in code_name:
                            continue

                        # 從"代號 名稱"中分割
                        parts = code_name.split(maxsplit=1)
                        if len(parts) < 2:
                            continue

                        code = parts[0]
                        name = parts[1]

                        # 檢查是否為權證（排除）
                        if any(keyword in industry or keyword in cfi_code for keyword in EXCLUDE_KEYWORDS):
                            continue

                        # 檢查是否為有效的股票代號
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

                    except Exception as e:
                        # 跳過無法解析的行
                        continue

            if companies:
                print(f"✓ 成功爬取 {market_name}：{len(companies)} 筆")
                return pd.DataFrame(companies)
            else:
                print(f"⚠️ 無法找到有效的公司數據：{market_name}")
                return pd.DataFrame()

        except requests.exceptions.Timeout:
            print(f"✗ 超時")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指數退避
                print(f"    等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
            else:
                print(f"✗ 爬取失敗 ({market_name})：多次超時")
        except requests.exceptions.ConnectionError as e:
            print(f"✗ 連線失敗")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"    等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
            else:
                print(f"✗ 爬取失敗 ({market_name})：無法連接 - {e}")
        except Exception as e:
            print(f"✗ 爬取失敗 ({market_name})：{e}")
            return pd.DataFrame()

    return pd.DataFrame()

def main():
    print("開始下載台灣證交所公司清單...")
    print("-" * 50)

    all_companies = []

    # 爬取三個市場的公司
    for market, url in SOURCES.items():
        print(f"\n正在爬取 {market}：")
        df = fetch_companies_from_url(url, market)
        if not df.empty:
            all_companies.append(df)
        else:
            print(f"  ⚠️ {market} 無法獲取數據")

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

    print("\n" + "-" * 50)
    print(f"✓ 更新完成！")
    print(f"✓ 總公司數：{len(result_df)}")
    print(f"✓ 輸出檔案：{filename}")
    print(f"  - 上市：{len(result_df[result_df['market'] == '上市'])}")
    print(f"  - 上櫃：{len(result_df[result_df['market'] == '上櫃'])}")
    print(f"  - 興櫃：{len(result_df[result_df['market'] == '興櫃'])}")

if __name__ == '__main__':
    main()
