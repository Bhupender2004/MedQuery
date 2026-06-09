"""
MedQuery RAG Chunking Module

Partitioning long medical documents into semantic slices with overlaps.
"""

class Chunker:
    """
    Implements character and word-based splitting rules to split medical texts.
    """

    @staticmethod
    def split_text(text, chunk_size=800, chunk_overlap=150):
        """
        Splits raw text strings into overlapping dictionary chunks.
        
        Args:
            text (str): Raw string content.
            chunk_size (int): Max character length of single chunk.
            chunk_overlap (int): Overlap character length between sequential chunks.
            
        Returns:
            list: List of dicts representing segment entries.
                  Example: [{"text": "...", "page": 1}]
        """
        if not text or not text.strip():
            return []

        chunks = []
        text_len = len(text)
        start_pos = 0

        # Edge safety checks
        if chunk_size <= 0:
            chunk_size = 800
        if chunk_overlap >= chunk_size or chunk_overlap < 0:
            chunk_overlap = int(chunk_size * 0.15)

        while start_pos < text_len:
            end_pos = min(start_pos + chunk_size, text_len)

            # Look for clean text boundary (like space or sentence end)
            if end_pos < text_len:
                # Seek backwards looking for space inside a 100-character margin
                boundary_idx = text.rfind(' ', end_pos - 100, end_pos)
                if boundary_idx != -1:
                    end_pos = boundary_idx

            segment_text = text[start_pos:end_pos].strip()
            if segment_text:
                chunks.append({
                    'text': segment_text,
                    'page': 1  # Default fallback page tracker
                })

            start_pos = end_pos - chunk_overlap
            # Prevent infinite loops in sliding window indices
            if start_pos >= text_len or (end_pos - start_pos) <= 0:
                break

        return chunks
