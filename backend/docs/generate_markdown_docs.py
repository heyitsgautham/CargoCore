"""
Generate Markdown documentation from OpenAPI JSON
Usage: python generate_markdown_docs.py
"""
import json
from pathlib import Path

def generate_markdown():
    # Load OpenAPI spec
    docs_dir = Path(__file__).parent
    with open(docs_dir / 'openapi.json', 'r', encoding='utf-8') as f:
        spec = json.load(f)

    md_lines = []

    # Header
    md_lines.append(f"# {spec['info']['title']}")
    md_lines.append(f"\n**Version:** {spec['info']['version']}")
    md_lines.append(f"\n**Description:** {spec['info'].get('description', 'N/A')}")
    md_lines.append("\n---\n")

    # Group endpoints by tags
    paths = spec.get('paths', {})
    endpoints_by_tag = {}

    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ['get', 'post', 'put', 'patch', 'delete']:
                tags = details.get('tags', ['Untagged'])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    endpoints_by_tag[tag].append({
                        'path': path,
                        'method': method.upper(),
                        'details': details
                    })

    # Generate documentation for each tag
    for tag, endpoints in sorted(endpoints_by_tag.items()):
        md_lines.append(f"\n## {tag}\n")

        for endpoint in endpoints:
            method = endpoint['method']
            path = endpoint['path']
            details = endpoint['details']

            md_lines.append(f"\n### {method} `{path}`\n")

            # Summary and description
            if 'summary' in details:
                md_lines.append(f"**Summary:** {details['summary']}\n")
            if 'description' in details:
                md_lines.append(f"**Description:** {details['description']}\n")

            # Security
            if 'security' in details:
                md_lines.append("\n**Authentication Required:** Yes\n")

            # Parameters
            if 'parameters' in details:
                md_lines.append("\n**Parameters:**\n")
                for param in details['parameters']:
                    required = "Required" if param.get('required', False) else "Optional"
                    param_type = param.get('schema', {}).get('type', 'string')
                    md_lines.append(f"- `{param['name']}` ({param['in']}) [{required}] - *{param_type}* - {param.get('description', 'N/A')}\n")

            # Request Body
            if 'requestBody' in details:
                md_lines.append("\n**Request Body:**\n")
                content = details['requestBody'].get('content', {})
                for content_type, schema_info in content.items():
                    md_lines.append(f"- Content-Type: `{content_type}`\n")
                    schema_ref = schema_info.get('schema', {}).get('$ref', '')
                    if schema_ref:
                        schema_name = schema_ref.split('/')[-1]
                        md_lines.append(f"- Schema: `{schema_name}`\n")

            # Responses
            if 'responses' in details:
                md_lines.append("\n**Responses:**\n")
                for status_code, response_info in details['responses'].items():
                    desc = response_info.get('description', 'N/A')
                    md_lines.append(f"- **{status_code}**: {desc}\n")

            md_lines.append("\n---\n")

    # Write to file
    output_file = docs_dir / 'API_DOCUMENTATION.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(md_lines))

    print(f"[OK] Generated {output_file}")
    print(f"  Total endpoints documented: {sum(len(eps) for eps in endpoints_by_tag.values())}")

if __name__ == '__main__':
    generate_markdown()
