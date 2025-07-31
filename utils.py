import aiohttp
import base64
import json
import time
import asyncpg

def log_message(msg, logs=None):
    print(msg)
    if logs is not None:
        logs.append(msg)

def encode_image_base64(image_path):
    with open(image_path, 'rb') as img_file:
        img_bytes = img_file.read()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        mime_type = 'image/jpeg'
        if image_path.lower().endswith('.png'):
            mime_type = 'image/png'
        elif image_path.lower().endswith('.webp'):
            mime_type = 'image/webp'
        image_url = f"data:{mime_type};base64,{img_base64}"
    return image_url

async def download_image_from_url(url, save_path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    with open(save_path, 'wb') as f:
                        f.write(await resp.read())
                    return True
    except Exception as e:
        return False
    return False

def clean_json_response(text):
    cleaned = text.strip()
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    if cleaned.startswith('```'):
        cleaned = cleaned[3:]
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def extract_estimate_from_response(ai_response, elapsed):
    usage = getattr(ai_response, 'usage', None)
    input_tokens = output_tokens = total_tokens = None
    usd_cost = None
    if usage:
        input_tokens = getattr(usage, 'prompt_tokens', None)
        output_tokens = getattr(usage, 'completion_tokens', None)
        total_tokens = getattr(usage, 'total_tokens', None)
        usd_cost = 0.0
        if input_tokens:
            usd_cost += input_tokens * 0.005 / 1000
        if output_tokens:
            usd_cost += output_tokens * 0.015 / 1000
    return {
        "total_tokens": total_tokens,
        "usd_cost": usd_cost,
        "elapsed_seconds": elapsed
    }

async def analyze_image_openai_json(image_path, PROMPT, openai):
    image_url = encode_image_base64(image_path)
    start_time = time.time()
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]}
        ],
        max_tokens=1024
    )
    elapsed = time.time() - start_time
    result_text = response.choices[0].message.content
    cleaned = clean_json_response(result_text)
    try:
        result_json = json.loads(cleaned)
        abt_label = json.dumps(result_json, ensure_ascii=False)
    except Exception as e:
        abt_label = json.dumps({"raw": result_text, "parse_error": str(e)}, ensure_ascii=False)
    estimate = extract_estimate_from_response(response, elapsed)
    abt_label_cost = json.dumps(estimate, ensure_ascii=False)
    return abt_label, abt_label_cost 

async def get_next_image_to_label(pool):
    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
            SELECT * FROM abt_image_to_products_1688
            WHERE best_match is NULL 
            AND abt_label IS NOT NULL 
            AND products_1688_filtered IS NOT NULL
            AND products_1688_filtered != ''
            ORDER BY id ASC
            LIMIT 1
        ''')
        return dict(row) if row else None

async def get_candidates_info(pool, offer_ids):
    if not offer_ids:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            'SELECT offer_id, image_url, subject_trans, price FROM abt_products_1688 WHERE offer_id = ANY($1)', offer_ids
        )
        return [dict(row) for row in rows]

async def get_batch_images_for_label(pool, batch_size):
    async with pool.acquire() as conn:
        rows = await conn.fetch('''
            SELECT * FROM abt_image_to_products_1688
            WHERE abt_label IS NULL
            ORDER BY id ASC
            LIMIT $1
        ''', batch_size)
        return [dict(row) for row in rows] 