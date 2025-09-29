"""Analyze schema patterns to find repeated structures in FHIR dataset."""
import json
from collections import defaultdict, Counter

def analyze_patterns():
    """Analyze the dataset schemas for repeated patterns."""

    # Load the full schema
    with open('dataset_schemas.json', 'r') as f:
        schemas = json.load(f)

    # Track patterns
    field_patterns = defaultdict(list)
    record_structures = defaultdict(list)
    field_name_frequency = Counter()
    field_type_combinations = Counter()

    print("Analyzing schema patterns...")
    print("=" * 60)

    # Analyze each table
    for table_name, table_info in schemas['tables'].items():
        for field in table_info['schema']:
            field_name = field['name']
            field_type = field['type']
            field_mode = field['mode']

            # Track field name frequency across tables
            field_name_frequency[field_name] += 1

            # Track field patterns (name + type + mode)
            pattern = f"{field_type}:{field_mode}"
            field_patterns[field_name].append({
                'table': table_name,
                'pattern': pattern
            })

            # Track type combinations
            field_type_combinations[pattern] += 1

            # If it's a RECORD type, track its structure
            if field_type == 'RECORD' and 'fields' in field:
                structure_key = get_record_structure_key(field['fields'])
                record_structures[structure_key].append({
                    'table': table_name,
                    'field': field_name
                })

    # Find common field names (appearing in multiple tables)
    print("\n1. MOST COMMON FIELD NAMES (across all tables):")
    print("-" * 40)
    for field_name, count in field_name_frequency.most_common(20):
        if count > 1:
            print(f"  {field_name:30} appears in {count} tables")

    # Find identical field patterns
    print("\n2. REPEATED FIELD PATTERNS:")
    print("-" * 40)
    repeated_patterns = {}
    for field_name, patterns in field_patterns.items():
        if len(patterns) > 1:
            # Check if all patterns are the same
            unique_patterns = set(p['pattern'] for p in patterns)
            if len(unique_patterns) == 1:
                pattern_str = unique_patterns.pop()
                tables_with_field = [p['table'] for p in patterns]
                if len(tables_with_field) > 2:  # Field appears in more than 2 tables
                    repeated_patterns[field_name] = {
                        'pattern': pattern_str,
                        'tables': tables_with_field
                    }

    for field_name, info in sorted(repeated_patterns.items(),
                                   key=lambda x: len(x[1]['tables']),
                                   reverse=True)[:15]:
        print(f"  {field_name:30} ({info['pattern']})")
        print(f"    Found in {len(info['tables'])} tables")

    # Find common record structures
    print("\n3. REPEATED RECORD STRUCTURES:")
    print("-" * 40)
    for structure_key, occurrences in record_structures.items():
        if len(occurrences) > 1:
            print(f"\n  Structure: {structure_key[:100]}...")
            print(f"  Appears {len(occurrences)} times:")
            for occ in occurrences[:5]:  # Show first 5 occurrences
                print(f"    - {occ['table']}.{occ['field']}")
            if len(occurrences) > 5:
                print(f"    ... and {len(occurrences) - 5} more")

    # Analyze field type distributions
    print("\n4. FIELD TYPE DISTRIBUTIONS:")
    print("-" * 40)
    for pattern, count in field_type_combinations.most_common(10):
        print(f"  {pattern:30} used {count} times")

    return repeated_patterns, record_structures, field_name_frequency

def get_record_structure_key(fields):
    """Get a unique key for a record structure based on its fields."""
    if not fields:
        return "empty"

    # Sort fields to create a consistent key
    field_signatures = []
    for field in sorted(fields, key=lambda x: x.get('name', '')):
        sig = f"{field.get('name', 'unknown')}:{field.get('type', 'unknown')}"
        field_signatures.append(sig)

    return "|".join(field_signatures)

def extract_common_types():
    """Extract common FHIR data types from the schema."""

    with open('dataset_schemas.json', 'r') as f:
        schemas = json.load(f)

    # Common FHIR complex types that appear as RECORD fields
    fhir_types = defaultdict(dict)

    # Known common FHIR types to look for
    common_type_fields = [
        'identifier', 'text', 'code', 'coding', 'reference',
        'period', 'asserter', 'recorder', 'performer', 'location',
        'subject', 'encounter', 'patient', 'practitioner'
    ]

    print("\n5. COMMON FHIR COMPLEX TYPES:")
    print("-" * 40)

    for table_name, table_info in schemas['tables'].items():
        for field in table_info['schema']:
            if field['name'] in common_type_fields and field['type'] == 'RECORD':
                field_name = field['name']
                if field_name not in fhir_types:
                    fhir_types[field_name] = {
                        'structure': field.get('fields', []),
                        'tables': []
                    }
                fhir_types[field_name]['tables'].append(table_name)

    for type_name, type_info in sorted(fhir_types.items(),
                                       key=lambda x: len(x[1]['tables']),
                                       reverse=True):
        print(f"\n  {type_name} (used in {len(type_info['tables'])} tables)")
        if type_info['structure']:
            print("    Structure:")
            for subfield in type_info['structure'][:3]:  # Show first 3 fields
                print(f"      - {subfield.get('name', 'unknown')}: {subfield.get('type', 'unknown')}")
            if len(type_info['structure']) > 3:
                print(f"      ... and {len(type_info['structure']) - 3} more fields")

if __name__ == "__main__":
    analyze_patterns()
    extract_common_types()