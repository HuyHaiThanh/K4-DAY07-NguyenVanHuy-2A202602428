# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Huy
**Nhóm:** G22
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
Độ tương tự cosine đo mức độ hai vector embedding cùng hướng với nhau. Điểm càng gần 1 cho thấy hai đoạn văn bản càng giống nhau về ý nghĩa; điểm gần 0 biểu thị ít liên quan, còn điểm gần -1 biểu thị hai vector có hướng đối lập.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên có thể gia hạn sách thư viện
- Câu B: Người học được phép kéo dài thời gian mượn sách
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng cùng diễn đạt việc người học được kéo dài thời gian mượn tài liệu thư viện.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên đăng ký học phần trên cổng học vụ.
- Câu B: Thời tiết hôm nay có mưa lớn.
- Tại sao khác: Hai câu thuộc hai chủ đề và mục đích hoàn toàn khác nhau; câu thứ nhất nói về thủ tục học vụ, còn câu thứ hai nói về thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
Cosine similarity tập trung vào góc, tức hướng ngữ nghĩa của hai vector, nên ít bị ảnh hưởng bởi độ lớn của vector. Khoảng cách Euclid đo khoảng cách tuyệt đối và có thể đánh giá hai vector cùng hướng là khác nhau chỉ vì chúng có độ lớn khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
Áp dụng công thức:

```text
ceil((độ dài tài liệu - overlap) / (chunk_size - overlap))
= ceil((10,000 - 50) / (500 - 50))
= ceil(9,950 / 450)
= ceil(22.111...)
= 23 chunks
```

**Đáp án:** 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
Khi `overlap=100`, số chunk là `ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = 25`, tăng từ 23 lên 25 chunks. Overlap lớn hơn giúp bảo toàn thông tin nằm ở ranh giới giữa hai chunk, nhưng đồng thời làm tăng dữ liệu trùng lặp, số lần embedding và chi phí lưu trữ/tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
Tôi tách câu bằng biểu thức chính quy `r"(?<=[.!?])\s+"`, nghĩa là tách tại khoảng trắng đứng sau dấu chấm, chấm than hoặc chấm hỏi nhưng vẫn giữ dấu câu. Sau đó, tôi loại bỏ chuỗi rỗng, gom tối đa `max_sentences_per_chunk` câu vào mỗi chunk và chuẩn hóa khoảng trắng. Với văn bản rỗng, hàm trả về danh sách rỗng; tham số số câu được giới hạn tối thiểu là 1.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
Tôi thử các dấu phân cách theo thứ tự ưu tiên `"\n\n"`, `"\n"`, `". "`, `" "`, rồi mới tách cứng theo ký tự. Base case là khi đoạn hiện tại không vượt quá `chunk_size`, khi đó trả về ngay đoạn này; nếu đoạn vẫn quá dài, `_split` tiếp tục xử lý bằng separator tiếp theo. Khi không còn separator phù hợp, văn bản được cắt thành các đoạn có độ dài tối đa bằng `chunk_size` để bảo đảm thuật toán luôn dừng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
Trong `add_documents`, mỗi `Document` được chuẩn hóa thành một record chứa ID nội bộ duy nhất, `doc_id`, nội dung, metadata và vector embedding; record được thêm vào kho lưu trữ trong bộ nhớ. Trong `search`, truy vấn chỉ được embedding một lần, sau đó tính tích vô hướng giữa vector truy vấn và từng vector đã lưu, sắp xếp theo `score` giảm dần và trả về tối đa `top_k` kết quả. Vì các embedding được chuẩn hóa, tích vô hướng có vai trò tương đương cosine similarity.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
`search_with_filter` áp dụng metadata filter trước khi tính similarity để chỉ xếp hạng các record thỏa mãn toàn bộ cặp khóa–giá trị; nếu không truyền filter thì hành vi giống `search`. `delete_document` loại bỏ tất cả record có `metadata["doc_id"]` trùng với ID tài liệu cần xóa, sau đó so sánh kích thước trước và sau để trả về `True` nếu đã xóa được ít nhất một chunk, ngược lại trả về `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
Phương thức `answer` gọi vector store để lấy `top_k` chunk liên quan nhất, đánh số các chunk và ghép nội dung của chúng thành phần ngữ cảnh trong prompt. Prompt yêu cầu LLM chỉ trả lời dựa trên ngữ cảnh được cung cấp, không tự suy đoán và phải nói rõ khi dữ liệu không đủ. Sau đó, câu hỏi của người dùng được đặt sau phần ngữ cảnh và toàn bộ prompt được truyền cho `llm_fn` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
Lệnh kiểm thử:
python -m pytest tests/ -v

Môi trường theo log chạy chính thức:
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\VIN_AI\LAB_07\K4-DAY07-NguyenVanHuy-2A202602428
collected 42 items

========================================== test session starts ===========================================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\VIN_AI\LAB_07\K4-DAY07-NguyenVanHuy-2A202602428\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\VIN_AI\LAB_07\K4-DAY07-NguyenVanHuy-2A202602428
plugins: anyio-4.15.1
collected 42 items                                                                                        

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED               [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                        [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                 [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                  [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                       [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED       [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED             [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED              [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED            [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                              [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED              [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                         [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                     [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                               [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED      [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED          [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED    [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED          [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                              [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                  [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                        [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED             [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED               [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED   [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                         [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                        [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                   [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED               [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED          [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED              [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                    [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED              [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED         [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED        [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED       [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED[100%]

=========================================== 42 passed in 0.23s ===========================================

Kết quả:
- Project structure: 2/2 passed
- Class-based interfaces: 2/2 passed
- FixedSizeChunker: 7/7 passed
- SentenceChunker: 4/4 passed
- RecursiveChunker: 4/4 passed
- EmbeddingStore: 8/8 passed
- KnowledgeBaseAgent: 2/2 passed
- compute_similarity: 4/4 passed
- ChunkingStrategyComparator: 3/3 passed
- EmbeddingStore.search_with_filter: 3/3 passed
- EmbeddingStore.delete_document: 3/3 passed

42 passed in 0.23s

Kết quả trên đã được kiểm tra lại độc lập trên toàn bộ tests/:
42 passed in 0.23s
```

**Số lượng bài test vượt qua (pass):** 42 / 42

**Điểm phần Hoàn thiện code theo rubric:** 30 / 30

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi sử dụng mô hình đa ngữ cục bộ `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` để tạo embedding, sau đó dùng hàm `compute_similarity` của bài lab để tính cosine similarity. Khi đối chiếu dự đoán, tôi xem điểm từ `0.50` trở lên là tương đồng cao, điểm dưới `0.50` là tương đồng thấp; các điểm sát ngưỡng được xem là trường hợp trung gian cần phân tích thêm.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên có thể gia hạn sách thư viện. | Người học được phép kéo dài thời gian mượn tài liệu. | Cao | 0.6107 | Đúng |
| 2 | Sinh viên đăng ký học phần trên cổng học vụ. | Người học chọn lớp học phần qua hệ thống đào tạo. | Cao | 0.5685 | Đúng |
| 3 | Sinh viên cần kiểm tra học phần tiên quyết trước khi đăng ký. | Sinh viên cần mang thẻ hợp lệ khi mượn sách. | Thấp | 0.4926 | Đúng, nhưng sát ngưỡng |
| 4 | Sinh viên được phép đăng ký học phần này. | Sinh viên không được phép đăng ký học phần này. | Cao về từ vựng, nhưng đối lập về ý nghĩa | 0.4787 | Phù hợp một phần |
| 5 | Thư viện cung cấp không gian học tập. | Hôm nay thời tiết có mưa lớn. | Thấp | 0.0422 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
Cặp 4 là kết quả đáng chú ý nhất: hai câu có ý nghĩa đối lập do từ “không”, nhưng vẫn đạt `0.4787`, cao hơn rất nhiều so với cặp hoàn toàn không liên quan (`0.0422`). Điều này cho thấy embedding nhận biết tốt sự gần nhau về chủ đề, từ vựng và cấu trúc câu, nhưng có thể chưa phản ánh đầy đủ tác động của phủ định. Cặp 3 cũng đạt `0.4926` dù nói về hai thủ tục khác nhau, có thể vì cả hai câu đều có cấu trúc “Sinh viên cần...” và cùng thuộc miền dịch vụ đại học.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Tôi sử dụng `FixedSizeChunker(chunk_size=500, overlap=50)` đúng với chiến lược cá nhân đã đăng ký trong báo cáo nhóm và mô hình `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Một kết quả chỉ được đánh dấu liên quan khi chunk thực sự chứa bằng chứng cần để trả lời, không chỉ vì lấy đúng tên tài liệu. Đây là lượt chạy cá nhân bằng mô hình local; điểm so sánh 7/10 trong báo cáo nhóm được tổng hợp từ lượt benchmark chung dùng `text-embedding-3-small`, vì vậy hai bộ score không được so sánh trực tiếp.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Học phí hệ đại học chính quy đại trà cho khóa 68 trong năm học 2026-2027 là bao nhiêu tiền mỗi tín chỉ? | Chunk tham khảo về công thức tính học phí, không chứa mức của khóa 68 | 0.709836 | Top-1 không liên quan trực tiếp; chunk chứa **880.000 đồng/tín chỉ** ở hạng 3 | Agent trả lời đúng 880.000 đồng/tín chỉ nhờ bằng chứng trong top-3. |
| 2 | Sinh viên IBD@NEU khóa 22, đợt tháng 8/2026, phải nộp học phí trước thời hạn nào và bằng phương thức nào? | Thông báo IBD khóa 22 kỳ Mùa Xuân 2026, sai đợt | 0.864897 | Không; tài liệu tháng 8 ở hạng 2 nhưng chunk chứa hạn nộp và phương thức không vào top-3 | Agent báo ngữ cảnh chưa đủ để xác định chính xác hạn và phương thức. |
| 3 | Sinh viên thuộc diện chính sách cần nộp hồ sơ miễn, giảm học phí đợt 2 năm học 2025-2026 ở đâu và trong thời gian nào? | Chunk miễn giảm chứa thời gian 02/03–20/03/2026 nhưng bị cắt giữa cụm “phòng 302” | 0.846917 | Có một phần; dùng `metadata_filter={"audience": "student"}` nhưng thiếu địa điểm đầy đủ | Agent trả lời được thời gian và nói rõ địa điểm trong ngữ cảnh bị thiếu. |
| 4 | Theo tài liệu tham khảo về học phí NEU 2026, công thức tham khảo để tính học phí là gì? | Phần giới thiệu nguồn tham khảo, chưa chứa công thức | 0.771451 | Không; chunk chứa công thức không nằm trong top-3 | Agent báo chưa đủ thông tin thay vì suy đoán công thức. |
| 5 | Trong năm học 2026-2027, chương trình Khoa học dữ liệu và Trí tuệ nhân tạo có mức học phí bao nhiêu? | Phần căn cứ và chương trình chuẩn của Quyết định 985 | 0.645267 | Không; chunk chứa dòng **54 triệu đồng** không nằm trong top-3 | Agent báo ngữ cảnh chưa đủ để kết luận mức học phí. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** Lượt kiểm tra độc lập bằng mô hình local đạt 2 / 5: câu 1 có đầy đủ bằng chứng ở hạng 3, còn câu 3 có bằng chứng liên quan nhưng bị cắt mất một phần địa điểm. Trong lượt benchmark chung dùng `text-embedding-3-small`, nhóm chấm chiến lược FixedSize của tôi 7 / 10 theo rubric; đây là kết quả chính thức dùng trong bảng so sánh nhóm. Hai kết quả cho thấy chất lượng embedding có ảnh hưởng, nhưng hạn chế cắt rời bảng của FixedSize vẫn xuất hiện ở cả phần phân tích định tính.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
Điều hữu ích nhất tôi học được là chiến lược của Nguyễn Quốc Đạt và Nguyễn Trần Nhựt Nam tôn trọng ranh giới cấu trúc tốt hơn: `RecursiveChunker` giữ các khối nội dung tự nhiên, còn `HeadingChunker` giữ tiêu đề cùng bảng hoặc điều khoản. So với hai cách đó, FixedSize của tôi dễ cắt rời con số, thời hạn hoặc địa điểm khỏi phần mô tả; overlap chỉ giảm chứ không loại bỏ hoàn toàn vấn đề này.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 7 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
