import os
import json
import uuid
import logging
import gradio as gr
from typing import Optional, List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from databricks.sdk import WorkspaceClient

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Injected from app resources via valueFrom (see app.yaml / databricks.yml)
VECTOR_SEARCH_INDEX_NAME = os.getenv("VECTOR_SEARCH_INDEX_NAME")
EMBEDDING_MODEL_ENDPOINT_NAME = os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en")
BATCH_SIZE = 16  # chunks per embeddings call and per upsert

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
        logger.error(f"Error generating embeddings: {e}")
        return None


def index_chunks(document_id: str, texts: List[str]) -> int:
    """Embed and upsert chunks in batches (one embeddings call + one upsert per batch).

    Returns:
        int: Number of chunks the index accepted.
    """
    indexed = 0
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        try:
            response = openai_client.embeddings.create(
                model=EMBEDDING_MODEL_ENDPOINT_NAME, input=batch
            )
            rows = [
                {"id": f"{document_id}_chunk{start + i}", "text": text, "text_vector": item.embedding}
                for i, (text, item) in enumerate(zip(batch, response.data))
            ]
            result = workspace_client.vector_search_indexes.upsert_data_vector_index(
                index_name=VECTOR_SEARCH_INDEX_NAME, inputs_json=json.dumps(rows)
            )
            indexed += result.result.success_row_count or 0
            if result.result.failed_primary_keys:
                logger.error(f"Index rejected chunks: {result.result.failed_primary_keys}")
        except Exception as e:
            logger.error(f"Error indexing chunks {start}-{start + len(batch) - 1}: {e}")
    return indexed


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

        indexed = index_chunks(str(uuid.uuid4()), [c.page_content for c in chunks])
        if indexed < len(chunks):
            return f"Ingested {indexed} of {len(chunks)} chunks; see app logs for the failures."
        return f"Successfully ingested {indexed} chunks into the vector search index!"
    except Exception as e:
        logger.error(f"Error ingesting file: {e}")
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
        logger.error(f"Error during vector search: {e}")
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
