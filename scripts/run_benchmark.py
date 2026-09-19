"""Run the Lab 7 retrieval benchmark on the cleaned NEU tuition corpus."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import (  # noqa: E402
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    LocalEmbedder,
    RecursiveChunker,
    SentenceChunker,
    _mock_embed,
)

CORPUS_DIR = ROOT / "data" / "hoc-phi"

BENCHMARKS = [
    {
        "query": "Học phí chương trình chuẩn của khóa 68 năm học 2026-2027 là bao nhiêu một tín chỉ?",
        "gold_doc_id": "neu-tuition-decision-985-2026-2027",
        "gold_answer": "Khóa 68 đóng 880.000 đồng mỗi tín chỉ.",
        "evidence_terms": ["khóa 68", "880.000"],
        "metadata_filter": {
            "audience": "student",
            "category": "tuition",
            "document_version": "2026-2027",
        },
    },
    {
        "query": "Sinh viên IBD khóa 22 nhập học chuyên ngành Ngân hàng tài chính phải đóng bao nhiêu?",
        "gold_doc_id": "neu-tuition-payment-ibd-2026",
        "gold_answer": "Mức học phí là 74.800.000 đồng, gồm học phí kỳ 1 và hai môn cơ sở.",
        "evidence_terms": ["ngân hàng tài chính", "74.800.000"],
    },
    {
        "query": "Hạn nộp hồ sơ miễn giảm học phí đợt 2 năm học 2025-2026 là ngày nào?",
        "gold_doc_id": "neu-tuition-waiver-2025-2026",
        "gold_answer": "Hồ sơ được nhận từ 02/03/2026 đến hết 20/03/2026.",
        "evidence_terms": ["02/03/2026", "20/03/2026"],
    },
    {
        "query": "Các bước thanh toán học phí trực tuyến qua cổng NEU là gì?",
        "gold_doc_id": "neu-tuition-payment-guide-2020",
        "gold_answer": "Đăng nhập cổng tương ứng, mở Tài chính sinh viên, kiểm tra nợ phí, chọn thanh toán online hoặc truy cập e-bills.vn/pay/neu và tra cứu bằng mã sinh viên.",
        "evidence_terms": ["tài chính sinh viên", "e-bills.vn/pay/neu"],
    },
    {
        "query": "Sinh viên học tiếng Anh cấp độ 1 tháng 9/2024 phải nộp bao nhiêu và trước thời hạn nào?",
        "gold_doc_id": "neu-tuition-ibd-english-level1-2024",
        "gold_answer": "Học phí là 23.000.000 đồng, hạn nộp hết ngày 11/09/2024 và gửi chứng từ trước 17:00 cùng ngày.",
        "evidence_terms": ["23.000.000", "11/09/2024"],
        "metadata_filter": {
            "audience": "student",
            "department": "international-programs",
            "document_version": "2024-2025",
        },
    },
]


def parse_front_matter(path: Path) -> tuple[dict[str, str], str]:
    """Parse the simple scalar YAML front matter used by this corpus."""
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        return {}, raw.strip()
    try:
        header, content = raw[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError(f"Invalid front matter in {path}") from exc

    metadata: dict[str, str] = {}
    for line in header.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"Invalid metadata line in {path}: {line!r}")
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, content.strip()


def heading_chunks(text: str, chunk_size: int) -> list[str]:
    """Keep Markdown headings with their section, recursively splitting long sections."""
    raw_sections = re.split(r"(?=^#{1,6}\s)", text, flags=re.MULTILINE)
    sections: list[str] = []
    pending_heading = ""
    for raw_section in raw_sections:
        section = raw_section.strip()
        if not section:
            continue
        if len(section) < 80 and section.startswith("#"):
            pending_heading = f"{pending_heading}\n{section}".strip()
            continue
        sections.append(f"{pending_heading}\n{section}".strip())
        pending_heading = ""
    if pending_heading:
        if sections:
            sections[-1] = f"{sections[-1]}\n{pending_heading}"
        else:
            sections.append(pending_heading)
    recursive = RecursiveChunker(chunk_size=chunk_size)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        chunks.extend(recursive.chunk(section))
    return chunks


def make_chunker(name: str, chunk_size: int) -> Callable[[str], list[str]]:
    if name == "fixed":
        return FixedSizeChunker(chunk_size=chunk_size, overlap=min(50, chunk_size // 5)).chunk
    if name == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3).chunk
    if name == "recursive":
        return RecursiveChunker(chunk_size=chunk_size).chunk
    return lambda text: heading_chunks(text, chunk_size)


def load_chunked_documents(strategy: str, chunk_size: int) -> list[Document]:
    chunk = make_chunker(strategy, chunk_size)
    documents: list[Document] = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        metadata, content = parse_front_matter(path)
        doc_id = metadata.get("doc_id", path.stem)
        for index, part in enumerate(chunk(content)):
            chunk_metadata = {**metadata, "chunk_index": index, "file_path": str(path.relative_to(ROOT))}
            documents.append(
                Document(id=f"{doc_id}#{index:03d}", content=part, metadata=chunk_metadata)
            )
    return documents


def choose_embedder(provider: str):
    if provider == "local":
        try:
            return LocalEmbedder()
        except Exception as exc:
            print(f"Local embedder unavailable ({exc}); falling back to mock embeddings.", file=sys.stderr)
    return _mock_embed


def run(strategy: str, chunk_size: int, provider: str) -> dict:
    documents = load_chunked_documents(strategy, chunk_size)
    embedder = choose_embedder(provider)
    store = EmbeddingStore(collection_name=f"neu_tuition_{strategy}", embedding_fn=embedder)
    store.add_documents(documents)

    rows = []
    for item in BENCHMARKS:
        metadata_filter = item.get("metadata_filter")
        results = store.search_with_filter(
            item["query"], top_k=3, metadata_filter=metadata_filter
        )
        retrieved_ids = [result["metadata"].get("doc_id") for result in results]
        retrieved_text = "\n".join(result["content"].lower() for result in results)
        contains_evidence = all(term.lower() in retrieved_text for term in item["evidence_terms"])
        rows.append(
            {
                **item,
                "top3_contains_gold": item["gold_doc_id"] in retrieved_ids,
                "top3_contains_evidence": contains_evidence,
                "results": [
                    {
                        "rank": rank,
                        "score": round(float(result["score"]), 4),
                        "doc_id": result["metadata"].get("doc_id"),
                        "chunk_index": result["metadata"].get("chunk_index"),
                        "preview": " ".join(result["content"].split())[:220],
                    }
                    for rank, result in enumerate(results, start=1)
                ],
            }
        )

    return {
        "strategy": strategy,
        "chunk_size": chunk_size,
        "embedding_backend": getattr(embedder, "_backend_name", type(embedder).__name__),
        "document_count": len(list(CORPUS_DIR.glob("*.md"))),
        "chunk_count": len(documents),
        "top3_recall": sum(row["top3_contains_evidence"] for row in rows),
        "queries": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", choices=("fixed", "sentence", "recursive", "heading"), default="heading")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--provider", choices=("mock", "local"), default="local")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = run(args.strategy, args.chunk_size, args.provider)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
