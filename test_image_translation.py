#!/usr/bin/env python3
"""
Test script cho tính năng Image Translation
"""

import asyncio
import aiohttp
import os
import time
import hmac
import hashlib
from datetime import datetime

# Cấu hình Aidge API
AIDGE_ACCESS_KEY = "508912"
AIDGE_ACCESS_SECRET = "LvtYlmGSEglYZX5KsaBXI3HHXBPc0jYU"
AIDGE_API_DOMAIN = "api.aidc-ai.com"

def generate_aidge_signature(access_key_secret: str, timestamp: str) -> str:
    """Tạo chữ ký cho Aidge API"""
    h = hmac.new(access_key_secret.encode('utf-8'), 
                 (access_key_secret + timestamp).encode('utf-8'), 
                 hashlib.sha256)
    return h.hexdigest().upper()

async def test_aidge_api():
    """Test Aidge Image Translation API với ảnh mẫu - sử dụng translation_mllm API"""
    print("🧪 Testing Aidge Image Translation API...")
    
    # URL ảnh mẫu (có thể thay đổi)
    test_image_url = "https://ae01.alicdn.com/kf/Sa78257f1d9a34dad8ee494178db12ec8l.jpg"
    
    try:
        # Tạo timestamp
        timestamp = str(int(time.time() * 1000))
        
        # Tạo chữ ký
        sign = generate_aidge_signature(AIDGE_ACCESS_SECRET, timestamp)
        
        # URL API - sử dụng translation_mllm API (synchronous)
        api_name = "ai/image/translation_mllm"
        url = f"https://{AIDGE_API_DOMAIN}/rest/{api_name}?partner_id=aidge&sign_method=sha256&sign_ver=v2&app_key={AIDGE_ACCESS_KEY}&timestamp={timestamp}&sign={sign}"
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "x-iop-trial": "true"  # Trial mode
        }
        
        # Data - theo documentation của translation_mllm API
        data = {
            "paramJson": {
                "imageUrl": test_image_url,
                "sourceLanguage": "en",
                "targetLanguage": "vi"
            }
        }
        
        print(f"📤 Sending request to: {url}")
        print(f"📋 Data: {data}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                result = await response.json()
                print(f"📥 Response status: {response.status}")
                print(f"📥 Response: {result}")
                
                if response.status == 200:
                    # Kiểm tra response code
                    res_code = result.get("resCode")
                    if res_code == 200:
                        print("✅ API call successful!")
                        
                        # Xử lý response từ translation_mllm API
                        data = result.get("data", {})
                        
                        # Lấy URL ảnh đã dịch từ response structure
                        translated_image_url = None
                        
                        # Thử lấy từ result_list trước
                        result_list = data.get("result", {}).get("data", {}).get("structData", {}).get("message", [{}])[0].get("result_list", [])
                        if result_list:
                            translated_image_url = result_list[0].get("fileUrl")
                        
                        # Nếu không có trong result_list, thử lấy từ repairedUrl
                        if not translated_image_url:
                            repaired_url = data.get("result", {}).get("data", {}).get("structData", {}).get("message", [{}])[0].get("edit_info", {}).get("repairedUrl")
                            if repaired_url:
                                translated_image_url = repaired_url
                        
                        # Nếu vẫn không có, thử lấy từ imageResultList
                        if not translated_image_url:
                            image_result_list = data.get("imageResultList", [])
                            if image_result_list:
                                result_list = image_result_list[0].get("result_list", [])
                                if result_list:
                                    translated_image_url = result_list[0].get("fileUrl")
                        
                        if translated_image_url:
                            print(f"🖼️ Translated image URL: {translated_image_url}")
                            return translated_image_url
                        else:
                            print("❌ No translated image URL found in response")
                            return None
                    else:
                        error_message = result.get("resMessage", "Unknown error")
                        print(f"❌ API Error: {error_message}")
                        return None
                else:
                    print(f"❌ API request failed with status {response.status}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None



async def main():
    """Main test function - sử dụng translation_mllm API (synchronous)"""
    print("🚀 Starting Aidge Image Translation API Test")
    print("=" * 50)
    
    # Test translation_mllm API (synchronous)
    translated_image_url = await test_aidge_api()
    
    if translated_image_url:
        print("🎉 Test completed successfully!")
        print(f"✅ Translated image URL: {translated_image_url}")
    else:
        print("❌ Failed to translate image")

if __name__ == "__main__":
    asyncio.run(main()) 