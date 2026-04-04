import chromadb
import uuid
from chromadb.config import Settings

class VectorService:
    def __init__(self, persist_directory: str = "/tmp/chroma"):
        # Initialize the persistent client (ephemeral on Vercel)
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="call_transcripts")
    
    def add_transcript(self, transcript: str, metadata: dict):
        """Adds a transcript and its metadata to the vector database."""
        doc_id = str(uuid.uuid4())
        self.collection.add(
            documents=[transcript],
            ids=[doc_id],
            metadatas=[metadata]
        )
        return doc_id
    
    def search_similar(self, query: str, n_results: int = 3):
        """Searches for similar transcripts."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
