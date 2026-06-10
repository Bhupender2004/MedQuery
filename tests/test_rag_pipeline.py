import pytest
from app import create_app
from rag.chunking import Chunker
from rag.embeddings import EmbeddingService
from rag.retrieval import RetrievalService
from unittest.mock import patch, MagicMock

def test_chunker_splitting():
    text = "Line one text string. Line two text string. Line three text string. Line four text string."
    # Test split size and overlaps
    chunks = Chunker.split_text(text, chunk_size=30, chunk_overlap=5)
    assert len(chunks) > 0
    assert all('text' in c for c in chunks)
    assert all('page' in c for c in chunks)

def test_embedding_service_mock():
    # Force mock pipeline
    with patch('rag.embeddings.EmbeddingService.get_model') as mock_model:
        mock_model.return_value = 'mock_service'
        texts = ["Aspirin", "Ibuprofen"]
        vectors = EmbeddingService.embed_texts(texts)
        assert len(vectors) == 2
        assert len(vectors[0]) == 384
        assert isinstance(vectors[0][0], float)

def test_retrieval_service_fallback():
    # Test fallback logic if ChromaDB throws an error
    with patch('chromadb.PersistentClient') as mock_chroma:
        mock_chroma.side_effect = Exception("Chroma offline")
        
        # Retrieval checks standard medical tokens in fallback
        results_aspirin = RetrievalService.retrieve("Is it safe to mix aspirin?")
        assert len(results_aspirin) > 0
        assert any("Aspirin" in r['text'] for r in results_aspirin)
        assert all(r['score'] > 0.0 for r in results_aspirin)
        
        results_ibuprofen = RetrievalService.retrieve("Lisinopril and Ibuprofen safety?")
        assert len(results_ibuprofen) > 0
        assert any("Ibuprofen" in r['text'] or "ACE Inhibitor" in r['text'] for r in results_ibuprofen)
        
        results_unrelated = RetrievalService.retrieve("random queries")
        assert len(results_unrelated) > 0
        assert any("CYP450" in r['text'] or "Standard Practice" in r['text'] for r in results_unrelated)
