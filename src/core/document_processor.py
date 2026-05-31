import re
from pathlib import Path
from typing import List
from pypdf import PdfReader

class DocumentProcessor:
    @staticmethod
    def load_document(file_path: Path) -> str:
        """Load text from a PDF or TXT file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        suffix = file_path.suffix.lower()
        if suffix == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        elif suffix == ".pdf":
            reader = PdfReader(file_path)
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts).strip()
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Only .txt and .pdf are supported.")

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """Split a text block into individual sentences safely."""
        # Simple sentence splitter using regex
        sentence_endings = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]

    @classmethod
    def smart_chunk_text(cls, text: str, max_chunk_size: int = 3500) -> List[str]:
        """
        Split text into chunks of maximum size, keeping paragraphs intact.
        If a paragraph is too large, it splits it into sentences.
        """
        if not text:
            return []

        # Split text into paragraphs
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If a single paragraph is too large, we must split it by sentences
            if len(para) > max_chunk_size:
                # Flush the current chunk first
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Split large paragraph into sentences and build chunks from sentences
                sentences = cls.split_into_sentences(para)
                for sentence in sentences:
                    if len(sentence) > max_chunk_size:
                        # Hard break if a single sentence is abnormally large
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))
                            current_chunk = []
                            current_length = 0
                        chunks.append(sentence)
                    elif current_length + len(sentence) + 1 > max_chunk_size:
                        chunks.append(" ".join(current_chunk))
                        current_chunk = [sentence]
                        current_length = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_length += len(sentence) + 1
                
                # Flush sentence chunk if any
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_length = 0
            
            # If paragraph fits into current chunk
            elif current_length + len(para) + 2 <= max_chunk_size:
                current_chunk.append(para)
                current_length += len(para) + 2  # account for \n\n
            
            # If paragraph doesn't fit, flush current chunk and start new one
            else:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_length = len(para)

        # Flush final chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks
