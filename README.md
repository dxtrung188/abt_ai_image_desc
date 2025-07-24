# abt_ai_image_desc 

## Website Documentation

### Mục đích

Xây dựng một website cho phép người dùng chọn sản phẩm trong danh sách lọc (candidates) giống nhất với sản phẩm gốc dựa trên hình ảnh.

---

### Mô tả dữ liệu

1. **Sản phẩm gốc**:  
   - Ảnh sản phẩm gốc lấy từ trường `image_url` của bảng `abt_image_to_product`.

2. **Danh sách sản phẩm lọc (candidates)**:  
   - Nằm trong cột `products_1688_filtered` (kiểu JSON) của bảng `abt_image_to_product`.
   - Trường `candidates` là một mảng gồm 10 sản phẩm, mỗi sản phẩm có trường `offer_id` (mã sản phẩm).

3. **Bảng sản phẩm 1688**:  
   - Bảng `abt_products_1688` chứa danh sách sản phẩm 1688.
   - Mỗi sản phẩm có `offer_id` (unique) và trường `image_url` (ảnh sản phẩm).

---

### Luồng quy trình

1. **Load dữ liệu**  
   - Đọc từng dòng dữ liệu trong bảng `abt_image_to_product`.

2. **Lấy danh sách candidates**  
   - Đọc trường `products_1688_filtered` để lấy mảng `candidates`.
   - Sử dụng `offer_id` của từng candidate để tra cứu thông tin sản phẩm tương ứng trong bảng `abt_products_1688` (lấy thêm ảnh, tên, v.v.).

3. **Hiển thị giao diện**  
   - Hiển thị ảnh sản phẩm gốc.
   - Hiển thị danh sách ảnh các sản phẩm candidates (lấy từ bảng `abt_products_1688`).

4. **Chọn sản phẩm giống nhất**  
   - Cho phép người dùng chọn 1 ảnh trong danh sách candidates (radio button hoặc click chọn ảnh).

5. **Gửi lựa chọn**  
   - Có nút "Submit" để xác nhận lựa chọn.

6. **Lưu kết quả**  
   - Khi người dùng submit, lưu `offer_id` của sản phẩm được chọn vào trường `best_match` của bảng `abt_image_to_product` tương ứng với dòng dữ liệu đang xử lý.

---

### Gợi ý giao diện

- **Bên trái**: Ảnh sản phẩm gốc.
- **Bên phải**: Lưới 10 ảnh candidates, mỗi ảnh có thể click chọn.
- **Bên dưới**: Nút "Submit" để lưu lựa chọn.

---

### Yêu cầu kỹ thuật

- Backend: Có thể dùng Python (Flask, FastAPI, Django, v.v.) kết nối PostgreSQL.
- Frontend: HTML/CSS/JS đơn giản, có thể dùng framework như React hoặc chỉ dùng template engine (Jinja2, v.v.).
- Đảm bảo mỗi lần chỉ xử lý 1 dòng dữ liệu, sau khi submit thì chuyển sang dòng tiếp theo hoặc thông báo hoàn thành.

---

### Lưu ý

- Đảm bảo dữ liệu được cập nhật chính xác vào trường `best_match`.
- Có thể thêm chức năng lọc, tìm kiếm, hoặc phân trang nếu số lượng dòng lớn.
- Giao diện nên trực quan, dễ thao tác, ưu tiên hiển thị rõ ràng ảnh sản phẩm.

---
