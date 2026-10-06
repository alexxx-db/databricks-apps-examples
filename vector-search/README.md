# Databricks Apps: Vector Search with Gradio example
This code sample shows how you can integrate [Databricks Apps](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html) with a [Mosaic AI Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html) direct query index.

Use this sample as a starting point to build your own applications based on Databricks Apps and Mosaic AI Vector Search.

## Features

* Document ingestion: upload a PDF, chunks PDF, ingests vector embeddings into vector search index
* Search: perform a vector search query on the index
* [Gradio](https://www.gradio.app/) for UI and [LangChain](https://python.langchain.com/docs/introduction/) for chunking
* Deployment notebook to set up necessary resources

![Databricks Vector Search example Gradio app screenshot](screenshot.png "Databricks Vector Search example Gradio app")

## Setup

1. **Create the index (once).** [Load this repository as a Git folder](https://docs.databricks.com/en/repos/index.html), open the [setup.py](setup.py) notebook, set `schema_name` and choose **Run all**. It creates a vector search endpoint (unless you give it one) and a direct access index, then prints the deploy command.
2. **Deploy the app** from this folder:

   ```bash
   databricks auth login --host https://<workspace> --profile <PROFILE>
   databricks bundle deploy -t dev --var vector_search_index=<catalog.schema.index> --profile <PROFILE>
   databricks bundle open vector_search_app -t dev --profile <PROFILE>
   ```

| Variable | Meaning |
|---|---|
| `vector_search_index` | Full name of the index created by `setup.py` |
| `embedding_endpoint` | Embedding endpoint (default `databricks-gte-large-en`) |

3. **Allow ingestion (once).** Upserts need `MODIFY` on the index, which an app resource can't add alongside `SELECT`, so grant it to the app's service principal:

   ```bash
   SP=$(databricks apps get vector-search-dev -o json --profile <PROFILE> | jq -r .service_principal_client_id)
   databricks grants update table <catalog.schema.index> --profile <PROFILE> \
     --json "{\"changes\": [{\"principal\": \"$SP\", \"add\": [\"MODIFY\"]}]}"
   ```

**Permissions.** The bundle grants the app's service principal `SELECT` on the index and `CAN_QUERY` on the embedding endpoint. Step 3 adds `MODIFY`. The principal also needs `USE CATALOG` / `USE SCHEMA` on the index's catalog and schema.

> Every app user writes into the same index, and documents can't be deleted from the UI. For production, prefer a Delta Sync index over a governed source table.
