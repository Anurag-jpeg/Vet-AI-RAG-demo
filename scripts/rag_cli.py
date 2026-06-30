import sys
from src import retrieve   

def main():
    if len(sys.argv) < 2:
        print("Usage: rag_cli.py <question> [k]")
        sys.exit(1)

    question = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    for i, hit in enumerate(retrieve(question, k), start=1):
        print(f"\n--- Chunk {i} (score {hit['score']:.3f}) ---")
        print(
            f"Source: {hit['source_file']} "
            f"(doc {hit['document_id']}, chunk {hit['chunk_id']})"
        )
        print(hit["text"])

if __name__ == "__main__":
    main()