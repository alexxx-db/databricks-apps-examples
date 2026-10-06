import os
import json
import uuid
import logging
import gradio as gr
from typing import Optional, List
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from databricks.sdk import WorkspaceClient

# Set up logging
logging.basicConfig(level=logging.ERROR)

# Injected from app resources via valueFrom (see app.yaml / databricks.yml)
VECTOR_SEARCH_INDEX_NAME = os.getenv("VECTOR_SEARCH_INDEX_NAME")
EMBEDDING_MODEL_ENDPOINT_NAME = os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en")

# Initialize Databricks SDK client
workspace_client = WorkspaceClient()
openai_client = workspace_client.serving_endpoints.get_open_ai_client()


def upload_file(file: gr.File) -> str:
    """Handle file upload and return a success message."""
    if file:
        return f"File {file.name} uploaded successfully!"
    else:
        return "No file uploaded."


def get_embeddings(text: str) -> Optional[List[float]]:
    """Generate embeddings for the given text using the OpenAI client.

    Args:
        text (str): The input text to generate embeddings for.

    Returns:
        Optional[List[float]]: The embedding vector, or None if an error occurs.
    """
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL_ENDPOINT_NAME, input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Error generating embeddings: {e}")
        return None


def index_chunk(chunk_id: str, chunk_text: str) -> Optional[dict]:
    """Index a text chunk into the vector search index.

    Args:
        chunk_id (str): The unique identifier for the chunk.
        chunk_text (str): The text content of the chunk.

    Returns:
        Optional[dict]: The result of the upsert operation, or None if an error occurs.
    """
    try:
        embedding = get_embeddings(chunk_text)
        if embedding is None:
            logging.error(f"Failed to get embeddings for chunk {chunk_id}")
            return None

        inputs = [{"id": chunk_id, "text": chunk_text, "text_vector": embedding}]
        inputs_json = json.dumps(inputs)

        result = workspace_client.vector_search_indexes.upsert_data_vector_index(
            index_name=VECTOR_SEARCH_INDEX_NAME, inputs_json=inputs_json
        )
        return result
    except Exception as e:
        logging.error(f"Error indexing chunk {chunk_id}: {e}")
        return None


def ingest_file(file: gr.File) -> str:
    """Load a PDF file, split it into chunks, and index them.

    Args:
        file (gr.File): The PDF file to ingest.

    Returns:
        str: A message indicating the result of the ingestion.
    """
    if not file:
        return "No file provided for ingestion."

    try:
        loader = PyPDFLoader(file.name)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50, add_start_index=True
        )
        chunks = text_splitter.split_documents(docs)

        document_id = str(uuid.uuid4())

        for index, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk{index}"
            result = index_chunk(chunk_id, chunk.page_content)
            if result is None:
                logging.warning(f"Chunk {chunk_id} was not indexed due to an error.")

        return (
            f"Successfully ingested {len(chunks)} chunks into the vector search index!"
        )
    except Exception as e:
        logging.error(f"Error ingesting file: {e}")
        return f"Failed to ingest file: {e}"


def run_vector_search(prompt: str) -> str:
    """Run a vector search query using the prompt.

    Args:
        prompt (str): The search query.

    Returns:
        str: The search results or an error message.
    """
    prompt_vector = get_embeddings(prompt)
    if prompt_vector is None:
        return "Failed to generate embeddings for the prompt."

    try:
        query_result = workspace_client.vector_search_indexes.query_index(
            index_name=VECTOR_SEARCH_INDEX_NAME,
            columns=["id", "text"],
            query_vector=prompt_vector,
            num_results=3,
        )
        return query_result.result.data_array
    except Exception as e:
        logging.error(f"Error during vector search: {e}")
        return f"Error during vector search: {e}"


# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("# Mosaic AI Vector Search Direct Access Index Demo")
    with gr.Row():
        with gr.Column():
            gr.Markdown("## Upload PDF")
            gr.Markdown(
                f"Upload a PDF to ingest its chunks into your vector search index **{VECTOR_SEARCH_INDEX_NAME}**."
            )
            with gr.Group():
                file_input = gr.File(
                    label="Choose a PDF to upload", file_count="single"
                )
                file_input.change(upload_file, inputs=file_input)
                ingest_result = gr.Textbox(
                    label="Ingest Status",
                    placeholder="Click the button below to start ingestion",
                )
                ingest_button = gr.Button("Ingest File into Vector Search")
                ingest_button.click(
                    ingest_file, inputs=file_input, outputs=ingest_result
                )
        with gr.Column():
            gr.Markdown("## Perform Vector Search Query")
            gr.Markdown("Use this search interface to query the index.")
            with gr.Group():
                query_input = gr.Textbox(label="Enter Search Query")
                search_result = gr.JSON(label="Search Results")
                search_button = gr.Button("Search")
                search_button.click(
                    fn=run_vector_search, inputs=query_input, outputs=search_result
                )

demo.launch(
    server_name="0.0.0.0", server_port=int(os.getenv("DATABRICKS_APP_PORT", "8000"))
)
