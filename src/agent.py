from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        chunks = self.store.search(question, top_k=top_k)
        context = "\n\n".join(
            f"[{index}] {chunk['content']}"
            for index, chunk in enumerate(chunks, start=1)
        )
        if not context:
            context = "Không tìm thấy ngữ cảnh liên quan trong cơ sở tri thức."
        prompt = (
            "Bạn là trợ lý tra cứu quy định đại học. Chỉ trả lời dựa trên "
            "ngữ cảnh được cung cấp, không suy đoán hoặc tự tạo quy định. "
            "Nếu ngữ cảnh không đủ thông tin, hãy nói rõ rằng không tìm thấy "
            "thông tin trong cơ sở tri thức.\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n"
            "TRẢ LỜI:"
        )
        return self.llm_fn(prompt)
