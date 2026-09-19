from __future__ import annotations

import heapq
from importlib import import_module
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    Kho vector dùng để lưu trữ và tìm kiếm các đoạn văn bản (chunk).

    Lớp ưu tiên sử dụng ChromaDB nếu thư viện này khả dụng. Nếu không, dữ liệu
    được lưu tạm trong bộ nhớ bằng một danh sách. Tham số ``embedding_fn`` cho
    phép truyền hàm embedding khác vào, rất hữu ích khi cần dùng mock trong test.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        # Nếu không truyền hàm embedding, dùng hàm mock mặc định của dự án.
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        # Nơi lưu các record khi ChromaDB không khả dụng.
        self._store: list[dict[str, Any]] = []
        self._collection = None
        # Chỉ số tăng dần giúp ID của từng chunk không bị trùng nhau.
        self._next_index = 0

        try:
            chromadb = import_module("chromadb")

            # Tạo collection mới hoặc lấy lại collection đã tồn tại.
            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            # Nếu chưa cài ChromaDB hoặc khởi tạo thất bại, chuyển sang lưu trong RAM.
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Chuyển một ``Document`` thành record hoàn chỉnh để lưu trữ."""
        # Sao chép metadata để không vô tình thay đổi metadata của Document gốc.
        metadata = dict(doc.metadata)
        # Một document có thể được chia thành nhiều chunk với ID dạng "doc#chunk".
        # Phần đứng trước dấu # được dùng làm ID của document gốc.
        metadata.setdefault("doc_id", doc.id.split("#", 1)[0])

        record = {
            # Ghép thêm chỉ số để mỗi record luôn có một ID riêng biệt.
            "id": f"{doc.id}-{self._next_index}",
            "doc_id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            # Chuyển nội dung văn bản thành vector số để có thể so sánh độ giống nhau.
            "embedding": self._embedding_fn(doc.content),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Tìm ``top_k`` record giống câu truy vấn nhất trong danh sách đã cho."""
        if top_k <= 0 or not records:
            return []

        # Embed câu truy vấn bằng cùng hàm đã dùng để embed tài liệu.
        query_embedding = self._embedding_fn(query)
        # Tích vô hướng càng lớn thì hai vector được xem là càng giống nhau.
        # Dùng generator để không phải tạo trước toàn bộ danh sách điểm số.
        scored = ((_dot(query_embedding, record["embedding"]), record) for record in records)
        # heapq.nlargest hiệu quả khi chỉ cần lấy một số ít kết quả tốt nhất.
        best = heapq.nlargest(top_k, scored, key=lambda item: item[0])
        # Tạo dict mới để bổ sung điểm mà không sửa record đang được lưu.
        return [{**record, "score": score} for score, record in best]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed nội dung của từng tài liệu rồi lưu lại.

        Với ChromaDB, các trường được tách thành từng danh sách để truyền vào
        ``collection.add``. Với chế độ trong bộ nhớ, record được nối vào
        ``self._store``.
        """
        records = [self._make_record(doc) for doc in docs]
        if not records:
            return

        if self._use_chroma and self._collection is not None:
            # ChromaDB nhận dữ liệu theo từng cột: ids, documents, embeddings, metadata.
            self._collection.add(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[record["metadata"] for record in records],
            )
        else:
            # extend thêm từng record; khác với append là không tạo danh sách lồng nhau.
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Tìm tối đa ``top_k`` tài liệu giống câu truy vấn nhất.

        Ở chế độ trong bộ nhớ, độ tương đồng được tính bằng tích vô hướng giữa
        embedding của câu truy vấn và embedding của từng record đã lưu.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Trả về tổng số chunk hiện đang được lưu."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Tìm kiếm sau khi lọc trước theo metadata (nếu có điều kiện lọc).

        Record chỉ được giữ lại khi tất cả cặp key-value trong ``metadata_filter``
        đều khớp. Sau đó mới tính độ tương đồng để lấy các kết quả tốt nhất.
        """
        if not metadata_filter:
            return self._search_records(query, self._store, top_k)

        # all(...) bảo đảm record phải thỏa mãn đồng thời mọi điều kiện lọc.
        filtered_records = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Xóa tất cả chunk thuộc về một document.

        Trả về ``True`` nếu có ít nhất một chunk bị xóa, ngược lại trả về ``False``.
        """
        if self._use_chroma and self._collection is not None:
            # Tìm ID của các chunk có cùng doc_id rồi yêu cầu ChromaDB xóa chúng.
            matches = self._collection.get(where={"doc_id": doc_id}, include=[])
            ids = matches["ids"]
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        # Với bộ nhớ trong, tạo lại danh sách và loại bỏ các record cần xóa.
        original_size = len(self._store)
        self._store = [
            record for record in self._store if record["metadata"].get("doc_id") != doc_id
        ]
        # Kích thước thay đổi nghĩa là đã tìm thấy và xóa ít nhất một record.
        return len(self._store) != original_size
