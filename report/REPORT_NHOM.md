# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G22 
**Thành viên:** Nguyễn Trọng Phúc, Nguyễn Văn Huy, Nguyễn Trần Nhựt Nam, Nguyễn Quốc Đạt  
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học phí đại học, tập trung vào học phí NEU.

Nhóm chọn chủ đề này vì tài liệu có nhiều dạng câu hỏi thực tế: mức thu theo tín chỉ, học phí chương trình, thời hạn và phương thức thanh toán, công thức tính và thủ tục miễn giảm. Đây cũng là chủ đề phù hợp để đánh giá retrieval vì thông tin quan trọng thường là các con số, ngày tháng, địa điểm và điều kiện áp dụng; chỉ lấy đúng chủ đề nhưng thiếu đúng chunk vẫn có thể dẫn tới câu trả lời sai.

### Danh sách tài liệu (Data Inventory)

Tập dữ liệu gồm 7 tài liệu công khai, đã được làm sạch và lưu tại `data/hoc-phi/`. Kích thước dưới đây là số ký tự của nội dung Markdown sau khi thu thập.

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quyết định học phí NEU 2026–2027 | [fit.neu.edu.vn](https://fit.neu.edu.vn/post/hoc-phi-neu-nam-hoc-2026-2027-theo-quyet-dinh-985) | 19/09/2026; 2026–2027 | 2.672 | `doc_id`, `source_url`, `retrieved_at`, `document_version`, `license_or_permission` |
| 2 | Học phí IBD English Level 1 | [isme.neu.edu.vn PDF](https://isme.neu.edu.vn/wp-content/uploads/2024/09/1877-TB-DHKTQD-nop-HP-lop-Tieng-Anh-cap-do-1-dot-T9-2024.pdf) | 19/09/2026; 2024–2025 | 1.329 | Như trên; thêm `audience=student` |
| 3 | Học phí IBD kỳ Mùa Xuân 2026 | [isme.neu.edu.vn PDF](https://isme.neu.edu.vn/wp-content/uploads/2026/02/TB-Hoc-phi-Khoa-22-mua-Xuan.pdf) | 19/09/2026; 2025–2026 | 1.989 | Như trên; thêm `audience=student` |
| 4 | Hướng dẫn thanh toán học phí NEU | [neu.edu.vn PDF](https://neu.edu.vn/Resources/Docs/SubDomain/cait/CongThanhtTantructuyen/H%C6%AF%E1%BB%9ANG%20D%E1%BA%AAN%20S%E1%BB%AC%20D%E1%BB%A5NG%20C%E1%BB%94NG%20THANHTO%C3%81N%20%C4%90%E1%BB%82%20THANH%20TO%C3%81N%20H%E1%8CC%20PH%C3%8D%202020-v1.pdf) | 19/09/2026; 2020 | 1.289 | Như trên; thêm `audience=student` |
| 5 | Thông báo học phí IBD đợt tháng 8/2026 | [isme.neu.edu.vn](https://isme.neu.edu.vn/admissions/thong-bao-hoc-phi-danh-cho-sinh-vien-ibdneu-khoa-22-dot-thang-8-2026/) | 19/09/2026; 2026–2027 | 2.429 | Như trên; thêm `audience=student` |
| 6 | Tài liệu tham khảo học phí NEU 2026 | [dienthoaivui.com.vn](https://dienthoaivui.com.vn/back-to-school-hoc-phi-neu) | 19/09/2026; 2026 | 2.026 | Như trên; `source_type=reference` |
| 7 | Thông báo hồ sơ miễn, giảm học phí 2025–2026 | [fit.neu.edu.vn](https://fit.neu.edu.vn/post/thong-bao-ve-viec-thu-ho-so-mien-giam-hoc-phi-va-ho-tro-chi-phi-hoc-tap-cho-sinh-vien-dot-2-nam-hoc-2025-2026) | 19/09/2026; 2025–2026 | 1.623 | Như trên; `audience=student` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [x] Tập tài liệu chỉ chứa nguồn công khai/được phép dùng; không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` hoặc ngày hiệu lực trong metadata.
- [x] Các tài liệu tham khảo được đánh dấu rõ để không nhầm với thông báo chính thức của trường.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|---|---|---|---|
| `doc_id` | string | `neu-tuition-payment-ibd-2026` | Định danh ổn định để truy vết tài liệu và xóa toàn bộ chunk của một tài liệu. |
| `source_url` | string | URL trang/PDF gốc | Cho phép kiểm chứng câu trả lời và truy ngược nguồn. |
| `retrieved_at` | date | `2026-09-19` | Theo dõi thời điểm thu thập và đánh giá độ mới. |
| `document_version` | string | `2026-2027` | Phân biệt các thông báo theo năm học/kỳ học. |
| `audience` | string | `student` | Cho phép pre-filter, đặc biệt ở câu hỏi về hồ sơ miễn giảm. |
| `source_type` | string | `official` / `reference` | Giúp ưu tiên nguồn chính thức khi có nguồn tham khảo cùng chủ đề. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Nhóm chạy `ChunkingStrategyComparator().compare()` với `chunk_size=200` trên ba tài liệu đại diện. Các số liệu dưới đây được chạy trực tiếp trên nội dung Markdown đã bỏ front matter.

| Tài liệu | Chiến lược | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|---|---|---:|---:|---|
| Quyết định học phí NEU 2026–2027 | FixedSizeChunker (`fixed_size`) | 12 | 190,1 | Trung bình; dễ cắt giữa tên chương trình và mức tiền. |
| Quyết định học phí NEU 2026–2027 | SentenceChunker (`by_sentences`) | 3 | 757,3 | Tốt ở ranh giới câu nhưng chunk dài, có thể gộp nhiều ý. |
| Quyết định học phí NEU 2026–2027 | RecursiveChunker (`recursive`) | 17 | 132,4 | Tốt; ưu tiên đoạn/dòng và chỉ cắt nhỏ khi cần. |
| Thông báo IBD đợt tháng 8/2026 | FixedSizeChunker (`fixed_size`) | 11 | 182,5 | Trung bình; có nguy cơ tách ngày hạn khỏi phương thức nộp. |
| Thông báo IBD đợt tháng 8/2026 | SentenceChunker (`by_sentences`) | 4 | 499,5 | Khá tốt; giữ câu nhưng một chunk vẫn tương đối dài. |
| Thông báo IBD đợt tháng 8/2026 | RecursiveChunker (`recursive`) | 13 | 152,8 | Tốt; cân bằng giữa độ ngắn và đầy đủ ngữ cảnh. |
| Thông báo miễn, giảm học phí 2025–2026 | FixedSizeChunker (`fixed_size`) | 6 | 195,3 | Trung bình; có thể cắt rời địa điểm khỏi thời gian. |
| Thông báo miễn, giảm học phí 2025–2026 | SentenceChunker (`by_sentences`) | 3 | 388,0 | Khá tốt; số chunk ít nhưng mỗi chunk dài hơn. |
| Thông báo miễn, giảm học phí 2025–2026 | RecursiveChunker (`recursive`) | 10 | 115,4 | Tốt; giữ các cụm thông tin nhỏ và dễ truy xuất. |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Trọng Phúc**

- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Chia tài liệu thành các chunk tối đa 3 câu, giữ ranh giới câu để hạn chế cắt giữa điều kiện, thời hạn và mức học phí. Chiến lược này cho kết quả ổn định trên các thông báo có cấu trúc câu rõ ràng và được dùng làm cấu hình benchmark chung.
- **Code snippet:**

```python
SentenceChunker(max_sentences_per_chunk=3)
```

**Thành viên 2 — Nguyễn Văn Huy**

- **Loại chiến lược:** FixedSizeChunker (`chunk_size=500, overlap=50`)
- **Mô tả & lý do chọn:** Chia theo cửa sổ trượt có overlap để giữ một phần ngữ cảnh tại ranh giới. Cách này đơn giản, ổn định về kích thước và phù hợp khi cần kiểm soát chi phí embedding, nhưng có thể cắt rời ngày tháng, địa điểm hoặc dòng trong bảng.
- **Code snippet:**

```python
FixedSizeChunker(chunk_size=500, overlap=50)
```

**Thành viên 3 — Nguyễn Trần Nhựt Nam**

- **Loại chiến lược:** RecursiveChunker (`chunk_size=700`)
- **Mô tả & lý do chọn:** Thử các separator theo thứ tự đoạn, dòng, câu, khoảng trắng rồi mới cắt cứng. Cách này ưu tiên giữ các đơn vị ngữ nghĩa tự nhiên và giúp các con số trong bảng/thông báo đi cùng phần mô tả liên quan.
- **Code snippet:**

```python
RecursiveChunker(chunk_size=700)
```

**Thành viên 4 — Nguyễn Quốc Đạt**

- **Loại chiến lược:** RecursiveChunker, kiểm tra bổ sung với bộ test và truy xuất có metadata filter.
- **Mô tả & lý do chọn:** Tập trung kiểm tra fallback khi văn bản quá dài, input rỗng và pre-filter theo metadata. Kết quả cho thấy recursive chunking bảo toàn ngữ cảnh tốt hơn fixed-size ở các câu hỏi yêu cầu nhiều trường thông tin.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|---|---|---:|---|---|
| Nguyễn Trọng Phúc | SentenceChunker + `text-embedding-3-small` | 9/10 | Giữ ranh giới câu, kết quả ổn định và dễ giải thích. | Có thể tạo chunk dài, đôi khi nhiều ý bị gộp. |
| Nguyễn Văn Huy | FixedSize, overlap 50 | 7/10 | Đơn giản, kiểm soát kích thước và chi phí tốt. | Có thể cắt rời ngày, số tiền hoặc địa điểm khỏi ngữ cảnh. |
| Nguyễn Trần Nhựt Nam | Recursive, chunk size 700 | 10/10 | Giữ cấu trúc tự nhiên, bảo toàn bằng chứng cần trả lời. | Chunk có độ dài không đồng đều, cần kiểm soát ngưỡng. |
| Nguyễn Quốc Đạt | Recursive + metadata filter | 9/10 | Tốt với câu hỏi có điều kiện lọc và các đoạn dài. | Phụ thuộc vào metadata được gán đầy đủ, nhất quán. |

**Chiến lược tốt nhất cho chủ đề này:** Nhóm chọn SentenceChunker với tối đa 3 câu/chunk làm cấu hình benchmark chung vì nó cân bằng giữa độ dễ kiểm soát, khả năng giữ ranh giới câu và kết quả truy xuất. Tuy nhiên, kết quả so sánh cho thấy RecursiveChunker phù hợp hơn khi tài liệu có bảng, nhiều dòng hoặc câu trả lời cần lấy đồng thời ngày, địa điểm và điều kiện. Vì vậy, nếu triển khai thực tế, nhóm sẽ ưu tiên recursive chunking cho thông báo dài và kết hợp metadata filter với embedding.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|---|---|---|
| 1 | Học phí hệ đại học chính quy đại trà cho khóa 68 trong năm học 2026–2027 là bao nhiêu tiền mỗi tín chỉ? | Theo Quyết định 985, mức thu của khóa 68 là **880.000 đồng/tín chỉ**. | `neu-tuition-decision-985-2026-2027.md`, mục Chương trình chuẩn. |
| 2 | Sinh viên IBD@NEU khóa 22, đợt tháng 8/2026, phải nộp học phí trước thời hạn nào và bằng phương thức nào? | Hạn nộp là **17h00 ngày 21/08/2026**; chuyển khoản vào tài khoản VND **2116678989** của Đại học Kinh tế Quốc dân tại BIDV, chi nhánh Hà Nội. | `neu-tuition-payment-ibd-2026.md`, mục Phương thức và hạn nộp. |
| 3 | Sinh viên thuộc diện chính sách cần nộp hồ sơ miễn, giảm học phí đợt 2 năm học 2025–2026 ở đâu và trong thời gian nào? | Nộp trực tiếp tại **Phòng Công tác chính trị và Quản lý sinh viên — phòng 302 Nhà A1**, từ **02/03/2026 đến hết 20/03/2026**. Câu hỏi dùng `metadata_filter={"audience": "student"}`. | `neu-tuition-waiver-2025-2026.md`, mục Thời gian, hồ sơ và địa điểm nộp. |
| 4 | Theo tài liệu tham khảo về học phí NEU 2026, công thức tham khảo để tính học phí là gì? | **Học phí = số tín chỉ đăng ký × đơn giá mỗi tín chỉ**; cần đối chiếu với thông báo chính thức khi sử dụng. | `neu-tuition-reference-2026.md`, mục Cách tính và khoản thu liên quan. |
| 5 | Trong năm học 2026–2027, chương trình Khoa học dữ liệu và Trí tuệ nhân tạo có mức học phí bao nhiêu? | Cả **Data Science** và **AI** có mức học phí **54 triệu đồng/năm**. | `neu-tuition-decision-985-2026-2027.md`, mục Các chương trình đào tạo bằng tiếng Anh. |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---|---|---|---|
| 1 | Mức học phí khóa 68 theo tín chỉ? | SentenceChunker + `text-embedding-3-small` | Có — hạng 1, score **0.663438** | Tài liệu Quyết định 985 được truy xuất đúng ở top-1. |
| 2 | Hạn và phương thức nộp học phí IBD khóa 22 tháng 8/2026? | SentenceChunker + `text-embedding-3-small` | Có — hạng 2 và 3, score tốt nhất **0.701000** | Tài liệu đúng có trong top-3; hạng 1 là thông báo IBD kỳ khác. |
| 3 | Địa điểm và thời gian nộp hồ sơ miễn giảm học phí? | SentenceChunker + `metadata_filter={"audience": "student"}` | Có — hạng 1, score **0.740978** | Metadata filter loại bớt tài liệu không dành cho sinh viên. |
| 4 | Công thức tham khảo để tính học phí? | SentenceChunker + `text-embedding-3-small` | Có — hạng 1, score **0.713135** | Tài liệu tham khảo đúng đứng hạng 1–2. |
| 5 | Học phí chương trình Data Science và AI? | SentenceChunker + `text-embedding-3-small` | Có — hạng 1, score **0.690119** | Quyết định 985 được truy xuất đúng ở top-1. |

**Tổng kết:** 5/5 câu hỏi có chunk liên quan trong top-3; 4/5 câu có chunk đúng ở top-1. Câu 2 cho thấy đúng tài liệu chưa đủ: nếu chunk không chứa đồng thời ngày hạn và phương thức nộp, agent vẫn có thể trả lời thiếu. Câu 3 cho thấy metadata filter có tác dụng rõ rệt khi câu hỏi có phạm vi đối tượng cụ thể.

**Cấu hình chạy benchmark:** 7 tài liệu trong `data/hoc-phi`, chia thành 25 chunks bằng `SentenceChunker(max_sentences_per_chunk=3)`, dùng `text-embedding-3-small` và lấy top-3 kết quả. Khi chạy bằng `MockEmbedder`, điểm similarity chỉ dùng để kiểm tra pipeline và công thức, không đại diện cho chất lượng hiểu ngữ nghĩa.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích nhóm sẽ trình bày:**

1. Cùng một câu hỏi có thể cho kết quả khác nhau tùy chunking: FixedSize dễ cắt rời bằng chứng, trong khi SentenceChunker và RecursiveChunker giữ ngữ cảnh tốt hơn.
2. Metadata filter là một lớp lọc quan trọng trước similarity search; ở câu hỏi về hồ sơ miễn giảm, `audience=student` giúp chunk đúng đứng hạng 1.
3. Retrieval cần được chấm theo bằng chứng trong chunk, không chỉ theo `doc_id`. Một tài liệu đúng chủ đề nhưng không chứa ngày, số tiền hoặc địa điểm cần thiết vẫn chưa đủ để trả lời đúng.

**Bài học rút ra khi so sánh trong nhóm:**

Cùng một tập tài liệu nhưng chiến lược khác nhau tạo ra ranh giới chunk và mức độ đầy đủ ngữ cảnh khác nhau. FixedSize dễ triển khai và kiểm soát chi phí, SentenceChunker phù hợp với văn bản dạng thông báo, còn RecursiveChunker bảo toàn cấu trúc tốt hơn với đoạn dài và bảng. Kết quả cuối cùng còn phụ thuộc vào embedding model, vì vậy cần cố định cấu hình khi so sánh công bằng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu?**

Nhóm sẽ giữ riêng các bảng, tiêu đề và mục “thời hạn/phương thức” thành các chunk có cấu trúc; đồng thời gắn thêm metadata `audience`, `document_type`, `effective_date` và `authority_level`. Nhóm cũng sẽ dùng hybrid retrieval hoặc reranking cho các câu hỏi chứa số tiền và ngày tháng, vì embedding thuần túy đôi khi nhận diện đúng chủ đề nhưng bỏ sót bằng chứng chính xác.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **38 / 40** |

