#!/usr/bin/env python3
"""
下載台灣證交所上市上櫃公司清單
資料來源：data.gov.tw 開放資料
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime

def download_from_twse_api():
    """從 TWSE API 取得上市公司清單"""
    try:
        # 從政府開放資料取得上市公司
        url = 'https://openapi.twse.com.tw/v1/listings'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data)
        
        # 重新命名欄位為中文
        df_renamed = df.rename(columns={
            'tse_listed': 'TSE_listed',
            'otc_listed': 'OTC_listed',
            'market_category': 'market_category',
            'code': 'stock_code',
            'name': 'company_name',
            'cfi_code': 'cfi_code',
            'cfi_desc': 'cfi_desc',
        })
        
        print(f"✓ 成功下載 {len(df_renamed)} 筆公司資料")
        return df_renamed
        
    except Exception as e:
        print(f"✗ 從 TWSE API 下載失敗: {e}")
        return None

def save_data(df, output_dir='data'):
    """儲存資料到 CSV 和 JSON"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 儲存 CSV
    csv_path = os.path.join(output_dir, 'companies.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"✓ 已儲存 CSV: {csv_path}")
    
    # 儲存 JSON
    json_path = os.path.join(output_dir, 'companies.json')
    df.to_json(json_path, orient='records', force_ascii=False, indent=2)
    print(f"✓ 已儲存 JSON: {json_path}")
    
    # 儲存統計資訊
    summary = {
        'update_time': datetime.now().isoformat(),
        'total_companies': len(df),
        'tse_listed': len(df[df['TSE_listed'] == 'Y']),
        'otc_listed': len(df[df['OTC_listed'] == 'Y']),
    }
    summary_path = os.path.join(output_dir, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✓ 已儲存統計: {summary_path}")

def main():
    print("開始下載台灣證交所公司清單...")
    df = download_from_twse_api()
    
    if df is not None:
        save_data(df)
        print("\n✓ 更新完成！")
    else:
        print("\n✗ 下載失敗，請檢查網路連線")
        exit(1)

if __name__ == '__main__':
    main()
