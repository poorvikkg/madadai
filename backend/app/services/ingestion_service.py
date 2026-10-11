import os
import re
import logging
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader

logger = logging.getLogger(__name__)

class DocumentIngestionService:
    @staticmethod
    def extract_text_from_file(file_path: str, file_type: str) -> List[Tuple[str, int]]:
        """
        Extract text from file.
        Returns a list of tuples: (extracted_text, page_number)
        """
        results: List[Tuple[str, int]] = []
        file_type = file_type.lower().replace(".", "")

        if file_type == "pdf":
            try:
                reader = PdfReader(file_path)
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    cleaned = DocumentIngestionService.clean_text(text)
                    if cleaned:
                        results.append((cleaned, idx + 1))
            except Exception as e:
                logger.error(f"Error reading PDF {file_path}: {e}")
                raise ValueError(f"Failed to parse PDF: {str(e)}")
        
        elif file_type in ["txt", "md", "markdown"]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                    cleaned = DocumentIngestionService.clean_text(text)
                    if cleaned:
                        results.append((cleaned, 1))
            except Exception as e:
                logger.error(f"Error reading text/markdown file {file_path}: {e}")
                raise ValueError(f"Failed to parse document: {str(e)}")
        else:
            raise ValueError(f"Unsupported document format: {file_type}. Supported: PDF, TXT, MD.")

        return results

    @staticmethod
    def clean_text(text: str) -> str:
        """Cleans and normalizes document text."""
        if not text:
            return ""
        # Normalize whitespace and excessive line breaks
        text = re.sub(r'\r\n|\r', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    @staticmethod
    def chunk_text(
        text: str, 
        chunk_size: int = 500, 
        overlap: int = 100, 
        page_number: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Sliding window chunking with word boundary protection.
        """
        if not text:
            return []

        words = text.split()
        if not words:
            return []

        chunks: List[Dict[str, Any]] = []
        step = max(1, chunk_size - overlap)

        for i in range(0, len(words), step):
            chunk_words = words[i : i + chunk_size]
            chunk_str = " ".join(chunk_words)
            chunks.append({
                "content": chunk_str,
                "page_number": page_number,
                "word_count": len(chunk_words),
                "start_word_index": i
            })
            if i + chunk_size >= len(words):
                break

        return chunks

ingestion_service = DocumentIngestionService()
