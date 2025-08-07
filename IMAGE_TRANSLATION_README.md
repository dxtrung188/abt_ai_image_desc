# Image Translation Feature

## Tổng quan

Tính năng Image Translation cho phép người dùng upload ảnh và sử dụng Aidge API để dịch văn bản trong ảnh sang ngôn ngữ khác.

## Cách sử dụng

### 1. Truy cập trang Image Translation

- Vào trang chủ và click vào menu "🖼️ Image Translation"
- Hoặc truy cập trực tiếp: `http://localhost:8000/image_translation`

### 2. Upload ảnh

- Click vào nút "📁 Chọn ảnh" để chọn file ảnh từ máy tính
- Hỗ trợ các định dạng: JPG, PNG, GIF, BMP, etc.
- Kích thước file tối đa: 10MB

### 3. Chọn ngôn ngữ

**Ngôn ngữ nguồn:**
- `auto`: Tự động nhận diện (chỉ có trong Pro version)
- `zh`: Tiếng Trung (Giản thể)
- `en`: Tiếng Anh
- `fr`: Tiếng Pháp
- `it`: Tiếng Ý
- `ja`: Tiếng Nhật
- `ko`: Tiếng Hàn
- `pt`: Tiếng Bồ Đào Nha
- `es`: Tiếng Tây Ban Nha
- `tr`: Tiếng Thổ Nhĩ Kỳ

**Ngôn ngữ đích:**
- Tất cả các ngôn ngữ trên + các ngôn ngữ khác như: Ả Rập, Bengali, Séc, Hà Lan, Đức, Hy Lạp, Hebrew, Hungary, Indonesia, Kazakhstan, Malay, Ba Lan, Nga, Thái, Ukraine, Urdu, Việt Nam

### 4. Dịch ảnh

- Click nút "🚀 Dịch Ảnh" để bắt đầu quá trình dịch
- Hệ thống sẽ hiển thị loading spinner trong khi xử lý
- Thời gian xử lý thường từ 10-30 giây tùy thuộc vào độ phức tạp của ảnh

### 5. Xem kết quả

- Sau khi hoàn thành, hệ thống sẽ hiển thị:
  - Ảnh gốc (bên trái)
  - Ảnh đã dịch (bên phải)
- Ảnh đã dịch sẽ được lưu trong thư mục `translated_images/`

## Cấu hình API

### Biến môi trường

Thêm các biến sau vào file `.env`:

```env
AIDGE_ACCESS_KEY=508912
AIDGE_ACCESS_SECRET=LvtYlmGSEglYZX5KsaBXI3HHXBPc0jYU
AIDGE_API_DOMAIN=api.aidc-ai.com
```

### Cấu hình mặc định

Nếu không có file `.env`, hệ thống sẽ sử dụng các giá trị mặc định:
- Access Key: `508912`
- Access Secret: `LvtYlmGSEglYZX5KsaBXI3HHXBPc0jYU`
- API Domain: `api.aidc-ai.com`

## Cấu trúc thư mục

```
abt_ai_image_desc/
├── translated_images/          # Thư mục lưu ảnh đã dịch
│   ├── original_20250107_104500.jpg
│   ├── translated_20250107_104500.jpg
│   └── ...
├── templates/
│   └── image_translation.html  # Template cho trang Image Translation
└── main.py                     # Backend logic
```

## API Endpoints

### POST /translate_image

**Request:**
```json
{
  "image": "file upload",
  "source_language": "en",
  "target_language": "vi"
}
```

**Response:**
```json
{
  "success": true,
  "original_image_url": "/static/translated_images/original_20250107_104500.jpg",
  "translated_image_url": "/static/translated_images/translated_20250107_104500.jpg",
  "task_id": "task_123456"
}
```

## Lưu ý quan trọng

1. **Trial Mode**: Hiện tại đang sử dụng trial mode với tag `x-iop-trial: true`. Cần xóa tag này sau khi mua API chính thức.

2. **File Storage**: Ảnh được lưu locally trong thư mục `translated_images/`. Đảm bảo thư mục này có quyền ghi.

3. **Timeout**: Hệ thống sẽ timeout sau 60 giây nếu không nhận được kết quả từ Aidge API.

4. **Error Handling**: Nếu có lỗi, hệ thống sẽ hiển thị thông báo lỗi chi tiết.

## Troubleshooting

### Lỗi thường gặp

1. **"Không có file được upload"**
   - Kiểm tra lại file đã được chọn chưa
   - Đảm bảo file có định dạng ảnh hợp lệ

2. **"Lỗi API: ..."**
   - Kiểm tra kết nối internet
   - Kiểm tra API key và secret có đúng không
   - Kiểm tra API domain có đúng không

3. **"Timeout: Không nhận được kết quả trong thời gian chờ"**
   - Ảnh có thể quá phức tạp hoặc lớn
   - Thử lại với ảnh khác
   - Kiểm tra server Aidge có hoạt động không

4. **"Không thể download ảnh đã dịch"**
   - Kiểm tra quyền ghi vào thư mục `translated_images/`
   - Kiểm tra dung lượng ổ cứng còn trống

### Debug

Để debug, kiểm tra logs của server FastAPI để xem chi tiết lỗi:

```bash
uvicorn main:app --reload --log-level debug
```

## Tính năng nâng cao

### Pro Version Features

- Tự động nhận diện ngôn ngữ nguồn
- Hỗ trợ nhiều ngôn ngữ hơn
- Chất lượng dịch tốt hơn
- Xử lý ảnh phức tạp tốt hơn

### Brand Protection

- Bảo vệ tên thương hiệu khỏi bị dịch
- Giữ nguyên logo và brand name

### Layout Preservation

- Giữ nguyên layout của ảnh gốc
- Điều chỉnh kích thước text phù hợp
- Hỗ trợ text từ phải sang trái (Arabic, Hebrew)

## Liên hệ hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs của server
2. Thử lại với ảnh khác
3. Liên hệ admin để được hỗ trợ 