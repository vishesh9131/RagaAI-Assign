import os
import pickle
from typing import List, Dict, Optional, Any
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# ---------------------------------------------------------------------------
# Compatibility Patch: sentence-transformers <=4.1.0 expects `cached_download`
# at the top-level of huggingface_hub, but the function was moved/removed in
# newer versions (>=0.31). We add a simple shim mapping to `hf_hub_download`.
# ---------------------------------------------------------------------------
try:
    import huggingface_hub as _hf
    if not hasattr(_hf, "cached_download"):
        def _cached_download(*args, **kwargs):
            """Mimic removed huggingface_hub.cached_download API using hf_hub_download.
            Handles signature used by sentence_transformers.snapshot_download which
            calls cached_download(url=..., cache_dir=..., force_download=..., proxies=..., resume_download=..., etag_timeout=...)
            """
            # Allow positional url or keyword url
            url = kwargs.pop("url", None)
            if url is None and len(args) > 0:
                url, *args = args
            cache_dir = kwargs.pop("cache_dir", None)
            force_download = kwargs.pop("force_download", False)
            proxies = kwargs.pop("proxies", None)
            etag_timeout = kwargs.pop("etag_timeout", 10)
            resume_download = kwargs.pop("resume_download", None)  # ignored
            # Quick heuristic parse of HF URL pattern
            if url and url.startswith("https://huggingface.co/") and "/resolve/" in url:
                from urllib.parse import urlparse
                path = url.split("https://huggingface.co/")[1]
                repo_id, rest = path.split("/resolve/", 1)
                revision, filename = rest.split("/", 1)
                return _hf.hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    revision=revision,
                    cache_dir=cache_dir,
                    force_download=force_download,
                    proxies=proxies,
                    etag_timeout=etag_timeout,
                )
            else:
                # Fallback: direct HTTP GET with requests
                import requests, tempfile, os
                target_dir = cache_dir or tempfile.gettempdir()
                os.makedirs(target_dir, exist_ok=True)
                local_path = os.path.join(target_dir, os.path.basename(url))
                if force_download or not os.path.exists(local_path):
                    with requests.get(url, stream=True, proxies=proxies, timeout=etag_timeout) as r:
                        r.raise_for_status()
                        with open(local_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                return local_path
        _hf.cached_download = _cached_download
except Exception as _patch_err:
    # If patching fails, we log but continue – HuggingFaceEmbeddings may fail later and raise clearer error
    print(f"[RetrieverAgent] Warning: Failed to patch huggingface_hub.cached_download: {_patch_err}")

# Default model for embeddings. Can be changed.
DEFAULT_EMBEDDING_MODEL = "thenlper/gte-small"  # compact, sentence-transformers compatible

# Ordered fallbacks – will be tried one-by-one until one loads correctly.
_CANDIDATE_EMBED_MODELS = [
    "thenlper/gte-small",
    "all-MiniLM-L6-v2",
    "paraphrase-MiniLM-L6-v2",
]

DEFAULT_FAISS_INDEX_PATH = "faiss_index_store" # Directory to save FAISS index and documents

class RetrieverAgent:
    """
    An agent that stores and searches information using text embeddings and a FAISS vector store.
    """
    
    def __init__(self, 
                 model_name: str = DEFAULT_EMBEDDING_MODEL, 
                 index_path: str = DEFAULT_FAISS_INDEX_PATH,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 100):
        """
        Initialize the Retriever Agent.

        Args:
            model_name: Name of the HuggingFace sentence-transformer model to use for embeddings.
            index_path: Path to the directory where the FAISS index and documents will be stored/loaded.
            chunk_size: Size of text chunks for splitting documents.
            chunk_overlap: Overlap between text chunks.
        """
        self.index_path = index_path
        self.faiss_file = os.path.join(index_path, "index.faiss")
        self.documents_file = os.path.join(index_path, "documents.pkl") # To store original docs with IDs

        print(f"Initializing embeddings with model: {model_name}")
        self.embeddings = None
        for candidate in _CANDIDATE_EMBED_MODELS:
            print(f"[RetrieverAgent] Attempting to load embedding model: {candidate}")
            try:
                self.embeddings = HuggingFaceEmbeddings(model_name=candidate)
                print(f"[RetrieverAgent] Successfully loaded '{candidate}'.")
                break
            except ValueError as ve:
                # Detect corrupted local cache path and delete it, then retry once
                msg = str(ve)
                if "Unrecognized model" in msg and "cache" in msg:
                    import re, shutil
                    m = re.search(r"(/[^ ]+sentence_transformers_[^ '\"]+)", msg)
                    if m:
                        bad_path = m.group(1)
                        if os.path.isdir(bad_path):
                            print(f"[RetrieverAgent] Removing corrupted cache dir {bad_path} and retrying.")
                            shutil.rmtree(bad_path, ignore_errors=True)
                            try:
                                self.embeddings = HuggingFaceEmbeddings(model_name=candidate)
                                print(f"[RetrieverAgent] Successfully loaded '{candidate}' after cache reset.")
                                break
                            except Exception:
                                pass
                print(f"[RetrieverAgent] Could not load '{candidate}': {ve}")
            except Exception as e:
                print(f"[RetrieverAgent] Could not load '{candidate}': {e}")

        if self.embeddings is None:
            print("[RetrieverAgent] All HuggingFace embedding models failed to load. Falling back to SimpleHashEmbeddings (deterministic hash-based vectors). Accuracy will be lower, but the system will remain functional.")

            import numpy as _np, hashlib as _hashlib

            class SimpleHashEmbeddings:
                """A minimal, deterministic embeddings fallback using hashing.
                NOT suitable for production-quality semantic search, but avoids
                hard runtime failures when no transformer models are available.
                Each text is mapped to a fixed-length vector via seeded RNG
                based on the MD5 hash of the text.
                """

                def __init__(self, dim: int = 384):
                    self.dim = dim
                    self.model_name = "simple-hash-embeddings"  # Required for compatibility

                def _hash_to_vector(self, text: str):
                    seed_bytes = _hashlib.md5(text.encode("utf-8")).digest()
                    seed_int = int.from_bytes(seed_bytes, "little")
                    rng = _np.random.default_rng(seed_int)
                    # Generate deterministic float32 vector between 0 and 1
                    return rng.random(self.dim, dtype=_np.float32).tolist()

                def embed_documents(self, texts):
                    """Embed a list of documents."""
                    return [self._hash_to_vector(t) for t in texts]

                def embed_query(self, text):
                    """Embed a query string."""
                    return self._hash_to_vector(text)

            self.embeddings = SimpleHashEmbeddings()
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        
        self.vector_store: Optional[FAISS] = None
        self.stored_documents: Dict[str, Document] = {} # Store text by ID for context
        self._load_vector_store()

    def _create_dir_if_not_exists(self):
        if not os.path.exists(self.index_path):
            os.makedirs(self.index_path)

    def _load_vector_store(self):
        """Loads the FAISS index and documents from disk if they exist."""
        self._create_dir_if_not_exists()
        try:
            if os.path.exists(self.faiss_file) and os.path.exists(self.documents_file):
                print(f"Loading FAISS index from {self.faiss_file}")
                self.vector_store = FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
                print(f"Loading documents from {self.documents_file}")
                with open(self.documents_file, "rb") as f:
                    self.stored_documents = pickle.load(f)
                print(f"Successfully loaded {len(self.stored_documents)} documents and FAISS index.")
            else:
                print("No existing FAISS index found. A new one will be created upon adding documents.")
                # Initialize an empty store if no documents are to be added immediately
                # self.vector_store = FAISS.from_texts(["_init_placeholder_"], self.embeddings) # Temp init
                # self.vector_store.delete([self.vector_store.index_to_docstore_id[0]]) # Remove placeholder
        except Exception as e:
            print(f"Error loading FAISS index or documents: {e}. A new store might be created.")
            # Potentially corrupted files, allow to proceed with a new store
            self.vector_store = None 
            self.stored_documents = {}


    def _save_vector_store(self):
        """Saves the FAISS index and documents to disk."""
        self._create_dir_if_not_exists()
        if self.vector_store:
            print(f"Saving FAISS index to {self.faiss_file}")
            self.vector_store.save_local(self.index_path)
            print(f"Saving documents to {self.documents_file}")
            with open(self.documents_file, "wb") as f:
                pickle.dump(self.stored_documents, f)
            print("FAISS index and documents saved.")
        else:
            print("No vector store to save.")

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[str]:
        """
        Adds texts to the vector store. Texts are split into chunks.

        Args:
            texts: A list of text strings to add.
            metadatas: Optional list of dictionaries, one metadata object per text.

        Returns:
            A list of document IDs for the added texts.
        """
        if not texts:
            return []

        documents_to_add = []
        doc_ids = []

        for i, text_content in enumerate(texts):
            # Create LangChain Document objects
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            # Ensure basic source if not provided
            if 'source' not in metadata:
                 metadata['source'] = f"text_input_{len(self.stored_documents) + i}"
            
            # Split the document
            chunks = self.text_splitter.split_text(text_content)
            for j, chunk in enumerate(chunks):
                # Create a unique ID for each chunk, but store original text by its primary ID
                # We use the metadata 'source' as a way to group chunks from the same original text.
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = j 
                # chunk_metadata['original_doc_id'] = metadata['source'] # Link back to original document id

                doc = Document(page_content=chunk, metadata=chunk_metadata)
                documents_to_add.append(doc)
        
        if not documents_to_add:
            print("No processable documents created from input texts.")
            return []

        if self.vector_store is None:
            print("Creating new FAISS vector store.")
            self.vector_store = FAISS.from_documents(documents_to_add, self.embeddings)
        else:
            print(f"Adding {len(documents_to_add)} document chunks to existing FAISS vector store.")
            # FAISS.add_documents returns list of new docstore_ids.
            new_doc_ids = self.vector_store.add_documents(documents_to_add)
            doc_ids.extend(new_doc_ids) # These are IDs for chunks

        # Storing the original texts for context or lookup if needed (mainly for whole text, not chunks)
        # The actual searchable units in FAISS are chunks.
        # For simplicity, we're not separately storing original full texts here, relying on chunk metadata.
        # If you needed to retrieve the *full original text* based on a chunk match,
        # you would need a more elaborate document storage mechanism.
        # For now, the source in metadata is the main link.

        self._save_vector_store()
        print(f"Successfully added {len(texts)} original texts (split into {len(documents_to_add)} chunks).")
        # The returned IDs are from FAISS for the chunks. For user convenience, maybe return original text identifiers
        # but FAISS operates on chunk IDs.
        return doc_ids # these are FAISS internal IDs for the added document chunks

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a similarity search in the vector store.

        Args:
            query: The text query to search for.
            k: The number of top similar documents to retrieve.

        Returns:
            A list of dictionaries, where each dictionary contains 
            'content' (the text chunk) and 'metadata' and 'score'.
        """
        if not self.vector_store:
            print("Vector store not initialized. Add documents first.")
            return []
        
        print(f"Searching for: '{query}' (top {k} results)")
        try:
            # similarity_search_with_score returns (Document, score) tuples
            results_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results_with_scores:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score) # Score is often distance, lower is better for FAISS L2
                })
            return formatted_results
        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def get_document_count(self) -> int:
        """Returns the total number of document chunks in the store."""
        if self.vector_store and self.vector_store.index:
            return self.vector_store.index.ntotal
        return 0

    def list_all_chunk_sources(self) -> List[str]:
        """Lists all unique sources from the metadata of stored chunks."""
        if not self.vector_store or not self.vector_store.docstore:
            return []
        
        sources = set()
        # Iterate through the docstore if available (FAISS.docstore._dict)
        # This is an internal structure, might change. A more robust way is needed if docstore API is not public.
        # For now, assuming we want to see sources from metadata of stored chunks.
        
        # FAISS.index_to_docstore_id is a mapping from FAISS index to internal docstore ID
        # FAISS.docstore.search(id) gets the document.
        if hasattr(self.vector_store, 'index_to_docstore_id') and hasattr(self.vector_store, 'docstore'):
            all_doc_ids = list(self.vector_store.index_to_docstore_id.values())
            for doc_id in all_doc_ids:
                doc = self.vector_store.docstore.search(doc_id)
                if doc and doc.metadata and 'source' in doc.metadata:
                    sources.add(doc.metadata['source'])
        return sorted(list(sources))

if __name__ == '__main__':
    # Basic Example Usage:
    print("--- Retriever Agent Example ---")
    # Create an agent (will load or create 'faiss_index_store' in the current directory)
    agent = RetrieverAgent(index_path="my_retriever_data") 

    print(f"Initial document chunk count: {agent.get_document_count()}")
    print(f"Initial sources: {agent.list_all_chunk_sources()}")

    # Add some texts
    texts_to_add = [
        "The quick brown fox jumps over the lazy dog.",
        "Paris is the capital of France.",
        "The Eiffel Tower is a famous landmark in Paris.",
        "Artificial intelligence is a rapidly growing field.",
        "LangChain provides tools for building applications with LLMs."
    ]
    metadatas_to_add = [
        {"source": "common_phrases"},
        {"source": "geography_facts", "topic": "europe"},
        {"source": "landmark_facts", "related_to": "Paris"},
        {"source": "tech_trends_2024", "category": "AI"},
        {"source": "llm_tools"}
    ]
    
    # Check if we need to add new documents (e.g., if store is empty or specific sources are missing)
    if not agent.list_all_chunk_sources() or "common_phrases" not in agent.list_all_chunk_sources():
        print("\nAdding new documents...")
        added_ids = agent.add_texts(texts_to_add, metadatas_to_add)
        print(f"IDs of added document chunks (FAISS internal): {added_ids}")
    else:
        print("\nDocuments from example sources already seem to exist in the store.")

    print(f"Document chunk count after potential add: {agent.get_document_count()}")
    print(f"Sources after potential add: {agent.list_all_chunk_sources()}")

    # Perform a search
    print("\nSearching for 'capital city of France'...")
    search_results_france = agent.search("capital city of France", k=2)
    for result in search_results_france:
        print(f"  Content: {result['content'][:100]}...")
        print(f"  Metadata: {result['metadata']}")
        print(f"  Score: {result['score']:.4f}\n")

    print("Searching for 'machine learning tools'...")
    search_results_ml = agent.search("machine learning tools", k=2)
    for result in search_results_ml:
        print(f"  Content: {result['content'][:100]}...")
        print(f"  Metadata: {result['metadata']}")
        print(f"  Score: {result['score']:.4f}\n")
        
    print("--- End of Example ---")