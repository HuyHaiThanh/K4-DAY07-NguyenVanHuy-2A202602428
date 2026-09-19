# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Sentinel
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học phí hệ đại học chính quy tại Đại học Kinh tế Quốc dân (NEU)

**Tại sao nhóm chọn chủ đề này?**
Nhóm chọn học phí NEU vì dữ liệu có nhiều mức thu theo khóa, tín chỉ và chương trình đào tạo, phù hợp để thử nghiệm retrieval trên các câu hỏi có điều kiện cụ thể. Hai tài liệu hiện có cho phép so sánh một bài tổng hợp tham khảo với nguồn chính thức dẫn Quyết định 985/QĐ-ĐHKTQD, qua đó đánh giá ảnh hưởng của độ tin cậy và phiên bản tài liệu đến kết quả truy xuất.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Học phí NEU 2026: Cập nhật đầy đủ, mới nhất tháng 9/2026 | https://dienthoaivui.com.vn/back-to-school-hoc-phi-neu | Lấy ngày 2026-09-19; bài đăng ngày 2026-04-16; không có ngày hiệu lực chính thức; HTTP `200 OK`; HTML | 16.241 | `doc_id=back-to-school-hoc-phi-neu`, `audience=student`, `department=admissions`, `category=tuition-overview`, `language=vi`, `document_version=article-2026-04-16`, `license_or_permission=public-third-party-source-no-explicit-reuse-license` |
| 2 | Học phí NEU năm học 2026–2027 theo Quyết định 985/QĐ-ĐHKTQD | https://fit.neu.edu.vn/post/hoc-phi-neu-nam-hoc-2026-2027-theo-quyet-dinh-985 | Lấy ngày 2026-09-19; bài đăng ngày 2026-08-16; Quyết định ngày 2026-08-10; hiệu lực 2026-08-01 đến 2027-07-31; HTTP `200 OK`; HTML | 6.598 | `doc_id=hoc-phi-neu-nam-hoc-2026-2027-theo-quyet-dinh-985`, `audience=student`, `department=finance`, `category=tuition-per-credit`, `language=vi`, `document_version=QD985-AY2026-2027`, `license_or_permission=public-official-source-no-explicit-reuse-license` |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Kết quả kiểm tra nguồn:** Cả hai URL trả `HTTP 200 OK` khi kiểm tra ngày 2026-09-19 bằng `curl.exe -I -L` và đều là HTML, nên crawler mẫu có thể xử lý. `robots.txt` của Điện Thoại Vui không cấm đường dẫn bài viết; `robots.txt` của `fit.neu.edu.vn` khai báo `Allow: /` và cũng không cấm đường dẫn nguồn số 2. Nguồn số 1 là bài tổng hợp của bên thứ ba, không phải công bố chính thức của NEU, không nêu ngày hiệu lực và còn ghi rõ các mức học phí chỉ mang tính tham khảo; vì vậy không dùng riêng nguồn này để tạo gold answer. Nguồn số 2 thuộc tên miền Khoa Công nghệ thông tin NEU, dẫn Quyết định 985/QĐ-ĐHKTQD và nêu rõ hiệu lực từ ngày 2026-08-01 đến hết ngày 2027-07-31, nên được ưu tiên khi hai nguồn mâu thuẫn. Cả hai trang đều truy cập công khai nhưng không nêu giấy phép tái sử dụng riêng; nhóm chỉ trích xuất phần cần thiết cho mục đích học tập, ghi nguồn đầy đủ và không coi khả năng truy cập công khai là giấy phép sao chép không giới hạn.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
