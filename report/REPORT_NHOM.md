# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm G22
**Thành viên:**
- Nguyễn Trần Nhựt Nam
- Nguyễn Quốc Đạt
- Nguyễn Văn Huy
- Nguyễn Trọng Phúc
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ & Quy định học phí, hướng dẫn thanh toán và chính sách miễn giảm học phí Đại học Kinh tế Quốc dân (NEU).

**Tại sao nhóm chọn chủ đề này?**
> Học phí và các chính sách tài chính sinh viên là mối quan tâm hàng đầu, mang tính pháp lý cao và ảnh hưởng trực tiếp đến người học ở mọi hệ đào tạo. Tập văn bản này chứa nhiều dữ liệu phức tạp (biểu phí theo tín chỉ/năm, các mốc thời hạn chót, thông tin tài khoản ngân hàng, các diện miễn giảm), rất phù hợp để thử nghiệm năng lực truy xuất ngữ nghĩa chính xác và khả năng lọc theo đối tượng (`audience: student/all`) của hệ thống RAG.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Học phí NEU năm học 2026-2027 theo Quyết định 985 | `https://fit.neu.edu.vn/post/hoc-phi-neu-nam-hoc-2026-2027-theo-quyet-dinh-985` | 2026-09-19 / 2026-2027 | ~3.160 | `doc_id: neu-tuition-decision-985-2026-2027`, `audience: student`, `department: information-technology`, `category: tuition` |
| 2 | Thông báo học phí IBD@NEU khóa 22 đợt tháng 8 2026 | `https://isme.neu.edu.vn/admissions/...` | 2026-09-19 / 2026-2027 | ~2.900 | `doc_id: neu-tuition-payment-ibd-2026`, `audience: student`, `department: international-programs`, `category: tuition-payment` |
| 3 | Thông báo học phí IBD@NEU khóa 22 kỳ Mùa Xuân 2026 | `https://isme.neu.edu.vn/wp-content/.../TB-Hoc-phi...pdf` | 2026-09-19 / 2025-2026 | ~2.400 | `doc_id: neu-tuition-ibd-spring-2026`, `audience: student`, `department: international-programs`, `category: tuition-payment` |
| 4 | Thông báo học phí IBD@NEU tiếng Anh cấp độ 1 tháng 9 2024 | `https://isme.neu.edu.vn/wp-content/.../1877-TB...pdf` | 2026-09-19 / 2024-2025 | ~1.570 | `doc_id: neu-tuition-ibd-english-level1-2024`, `audience: student`, `department: international-programs`, `category: tuition-payment` |
| 5 | Hướng dẫn cổng thanh toán học phí NEU | `https://neu.edu.vn/Resources/.../CongThanhtTantructuyen...pdf` | 2026-09-19 / 2020 | ~1.480 | `doc_id: neu-tuition-payment-guide-2020`, `audience: all`, `department: finance`, `category: tuition-payment` |
| 6 | Thu hồ sơ miễn giảm học phí NEU đợt 2 năm học 2025-2026 | `https://fit.neu.edu.vn/post/thong-bao-ve-viec-thu-ho-so...` | 2026-09-19 / 2025-2026 | ~1.990 | `doc_id: neu-tuition-waiver-2025-2026`, `audience: student`, `department: student-affairs`, `category: tuition-waiver` |
| 7 | Học phí NEU 2026 - nguồn tham khảo | `https://dienthoaivui.com.vn/back-to-school-hoc-phi-neu` | 2026-09-19 / 2026 | ~2.520 | `doc_id: neu-tuition-reference-2026`, `audience: all`, `department: education-media`, `category: tuition` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | string | `student`, `all` | Phân tách đối tượng sinh viên chính sách / sinh viên quốc tế / toàn bộ người học để lọc trước (pre-filtering), tránh lẫn lộn quy định. |
| `department` | string | `finance`, `international-programs`, `student-affairs` | Khoanh vùng chính xác đơn vị ban hành và phụ trách giải quyết thủ tục. |
| `category` | string | `tuition`, `tuition-payment`, `tuition-waiver` | Phân loại mục đích nghiệp vụ: tra cứu biểu phí, hướng dẫn nộp tiền, hay chính sách miễn giảm. |
| `document_version` | string | `2026-2027`, `2025-2026` | Đảm bảo tính cập nhật, tránh trả về các mức học phí của những năm học cũ đã hết hiệu lực. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu tiêu biểu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `neu-tuition-decision-985-2026-2027.md` | FixedSizeChunker (`fixed_size`) | 9 | 279.7 | Một số dòng trong bảng biểu học phí các ngành tiếng Anh bị cắt đôi giữa chừng. |
| | SentenceChunker (`by_sentences`) | 3 | 757.3 | Chunk quá dài do bảng biểu ít dấu câu kết thúc, làm loãng ngữ nghĩa. |
| | RecursiveChunker (`recursive`) | 11 | 205.5 | Giữ nguyên các nhóm ngành theo dòng, tính mạch lạc cao. |
| `neu-tuition-payment-ibd-2026.md` | FixedSizeChunker (`fixed_size`) | 8 | 276.8 | Cắt ngang phần thông tin số tài khoản và hạn chót nộp tiền. |
| | SentenceChunker (`by_sentences`) | 4 | 499.5 | Gom các đoạn thông báo khá tốt nhưng bảng học phí bị dồn cục. |
| | RecursiveChunker (`recursive`) | 7 | 285.1 | Rất cân bằng, tách riêng phần hạn nộp và phần bảng mức phí. |
| `neu-tuition-waiver-2025-2026.md` | FixedSizeChunker (`fixed_size`) | 5 | 257.6 | Ranh giới cắt cơ học, dễ mất điều kiện diện chính sách ở chunk sau. |
| | SentenceChunker (`by_sentences`) | 3 | 388.0 | Khá tốt với văn bản dạng danh sách điều kiện gạch đầu dòng. |
| | RecursiveChunker (`recursive`) | 5 | 232.6 | Tách rõ phần đối tượng áp dụng và phần địa điểm nộp hồ sơ. |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Trần Nhựt Nam (Lead Tech)**
- **Loại chiến lược:** HeadingChunker (Custom Chunker)
- **Mô tả & lý do chọn cho chủ đề này:** Chia nhỏ văn bản dựa trên các tiêu đề Markdown (`#`, `##`, `###`). Với các section dài vượt ngưỡng, tự động cắt nhỏ và **gắn lại tiêu đề mục vào từng mảnh con**, đảm bảo không bao giờ bị mất ngữ cảnh quy định.

**Thành viên 2 — Nguyễn Quốc Đạt**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=700`)
- **Mô tả & lý do chọn:** Sử dụng đệ quy ưu tiên cắt theo `\n\n`, `\n`, `. `, ` ` kết hợp bước gom (merge). Với `chunk_size=700`, chiến lược giữ được trọn vẹn từng bảng học phí tiếng Anh và các hướng dẫn nộp tiền mà không bị đứt đoạn.

**Thành viên 3 — Nguyễn Văn Huy**
- **Loại chiến lược:** FixedSizeChunker (`chunk_size=500, overlap=50`)
- **Mô tả & lý do chọn:** Chia nhỏ văn bản theo độ dài cố định 500 ký tự với độ chồng chéo 50 ký tự. Đơn giản, đảm bảo kích thước các vector embedding đồng đều, nhưng nhược điểm là dễ cắt ngang giữa bảng số liệu.
- **Code snippet:**
```python
from src import Document, FixedSizeChunker

chunker = FixedSizeChunker(chunk_size=500, overlap=50)
chunks = chunker.chunk(document_content)

chunk_documents = [
    Document(
        id=f"{doc_id}#{index:03d}",
        content=chunk,
        metadata={
            **document_metadata,
            "doc_id": doc_id,
            "chunk_index": index,
            "chunking_strategy": "fixed_size_500_overlap_50",
        },
    )
    for index, chunk in enumerate(chunks)
]
```

**Thành viên 4 — Nguyễn Trọng Phúc**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Chia theo ranh giới câu tự nhiên. Rất tốt cho các đoạn văn mô tả điều kiện miễn giảm, nhưng gặp khó khăn khi văn bản chứa bảng biểu dạng Markdown.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Văn Huy | FixedSizeChunker (`chunk_size=500, overlap=50`) | 7 / 10 | Đơn giản, kích thước vector đồng đều, chi phí tính toán ổn định. | Bị cắt đôi các dòng bảng học phí, mất ngữ cảnh tiêu đề cột. |
| Nguyễn Quốc Đạt | RecursiveChunker (`chunk_size=700`) | 10 / 10 | Giữ trọn bảng biểu học phí, ranh giới cắt tự nhiên, kết quả đạt Top-1 cả 5 câu hỏi. | Cần tinh chỉnh ngưỡng kích thước khối theo độ phức tạp tài liệu. |
| Nguyễn Trọng Phúc | SentenceChunker (`max_sentences_per_chunk=3`) | 8 / 10 | Rất mạch lạc với các điều khoản miễn giảm học phí dạng câu văn. | Bảng biểu không có dấu chấm câu nên bị dồn thành chunk quá dài. |
| Nguyễn Trần Nhựt Nam | HeadingChunker (Custom) | 10 / 10 | Giữ nguyên vẹn đơn vị ngữ nghĩa từng mục/tiêu đề; tự động gắn lại tiêu đề chống mất ngữ cảnh khi phân tách nhỏ. | Cần tài liệu có định dạng Markdown tiêu đề hoặc cấu trúc Điều/Khoản rõ ràng. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược **RecursiveChunker (`chunk_size=700`)** và **HeadingChunker** đạt hiệu quả tốt nhất (10/10 điểm truy xuất). Lý do là vì văn bản quy định học phí có tính phân cấp cao và chứa nhiều bảng biểu dữ liệu; hai chiến lược này tôn trọng ranh giới cấu trúc văn bản, giữ trọn vẹn tiêu đề mục và bảng số liệu, giúp mô hình embedding nhận diện chính xác câu trả lời ở ngay vị trí Top-1.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Học phí hệ đại học chính quy đại trà cho khóa 68 trong năm học 2026-2027 là bao nhiêu tiền mỗi tín chỉ? | Theo Quyết định 985, mức thu của khóa 68 là **880.000 đồng/tín chỉ**. | `neu-tuition-decision-985-2026-2027.md` — mục **Chương trình chuẩn**. |
| 2 | Sinh viên IBD@NEU khóa 22, đợt tháng 8/2026, phải nộp học phí trước thời hạn nào và bằng phương thức nào? | Hạn nộp là **17h00 ngày 21/08/2026**; phương thức nộp là **chuyển khoản** vào tài khoản VND **2116678989** của Đại học Kinh tế Quốc dân tại BIDV, chi nhánh Hà Nội. | `neu-tuition-payment-ibd-2026.md` — mục **Phương thức và hạn nộp**. |
| 3 | Sinh viên thuộc diện chính sách cần nộp hồ sơ miễn, giảm học phí đợt 2 năm học 2025-2026 ở đâu và trong thời gian nào? | Hồ sơ được nộp trực tiếp tại **Phòng Công tác chính trị và Quản lý sinh viên — phòng 302 Nhà A1**, từ **02/03/2026 đến hết ngày 20/03/2026**. Câu hỏi cần lọc `metadata_filter={"audience": "student"}`. | `neu-tuition-waiver-2025-2026.md` — mục **Thời gian, hồ sơ và địa điểm nộp**. |
| 4 | Theo tài liệu tham khảo về học phí NEU 2026, công thức tham khảo để tính học phí là gì? | Công thức là **Học phí = số tín chỉ đăng ký × đơn giá mỗi tín chỉ**. Đây là nguồn tham khảo, cần ưu tiên đối chiếu với thông báo chính thức của trường. | `neu-tuition-reference-2026.md` — mục **Cách tính và khoản thu liên quan**. |
| 5 | Trong năm học 2026-2027, chương trình Khoa học dữ liệu và Trí tuệ nhân tạo có mức học phí bao nhiêu? | Cả **Khoa học dữ liệu — Data Science** và **Trí tuệ nhân tạo — AI** có mức học phí **54 triệu đồng/năm**. | `neu-tuition-decision-985-2026-2027.md` — mục **Các chương trình đào tạo bằng tiếng Anh**. |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Mức học phí khóa 68 theo tín chỉ? | Recursive, `chunk_size=700` + `text-embedding-3-small` | Có — hạng 1, score **0.657766** | Tài liệu Quyết định 985 được truy xuất đúng ở top-1. |
| 2 | Hạn và phương thức nộp học phí IBD khóa 22 tháng 8/2026? | Recursive, `chunk_size=700` + `text-embedding-3-small` | Có — hạng 1, score **0.777727** | Tài liệu IBD đúng đứng top-1; hai tài liệu IBD khác nằm ở hạng 2–3. |
| 3 | Địa điểm và thời gian nộp hồ sơ miễn giảm học phí? | Recursive, `chunk_size=700` + `metadata_filter={"audience": "student"}` + `text-embedding-3-small` | Có — hạng 1, score **0.766433** | Bộ lọc sinh viên được áp dụng; hai chunk liên quan của tài liệu miễn giảm đứng hạng 1–2. |
| 4 | Công thức tham khảo để tính học phí? | Recursive, `chunk_size=700` + `text-embedding-3-small` | Có — hạng 1, score **0.727442** | Tài liệu tham khảo đúng đứng cả hạng 1–3. |
| 5 | Học phí chương trình Data Science và AI? | Recursive, `chunk_size=700` + `text-embedding-3-small` | Có — hạng 1, score **0.672587** | Tài liệu Quyết định 985 được truy xuất đúng ở top-1. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata **cực kỳ hữu ích, đặc biệt ở Câu hỏi số 3**. Khi không có bộ lọc `audience="student"`, hệ thống có thể bị phân tán và trả về các hướng dẫn thanh toán chung chung của cổng e-bills (`audience="all"`). Khi kích hoạt bộ lọc pre-filtering, hệ thống chỉ tìm kiếm trong các văn bản hướng dẫn trực tiếp cho sinh viên, đảm bảo trích xuất chính xác 100% thời gian và địa điểm nộp hồ sơ tại phòng 302 Nhà A1.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. Sự khác biệt mang tính quyết định giữa các chiến lược chunking đối với văn bản quy định hành chính có bảng biểu: Recursive và Heading vượt trội hoàn toàn so với cắt cố định.
> 2. Vai trò sống còn của **Pre-filtering metadata**: lọc trước khi tính similarity giúp bảo vệ top-k khỏi việc bị chiếm dụng bởi các tài liệu sai đối tượng.
> 3. Tầm quan trọng của tính năng truy vết nguồn gốc (Source Traceability): Agent đánh số trích dẫn nguồn `[1]`, `[2]` giúp người dùng kiểm chứng ngay con số học phí trên văn bản gốc.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một tập dữ liệu và cùng một câu hỏi nhưng chỉ cần thay đổi chiến lược chunking là kết quả retrieval khác biệt rõ rệt. `FixedSizeChunker` dễ cắt vụn bảng số liệu làm mất ngữ cảnh hàng - cột; trong khi `RecursiveChunker` và `HeadingChunker` giữ được cấu trúc phân cấp của văn bản quy định, giúp vector embedding mã hóa trọn vẹn ý nghĩa ngữ nghĩa.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa dữ liệu bảng Markdown sang định dạng cặp key-value hoặc bổ sung trực tiếp tiêu đề cột vào từng dòng của bảng trước khi chunk. Điều này sẽ giúp mô hình embedding bắt được chính xác tên ngành học và con số học phí tương ứng ngay cả khi bảng biểu bị chia tách.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
