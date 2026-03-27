"""Document processing utilities for FinanceRAG."""

import os
from pathlib import Path
from typing import List, Optional
import structlog

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
)

from src.config.settings import get_settings

logger = structlog.get_logger()


class DocumentProcessor:
    """Process and chunk documents for RAG pipeline."""
    
    def __init__(self):
        self.settings = get_settings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Supported file extensions and their loaders
        self.loaders = {
            ".txt": TextLoader,
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".md": UnstructuredMarkdownLoader,
        }
    
    def load_document(self, file_path: str) -> List[Document]:
        """Load a single document from file path."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = path.suffix.lower()
        
        if extension not in self.loaders:
            raise ValueError(f"Unsupported file type: {extension}")
        
        loader_class = self.loaders[extension]
        
        try:
            loader = loader_class(str(path))
            documents = loader.load()
            
            # Add metadata
            for doc in documents:
                doc.metadata["source"] = str(path)
                doc.metadata["filename"] = path.name
                doc.metadata["file_type"] = extension
            
            logger.info("document_loaded", file=path.name, pages=len(documents))
            return documents
            
        except Exception as e:
            logger.error("document_load_error", file=path.name, error=str(e))
            raise
    
    def load_directory(self, directory_path: str) -> List[Document]:
        """Load all supported documents from a directory."""
        path = Path(directory_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        all_documents = []
        
        for extension in self.loaders.keys():
            for file_path in path.glob(f"*{extension}"):
                try:
                    docs = self.load_document(str(file_path))
                    all_documents.extend(docs)
                except Exception as e:
                    logger.warning("skip_file", file=file_path.name, error=str(e))
                    continue
        
        logger.info("directory_loaded", 
                   directory=directory_path, 
                   total_documents=len(all_documents))
        
        return all_documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        chunks = self.text_splitter.split_documents(documents)
        
        # Add chunk metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunk_size"] = len(chunk.page_content)
        
        logger.info("documents_chunked", 
                   input_docs=len(documents), 
                   output_chunks=len(chunks))
        
        return chunks
    
    def process_documents(self, source_path: str) -> List[Document]:
        """Load and chunk documents from file or directory."""
        path = Path(source_path)
        
        if path.is_file():
            documents = self.load_document(source_path)
        elif path.is_dir():
            documents = self.load_directory(source_path)
        else:
            raise ValueError(f"Invalid path: {source_path}")
        
        chunks = self.chunk_documents(documents)
        
        return chunks


# Convenience function
def process_documents(source_path: str) -> List[Document]:
    """Process documents from a file or directory path."""
    processor = DocumentProcessor()
    return processor.process_documents(source_path)
