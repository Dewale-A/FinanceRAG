#!/usr/bin/env python3
"""
FinanceRAG - Production-grade RAG system for financial document Q&A

Usage:
    # Ingest documents
    python main.py ingest --source ./sample_docs
    
    # Query (interactive)
    python main.py query
    
    # Query (single question)
    python main.py query --question "What is the minimum CET1 ratio under Basel III?"
    
    # Start API server
    python main.py serve
    
    # Get stats
    python main.py stats
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def cmd_ingest(args):
    """Ingest documents into the vector store."""
    from src.tools.document_processor import DocumentProcessor
    from src.tools.vector_store import get_vector_store_manager
    
    print(f"\n📄 Ingesting documents from: {args.source}")
    print("=" * 60)
    
    processor = DocumentProcessor()
    vector_store = get_vector_store_manager()
    
    try:
        chunks = processor.process_documents(args.source)
        
        if not chunks:
            print("❌ No documents found to process")
            return
        
        ids = vector_store.add_documents(chunks)
        
        source_files = set(chunk.metadata.get("filename", "") for chunk in chunks)
        
        print(f"\n✅ Ingestion complete!")
        print(f"   Documents processed: {len(source_files)}")
        print(f"   Chunks created: {len(ids)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_query(args):
    """Query the RAG system."""
    from src.tools.rag_chain import get_rag_chain
    
    rag_chain = get_rag_chain()
    
    if args.question:
        # Single question mode
        print(f"\n🔍 Query: {args.question}")
        print("=" * 60)
        
        result = rag_chain.query(args.question, k=args.k)
        
        print(f"\n📝 Answer:\n{result['answer']}")
        
        if result['sources']:
            print(f"\n📚 Sources ({len(result['sources'])}):")
            for i, source in enumerate(result['sources'], 1):
                print(f"   {i}. {source['filename']} (relevance: {source['relevance_score']:.2%})")
    else:
        # Interactive mode
        print("\n💬 FinanceRAG Interactive Query Mode")
        print("=" * 60)
        print("Type your questions about financial documents.")
        print("Type 'quit' or 'exit' to stop.\n")
        
        while True:
            try:
                question = input("You: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye! 👋")
                    break
                
                result = rag_chain.query(question, k=args.k)
                
                print(f"\n🤖 Assistant: {result['answer']}")
                
                if result['sources']:
                    print(f"\n   Sources: {', '.join(s['filename'] for s in result['sources'][:3])}")
                
                print()
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break


def cmd_serve(args):
    """Start the FastAPI server."""
    import uvicorn
    from src.config.settings import get_settings
    
    settings = get_settings()
    host = args.host or settings.api_host
    port = args.port or settings.api_port
    
    print(f"\n🚀 Starting FinanceRAG API server")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Docs: http://{host}:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=args.reload
    )


def cmd_stats(args):
    """Show vector store statistics."""
    from src.tools.vector_store import get_vector_store_manager
    
    print("\n📊 Vector Store Statistics")
    print("=" * 60)
    
    vector_store = get_vector_store_manager()
    stats = vector_store.get_collection_stats()
    
    for key, value in stats.items():
        print(f"   {key}: {value}")


def cmd_clear(args):
    """Clear the vector store."""
    from src.tools.vector_store import get_vector_store_manager
    
    if not args.yes:
        confirm = input("⚠️  This will delete all documents. Continue? [y/N]: ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    
    vector_store = get_vector_store_manager()
    success = vector_store.clear_collection()
    
    if success:
        print("✅ Collection cleared successfully")
    else:
        print("❌ Failed to clear collection")


def main():
    parser = argparse.ArgumentParser(
        description="FinanceRAG - Financial Document Q&A System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents")
    ingest_parser.add_argument(
        "--source", "-s",
        required=True,
        help="Path to file or directory to ingest"
    )
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the RAG system")
    query_parser.add_argument(
        "--question", "-q",
        help="Question to ask (omit for interactive mode)"
    )
    query_parser.add_argument(
        "--k", "-k",
        type=int,
        default=5,
        help="Number of documents to retrieve (default: 5)"
    )
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--host", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, help="Port to bind to")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # Stats command
    subparsers.add_parser("stats", help="Show vector store statistics")
    
    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear vector store")
    clear_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "clear":
        cmd_clear(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
