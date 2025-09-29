"""Extract complete database schema from BigQuery FHIR Synthea dataset."""
import json
import os
from google.cloud import bigquery
from config import Config
from datetime import datetime

# Setup credentials
Config.setup_credentials()

def extract_field_schema(field):
    """Extract detailed schema for a field, including nested fields."""
    field_info = {
        "name": field.name,
        "type": field.field_type,
        "mode": field.mode,
        "description": field.description or ""
    }

    # If field has nested fields (RECORD type), extract them recursively
    if field.fields:
        field_info["fields"] = [extract_field_schema(sub_field) for sub_field in field.fields]

    return field_info

def get_complete_schema():
    """Extract complete schema for all tables in the dataset."""
    # Initialize BigQuery client
    client = bigquery.Client(project=Config.GCP_PROJECT_ID)

    # Use the configured dataset
    dataset_id = Config.BIGQUERY_DATASET

    print(f"Extracting schema from dataset: {dataset_id}")
    print("-" * 50)

    schemas = {
        "dataset_id": dataset_id,
        "extraction_time": datetime.now().isoformat(),
        "tables": {}
    }

    try:
        # List all tables in the dataset
        tables = list(client.list_tables(dataset_id))
        print(f"Found {len(tables)} tables in dataset")

        for table_item in tables:
            table_id = table_item.table_id
            print(f"\nProcessing table: {table_id}")

            # Get full table reference with metadata
            table_ref = client.get_table(f"{dataset_id}.{table_id}")

            # Extract table metadata
            table_info = {
                "table_id": table_id,
                "full_table_id": f"{dataset_id}.{table_id}",
                "description": table_ref.description or "",
                "num_rows": table_ref.num_rows,
                "num_bytes": table_ref.num_bytes,
                "created": table_ref.created.isoformat() if table_ref.created else None,
                "modified": table_ref.modified.isoformat() if table_ref.modified else None,
                "schema": []
            }

            # Extract schema for each field
            for field in table_ref.schema:
                field_info = extract_field_schema(field)
                table_info["schema"].append(field_info)

            # Add partition and clustering information if available
            if table_ref.time_partitioning:
                table_info["partitioning"] = {
                    "type": table_ref.time_partitioning.type_,
                    "field": table_ref.time_partitioning.field
                }

            if table_ref.clustering_fields:
                table_info["clustering_fields"] = table_ref.clustering_fields

            schemas["tables"][table_id] = table_info
            print(f"  - Extracted {len(table_info['schema'])} fields")
            print(f"  - Table size: {table_ref.num_rows:,} rows, {table_ref.num_bytes:,} bytes")

    except Exception as e:
        print(f"Error extracting schema: {e}")
        raise

    return schemas

def save_schema(schemas, output_file="dataset_schemas.json"):
    """Save the extracted schema to JSON and markdown files."""
    with open(output_file, 'w') as f:
        json.dump(schemas, f, indent=2, default=str)
    print(f"\nSchema saved to: {output_file}")

    # Also create a simplified version for quick reference
    simplified = {
        "dataset": schemas["dataset_id"],
        "extraction_time": schemas["extraction_time"],
        "tables": {}
    }

    for table_name, table_info in schemas["tables"].items():
        simplified["tables"][table_name] = {
            "row_count": table_info["num_rows"],
            "size_bytes": table_info["num_bytes"],
            "fields": [
                {
                    "name": field["name"],
                    "type": field["type"],
                    "mode": field["mode"]
                }
                for field in table_info["schema"]
            ]
        }

    simplified_file = output_file.replace(".json", "_simplified.json")
    with open(simplified_file, 'w') as f:
        json.dump(simplified, f, indent=2)
    print(f"Simplified schema saved to: {simplified_file}")

    # Create markdown documentation for Vertex AI and users
    markdown_file = output_file.replace(".json", ".md")
    create_markdown_docs(schemas, markdown_file)
    print(f"Documentation saved to: {markdown_file}")

def create_markdown_docs(schemas, output_file):
    """Create markdown documentation for the schema - useful for Vertex AI context."""
    with open(output_file, 'w') as f:
        f.write(f"# BigQuery FHIR Synthea Dataset Schema\n\n")
        f.write(f"**Dataset:** `{schemas['dataset_id']}`\n")
        f.write(f"**Extracted:** {schemas['extraction_time']}\n")
        f.write(f"**Tables:** {len(schemas['tables'])}\n\n")

        # Table of contents
        f.write("## Table of Contents\n\n")
        for table_name in sorted(schemas["tables"].keys()):
            f.write(f"- [{table_name}](#{table_name.lower()})\n")
        f.write("\n")

        # Detailed table information
        for table_name in sorted(schemas["tables"].keys()):
            table_info = schemas["tables"][table_name]
            f.write(f"## {table_name}\n\n")

            if table_info.get("description"):
                f.write(f"*{table_info['description']}*\n\n")

            f.write(f"- **Rows:** {table_info['num_rows']:,}\n")
            f.write(f"- **Size:** {table_info['num_bytes'] / (1024**3):.2f} GB\n")
            f.write(f"- **Fields:** {len(table_info['schema'])}\n\n")

            f.write("### Schema\n\n")
            f.write("| Field | Type | Mode | Description |\n")
            f.write("|-------|------|------|-------------|\n")

            for field in table_info["schema"]:
                desc = field.get("description", "").replace("\n", " ")
                f.write(f"| {field['name']} | {field['type']} | {field['mode']} | {desc} |\n")

            f.write("\n")

def print_summary(schemas):
    """Print a summary of the extracted schema."""
    print("\n" + "=" * 50)
    print("SCHEMA EXTRACTION SUMMARY")
    print("=" * 50)
    print(f"Dataset: {schemas['dataset_id']}")
    print(f"Tables: {len(schemas['tables'])}")
    print(f"Extraction time: {schemas['extraction_time']}")
    print("\nTable Summary:")

    total_rows = 0
    total_bytes = 0

    for table_name, table_info in schemas["tables"].items():
        rows = table_info.get("num_rows", 0) or 0
        bytes_size = table_info.get("num_bytes", 0) or 0
        total_rows += rows
        total_bytes += bytes_size

        print(f"  - {table_name:30} {rows:>12,} rows, {len(table_info['schema']):>3} fields")

    print(f"\nTotal rows across all tables: {total_rows:,}")
    print(f"Total size: {total_bytes / (1024**3):.2f} GB")

if __name__ == "__main__":
    # Extract the complete schema
    schemas = get_complete_schema()

    # Save to JSON files
    save_schema(schemas)

    # Print summary
    print_summary(schemas)