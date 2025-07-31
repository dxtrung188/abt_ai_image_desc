# Tính năng Thang điểm Chính xác (Accuracy Score)

## Tổng quan

Tính năng này cho phép người dùng đánh giá mức độ chính xác của việc lọc sản phẩm theo thang điểm từ 1-6.

## Thang điểm

| Điểm | Mô tả |
|------|-------|
| 1 | Chính xác sản phẩm |
| 2 | Cùng sản phẩm nhưng khác chi tiết nhỏ |
| 3 | Gần giống |
| 4 | Cùng loại sản phẩm, nhưng khác màu sắc, chất liệu |
| 5 | Cùng loại sản phẩm, nhưng khác biệt |
| 6 | Không có sản phẩm trùng |

## Các thay đổi đã thực hiện

### 1. Frontend (templates/index.html)

- ✅ Thêm dropdown lựa chọn thang điểm
- ✅ Validation cho accuracy_score
- ✅ Hiển thị accuracy_score trong bảng lịch sử
- ✅ Tự động điền accuracy_score khi edit
- ✅ Cập nhật JavaScript validation

### 2. Backend (main.py)

- ✅ Cập nhật route `/submit` để nhận accuracy_score
- ✅ Cập nhật API `/api/filter_history` để trả về accuracy_score
- ✅ Cập nhật API `/api/admin_filtered_products` để bao gồm accuracy_score
- ✅ Cập nhật API `/api/admin_product_detail` để bao gồm accuracy_score
- ✅ Cập nhật API `/api/filter_item` để bao gồm accuracy_score

### 3. Database

- ✅ Lưu accuracy_score trong JSON field `best_match`
- ✅ Cấu trúc dữ liệu:
```json
{
  "offer_id": "string",
  "timestamp": "ISO datetime",
  "review_status": 0,
  "user": "string",
  "elapsed_time": number,
  "accuracy_score": number (1-6)
}
```

## Cách sử dụng

### 1. Trên giao diện lọc sản phẩm

1. Nhập username/điện thoại
2. **Chọn thang điểm chính xác** (bắt buộc)
3. Chọn sản phẩm candidate
4. Click Submit

### 2. Xem lịch sử

- Bảng lịch sử sẽ hiển thị cột "Thang điểm"
- Hiển thị mô tả đầy đủ của từng điểm

### 3. Admin panel

- Có thể xem accuracy_score trong chi tiết sản phẩm
- Có thể filter theo accuracy_score

## API Endpoints

### POST /submit
```json
{
  "row_id": 123,
  "selected_offer_id": "offer_123",
  "user": "username",
  "elapsed_time": 30,
  "accuracy_score": 2
}
```

### GET /api/filter_history
Response bao gồm:
```json
{
  "id": 123,
  "image_url": "...",
  "candidate_img": "...",
  "subject_trans": "...",
  "user": "username",
  "elapsed_time": 30,
  "timestamp": "2024-01-01T12:00:00",
  "accuracy_score": 2,
  "offer_id": "offer_123"
}
```

## Validation

### Frontend
- ✅ Bắt buộc chọn thang điểm trước khi submit
- ✅ Hiển thị thông báo lỗi nếu chưa chọn
- ✅ Disable submit button nếu chưa chọn

### Backend
- ✅ Kiểm tra accuracy_score là số từ 1-6
- ✅ Lưu vào database với validation

## Test

Chạy script test:
```bash
python3 test_accuracy_score.py
```

## Migration

Nếu có dữ liệu cũ không có accuracy_score:
- Các record cũ sẽ hiển thị accuracy_score = null
- Không ảnh hưởng đến chức năng hiện tại
- Có thể cập nhật dần dần

## Monitoring

### Database query để thống kê accuracy_score:
```sql
SELECT 
  best_match->>'accuracy_score' as score,
  COUNT(*) as count
FROM abt_image_to_products_1688 
WHERE best_match IS NOT NULL 
  AND best_match->>'accuracy_score' IS NOT NULL
GROUP BY best_match->>'accuracy_score'
ORDER BY score;
```

### Thống kê theo user:
```sql
SELECT 
  best_match->>'user' as user,
  best_match->>'accuracy_score' as score,
  COUNT(*) as count
FROM abt_image_to_products_1688 
WHERE best_match IS NOT NULL 
  AND best_match->>'accuracy_score' IS NOT NULL
GROUP BY best_match->>'user', best_match->>'accuracy_score'
ORDER BY user, score;
```

## Troubleshooting

### Lỗi thường gặp

1. **"Vui lòng chọn thang điểm chính xác!"**
   - Giải pháp: Chọn một giá trị từ dropdown

2. **accuracy_score không hiển thị trong lịch sử**
   - Kiểm tra dữ liệu trong database
   - Chạy script test để verify

3. **Dropdown không hoạt động**
   - Kiểm tra JavaScript console
   - Refresh trang và thử lại

### Debug

1. Kiểm tra database:
```sql
SELECT id, best_match FROM abt_image_to_products_1688 
WHERE best_match->>'accuracy_score' IS NOT NULL 
LIMIT 5;
```

2. Kiểm tra API response:
```bash
curl "http://localhost:8000/api/filter_history?user=test_user"
```

3. Kiểm tra form submission:
- Mở Developer Tools
- Xem Network tab khi submit
- Kiểm tra request payload

## Future Enhancements

1. **Filter theo accuracy_score** trong admin panel
2. **Thống kê biểu đồ** accuracy_score
3. **Export data** với accuracy_score
4. **Bulk update** accuracy_score
5. **Validation rules** nâng cao 