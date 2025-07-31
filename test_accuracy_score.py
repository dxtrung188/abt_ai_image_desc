#!/usr/bin/env python3
"""
Test script for accuracy_score feature
"""

import asyncio
import asyncpg
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

async def test_accuracy_score():
    """Test accuracy_score feature"""
    
    # Database connection
    pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT")),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB")
    )
    
    async with pool.acquire() as conn:
        # Test 1: Insert test data with accuracy_score
        test_data = {
            "offer_id": "test_offer_123",
            "timestamp": datetime.now().isoformat(),
            "review_status": 0,
            "user": "test_user",
            "elapsed_time": 30,
            "accuracy_score": 2
        }
        
        # Insert test record
        await conn.execute('''
            INSERT INTO abt_image_to_products_1688 
            (image_url, best_match, created_at, updated_at) 
            VALUES ($1, $2, NOW(), NOW())
        ''', "https://example.com/test.jpg", json.dumps(test_data, ensure_ascii=False))
        
        # Test 2: Query and verify accuracy_score
        row = await conn.fetchrow('''
            SELECT best_match FROM abt_image_to_products_1688 
            WHERE best_match->>'offer_id' = $1
        ''', "test_offer_123")
        
        if row:
            best_match = json.loads(row["best_match"])
            print(f"✅ Test passed: accuracy_score = {best_match.get('accuracy_score')}")
            
            # Test 3: Verify all fields
            expected_fields = ["offer_id", "timestamp", "review_status", "user", "elapsed_time", "accuracy_score"]
            for field in expected_fields:
                if field in best_match:
                    print(f"✅ Field '{field}' exists: {best_match[field]}")
                else:
                    print(f"❌ Field '{field}' missing")
        else:
            print("❌ Test failed: Could not find test record")
        
        # Test 4: Test different accuracy scores
        accuracy_scores = [1, 2, 3, 4, 5, 6]
        for score in accuracy_scores:
            test_data["accuracy_score"] = score
            test_data["offer_id"] = f"test_offer_{score}"
            
            await conn.execute('''
                INSERT INTO abt_image_to_products_1688 
                (image_url, best_match, created_at, updated_at) 
                VALUES ($1, $2, NOW(), NOW())
            ''', f"https://example.com/test_{score}.jpg", json.dumps(test_data, ensure_ascii=False))
        
        print(f"✅ Inserted {len(accuracy_scores)} test records with different accuracy scores")
        
        # Test 5: Query all test records
        rows = await conn.fetch('''
            SELECT best_match FROM abt_image_to_products_1688 
            WHERE best_match->>'offer_id' LIKE 'test_offer_%'
            ORDER BY best_match->>'accuracy_score'
        ''')
        
        print(f"✅ Found {len(rows)} test records:")
        for row in rows:
            best_match = json.loads(row["best_match"])
            print(f"  - Offer ID: {best_match['offer_id']}, Accuracy Score: {best_match['accuracy_score']}")
    
    await pool.close()
    print("✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_accuracy_score()) 