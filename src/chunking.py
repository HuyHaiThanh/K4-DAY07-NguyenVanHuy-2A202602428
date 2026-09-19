from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        # Lưu kích thước tối đa của mỗi chunk và số ký tự được lặp lại giữa
        # hai chunk liên tiếp để hạn chế mất ngữ cảnh tại vị trí cắt.
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        # Văn bản rỗng không tạo ra chunk nào.
        if not text:
            return []
        # Nếu toàn bộ văn bản đã vừa một chunk thì không cần chia nhỏ.
        if len(text) <= self.chunk_size:
            return [text]

        # Mỗi lần dịch cửa sổ ít hơn chunk_size một khoảng overlap, nhờ đó
        # phần cuối của chunk trước sẽ xuất hiện lại ở đầu chunk sau.
        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            # Dừng ngay khi cửa sổ hiện tại đã bao phủ hết phần văn bản còn lại.
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        # Luôn yêu cầu ít nhất một câu trong mỗi chunk để bước nhảy không bằng 0.
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        # Chuỗi rỗng không chứa câu nào, vì vậy trả về danh sách rỗng ngay
        # để tránh thực hiện biểu thức chính quy và tạo chunk không cần thiết.
        if not text:
            return []

        # Tách câu tại đúng các dấu phân cách đã mô tả trong docstring:
        # ". ", "! ", "? " hoặc dấu chấm đứng ngay trước ký tự xuống dòng.
        # Positive lookbehind (?<=...) giúp giữ lại dấu câu ở cuối mỗi câu.
        # strip() loại bỏ khoảng trắng thừa; điều kiện cuối bỏ qua phần tử rỗng.
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?]) |(?<=\.)\n", text)
            if sentence.strip()
        ]

        # Gom liên tiếp tối đa `size` câu vào mỗi chunk. Các câu được nối bằng
        # một dấu cách để kết quả dễ đọc và không giữ lại khoảng trắng dư thừa.
        # Chunk cuối có thể chứa ít câu hơn nếu tổng số câu không chia hết.
        size = self.max_sentences_per_chunk
        return [" ".join(sentences[start : start + size]) for start in range(0, len(sentences), size)]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        # Sao chép danh sách do người gọi truyền vào để tránh sửa dữ liệu bên ngoài.
        # Thứ tự separator thể hiện mức ưu tiên: đoạn văn, dòng, câu, từ, ký tự.
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        # Điểm vào công khai: bỏ qua văn bản rỗng rồi bắt đầu với toàn bộ
        # danh sách dấu phân cách theo thứ tự ưu tiên.
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Bảo đảm kích thước hợp lệ ngay cả khi chunk_size được truyền là 0 hoặc âm.
        size = max(1, self.chunk_size)
        if len(current_text) <= size:
            return [current_text]

        # Khi hết separator, cắt cứng theo số ký tự để mọi chunk vẫn đúng kích thước.
        if not remaining_separators:
            return [current_text[i : i + size] for i in range(0, len(current_text), size)]

        separator = remaining_separators[0]
        rest = remaining_separators[1:]
        # Chuỗi rỗng là mức ưu tiên cuối cùng, tương ứng với việc cắt theo ký tự.
        if not separator:
            return [current_text[i : i + size] for i in range(0, len(current_text), size)]
        # Nếu separator hiện tại không tồn tại, thử separator ưu tiên thấp hơn.
        if separator not in current_text:
            return self._split(current_text, rest)

        # Giữ separator ở cuối mỗi mảnh để khi ghép lại nội dung ban đầu không đổi.
        pieces: list[str] = []
        start = 0
        separator_length = len(separator)
        while True:
            index = current_text.find(separator, start)
            if index < 0:
                if start < len(current_text):
                    pieces.append(current_text[start:])
                break
            end = index + separator_length
            pieces.append(current_text[start:end])
            start = end

        # Những mảnh còn quá dài tiếp tục được chia bằng separator kế tiếp.
        split_pieces: list[str] = []
        for piece in pieces:
            if len(piece) <= size:
                split_pieces.append(piece)
            else:
                split_pieces.extend(self._split(piece, rest))

        # Ghép các mảnh nhỏ liền kề cho tới sát giới hạn, tránh sinh quá nhiều
        # chunk vụn nhưng vẫn không vượt quá chunk_size.
        chunks: list[str] = []
        current = ""
        for piece in split_pieces:
            if current and len(current) + len(piece) > size:
                chunks.append(current)
                current = piece
            else:
                current += piece
        if current:
            chunks.append(current)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    """Tính tích vô hướng của hai vector trên phần tử có cùng vị trí."""
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # Tính tích vô hướng và bình phương độ dài trong cùng một vòng lặp để
    # tránh phải duyệt hai vector nhiều lần.
    dot = norm_a = norm_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        norm_a += a * a
        norm_b += b * b

    # Cosine similarity không xác định với vector 0; quy ước trả về 0.0.
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / math.sqrt(norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # Khởi tạo ba chiến lược với cùng giới hạn kích thước khi chiến lược hỗ trợ.
        # SentenceChunker dùng số câu mặc định vì nó không chia theo số ký tự.
        strategies = (
            ("fixed_size", FixedSizeChunker(chunk_size=chunk_size)),
            ("by_sentences", SentenceChunker()),
            ("recursive", RecursiveChunker(chunk_size=chunk_size)),
        )

        # Chạy từng chiến lược một lần và giữ lại kết quả để vừa tính thống kê,
        # vừa trả về chunks mà không phải thực hiện chia văn bản lần thứ hai.
        comparison = {}
        for name, chunker in strategies:
            chunks = chunker.chunk(text)
            count = len(chunks)
            comparison[name] = {
                "count": count,
                # Chặn phép chia cho 0 khi đầu vào rỗng và không có chunk nào.
                "avg_length": sum(map(len, chunks)) / count if count else 0.0,
                "chunks": chunks,
            }
        return comparison
