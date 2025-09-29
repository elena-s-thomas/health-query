"""Generate a compact schema representation by extracting common FHIR data types."""
import json
from collections import defaultdict

def generate_compact_schema():
    """Generate a compact schema by extracting common types."""

    # Load the full schema
    with open('dataset_schemas.json', 'r') as f:
        schemas = json.load(f)

    # Common FHIR data types that appear across tables
    common_types = {
        "CommonFields": {
            "description": "Fields that appear in all FHIR resources",
            "fields": [
                {"name": "id", "type": "STRING", "mode": "NULLABLE"},
                {"name": "meta", "type": "Meta", "mode": "NULLABLE"},
                {"name": "identifier", "type": "Identifier[]", "mode": "REPEATED"},
                {"name": "implicitRules", "type": "STRING", "mode": "NULLABLE"},
                {"name": "language", "type": "STRING", "mode": "NULLABLE"},
                {"name": "text", "type": "Narrative", "mode": "NULLABLE"}
            ]
        },
        "Identifier": {
            "description": "Identifier for a resource",
            "fields": [
                {"name": "use", "type": "STRING"},
                {"name": "type", "type": "CodeableConcept"},
                {"name": "system", "type": "STRING"},
                {"name": "value", "type": "STRING"},
                {"name": "period", "type": "Period"},
                {"name": "assigner", "type": "Reference"}
            ]
        },
        "Meta": {
            "description": "Metadata about a resource",
            "fields": [
                {"name": "versionId", "type": "STRING"},
                {"name": "lastUpdated", "type": "TIMESTAMP"},
                {"name": "profile", "type": "STRING"},
                {"name": "security", "type": "Coding[]"},
                {"name": "tag", "type": "Coding[]"}
            ]
        },
        "Narrative": {
            "description": "Human-readable text",
            "fields": [
                {"name": "status", "type": "STRING"},
                {"name": "div", "type": "STRING"}
            ]
        },
        "CodeableConcept": {
            "description": "Concept with coding and text",
            "fields": [
                {"name": "coding", "type": "Coding[]"},
                {"name": "text", "type": "STRING"}
            ]
        },
        "Coding": {
            "description": "Reference to a code system",
            "fields": [
                {"name": "system", "type": "STRING"},
                {"name": "version", "type": "STRING"},
                {"name": "code", "type": "STRING"},
                {"name": "display", "type": "STRING"},
                {"name": "userSelected", "type": "BOOLEAN"}
            ]
        },
        "Reference": {
            "description": "Reference to another resource",
            "fields": [
                {"name": "reference", "type": "STRING"},
                {"name": "identifier", "type": "Identifier"},
                {"name": "display", "type": "STRING"}
            ],
            "variants": {
                "PatientReference": ["patientId"],
                "PractitionerReference": ["practitionerId"],
                "OrganizationReference": ["organizationId"],
                "EncounterReference": ["encounterId"],
                "LocationReference": ["locationId"]
            }
        },
        "Period": {
            "description": "Time period",
            "fields": [
                {"name": "start", "type": "STRING"},
                {"name": "end", "type": "STRING"}
            ]
        },
        "Annotation": {
            "description": "Text note with metadata",
            "fields": [
                {"name": "author", "type": "Reference"},
                {"name": "time", "type": "STRING"},
                {"name": "text", "type": "STRING"}
            ]
        },
        "Quantity": {
            "description": "Measured amount",
            "fields": [
                {"name": "value", "type": "FLOAT"},
                {"name": "comparator", "type": "STRING"},
                {"name": "unit", "type": "STRING"},
                {"name": "system", "type": "STRING"},
                {"name": "code", "type": "STRING"}
            ]
        }
    }

    # Create compact schema
    compact_schema = {
        "dataset": schemas["dataset_id"],
        "extraction_time": schemas["extraction_time"],
        "common_types": common_types,
        "tables": {}
    }

    # Process each table
    for table_name, table_info in schemas['tables'].items():
        compact_table = {
            "row_count": table_info["num_rows"],
            "size_gb": round(table_info["num_bytes"] / (1024**3), 2),
            "extends": "CommonFields",  # All tables extend common fields
            "specific_fields": []
        }

        # Track which fields are already covered by CommonFields
        common_field_names = {"id", "meta", "identifier", "implicitRules", "language", "text"}

        for field in table_info['schema']:
            field_name = field['name']

            # Skip if it's a common field
            if field_name in common_field_names:
                continue

            # Simplify field representation
            simplified_field = {
                "name": field_name,
                "type": simplify_type(field),
                "mode": field['mode']
            }

            # Add description if meaningful
            if field.get('description'):
                simplified_field["desc"] = field['description'][:50]  # Truncate long descriptions

            compact_table["specific_fields"].append(simplified_field)

        compact_schema["tables"][table_name] = compact_table

    return compact_schema

def simplify_type(field):
    """Simplify type representation using common type references."""
    field_type = field['type']
    field_name = field['name']

    # Map to common types
    if field_type == 'RECORD':
        # Check if it matches a known pattern
        if field_name == 'code' or field_name == 'category':
            return "CodeableConcept"
        elif field_name == 'period':
            return "Period"
        elif field_name == 'subject':
            return "Reference<Patient/Group>"
        elif field_name == 'patient':
            return "Reference<Patient>"
        elif field_name == 'practitioner':
            return "Reference<Practitioner>"
        elif field_name == 'organization':
            return "Reference<Organization>"
        elif field_name == 'encounter' or field_name == 'context':
            return "Reference<Encounter>"
        elif field_name == 'location':
            return "Reference<Location>"
        elif field_name == 'note':
            return "Annotation[]"
        elif 'reference' in field_name.lower() or 'basedOn' in field_name:
            return "Reference"
        else:
            # Generic RECORD
            return "RECORD"
    else:
        return field_type

def save_compact_schema(compact_schema):
    """Save the compact schema to files."""

    # Save as JSON
    with open('dataset_schema_compact.json', 'w') as f:
        json.dump(compact_schema, f, indent=2)
    print("Compact JSON saved to: dataset_schema_compact.json")

    # Generate compact markdown for Vertex AI
    with open('dataset_schema_compact.md', 'w') as f:
        f.write("# FHIR Synthea Dataset Schema (Compact)\n\n")
        f.write(f"**Dataset:** `{compact_schema['dataset']}`\n")
        f.write(f"**Tables:** {len(compact_schema['tables'])}\n\n")

        f.write("## Common FHIR Types\n\n")
        f.write("All tables include these common fields: id, meta, identifier[], implicitRules, language, text\n\n")

        f.write("### Key Type Definitions\n")
        f.write("- **Reference**: Links to other resources (with display, identifier, reference fields)\n")
        f.write("- **CodeableConcept**: Coded value with text (coding[], text)\n")
        f.write("- **Period**: Time range (start, end)\n")
        f.write("- **Identifier**: Resource identifier (system, value, type, use)\n")
        f.write("- **Annotation**: Note with metadata (author, time, text)\n\n")

        f.write("## Tables\n\n")

        for table_name, table_info in compact_schema['tables'].items():
            f.write(f"### {table_name}\n")
            f.write(f"- **Rows:** {table_info['row_count']:,}\n")
            f.write(f"- **Size:** {table_info['size_gb']} GB\n")
            f.write(f"- **Key Fields:**\n")

            # Group fields by type for better readability
            string_fields = []
            reference_fields = []
            code_fields = []
            other_fields = []

            for field in table_info['specific_fields'][:15]:  # Limit to top 15 fields
                field_str = f"  - {field['name']}"
                if 'Reference' in field['type']:
                    reference_fields.append(field_str + f" ({field['type']})")
                elif 'Code' in field['type']:
                    code_fields.append(field_str + f" ({field['type']})")
                elif field['type'] == 'STRING':
                    string_fields.append(field_str)
                else:
                    other_fields.append(field_str + f" ({field['type']})")

            # Output grouped fields
            if reference_fields:
                f.write("  **References:**\n")
                for ref in reference_fields:
                    f.write(f"{ref}\n")
            if code_fields:
                f.write("  **Codes:**\n")
                for code in code_fields:
                    f.write(f"{code}\n")
            if string_fields:
                f.write("  **Attributes:**\n")
                for s in string_fields[:5]:  # Limit string fields
                    f.write(f"{s}\n")
            if other_fields:
                f.write("  **Other:**\n")
                for o in other_fields:
                    f.write(f"{o}\n")

            f.write("\n")

    print("Compact markdown saved to: dataset_schema_compact.md")

    # Print size comparison
    import os
    original_size = os.path.getsize('dataset_schemas.json')
    compact_size = os.path.getsize('dataset_schema_compact.json')
    reduction = ((original_size - compact_size) / original_size) * 100

    print(f"\nSize comparison:")
    print(f"  Original: {original_size:,} bytes")
    print(f"  Compact:  {compact_size:,} bytes")
    print(f"  Reduction: {reduction:.1f}%")

if __name__ == "__main__":
    compact_schema = generate_compact_schema()
    save_compact_schema(compact_schema)

    # Show sample of compact schema
    print("\nSample of compact schema structure:")
    print(json.dumps({
        "common_types": list(compact_schema["common_types"].keys()),
        "sample_table": list(compact_schema["tables"].keys())[0],
        "sample_fields": compact_schema["tables"][list(compact_schema["tables"].keys())[0]]["specific_fields"][:3]
    }, indent=2))