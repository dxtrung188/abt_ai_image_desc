#!/usr/bin/env python3
"""
Test script for URL-based image translation
"""

import asyncio
import aiohttp
import json

async def test_url_translation():
    """Test the URL-based image translation endpoint"""
    
    # Test URL - using a sample image
    test_image_url = "https://ae01.alicdn.com/kf/Sa78257f1d9a34dad8ee494178db12ec8l.jpg"
    
    # Test data
    form_data = aiohttp.FormData()
    form_data.add_field('image_url', test_image_url)
    form_data.add_field('source_language', 'auto')
    form_data.add_field('target_language', 'vi')
    
    print(f"🧪 Testing URL-based image translation...")
    print(f"📸 Image URL: {test_image_url}")
    print(f"🌐 Source Language: auto")
    print(f"🎯 Target Language: vi")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:8000/translate_image',
                data=form_data
            ) as response:
                
                print(f"📊 Response Status: {response.status}")
                print(f"📋 Response Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    if result.get('success'):
                        print(f"🎉 Translation successful!")
                        print(f"📁 Original image saved at: {result.get('original_image_url')}")
                        print(f"🔄 Translated image saved at: {result.get('translated_image_url')}")
                    else:
                        print(f"❌ Translation failed: {result.get('message')}")
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    error_text = await response.text()
                    print(f"📄 Error Response: {error_text}")
                    
    except Exception as e:
        print(f"💥 Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting URL-based image translation test...")
    asyncio.run(test_url_translation())
    print("🏁 Test completed!") 