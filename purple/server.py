import os
import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# --- DIRECT SDK IMPORTS ---
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions

# 1. SETUP
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", 8))

if not api_key:
    print("CRITICAL: GOOGLE_API_KEY is missing in .env")

# Configure Google Gemini
genai.configure(api_key=api_key)

# Configure ChromaDB (In-memory for this session)
chroma_client = chromadb.Client()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. DATA MODELS
class QueryRequest(BaseModel):
    url: str
    query: str

class QueryResponse(BaseModel):
    answer: str

# 3. HELPER: Manual Text Chunking
def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

# 4. HELPER: Rate-Limit Safe Embedding Function
# This class handles the "429 Quota Exceeded" errors for you
class GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            retry_count = 0
            while retry_count < 3:
                try:
                    # Create embedding
                        response = genai.embed_content(
                            model="models/embedding-001",
                            content=text,
                            task_type="retrieval_document"
                        )
                        embeddings.append(response['embedding'])
                        break
                except Exception as e:
                    if "429" in str(e) or "Quota" in str(e):
                        print(f"Rate limit hit. Waiting 20 seconds... (Attempt {retry_count+1}/3)")
                        time.sleep(20) # Wait for quota to reset
                        retry_count += 1
                    else:
                        print(f"Error embedding chunk: {e}")
                        # Append zero vector as fallback to avoid crashing
                        embeddings.append([0.0] * 768) 
                        break
        return embeddings

@app.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest):
    try:
        # A. SCRAPE
        print(f"Scraping {request.url}...")
        resp = requests.get(request.url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to load page")
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.extract()
        text = soup.get_text(separator=' ', strip=True)

        # B. CHUNK & INDEX
        collection_name = "temp_docs"
        try:
            chroma_client.delete_collection(collection_name)
        except:
            pass 
            
        collection = chroma_client.create_collection(
            name=collection_name,
            embedding_function=GeminiEmbeddingFunction() # Uses the new safe function
        )

        chunks = chunk_text(text)
        
        # Limit chunks to avoid waiting forever on huge pages
        if len(chunks) > MAX_CHUNKS:
            print(f"Page is long ({len(chunks)} chunks). Only indexing first {MAX_CHUNKS} to save time.")
            chunks = chunks[:MAX_CHUNKS]

        if not chunks:
             return QueryResponse(answer="I couldn't find any text on this page.")

        print(f"Indexing {len(chunks)} text chunks (this may take a moment)...")
        collection.add(
            documents=chunks,
            ids=[str(i) for i in range(len(chunks))]
        )

        # C. RETRIEVE
        results = collection.query(
            query_texts=[request.query],
            n_results=5
        )
        
        context_text = "\n\n".join(results['documents'][0])

        # D. GENERATE
        print("Asking Gemini...")
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are a helpful assistant. Answer the user's question using ONLY the context provided below.
        
        CONTEXT:
        {context_text}
        
        USER QUESTION: 
        {request.query}
        """

        response = model.generate_content(prompt)
        
        return QueryResponse(answer=response.text)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
