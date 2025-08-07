import requests
import json

def test_translation_debug():
    """Test the translation API with debug output"""
    
    # Test data
    data = {
        "image_url": "https://ae01.alicdn.com/kf/Sa78257f1d9a34dad8ee494178db12ec8l.jpg",
        "source_language": "en",
        "target_language": "vi"
    }
    
    try:
        # Send POST request to the translation endpoint
        response = requests.post(
            "http://localhost:8000/translate_image",
            data=data,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Translation successful!")
            print(f"Original URL: {result.get('original_url', 'N/A')}")
            print(f"Translated URL: {result.get('translated_url', 'N/A')}")
            print(f"Log file: {result.get('log_file', 'N/A')}")
            
            # Check if detailed info was extracted
            detailed_info = result.get('detailed_info', {})
            if detailed_info:
                print("\n=== Detailed Info ===")
                print(f"Text areas: {len(detailed_info.get('text_areas', []))}")
                print(f"Fonts: {len(detailed_info.get('fonts', []))}")
                print(f"Colors: {len(detailed_info.get('colors', []))}")
                print(f"Text positions: {len(detailed_info.get('text_positions', []))}")
                
                summary = detailed_info.get('translation_summary', {})
                if summary:
                    print(f"\nSummary: {summary}")
            else:
                print("No detailed info found in response")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing translation: {e}")

if __name__ == "__main__":
    test_translation_debug() 