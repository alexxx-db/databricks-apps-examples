# Databricks notebook source
# MAGIC %md
# MAGIC # Databricks Apps and Vector Search Gradio Sample - Setup Notebook
# MAGIC
# MAGIC Follow the instruction in this notebook to deploy the Databricks Apps and Vector Search Gradio example application.
# MAGIC
# MAGIC This notebook creates the one-time infrastructure the app needs:
# MAGIC 1. A vector search endpoint (unless you supply one)
# MAGIC 1. A direct access vector search index in your Unity Catalog schema
# MAGIC
# MAGIC The app itself is deployed with the bundle in this folder (`databricks.yml`); the last cell prints the command.
# MAGIC
# MAGIC Start by configuring a Unity Catalog schema name in the next notebook section in **cell 5: Define schema name and existing resources**.
# MAGIC
# MAGIC Optionally, input an existing vector search endpoint. If you do not specify one, it will be created for you.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configure schema name and existing resources

# COMMAND ----------

# DBTITLE 1,Install required packages
# MAGIC %pip install databricks-sdk>=0.38.0 --quiet

# COMMAND ----------

# DBTITLE 1,Restart Python
dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Define schema name and existing resources
# Input a Unity Catalog schema where your vector search index should be created
schema_name = ""  # Example: catalog.schema

# Optionally, input your existing resources here
vector_search_endpoint_name = ""

# COMMAND ----------

# MAGIC %md
# MAGIC Choose **Run all**. This will take a couple of minutes.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get or create vector search endpoint and index
# MAGIC
# MAGIC If you have provided vector search endpoint and index names above, the following cells will check if they exist.
# MAGIC
# MAGIC If you didn't provide these resources, the following cells will create them for you.

# COMMAND ----------

# DBTITLE 1,Import dependencies and create workspace client
import json
import uuid
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import (
    DirectAccessVectorIndexSpec,
    EmbeddingVectorColumn,
    VectorIndexType,
    EndpointType,
    EndpointStatusState,
)

w = WorkspaceClient()

# COMMAND ----------

# DBTITLE 1,Get or create vector search endpoint
if vector_search_endpoint_name:
    print(f"Checking vector search endpoint {vector_search_endpoint_name}...")
    try:
        endpoint = w.vector_search_endpoints.get_endpoint(vector_search_endpoint_name)

        if endpoint.endpoint_status.state == EndpointStatusState.ONLINE:
            print(f"Endpoint {endpoint.name} confirmed and in status ONLINE.")
        else:
            print("Endpoint exists but does not appear to be in status ONLINE.")
    except Exception as e:
        print(e)
else:
    endpoint_name = f"{str(uuid.uuid4().hex)[:12]}_vs_endpoint"
    print(
        f"Creating vector search endpoint {endpoint_name}. This will take a few minutes."
    )
    try:
        endpoint = w.vector_search_endpoints.create_endpoint_and_wait(
            name=endpoint_name, endpoint_type=EndpointType.STANDARD
        )
        vector_search_endpoint_name = endpoint.name
        print(f"Created vector search endpoint {endpoint.name}")
    except Exception as e:
        print(e)

# COMMAND ----------

# DBTITLE 1,Create vector search index
vector_search_index_name = f"{str(uuid.uuid4().hex)[:12]}_vs_index"

schema = json.dumps({"id": "string", "text": "string", "text_vector": "array<float>"})

try:
    index = w.vector_search_indexes.create_index(
        name=f"{schema_name}.{vector_search_index_name}",
        endpoint_name=vector_search_endpoint_name,
        primary_key="id",
        index_type=VectorIndexType.DIRECT_ACCESS,
        direct_access_index_spec=DirectAccessVectorIndexSpec(
            embedding_vector_columns=[
                EmbeddingVectorColumn(
                    name="text_vector",
                    embedding_dimension=1024,
                )
            ],
            schema_json=schema,
        ),
    )
    vector_search_index_name = index.vector_index.name
except Exception as e:
    print(e)

# COMMAND ----------

# DBTITLE 1,Deploy the app with the bundle
print("Infrastructure ready. From the vector-search folder on your machine, run:\n")
print(
    "databricks bundle deploy -t dev "
    f"--var vector_search_index={schema_name}.{vector_search_index_name} "
    "--profile <PROFILE>"
)
