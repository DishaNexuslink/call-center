from fastapi import FastAPI, File, UploadFile, HTTPException
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from faster_whisper import WhisperModel
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = QdrantClient("localhost", port=6333)

model = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")
whisper_model = WhisperModel("small")


class DepartmentPayload(BaseModel):
    Department: list[str]

class textInput(BaseModel):
    text: str
    
@app.post("/route_divert/")
async def route_divert(text: textInput):
    department = determine_category(text.text)
    return f"Your call is forwarded to {department[0]} department"
    

@app.post("/add_department/")
async def update_categories(categories_payload: DepartmentPayload):
    Department_list = categories_payload.Department

    collections = client.get_collections()
    collection_names = [
        collection.name for collection in collections.collections
    ]

    if "departments" not in collection_names:
        client.create_collection(
            collection_name="departments",
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
        )

    embeddings_department = model.encode(Department_list)
    vectors = embeddings_department.tolist()

    existing_points, _ = client.scroll(collection_name="departments", limit=1000)

    existing_ids = [point.id for point in existing_points]  # Use .id instead of ['id']

    if existing_ids:
        start_id = max(existing_ids) + 1
    else:
        start_id = 0  

    num_points = len(embeddings_department)
    new_ids = list(range(start_id, start_id + num_points))

    payload = [{"department": department} for department in Department_list]

    client.upsert(
        collection_name="departments",
        points=models.Batch(ids=new_ids, vectors=vectors, payloads=payload),
    )

    return {"message": "departments updated successfully"}


def determine_category(text): 
    embeddings_text = model.encode(text)
    hits = client.search(
        collection_name="departments",  
        query_vector=embeddings_text.tolist(),
        limit=4,
    )
    print(hits)
    for hit in hits:
        print(hit.payload, "score:", hit.score)
    
    department = [hit.payload['department'] for hit in hits]  
    print(department)
    return department

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

# ================================================================
