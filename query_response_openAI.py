import os
import pickle
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

import time
import openai
from tiktoken import encoding_for_model
from typing import Optional


# Load existing embeddings from the pickle file
EMBEDDINGS_PATH = "embeddings.pkl"
DATA_PATH = "data"

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")



import warnings
warnings.filterwarnings("ignore")

app = FastAPI()

# ------------------------------------------user query-------------------------------------------------
class QueryRequest(BaseModel):
    query: str

# @app.post("/Query Response",tags=["user query"])
# async def Query_Response(request: QueryRequest):

#     try:
#         start_time = time.time()

#         #  open pickle path
#         if os.path.exists(EMBEDDINGS_PATH):
#             with open(EMBEDDINGS_PATH, "rb") as f:
#                 Emb = pickle.load(f)
#         else:
#             raise HTTPException(status_code=500, detail="Embeddings not found. Please generate embeddings first.")

#         # Execute the query using the loaded embeddings
#         response = Emb.query(request.query)
#         end_time = time.time()
#         elapsed_time = end_time - start_time
#         return {"result": response.response,"time taken to respond":elapsed_time}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during query execution: {str(e)}")

@app.post("/Query Response", tags=["user query"])
async def Query_Response(request: QueryRequest):

    try:
        start_time = time.time()

        # Load embeddings from pickle file
        if os.path.exists(EMBEDDINGS_PATH):
            with open(EMBEDDINGS_PATH, "rb") as f:
                Emb = pickle.load(f)
        else:
            raise HTTPException(status_code=500, detail="Embeddings not found. Please generate embeddings first.")

        response = Emb.query(request.query)
        end_time = time.time()
        elapsed_time = end_time - start_time

        input_tokens = len(request.query.split())  
        output_tokens = len(response.response.split())  

        total_tokens = input_tokens + output_tokens

        tokens_used = total_tokens
        usd_cost_per_million_tokens = 0.50  
        usd_to_inr_rate = 83.94   
        
        millions_of_tokens = tokens_used / 1_000_000
        cost_in_usd = millions_of_tokens * usd_cost_per_million_tokens
        cost_in_inr = cost_in_usd * usd_to_inr_rate

        return {
            "result": response.response,
            "time taken to respond": elapsed_time,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_in_usd": cost_in_usd,
            "cost_in_inr": cost_in_inr
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during query execution: {str(e)}")


query_engine = None
# @app.post("/createEmbeddings",tags=["user query"])
# async def create_embeddings(files: list[UploadFile] = File(None)):
#     global query_engine

#     start_time = time.time()

#     # Step 1: Delete existing embeddings.pkl if it exists
#     if os.path.exists(EMBEDDINGS_PATH):
#         os.remove(EMBEDDINGS_PATH)
#         print("Deleted existing embeddings.pkl")


#     # Step 2: Save the uploaded PDF files to the 'data' folder
#     for file in files:
#         file_path = os.path.join(DATA_PATH, file.filename)
#         with open(file_path, "wb") as f:
#             f.write(await file.read())
#         print(f"Saved file: {file.filename} in data folder")

#     # Step 3: Generate new embeddings for all PDFs in the 'data' folder
#     print("Generating new embeddings...")
#     documents = SimpleDirectoryReader(DATA_PATH).load_data()

#     index = VectorStoreIndex.from_documents(documents, show_progress=True)
#     query_engine = index.as_query_engine()

#     # Step 4: Save the new embeddings to the pickle file
#     with open(EMBEDDINGS_PATH, "wb") as f:
#         pickle.dump(query_engine, f)

#     # Step 5: Calculate time taken to create embeddings
#     end_time = time.time()
#     elapsed_time = end_time - start_time

#     return {"result": "Embeddings created and saved successfully", "time_to_create_embeddings": elapsed_time}


USD_TO_INR_RATE = 83.94   # Approximate conversion rate, update as needed
COST_PER_MILLION_TOKENS = 0.100  # $0.100 per 1M tokens


# Function to count tokens
def count_tokens(text, model="gpt-3.5-turbo"):
    enc = encoding_for_model(model)  # Get the encoder for the model
    tokens = enc.encode(text)
    return len(tokens)

@app.post("/createEmbeddings", tags=["user query"])
async def create_embeddings(files: list[UploadFile] = File(None)):
    global query_engine

    start_time = time.time()
    total_tokens = 0  # Initialize total token count

    # Step 1: Delete existing embeddings.pkl if it exists
    if os.path.exists(EMBEDDINGS_PATH):
        os.remove(EMBEDDINGS_PATH)
        print("Deleted existing embeddings.pkl")

    # Step 2: Save the uploaded PDF files to the 'data' folder
    for file in files:
        file_path = os.path.join(DATA_PATH, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        print(f"Saved file: {file.filename} in data folder")

    # Step 3: Generate new embeddings for all PDFs in the 'data' folder
    print("Generating new embeddings...")
    documents = SimpleDirectoryReader(DATA_PATH).load_data()

    # Count tokens for each document                           
    for doc in documents:
        tokens_in_doc = count_tokens(doc.text)  # Assuming each document has a 'text' attribute
        total_tokens += tokens_in_doc

    index = VectorStoreIndex.from_documents(documents, show_progress=True)
    query_engine = index.as_query_engine()

    # Step 4: Save the new embeddings to the pickle file
    with open(EMBEDDINGS_PATH, "wb") as f:
        pickle.dump(query_engine, f)

    # Step 5: Calculate time taken to create embeddings
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Calculate cost based on tokens
    token_cost_usd = (total_tokens / 1_000_000) * COST_PER_MILLION_TOKENS
    token_cost_inr = token_cost_usd * USD_TO_INR_RATE

    return {
        "result": "Embeddings created and saved successfully",
        "total_tokens": total_tokens,
        "cost_in_usd": f"${token_cost_usd:.4f}",
        "cost_in_inr": f"₹{token_cost_inr:.4f}",
        "time_to_create_embeddings": elapsed_time 
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
