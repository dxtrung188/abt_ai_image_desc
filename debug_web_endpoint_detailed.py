#!/usr/bin/env python3
"""
Debug chi tiết cho web endpoint image translation
"""

import asyncio
import aiohttp
import os
import json
from datetime import datetime

async def debug_web_endpoint_detailed():
    """Debug chi tiết web endpoint"""
    print("🔍 Debug Web Endpoint Chi Tiết")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test GET endpoint
            print("\n1️⃣ Test GET /image_translation...")
            async with session.get("http://localhost:8000/image_translation") as response:
                print(f"📥 Status: {response.status}")
                if response.status == 200:
                    content = await response.text()
                    print(f"✅ Page loaded successfully ({len(content)} characters)")
                else:
                    print(f"❌ Failed to load page: {response.status}")
            
            # Test POST endpoint với file test
            print("\n2️⃣ Test POST /translate_image...")
            
            # Kiểm tra file test
            test_file = "debug_test_image.jpg"
            if not os.path.exists(test_file):
                print(f"❌ Test file not found: {test_file}")
                return
            
            print(f"✅ Test file exists: {test_file}")
            file_size = os.path.getsize(test_file)
            print(f"📏 File size: {file_size} bytes")
            
            # Tạo form data
            data = aiohttp.FormData()
            data.add_field('image', 
                         open(test_file, 'rb'),
                         filename="debug_test_image.jpg",
                         content_type='image/jpeg')
            data.add_field('source_language', 'en')
            data.add_field('target_language', 'vi')
            
            print("📤 Sending POST request...")
            print(f"📋 Form data fields: {len(data._fields)} fields")
            
            async with session.post("http://localhost:8000/translate_image", data=data) as response:
                print(f"📥 Response status: {response.status}")
                print(f"📥 Response headers: {dict(response.headers)}")
                
                if response.status == 200:
                    try:
                        result = await response.json()
                        print(f"✅ JSON Response: {json.dumps(result, indent=2)}")
                        
                        # Kiểm tra response structure
                        if "success" in result:
                            if result["success"]:
                                print("✅ Translation successful!")
                                if "original_image_url" in result:
                                    print(f"🖼️ Original: {result['original_image_url']}")
                                if "translated_image_url" in result:
                                    print(f"🖼️ Translated: {result['translated_image_url']}")
                            else:
                                print("❌ Translation failed!")
                                if "message" in result:
                                    print(f"💬 Error message: {result['message']}")
                        else:
                            print("⚠️ Response không có field 'success'")
                            
                    except Exception as e:
                        print(f"❌ Error parsing JSON: {e}")
                        text_response = await response.text()
                        print(f"📄 Raw response: {text_response}")
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

async def debug_server_logs():
    """Debug server logs"""
    print("\n3️⃣ Debug Server Logs...")
    print("📋 Kiểm tra server logs để tìm lỗi...")
    
    # Test với file ảnh thực tế
    print("\n4️⃣ Test với file ảnh thực tế...")
    
    # Tạo file ảnh test đơn giản
    test_image_path = "test_real_image.jpg"
    if not os.path.exists(test_image_path):
        # Tạo file ảnh test nhỏ hơn
        with open(test_image_path, "wb") as f:
            # Tạo một file ảnh test nhỏ hơn
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9')
        print(f"✅ Tạo file test thực tế: {test_image_path}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Tạo form data với file thực tế
            data = aiohttp.FormData()
            data.add_field('image', 
                         open(test_image_path, 'rb'),
                         filename="test_real_image.jpg",
                         content_type='image/jpeg')
            data.add_field('source_language', 'en')
            data.add_field('target_language', 'vi')
            
            print("📤 Sending POST request với file thực tế...")
            
            async with session.post("http://localhost:8000/translate_image", data=data) as response:
                print(f"📥 Response status: {response.status}")
                
                if response.status == 200:
                    try:
                        result = await response.json()
                        print(f"✅ JSON Response: {json.dumps(result, indent=2)}")
                    except Exception as e:
                        print(f"❌ Error parsing JSON: {e}")
                        text_response = await response.text()
                        print(f"📄 Raw response: {text_response}")
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

async def debug_aidge_api_direct():
    """Debug Aidge API trực tiếp từ web endpoint"""
    print("\n5️⃣ Debug Aidge API trực tiếp...")
    
    # Test với URL local
    test_url = "http://localhost:8000/static/translated_images/test_real_image.jpg"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Kiểm tra URL có accessible không
            async with session.get(test_url) as response:
                print(f"📥 Test URL status: {response.status}")
                if response.status == 200:
                    print("✅ URL accessible")
                else:
                    print("❌ URL not accessible")
                    
    except Exception as e:
        print(f"❌ Exception testing URL: {e}")

async def main():
    """Main debug function"""
    print("🚀 Starting Detailed Web Endpoint Debug")
    print("=" * 50)
    
    await debug_web_endpoint_detailed()
    await debug_server_logs()
    await debug_aidge_api_direct()
    
    print("\n🎉 Detailed debug completed!")

if __name__ == "__main__":
    asyncio.run(main()) 