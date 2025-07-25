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
from utils import (
    log_message, download_image_from_url, encode_image_base64, clean_json_response, extract_estimate_from_response, analyze_image_openai_json,
    get_pg_pool, get_next_image_to_label, get_candidates_info, get_batch_images_for_label
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
if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, OPENAI_API_KEY]):
    raise RuntimeError("Missing one or more required environment variables: POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

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

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, edit_id: int = None):
    pool = await get_pg_pool(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
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
            offer_ids = [c.get("offer_id") for c in candidates if c.get("offer_id")]
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
async def submit_best_match(request: Request, row_id: int = Form(...), selected_offer_id: str = Form(...), user: str = Form(...), elapsed_time: int = Form(...)):
    pool = await get_pg_pool(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
    offer_id = selected_offer_id if selected_offer_id else None
    best_match = {
        "offer_id": offer_id,
        "timestamp": datetime.now().isoformat(),
        "review_status": 0,
        "user": user,
        "elapsed_time": elapsed_time
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
    pool = await get_pg_pool(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
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
                log_message(f"Lỗi tải ảnh cho id={row_id}", logs)
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
    pool = await get_pg_pool(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
    rows = await get_batch_images_for_label(pool, batch_size)
    # Trả về id, image_url cho client
    return JSONResponse([{"id": row["id"], "image_url": row["image_url"]} for row in rows])

@app.post("/api/analyze_image_one")
async def api_analyze_image_one(data: dict = Body(...)):
    row_id = data.get("id")
    image_url = data.get("image_url")
    if not row_id or not image_url:
        return JSONResponse({"success": False, "msg": "Thiếu id hoặc image_url"})
    pool = await get_pg_pool(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
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
    pool = await get_pg_pool(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
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
    pool = await get_pg_pool(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
    async with pool.acquire() as conn:
        import json as pyjson
        if user:
            query = '''
                SELECT id, image_url, best_match, products_1688_filtered
                FROM abt_image_to_products_1688
                WHERE best_match IS NOT NULL AND best_match->>'user' = $1
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
                cand_row = await conn.fetchrow('SELECT image_url FROM abt_products_1688 WHERE offer_id = $1', offer_id)
                if cand_row:
                    candidate_img = cand_row["image_url"]
            result.append({
                "id": row["id"],
                "image_url": row["image_url"],
                "candidate_img": candidate_img,
                "subject_trans": subject_trans,
                "user": user_val,
                "elapsed_time": elapsed_time,
                "timestamp": timestamp
            })
        return JSONResponse(result)

@app.get("/filter_history", response_class=HTMLResponse)
async def filter_history_page(request: Request):
    return templates.TemplateResponse("filter_history.html", {"request": request})

@app.get("/api/filter_history_stats")
async def api_filter_history_stats():
    pool = await get_pg_pool(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
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
    pool = await get_pg_pool(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
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
                offer_ids = [c.get("offer_id") for c in candidates if c.get("offer_id")]
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
        return JSONResponse({
            "id": row.get("id"),
            "image_url": row.get("image_url"),
            "candidates": convert_decimal(candidates_full),
            "abt_label_fields": abt_label_fields
        }) 