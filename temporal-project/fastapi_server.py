from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from temporalio.client import Client
from pydantic import BaseModel
import os
import asyncio

from actions.generate_meta_document import get_metadocument_for_query
from workflows.generate_flashcards import GenerateFlashcardsWorkflow, GenerateFlashcardsParameters

class GenerateFlashcardsRequest(BaseModel):
    generate_flashcards_job_id: str

class GenerateMetadocumentRequest(BaseModel):
    query: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "localhost:3000")
    ],  
    allow_credentials=True, 
    allow_methods=["*"],    
    allow_headers=["*"],   
)


@app.on_event("startup")
async def startup_event():
    """Connects to Temporal on application startup and stores the client."""
    temporal_url = os.getenv("TEMPORAL_SERVER_URL", "localhost:7233")
    max_retries = 10
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            client = await Client.connect(temporal_url, namespace="default")
            app.state.temporal_client = client
            print("Successfully connected to Temporal service.")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"Error occurred - {e}")
                raise


def get_temporal_client(request: Request) -> Client:
    """Retrieves the Temporal client from the FastAPI app state via the request."""
    client = getattr(request.app.state, 'temporal_client', None)
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="Temporal client is not available. Connection may have failed on startup."
        )
    return client


@app.post("/generate-flashcards-job")
async def trigger_generate_flashcards_endpoint(payload: GenerateFlashcardsRequest, request: Request):
    temporal_client = get_temporal_client(request)
    job_params = GenerateFlashcardsParameters(job_record_id=payload.generate_flashcards_job_id)
    workflow_id = f"generate-flashcards-job-{payload.generate_flashcards_job_id}"

    await temporal_client.execute_workflow(
        GenerateFlashcardsWorkflow.run,
        job_params,
        id=workflow_id,
        task_queue="general-work-queue"
    )

    print(f"Successfully triggered workflow '{workflow_id}' for job record '{payload.generate_flashcards_job_id}'")
    return {
        "message": "Generate flashcards workflow triggered successfully.",
        "workflow_id": workflow_id
    }


@app.post("/generate-metadocument")
async def trigger_generate_metadocument_endpoint(payload: GenerateMetadocumentRequest, request: Request):
    print(f"Metadocument generation for query - {payload.query}")
    metadocument = await get_metadocument_for_query(payload.query)
    
    return {
        "message": "Generate a metadocument succesfully",
        "metadocument": metadocument
    }