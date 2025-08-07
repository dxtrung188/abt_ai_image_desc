#!/usr/bin/env python3
"""
Debug script cho tính năng Image Translation
"""

import asyncio
import aiohttp
import os
import time
import hmac
import hashlib
import json
from datetime import datetime
from pathlib import Path

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

async def debug_image_translation():
    """Debug từng bước của image translation"""
    print("🔍 Debug Image Translation Process")
    print("=" * 50)
    
    # Bước 1: Tạo file test
    print("\n1️⃣ Tạo file test...")
    test_image_path = "debug_test_image.jpg"
    
    # Tạo một file ảnh test đơn giản (hoặc copy từ file có sẵn)
    if not os.path.exists(test_image_path):
        # Tạo file test đơn giản
        with open(test_image_path, "wb") as f:
            # Tạo một file ảnh test nhỏ
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9')
        print(f"✅ Tạo file test: {test_image_path}")
    else:
        print(f"✅ File test đã tồn tại: {test_image_path}")
    
    # Bước 2: Kiểm tra thư mục translated_images
    print("\n2️⃣ Kiểm tra thư mục translated_images...")
    translated_dir = "translated_images"
    if not os.path.exists(translated_dir):
        os.makedirs(translated_dir)
        print(f"✅ Tạo thư mục: {translated_dir}")
    else:
        print(f"✅ Thư mục đã tồn tại: {translated_dir}")
    
    # Bước 3: Test API call
    print("\n3️⃣ Test API call...")
    
    # Sử dụng URL ảnh test từ internet
    test_image_url = "https://ae01.alicdn.com/kf/Sa78257f1d9a34dad8ee494178db12ec8l.jpg"
    
    try:
        # Tạo timestamp
        timestamp = str(int(time.time() * 1000))
        
        # Tạo chữ ký
        sign = generate_aidge_signature(AIDGE_ACCESS_SECRET, timestamp)
        
        # URL API
        api_name = "ai/image/translation_mllm"
        url = f"https://{AIDGE_API_DOMAIN}/{api_name}?partner_id=aidge&sign_method=sha256&sign_ver=v2&app_key={AIDGE_ACCESS_KEY}&timestamp={timestamp}&sign={sign}"
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "x-iop-trial": "true"
        }
        
        # Data
        data = {
            "paramJson": {
                "imageUrl": test_image_url,
                "sourceLanguage": "en",
                "targetLanguage": "vi"
            }
        }
        
        print(f"📤 URL: {url}")
        print(f"📋 Data: {json.dumps(data, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                result = await response.json()
                print(f"📥 Status: {response.status}")
                print(f"📥 Response: {json.dumps(result, indent=2)}")
                
                if response.status == 200:
                    res_code = result.get("resCode")
                    if res_code == 200:
                        print("✅ API call successful!")
                        
                        # Debug response structure
                        data = result.get("data", {})
                        print(f"📊 Data structure: {json.dumps(data, indent=2)}")
                        
                        # Tìm URL ảnh đã dịch
                        translated_image_url = None
                        
                        # Thử các path khác nhau
                        paths_to_try = [
                            "result.data.structData.message[0].result_list[0].fileUrl",
                            "result.data.structData.message[0].edit_info.repairedUrl",
                            "imageResultList[0].result_list[0].fileUrl"
                        ]
                        
                        for path in paths_to_try:
                            try:
                                current_data = data
                                for key in path.split('.'):
                                    if '[' in key:
                                        key_name, index = key.split('[')
                                        index = int(index.rstrip(']'))
                                        current_data = current_data[key_name][index]
                                    else:
                                        current_data = current_data[key]
                                
                                if current_data:
                                    translated_image_url = current_data
                                    print(f"✅ Tìm thấy URL tại path: {path}")
                                    print(f"🖼️ URL: {translated_image_url}")
                                    break
                            except (KeyError, IndexError, TypeError) as e:
                                print(f"❌ Path {path} không tồn tại: {e}")
                                continue
                        
                        if translated_image_url:
                            # Bước 4: Download ảnh
                            print("\n4️⃣ Download ảnh đã dịch...")
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            translated_filename = f"debug_translated_{timestamp}.jpg"
                            translated_path = os.path.join(translated_dir, translated_filename)
                            
                            async with session.get(translated_image_url) as download_response:
                                if download_response.status == 200:
                                    translated_content = await download_response.read()
                                    with open(translated_path, "wb") as f:
                                        f.write(translated_content)
                                    
                                    print(f"✅ Download thành công: {translated_path}")
                                    print(f"📏 File size: {len(translated_content)} bytes")
                                    
                                    # Kiểm tra file
                                    if os.path.exists(translated_path):
                                        file_size = os.path.getsize(translated_path)
                                        print(f"✅ File saved: {translated_path} ({file_size} bytes)")
                                    else:
                                        print("❌ File không được tạo")
                                else:
                                    print(f"❌ Download failed: {download_response.status}")
                        else:
                            print("❌ Không tìm thấy URL ảnh đã dịch")
                    else:
                        error_message = result.get("resMessage", "Unknown error")
                        print(f"❌ API Error: {error_message}")
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

async def debug_web_endpoint():
    """Debug web endpoint"""
    print("\n🌐 Debug Web Endpoint")
    print("=" * 30)
    
    # Test endpoint có hoạt động không
    try:
        async with aiohttp.ClientSession() as session:
            # Test GET endpoint
            async with session.get("http://localhost:8000/image_translation") as response:
                print(f"📥 GET /image_translation: {response.status}")
                if response.status == 200:
                    content = await response.text()
                    print(f"✅ Page loaded successfully ({len(content)} characters)")
                else:
                    print(f"❌ Failed to load page: {response.status}")
            
            # Test POST endpoint với file test
            if os.path.exists("debug_test_image.jpg"):
                print("\n📤 Testing POST /translate_image...")
                
                # Tạo form data
                data = aiohttp.FormData()
                data.add_field('image', 
                             open("debug_test_image.jpg", 'rb'),
                             filename="debug_test_image.jpg",
                             content_type='image/jpeg')
                data.add_field('source_language', 'en')
                data.add_field('target_language', 'vi')
                
                async with session.post("http://localhost:8000/translate_image", data=data) as response:
                    print(f"📥 POST /translate_image: {response.status}")
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Response: {json.dumps(result, indent=2)}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Error: {error_text}")
            else:
                print("❌ Test image file not found")
                
    except Exception as e:
        print(f"❌ Web endpoint test failed: {e}")

async def main():
    """Main debug function"""
    print("🚀 Starting Image Translation Debug")
    print("=" * 50)
    
    # Debug API
    #await debug_image_translation()
    
    # Debug web endpoint
    await debug_web_endpoint()
    
    print("\n🎉 Debug completed!")

if __name__ == "__main__":
    asyncio.run(main()) 