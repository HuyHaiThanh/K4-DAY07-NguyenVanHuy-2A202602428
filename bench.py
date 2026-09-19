"""Live benchmark entrypoint for the Lab 7 NEU tuition corpus.

Examples:
    python bench.py
    python bench.py --strategy fixed --query 3
    python bench.py --strategy recursive --provider local --output ket_qua_benchmark.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts.run_benchmark import CORPUS_DIR, heading_chunks, parse_front_matter
from src import (
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    LocalEmbedder,
    OpenAIEmbedder,
    RecursiveChunker,
    SentenceChunker,
    _mock_embed,
)


QUERIES = [
    {
        "query": "Học phí hệ đại học chính quy đại trà cho khóa 68 trong năm học 2026-2027 là bao nhiêu tiền mỗi tín chỉ?",
        "gold": "880.000 đồng/tín chỉ.",
    },
    {
        "query": "Sinh viên IBD@NEU khóa 22, đợt tháng 8/2026, phải nộp học phí trước thời hạn nào và bằng phương thức nào?",
        "gold": "Chuyển khoản trước 17:00 ngày 21/08/2026 vào tài khoản 2116678989.",
    },
    {
        "query": "Sinh viên thuộc diện chính sách cần nộp hồ sơ miễn, giảm học phí đợt 2 năm học 2025-2026 ở đâu và trong thời gian nào?",
        "gold": "Phòng 302 Nhà A1, từ 02/03/2026 đến hết 20/03/2026.",
        "metadata_filter": {"audience": "student"},
    },
    {
        "query": "Theo tài liệu tham khảo về học phí NEU 2026, công thức tham khảo để tính học phí là gì?",
        "gold": "Học phí = số tín chỉ đăng ký × đơn giá mỗi tín chỉ.",
    },
    {
        "query": "Trong năm học 2026-2027, chương trình Khoa học dữ liệu và Trí tuệ nhân tạo có mức học phí bao nhiêu?",
        "gold": "54 triệu đồng/năm cho cả Data Science và AI.",
    },
]


def build_chunker(strategy: str, chunk_size: int):
    if strategy == "fixed":
        overlap = min(50, max(0, chunk_size - 1))
        return FixedSizeChunker(chunk_size=chunk_size, overlap=overlap).chunk
    if strategy == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3).chunk
    if strategy == "recursive":
        return RecursiveChunker(chunk_size=chunk_size).chunk
    return lambda text: heading_chunks(text, chunk_size)


def load_documents(strategy: str, chunk_size: int) -> list[Document]:
    chunk = build_chunker(strategy, chunk_size)
    documents: list[Document] = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        metadata, content = parse_front_matter(path)
        doc_id = metadata.get("doc_id", path.stem)
        for index, part in enumerate(chunk(content)):
            documents.append(
                Document(
                    id=f"{doc_id}#{index:03d}",
                    content=part,
                    metadata={
                        **metadata,
                        "doc_id": doc_id,
                        "chunk_index": index,
                        "chunking_strategy": strategy,
                    },
                )
            )
    return documents


def select_embedder(provider: str):
    if provider == "openai":
        return OpenAIEmbedder()
    if provider == "local":
        return LocalEmbedder()
    return _mock_embed


def run(strategy: str, chunk_size: int, provider: str, query_number: int | None) -> str:
    embedder = select_embedder(provider)
    documents = load_documents(strategy, chunk_size)
    store = EmbeddingStore(
        collection_name=f"neu_live_{strategy}_{chunk_size}",
        embedding_fn=embedder,
    )
    store.add_documents(documents)

    selected = (
        [(query_number, QUERIES[query_number - 1])]
        if query_number is not None
        else list(enumerate(QUERIES, start=1))
    )
    lines = [
        "BENCHMARK LAB 7 — HỌC PHÍ NEU",
        f"Strategy: {strategy}; chunk_size: {chunk_size}; provider: {provider}",
        f"Documents: {len(list(CORPUS_DIR.glob('*.md')))}; chunks: {len(documents)}",
        "",
    ]
    for number, item in selected:
        results = store.search_with_filter(
            item["query"],
            top_k=3,
            metadata_filter=item.get("metadata_filter"),
        )
        lines.extend([f"Q{number}: {item['query']}", f"Gold answer: {item['gold']}"])
        if item.get("metadata_filter"):
            lines.append(f"Metadata filter: {item['metadata_filter']}")
        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]
            preview = " ".join(result["content"].split())[:240]
            lines.append(
                f"  {rank}. score={result['score']:.6f} "
                f"doc={metadata.get('doc_id')} chunk={metadata.get('chunk_index')}"
            )
            lines.append(f"     {preview}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the shared Lab 7 benchmark")
    parser.add_argument(
        "--strategy",
        choices=("fixed", "sentence", "recursive", "heading"),
        default="recursive",
    )
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--provider", choices=("mock", "local", "openai"), default="local")
    parser.add_argument("--query", type=int, choices=range(1, 6))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rendered = run(args.strategy, args.chunk_size, args.provider, args.query)
    print(rendered, end="")
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
