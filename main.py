from fastapi import FastAPI, Request, Form, UploadFile, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
import asyncpg
import json
from datetime import datetime
import openai
import base64
from glob import glob
import aiohttp
import hmac
import hashlib
import time
import asyncio
from utils import (
    log_message, download_image_from_url, encode_image_base64, clean_json_response, extract_estimate_from_response, analyze_image_openai_json,
    get_candidates_info, get_next_image_to_label, get_batch_images_for_label
)
import decimal

def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    if isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    return obj

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount translated_images as a separate static directory
app.mount("/translated_images", StaticFiles(directory="translated_images"), name="translated_images")

# Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Load environment variables from .env
load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = int(os.getenv("POSTGRES_PORT"))
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIDGE_ACCESS_KEY = os.getenv("AIDGE_ACCESS_KEY", "508912")
AIDGE_ACCESS_SECRET = os.getenv("AIDGE_ACCESS_SECRET", "LvtYlmGSEglYZX5KsaBXI3HHXBPc0jYU")
AIDGE_API_DOMAIN = os.getenv("AIDGE_API_DOMAIN", "api.aidc-ai.com")

if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, OPENAI_API_KEY]):
    raise RuntimeError("Missing one or more required environment variables: POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Global connection pool
_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            min_size=5,  # Tăng min_size cho production
            max_size=20,  # Tăng max_size cho 10-20 CCU
            command_timeout=60,
            server_settings={
                'application_name': 'abt_ai_image_desc'
            }
        )
    return _pool

@app.on_event("startup")
async def startup_event():
    # Khởi tạo connection pool khi app startup
    await get_pool()

@app.on_event("shutdown")
async def shutdown_event():
    global _pool
    if _pool:
        await _pool.close()

PROMPT = '''Bạn là một chuyên gia nội thất và thị giác máy tính.
Nhiệm vụ của bạn là quan sát hình ảnh nội thất đầu vào, và gán nhãn sản phẩm theo 7 nhóm thuộc tính chi tiết cùng với chỉ số tin cậy (confidence score) từ 0 đến 1.

🎯 Mục tiêu:
Trả về dữ liệu có cấu trúc JSON với các trường sau:
{
  "loai_san_pham": "...",
  "chat_lieu": "...",
  "vi_tri": "...",
  "mau_sac": "...",
  "phong_cach_thiet_ke": "...",
  "kieu_dang": "...",
  "chuc_nang_phu": "...",
  "dac_diem_nhan_dang": "...",
  "chi_so_tin_cay": 0.0
}

Trong đó:
- loai_san_pham: Ví dụ: ghế, giường, đèn, tủ, chậu cây, sofa, rèm cửa...
- chat_lieu: Ví dụ: gỗ, kim loại, vải, nỉ, da, kính, mây đan...
- vi_tri: 1 trong 3 vị trí sau: "Trên tường", "Trên trần nhà", "Trên sàn". Chú thích: trên sàn là bao gồm đặt trực tiếp trên sàn hoặc đặt trên các vật dụng trên sàn vd như bàn, kệ, tủ
- mau_sac: Màu chủ đạo quan sát được (ví dụ: trắng ngà, be, đen, gỗ sáng...)
- phong_cach_thiet_ke: Ví dụ: hiện đại, tối giản, Bắc Âu, retro, công nghiệp, cổ điển...
- kieu_dang: Mô tả cấu trúc tổng thể: khối hộp, trụ đứng, cong mềm, chân thấp, lưng cao...
- chuc_nang_phu: Ví dụ: gấp gọn, có ngăn kéo, trang trí, chiếu sáng, dùng ngoài trời...
- dac_diem_nhan_dang: Mô tả điểm đặc trưng giúp phân biệt với sản phẩm khác
- chi_so_tin_cay: Một số trong khoảng 0.00 – 1.00, thể hiện mức độ chắc chắn vào việc gán nhãn dựa trên ảnh

⚠️ Lưu ý khi gán nhãn:
Nếu ảnh không đủ thông tin cho một trường nào đó, hãy ghi rõ là "Không rõ" hoặc "Không xác định".
Đảm bảo tất cả mô tả khách quan, ngắn gọn, dễ dùng cho hệ thống tìm kiếm hoặc lọc ảnh.
Chỉ trả về đúng một đối tượng JSON, không giải thích, không thêm văn bản ngoài JSON.
📥 Đầu vào:
Một ảnh nội thất (bạn sẽ nhận được ảnh sản phẩm kèm theo).
'''

IMAGES_DIR = "images"
TRANSLATED_IMAGES_DIR = "translated_images"

def generate_aidge_signature(access_key_secret: str, timestamp: str) -> str:
    """Tạo chữ ký cho Aidge API"""
    h = hmac.new(access_key_secret.encode('utf-8'), 
                 (access_key_secret + timestamp).encode('utf-8'), 
                 hashlib.sha256)
    return h.hexdigest().upper()

async def call_aidge_image_translation(image_url: str, source_language: str, target_language: str) -> dict:
    """Gọi Aidge Image Translation API - sử dụng translation_mllm API"""
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
            "x-iop-trial": "true"  # Xóa tag này sau khi mua API
        }
        
        # Data - theo documentation của translation_mllm API
        data = {
            "paramJson": {
                "imageUrl": image_url,
                "sourceLanguage": source_language,
                "targetLanguage": target_language
            }
        }
        
        print(f"🔍 DEBUG: Calling Aidge API with URL: {image_url}")
        print(f"🔍 DEBUG: API URL: {url}")
        print(f"🔍 DEBUG: Data: {data}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                result = await response.json()
                print(f"🔍 DEBUG: Response status: {response.status}")
                print(f"🔍 DEBUG: Response: {result}")
                return result
                
    except Exception as e:
        print(f"🔍 DEBUG: Exception in call_aidge_image_translation: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}



@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, edit_id: int = None):
    pool = await get_pool()
    if edit_id:
        async with pool.acquire() as conn:  
            row = await conn.fetchrow('SELECT * FROM abt_image_to_products_1688 WHERE id = $1', edit_id)
            if row:
                row = dict(row)
            else:
                row = None
    else:
        row = await get_next_image_to_label(pool)
    if not row:
        return templates.TemplateResponse("index.html", {"request": request, "done": True})
    image_url = row.get("image_url")
    abt_label = row.get("abt_label")
    abt_label_fields = None
    if abt_label:
        try:
            abt_label_fields = json.loads(abt_label)
        except Exception:
            abt_label_fields = None
    candidates_json = row.get("products_1688_filtered")
    candidates = []
    offer_ids = []
    if candidates_json:
        try:
            data = json.loads(candidates_json)
            candidates = data.get("candidates", [])
            offer_ids = [str(c.get("offer_id")) for c in candidates if c.get("offer_id")]
        except Exception:
            pass
    # Lấy thêm trường price và subject_trans
    async def get_candidates_info_with_price(pool, offer_ids):
        if not offer_ids:
            return []
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT offer_id, image_url, subject_trans, price FROM abt_products_1688 WHERE offer_id = ANY($1)', offer_ids
            )
            return [dict(row) for row in rows]
    candidates_info = await get_candidates_info_with_price(pool, offer_ids)
    info_map = {c["offer_id"]: c for c in candidates_info}
    candidates_full = [info_map.get(oid) for oid in offer_ids if oid in info_map]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "image_url": image_url,
            "candidates": candidates_full,
            "row_id": row.get("id"),
            "done": False,
            "abt_label_fields": abt_label_fields
        }
    )

@app.post("/submit")
async def submit_best_match(request: Request, row_id: int = Form(...), selected_offer_id: str = Form(...), user: str = Form(...), elapsed_time: int = Form(...), accuracy_score: int = Form(...)):
    pool = await get_pool()
    offer_id = selected_offer_id if selected_offer_id else None
    best_match = {
        "offer_id": offer_id,
        "timestamp": datetime.now().isoformat(),
        "review_status": 0,
        "user": user,
        "elapsed_time": elapsed_time,
        "accuracy_score": accuracy_score
    }
    async with pool.acquire() as conn:
        await conn.execute(
            'UPDATE abt_image_to_products_1688 SET best_match = $1 WHERE id = $2',
            json.dumps(best_match, ensure_ascii=False),
            row_id
        )
    return RedirectResponse(url="/", status_code=303)

@app.get("/analyze_image", response_class=HTMLResponse)
async def analyze_image_form(request: Request):
    return templates.TemplateResponse("analyze_image.html", {"request": request, "result": None, "batch_size": 5})

@app.post("/analyze_image", response_class=HTMLResponse)
async def analyze_image_batch(request: Request, batch_size: int = Form(...)):
    pool = await get_pool()
    rows = await get_batch_images_for_label(pool, batch_size)
    logs = []
    for row in rows:
        image_url = row.get("image_url")
        row_id = row.get("id")
        if not image_url or not row_id:
            log_message(f"Bỏ qua dòng thiếu thông tin id={row_id}", logs)
            continue
        from urllib.parse import urlparse, unquote
        parsed_url = urlparse(image_url)
        path = parsed_url.path
        img_name = os.path.basename(path)
        local_path = os.path.join(IMAGES_DIR, f"dbimg_{row_id}_{img_name}")
        if not os.path.exists(local_path):
            ok = await download_image_from_url(image_url, local_path)
            if not ok:
                log_message(f"Lỗi tải ảnh {image_url} cho id={row_id}", logs)
                continue
        try:
            abt_label, abt_label_cost = await analyze_image_openai_json(local_path, PROMPT, openai)
            async with pool.acquire() as conn:
                await conn.execute(
                    'UPDATE abt_image_to_products_1688 SET abt_label = $1, abt_label_cost = $2 WHERE id = $3',
                    abt_label,
                    abt_label_cost,
                    row_id
                )
            log_message(f"Đã xử lý id={row_id}", logs)
        except Exception as e:
            log_message(f"Lỗi AI cho id={row_id}: {e}", logs)
    return templates.TemplateResponse("analyze_image.html", {"request": request, "result": '\n'.join(logs), "batch_size": batch_size})

@app.get("/api/get_batch_images")
async def api_get_batch_images(batch_size: int = 5):
    pool = await get_pool()
    rows = await get_batch_images_for_label(pool, batch_size)
    # Trả về id, image_url cho client
    return JSONResponse([{"id": row["id"], "image_url": row["image_url"]} for row in rows])

@app.post("/api/analyze_image_one")
async def api_analyze_image_one(data: dict = Body(...)):
    row_id = data.get("id")
    image_url = data.get("image_url")
    if not row_id or not image_url:
        return JSONResponse({"success": False, "msg": "Thiếu id hoặc image_url"})
    pool = await get_pool()
    from urllib.parse import urlparse
    parsed_url = urlparse(image_url)
    path = parsed_url.path
    img_name = os.path.basename(path)
    local_path = os.path.join(IMAGES_DIR, f"dbimg_{row_id}_{img_name}")
    if not os.path.exists(local_path):
        ok = await download_image_from_url(image_url, local_path)
        if not ok:
            return JSONResponse({"success": False, "msg": f"Lỗi tải ảnh cho id={row_id}"})
    try:
        abt_label, abt_label_cost = await analyze_image_openai_json(local_path, PROMPT, openai)
        async with pool.acquire() as conn:
            await conn.execute(
                'UPDATE abt_image_to_products_1688 SET abt_label = $1, abt_label_cost = $2, updated_at = NOW() WHERE id = $3',
                abt_label,
                abt_label_cost,
                row_id
            )
        abt_label_after = abt_label
        return JSONResponse({
            "success": True,
            "msg": f"Đã xử lý id={row_id}",
            "abt_label_cost": abt_label_cost,
            "abt_label_after": abt_label_after
        })
    except Exception as e:
        return JSONResponse({"success": False, "msg": f"Lỗi AI cho id={row_id}: {e}", "abt_label_cost": None, "abt_label_after": None})

@app.get("/api/analyze_stats")
async def api_analyze_stats():
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Lấy tổng số item
        total = await conn.fetchval("SELECT COUNT(*) FROM abt_image_to_products_1688")
        # Lấy tổng số item đã phân tích (có abt_label)
        analyzed = await conn.fetchval("SELECT COUNT(*) FROM abt_image_to_products_1688 WHERE abt_label IS NOT NULL")
        # Lấy thống kê theo ngày (dựa vào updated_at hoặc timestamp trong abt_label_cost nếu có)
        rows = await conn.fetch('''
            SELECT id, abt_label, abt_label_cost, updated_at
            FROM abt_image_to_products_1688
            WHERE abt_label IS NOT NULL
        ''')
        from collections import defaultdict
        import datetime
        import json as pyjson
        day_stats = defaultdict(lambda: {"count": 0, "confidence": [], "date": None})
        for row in rows:
            # Lấy ngày từ updated_at hoặc timestamp trong abt_label_cost
            date_str = None
            if row["abt_label_cost"]:
                try:
                    cost = pyjson.loads(row["abt_label_cost"])
                    ts = cost.get("timestamp")
                    if ts:
                        date_str = ts[:10]
                except Exception:
                    pass
            if not date_str and row.get("updated_at"):
                date_str = str(row["updated_at"])[:10]
            if not date_str:
                date_str = "unknown"
            # Lấy confidence score
            conf = None
            if row["abt_label"]:
                try:
                    label = pyjson.loads(row["abt_label"])
                    conf = label.get("chi_so_tin_cay")
                except Exception:
                    pass
            day_stats[date_str]["count"] += 1
            if conf is not None:
                try:
                    day_stats[date_str]["confidence"].append(float(conf))
                except Exception:
                    pass
            day_stats[date_str]["date"] = date_str
        # Chuyển sang list, sort theo ngày
        stats_list = sorted(day_stats.values(), key=lambda x: x["date"])
        for s in stats_list:
            if s["confidence"]:
                s["avg_confidence"] = sum(s["confidence"]) / len(s["confidence"])
            else:
                s["avg_confidence"] = None
        return JSONResponse({
            "total": total,
            "analyzed": analyzed,
            "pending": total - analyzed,
            "stats": stats_list
        })

@app.get("/api/filter_history")
async def api_filter_history(user: str = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        import json as pyjson
        if user:
            query = '''
                SELECT id, image_url, best_match, products_1688_filtered
                FROM abt_image_to_products_1688
                WHERE best_match IS NOT NULL AND best_match->>'user' = $1::text
                ORDER BY id DESC
                LIMIT 500
            '''
            rows = await conn.fetch(query, user)
        else:
            query = '''
                SELECT id, image_url, best_match, products_1688_filtered
                FROM abt_image_to_products_1688
                WHERE best_match IS NOT NULL
                ORDER BY id DESC
                LIMIT 500
            '''
            rows = await conn.fetch(query)
        result = []
        for row in rows:
            best_match = None
            try:
                best_match = pyjson.loads(row["best_match"])
            except Exception:
                continue
            offer_id = best_match.get("offer_id")
            user_val = best_match.get("user")
            elapsed_time = best_match.get("elapsed_time")
            timestamp = best_match.get("timestamp")
            subject_trans = offer_id
            candidate_img = None
            if row["products_1688_filtered"]:
                try:
                    candidates = pyjson.loads(row["products_1688_filtered"]).get("candidates", [])
                    for c in candidates:
                        if c.get("offer_id") == offer_id:
                            subject_trans = c.get("subject_trans") or offer_id
                            break
                except Exception:
                    pass
            candidate_img = None
            if offer_id:
                cand_row = await conn.fetchrow('SELECT image_url FROM abt_products_1688 WHERE offer_id = $1', str(offer_id))
                if cand_row:
                    candidate_img = cand_row["image_url"]
            result.append({
                "id": row["id"],
                "image_url": row["image_url"],
                "candidate_img": candidate_img,
                "subject_trans": subject_trans,
                "user": user_val,
                "elapsed_time": elapsed_time,
                "timestamp": timestamp,
                "accuracy_score": best_match.get("accuracy_score"),
                "offer_id": offer_id
            })
        return JSONResponse(result) 

@app.get("/image_translation", response_class=HTMLResponse)
async def image_translation_page(request: Request):
    """Trang image translation"""
    return templates.TemplateResponse("image_translation.html", {"request": request})

@app.post("/translate_image")
async def translate_image(
    image_url: str = Form(...),
    source_language: str = Form(...),
    target_language: str = Form(...)
):
    """API endpoint để dịch ảnh - sử dụng translation_mllm API với URL input"""
    try:
        # Kiểm tra URL
        if not image_url or not image_url.strip():
            return JSONResponse({"success": False, "message": "Không có URL ảnh được cung cấp"})
        
        # Tạo tên file unique cho việc lưu trữ local
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = ".jpg"  # Default extension
        unique_filename = f"original_{timestamp}{file_extension}"
        
        # Tạo thư mục nếu chưa có
        os.makedirs(TRANSLATED_IMAGES_DIR, exist_ok=True)
        
        # Download và lưu ảnh gốc từ URL
        original_path = os.path.join(TRANSLATED_IMAGES_DIR, unique_filename)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(original_path, "wb") as f:
                            f.write(content)
                    else:
                        return JSONResponse({"success": False, "message": f"Không thể download ảnh từ URL: {response.status}"})
        except Exception as e:
            return JSONResponse({"success": False, "message": f"Lỗi khi download ảnh: {str(e)}"})
        
        # Tạo URL local cho ảnh gốc
        original_url = f"/translated_images/{unique_filename}"
        
        # Gọi Aidge API - translation_mllm là synchronous
        print(f"🔍 DEBUG: Calling Aidge API with image_url: {image_url}")
        result = await call_aidge_image_translation(image_url, source_language, target_language)
        
        print(f"🔍 DEBUG: Aidge API result: {result}")
        
        if "error" in result:
            print(f"🔍 DEBUG: API error: {result['error']}")
            return JSONResponse({"success": False, "message": f"Lỗi API: {result['error']}"})
        
        # Kiểm tra response code
        res_code = result.get("resCode")
        print(f"🔍 DEBUG: Response code: {res_code}")
        
        if res_code != 200:
            error_message = result.get("resMessage", "Unknown error")
            print(f"🔍 DEBUG: API Error: {error_message}")
            return JSONResponse({"success": False, "message": f"API Error: {error_message}"})
        
        # Xử lý response từ translation_mllm API
        data = result.get("data", {})
        
        # Lấy URL ảnh đã dịch từ response structure
        # Theo sample response: data.result.data.structData.message[0].result_list[0].fileUrl
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
        
        if not translated_image_url:
            return JSONResponse({"success": False, "message": "Không tìm thấy URL ảnh đã dịch trong response"})
        
        # Download ảnh đã dịch
        translated_filename = f"translated_{timestamp}{file_extension}"
        translated_path = os.path.join(TRANSLATED_IMAGES_DIR, translated_filename)
        
        # Download ảnh từ URL
        async with aiohttp.ClientSession() as session:
            async with session.get(translated_image_url) as response:
                if response.status == 200:
                    translated_content = await response.read()
                    with open(translated_path, "wb") as f:
                        f.write(translated_content)
                    
                    translated_url = f"/translated_images/{translated_filename}"
                    
                    # Trích xuất thông tin chi tiết từ response
                    detailed_info = extract_detailed_translation_info(data)
                    
                    # Lưu log kết quả translate
                    log_data = {
                        "timestamp": timestamp,
                        "original_image_url": image_url,
                        "original_local_path": original_path,
                        "original_local_url": original_url,
                        "translated_image_url": translated_image_url,
                        "translated_local_path": translated_path,
                        "translated_local_url": translated_url,
                        "source_language": source_language,
                        "target_language": target_language,
                        "api_response": result,
                        "detailed_info": detailed_info
                    }
                    
                    # Lưu log vào file JSON
                    log_filename = f"translation_log_{timestamp}.json"
                    log_path = os.path.join(TRANSLATED_IMAGES_DIR, log_filename)
                    with open(log_path, "w", encoding="utf-8") as f:
                        json.dump(log_data, f, ensure_ascii=False, indent=2)
                    
                    return JSONResponse({
                        "success": True,
                        "original_image_url": original_url,
                        "translated_image_url": translated_url,
                        "message": "Dịch ảnh thành công",
                        "detailed_info": detailed_info,
                        "log_file": log_filename
                    })
                else:
                    return JSONResponse({"success": False, "message": "Không thể download ảnh đã dịch"})
        
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Lỗi xử lý: {str(e)}"})

def extract_detailed_translation_info(data):
    """Trích xuất thông tin chi tiết từ response của Aidge API"""
    detailed_info = {
        "text_areas": [],
        "fonts": [],
        "colors": [],
        "text_positions": [],
        "translation_summary": {}
    }
    
    try:
        # Lấy thông tin từ structData.message
        struct_data = data.get("result", {}).get("data", {}).get("structData", {})
        messages = struct_data.get("message", [])
        
        if messages:
            message = messages[0]
            edit_info = message.get("edit_info", {})
            
            # Lấy thông tin text areas từ edit_info
            text_areas = edit_info.get("textAreas", [])
            for area in text_areas:
                area_info = {
                    "content": area.get("content", ""),
                    "fontsize": area.get("fontsize", ""),
                    "lineCount": area.get("lineCount", 0),
                    "horizontalLayout": area.get("horizontalLayout", ""),
                    "verticalLayout": area.get("verticalLayout", ""),
                    "color": area.get("color", ""),
                    "texts": []
                }
                
                # Lấy thông tin chi tiết của từng text
                texts = area.get("texts", [])
                for text in texts:
                    text_info = {
                        "value": text.get("value", ""),
                        "language": text.get("language", ""),
                        "fontsize": text.get("fontsize", ""),
                        "color": text.get("color", ""),
                        "valid": text.get("valid", False),
                        "lineCount": text.get("lineCount", 0),
                        "trans_model_name": text.get("trans_model_name", ""),
                        "imageRect": text.get("imageRect", {}),
                        "textRect": text.get("textRect", {})
                    }
                    area_info["texts"].append(text_info)
                
                detailed_info["text_areas"].append(area_info)
            
            # Lấy thông tin fonts từ edit_info
            fonts = edit_info.get("font", [])
            detailed_info["fonts"] = fonts
            
            # Lấy thông tin colors từ text areas
            colors = set()
            for area in text_areas:
                if area.get("color"):
                    colors.add(area.get("color"))
                for text in area.get("texts", []):
                    if text.get("color"):
                        colors.add(text.get("color"))
            detailed_info["colors"] = list(colors)
            
            # Lấy thông tin vị trí text
            for area in text_areas:
                for text in area.get("texts", []):
                    if text.get("imageRect"):
                        position_info = {
                            "text": text.get("value", ""),
                            "position": text.get("imageRect", {}),
                            "language": text.get("language", ""),
                            "fontsize": text.get("fontsize", "")
                        }
                        detailed_info["text_positions"].append(position_info)
            
            # Tạo summary
            total_texts = sum(len(area.get("texts", [])) for area in text_areas)
            total_areas = len(text_areas)
            languages = set()
            for area in text_areas:
                for text in area.get("texts", []):
                    if text.get("language"):
                        languages.add(text.get("language"))
            
            detailed_info["translation_summary"] = {
                "total_text_areas": total_areas,
                "total_texts": total_texts,
                "languages_detected": list(languages),
                "fonts_used": len(fonts),
                "colors_used": len(colors)
            }
    
    except Exception as e:
        print(f"Lỗi khi trích xuất thông tin chi tiết: {e}")
        detailed_info["error"] = str(e)
    
    return detailed_info

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin_filtered_products.html", {"request": request})

@app.get("/api/admin_stats")
async def api_admin_stats():
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Tổng số sản phẩm đã filter
        total = await conn.fetchval("SELECT COUNT(*) FROM abt_image_to_products_1688 WHERE best_match IS NOT NULL")
        
        # Số sản phẩm đã verify (pass)
        pass_count = await conn.fetchval("""
            SELECT COUNT(*) FROM abt_image_to_products_1688 
            WHERE best_match IS NOT NULL AND verify_result IS NOT NULL 
            AND verify_result->>'result' = 'pass'::text
        """)
        
        # Số sản phẩm đã verify (fail)
        fail_count = await conn.fetchval("""
            SELECT COUNT(*) FROM abt_image_to_products_1688 
            WHERE best_match IS NOT NULL AND verify_result IS NOT NULL 
            AND verify_result->>'result' = 'fail'::text
        """)
        
        # Số sản phẩm chưa verify
        pending_count = await conn.fetchval("""
            SELECT COUNT(*) FROM abt_image_to_products_1688 
            WHERE best_match IS NOT NULL AND verify_result IS NULL
        """)
        
        return JSONResponse({
            "total": total,
            "pass": pass_count,
            "fail": fail_count,
            "pending": pending_count
        })

@app.get("/api/admin_users")
async def api_admin_users():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT DISTINCT best_match->>'user' as user 
            FROM abt_image_to_products_1688 
            WHERE best_match IS NOT NULL AND best_match->>'user' IS NOT NULL
            ORDER BY user
        """)
        return JSONResponse([row["user"] for row in rows])

@app.get("/api/admin_filtered_products")
async def api_admin_filtered_products(
    status: str = None,
    user: str = None,
    date_from: str = None,
    date_to: str = None
):
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Xây dựng query với điều kiện lọc
        where_conditions = ["best_match IS NOT NULL"]
        params = []
        param_count = 0
        
        if status == "pass":
            where_conditions.append("verify_result IS NOT NULL AND verify_result->>'result' = 'pass'::text")
        elif status == "fail":
            where_conditions.append("verify_result IS NOT NULL AND verify_result->>'result' = 'fail'::text")
        elif status == "pending":
            where_conditions.append("verify_result IS NULL")
        
        if user:
            param_count += 1
            where_conditions.append(f"best_match->>'user' = ${param_count}::text")
            params.append(user)
        
        if date_from:
            param_count += 1
            where_conditions.append(f"best_match->>'timestamp' >= ${param_count}::text")
            params.append(date_from + "T00:00:00")
        
        if date_to:
            param_count += 1
            where_conditions.append(f"best_match->>'timestamp' <= ${param_count}::text")
            params.append(date_to + "T23:59:59")
        
        where_clause = " AND ".join(where_conditions)
        
        # Lấy tất cả dữ liệu
        data_query = f"""
            SELECT id, image_url, best_match, verify_result, products_1688_filtered
            FROM abt_image_to_products_1688 
            WHERE {where_clause}
            ORDER BY id DESC
        """
        
        rows = await conn.fetch(data_query, *params)
        
        # Xử lý dữ liệu
        products = []
        for row in rows:
            try:
                best_match = json.loads(row["best_match"]) if row["best_match"] else {}
                verify_result = json.loads(row["verify_result"]) if row["verify_result"] else None
                
                # Lấy thông tin candidate
                candidate_img = None
                subject_trans = None
                if row["products_1688_filtered"]:
                    try:
                        candidates_data = json.loads(row["products_1688_filtered"])
                        candidates = candidates_data.get("candidates", [])
                        offer_id = best_match.get("offer_id")
                        for candidate in candidates:
                            if candidate.get("offer_id") == offer_id:
                                subject_trans = candidate.get("subject_trans")
                                break
                    except Exception:
                        pass
                
                # Lấy ảnh candidate
                if best_match.get("offer_id"):
                    cand_row = await conn.fetchrow(
                        'SELECT image_url FROM abt_products_1688 WHERE offer_id = $1', 
                        str(best_match["offer_id"])
                    )
                    if cand_row:
                        candidate_img = cand_row["image_url"]
                
                products.append({
                    "id": row["id"],
                    "image_url": row["image_url"],
                    "candidate_img": candidate_img,
                    "subject_trans": subject_trans,
                    "user": best_match.get("user"),
                    "elapsed_time": best_match.get("elapsed_time"),
                    "timestamp": best_match.get("timestamp"),
                    "accuracy_score": best_match.get("accuracy_score"),
                    "verify_result": verify_result
                })
            except Exception as e:
                print(f"Lỗi xử lý row {row['id']}: {e}")
                continue
        
        return JSONResponse({
            "products": products,
            "total": len(products)
        })

@app.get("/api/admin_product_detail")
async def api_admin_product_detail(id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
            SELECT id, image_url, best_match, verify_result, products_1688_filtered, abt_label
            FROM abt_image_to_products_1688 WHERE id = $1
        ''', id)
        
        if not row:
            return JSONResponse({"error": "Not found"}, status_code=404)
        
        try:
            try:
                best_match = json.loads(row["best_match"]) if row["best_match"] else {}
            except Exception:
                best_match = {}
            
            try:
                verify_result = json.loads(row["verify_result"]) if row["verify_result"] else None
            except Exception:
                verify_result = None
                
            try:
                abt_label = json.loads(row["abt_label"]) if row["abt_label"] else None
            except Exception:
                abt_label = None
            
            # Lấy thông tin candidate từ products_1688_filtered
            if row["products_1688_filtered"]:
                try:
                    candidates_data = json.loads(row["products_1688_filtered"])
                    candidates = candidates_data.get("candidates", [])
                    offer_id = best_match.get("offer_id")
                    for candidate in candidates:
                        if candidate.get("offer_id") == offer_id:
                            subject_trans = candidate.get("subject_trans")
                            break
                except Exception as e:
                    print(f"Lỗi khi parse products_1688_filtered: {e}")
            
            

            # Lấy ảnh và thông tin candidate
            candidate_img = None
            subject_trans = None
            candidate_price = None
            if best_match.get("offer_id"):
                try:
                    cand_row = await conn.fetchrow(
                        'SELECT image_url, subject_trans, price FROM abt_products_1688 WHERE offer_id = $1', 
                        str(best_match["offer_id"])
                    )
                    if cand_row:
                        candidate_img = cand_row["image_url"]
                        subject_trans = cand_row["subject_trans"]
                        candidate_price = convert_decimal(cand_row["price"]) if cand_row["price"] else None
                except Exception as e:
                    print(f"Lỗi khi lấy candidate info: {e}")
                    
            

            # Lấy 10 ảnh từ products_1688_filtered
            other_images = []
            if row["products_1688_filtered"]:
                try:
                    candidates_data = json.loads(row["products_1688_filtered"])
                    candidates = candidates_data.get("candidates", [])
                    # Lấy 10 candidate đầu tiên
                    for candidate in candidates[:10]:
                        if candidate.get("offer_id"):
                            # Lấy ảnh từ bảng abt_products_1688
                            cand_row = await conn.fetchrow(
                                'SELECT image_url, subject_trans FROM abt_products_1688 WHERE offer_id = $1',
                                str(candidate["offer_id"])
                            )
                            if cand_row:
                                other_images.append({
                                    "id": candidate["offer_id"],
                                    "image_url": cand_row["image_url"],
                                    "subject_trans": cand_row["subject_trans"] or candidate.get("subject_trans", "")
                                })
                except Exception as e:
                    print(f"Lỗi khi lấy other_images từ products_1688_filtered: {e}")
            
            json_return = {
                "id": row["id"],
                "image_url": row["image_url"],
                "candidate_img": candidate_img,
                "subject_trans": subject_trans,
                "candidate_price": candidate_price,
                "user": best_match.get("user"),
                "elapsed_time": best_match.get("elapsed_time"),
                "timestamp": best_match.get("timestamp"),
                "accuracy_score": best_match.get("accuracy_score"),
                "verify_result": verify_result,
                "abt_label": abt_label,
                "other_images": [{"id": img["id"], "image_url": img["image_url"]} for img in other_images]
            }
            return JSONResponse(json_return)
        except Exception as e:
            return JSONResponse({"error": f"Lỗi xử lý dữ liệu: {e}"}, status_code=500)

@app.post("/api/admin_verify_product")
async def api_admin_verify_product(data: dict = Body(...)):
    product_id = data.get("id")
    result = data.get("result")
    
    if not product_id or result not in ["pass", "fail"]:
        return JSONResponse({"success": False, "msg": "Thiếu thông tin hoặc kết quả không hợp lệ"})
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Kiểm tra sản phẩm tồn tại
        exists = await conn.fetchval(
            'SELECT 1 FROM abt_image_to_products_1688 WHERE id = $1 AND best_match IS NOT NULL',
            product_id
        )
        
        if not exists:
            return JSONResponse({"success": False, "msg": "Sản phẩm không tồn tại hoặc chưa được filter"})
        
        # Cập nhật verify_result
        verify_data = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        await conn.execute(
            'UPDATE abt_image_to_products_1688 SET verify_result = $1 WHERE id = $2',
            json.dumps(verify_data, ensure_ascii=False),
            product_id
        )
        
        return JSONResponse({"success": True, "msg": "Đã cập nhật kết quả verify"})

@app.get("/filter_history", response_class=HTMLResponse)
async def filter_history_page(request: Request):
    return templates.TemplateResponse("filter_history.html", {"request": request})

@app.get("/api/filter_history_stats")
async def api_filter_history_stats():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch('''
            SELECT best_match FROM abt_image_to_products_1688 WHERE best_match IS NOT NULL
        ''')
        import json as pyjson
        from collections import defaultdict
        # Thống kê theo ngày
        day_stats = defaultdict(lambda: {"count": 0, "sum_time": 0, "users": defaultdict(lambda: {"count": 0, "sum_time": 0})})
        # Thống kê theo user
        user_stats = defaultdict(lambda: {"count": 0, "sum_time": 0})
        for row in rows:
            try:
                bm = pyjson.loads(row["best_match"])
                ts = bm.get("timestamp", "")[:10]
                user = bm.get("user", "?")
                elapsed = bm.get("elapsed_time")
                if elapsed is not None:
                    elapsed = int(elapsed)
                else:
                    elapsed = 0
                # Theo ngày
                day_stats[ts]["count"] += 1
                day_stats[ts]["sum_time"] += elapsed
                day_stats[ts]["users"][user]["count"] += 1
                day_stats[ts]["users"][user]["sum_time"] += elapsed
                # Theo user
                user_stats[user]["count"] += 1
                user_stats[user]["sum_time"] += elapsed
            except Exception:
                pass
        # Chuẩn bị dữ liệu trả về
        stats_by_day = []
        for day, v in sorted(day_stats.items()):
            avg_time = v["sum_time"] / v["count"] if v["count"] else 0
            stats_by_day.append({
                "date": day,
                "count": v["count"],
                "sum_time": v["sum_time"],
                "avg_time": avg_time
            })
        stats_by_user = []
        for user, v in sorted(user_stats.items()):
            avg_time = v["sum_time"] / v["count"] if v["count"] else 0
            stats_by_user.append({
                "user": user,
                "count": v["count"],
                "sum_time": v["sum_time"],
                "avg_time": avg_time
            })
        return JSONResponse({
            "stats_by_day": stats_by_day,
            "stats_by_user": stats_by_user
        })

@app.get("/api/filter_item")
async def api_filter_item(id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM abt_image_to_products_1688 WHERE id = $1', id)
        if not row:
            return JSONResponse({"error": "Not found"}, status_code=404)
        row = dict(row)
        import json as pyjson
        abt_label = row.get("abt_label")
        abt_label_fields = None
        if abt_label:
            try:
                abt_label_fields = pyjson.loads(abt_label)
            except Exception:
                abt_label_fields = None
        candidates_json = row.get("products_1688_filtered")
        candidates = []
        offer_ids = []
        if candidates_json:
            try:
                data = pyjson.loads(candidates_json)
                candidates = data.get("candidates", [])
                offer_ids = [str(c.get("offer_id")) for c in candidates if c.get("offer_id")]
            except Exception:
                pass
        # Lấy thêm trường price và subject_trans
        async def get_candidates_info_with_price(pool, offer_ids):
            if not offer_ids:
                return []
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    'SELECT offer_id, image_url, subject_trans, price FROM abt_products_1688 WHERE offer_id = ANY($1)', offer_ids
                )
                return [dict(row) for row in rows]
        candidates_info = await get_candidates_info_with_price(pool, offer_ids)
        info_map = {c["offer_id"]: c for c in candidates_info}
        candidates_full = [info_map.get(oid) for oid in offer_ids if oid in info_map]
        # Parse best_match để lấy accuracy_score
        best_match = None
        if row.get("best_match"):
            try:
                best_match = json.loads(row["best_match"])
            except Exception:
                pass
        
        return JSONResponse({
            "id": row.get("id"),
            "image_url": row.get("image_url"),
            "candidates": convert_decimal(candidates_full),
            "abt_label_fields": abt_label_fields,
            "accuracy_score": best_match.get("accuracy_score") if best_match else None
        }) 

@app.get("/api/analyze_history")
async def api_analyze_history(limit: int = 50):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch('''
            SELECT id, image_url, abt_label, abt_label_cost, updated_at
            FROM abt_image_to_products_1688
            WHERE abt_label IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT $1
        ''', limit)
        
        result = []
        for row in rows:
            item = {
                "id": row["id"],
                "image_url": row["image_url"],
                "updated_at": str(row["updated_at"]) if row["updated_at"] else None,
                "abt_label_cost": row["abt_label_cost"]
            }
            
            # Parse abt_label để lấy các thuộc tính
            if row["abt_label"]:
                try:
                    label_data = json.loads(row["abt_label"])
                    item.update({
                        "loai_san_pham": label_data.get("loai_san_pham"),
                        "chat_lieu": label_data.get("chat_lieu"),
                        "vi_tri": label_data.get("vi_tri"),
                        "mau_sac": label_data.get("mau_sac"),
                        "phong_cach_thiet_ke": label_data.get("phong_cach_thiet_ke"),
                        "kieu_dang": label_data.get("kieu_dang"),
                        "chuc_nang_phu": label_data.get("chuc_nang_phu"),
                        "dac_diem_nhan_dang": label_data.get("dac_diem_nhan_dang"),
                        "chi_so_tin_cay": label_data.get("chi_so_tin_cay")
                    })
                except Exception:
                    item.update({
                        "loai_san_pham": None,
                        "chat_lieu": None,
                        "vi_tri": None,
                        "mau_sac": None,
                        "phong_cach_thiet_ke": None,
                        "kieu_dang": None,
                        "chuc_nang_phu": None,
                        "dac_diem_nhan_dang": None,
                        "chi_so_tin_cay": None
                    })
            else:
                item.update({
                    "loai_san_pham": None,
                    "chat_lieu": None,
                    "vi_tri": None,
                    "mau_sac": None,
                    "phong_cach_thiet_ke": None,
                    "kieu_dang": None,
                    "chuc_nang_phu": None,
                    "dac_diem_nhan_dang": None,
                    "chi_so_tin_cay": None
                })
            
            result.append(item)
        
        return JSONResponse(result) 

@app.get("/translation_history", response_class=HTMLResponse)
async def translation_history_page(request: Request):
    """Trang lịch sử translate"""
    return templates.TemplateResponse("translation_history.html", {"request": request})

@app.get("/api/translation_history")
async def api_translation_history():
    """API để lấy lịch sử translate"""
    try:
        # Tìm tất cả file log trong thư mục translated_images
        log_files = []
        if os.path.exists(TRANSLATED_IMAGES_DIR):
            for filename in os.listdir(TRANSLATED_IMAGES_DIR):
                if filename.startswith("translation_log_") and filename.endswith(".json"):
                    log_path = os.path.join(TRANSLATED_IMAGES_DIR, filename)
                    try:
                        with open(log_path, "r", encoding="utf-8") as f:
                            log_data = json.load(f)
                            log_data["log_filename"] = filename
                            log_files.append(log_data)
                    except Exception as e:
                        print(f"Lỗi đọc file log {filename}: {e}")
        
        # Sắp xếp theo timestamp (mới nhất trước)
        log_files.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return JSONResponse(log_files)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500) 