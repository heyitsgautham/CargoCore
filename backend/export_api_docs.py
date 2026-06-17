from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json

from app.main import app


ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
OPENAPI_JSON_PATH = DOCS_DIR / "openapi.json"
CATALOG_MD_PATH = DOCS_DIR / "API_ENDPOINT_CATALOG.md"


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def humanize_identifier(value: str) -> str:
    if not value:
        return "Unspecified"

    value = value.split("_api_v1_", 1)[0]
    parts = [part for part in value.replace("-", "_").split("_") if part]
    if not parts:
        return "Unspecified"
    return " ".join(part.capitalize() for part in parts)


def schema_name(schema: dict | None) -> str:
    if not schema:
        return "None"

    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]

    if schema.get("type") == "array":
        return f"array[{schema_name(schema.get('items'))}]"

    for key in ("allOf", "anyOf", "oneOf"):
        if key in schema and schema[key]:
            names = [schema_name(item) for item in schema[key]]
            return " / ".join(names)

    if "title" in schema:
        return str(schema["title"])

    if "type" in schema:
        return str(schema["type"])

    return "Unknown"


def request_body_summary(operation: dict) -> str:
    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    if not content:
        return "None"

    parts: list[str] = []
    for media_type, media_info in content.items():
        parts.append(f"{media_type} -> {schema_name(media_info.get('schema'))}")
    return "; ".join(parts)


def response_summary(operation: dict) -> str:
    responses = operation.get("responses", {})
    success_codes = sorted(code for code in responses if code.startswith("2"))
    if not success_codes:
        return "Unknown"

    code = success_codes[0]
    response = responses.get(code, {})
    content = response.get("content", {})
    if not content:
        return code

    media_type, media_info = next(iter(content.items()))
    return f"{code} {media_type} -> {schema_name(media_info.get('schema'))}"


def feature_summary(operation: dict) -> str:
    summary = (operation.get("summary") or "").strip()
    if summary:
        return summary

    description = (operation.get("description") or "").strip()
    if description:
        return description.splitlines()[0].strip()

    return humanize_identifier(operation.get("operationId", ""))


def auth_summary(operation: dict) -> str:
    security = operation.get("security")
    if not security:
        return "No"

    schemes: list[str] = []
    for requirement in security:
        schemes.extend(requirement.keys())

    if not schemes:
        return "Yes"

    normalized = []
    for scheme in schemes:
        if "oauth2" in scheme.lower() or "bearer" in scheme.lower():
            normalized.append("Bearer token")
        else:
            normalized.append(scheme)
    return ", ".join(sorted(set(normalized)))


def build_catalog(schema: dict) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    paths: dict = schema.get("paths", {})
    operations: list[dict] = []

    for path, methods in sorted(paths.items()):
        for method, operation in sorted(methods.items()):
            tags = operation.get("tags") or ["Untagged"]
            primary_tag = tags[0]
            operations.append(
                {
                    "tag": primary_tag,
                    "method": method.upper(),
                    "path": path,
                    "feature": feature_summary(operation),
                    "auth": auth_summary(operation),
                    "request": request_body_summary(operation),
                    "response": response_summary(operation),
                    "operation_id": operation.get("operationId", ""),
                }
            )

    tag_counts = Counter(item["tag"] for item in operations)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in operations:
        grouped[item["tag"]].append(item)

    lines: list[str] = []
    lines.append("# API Endpoint Catalog")
    lines.append("")
    lines.append(f"Generated from FastAPI OpenAPI schema on `{generated_at}`.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Tags: `{len(tag_counts)}`")
    lines.append(f"- Paths: `{len(paths)}`")
    lines.append(f"- Operations: `{len(operations)}`")
    lines.append(f"- Swagger UI: `http://localhost:8000/docs`")
    lines.append(f"- ReDoc: `http://localhost:8000/redoc`")
    lines.append("")
    lines.append("## Swagger Testing Flow")
    lines.append("")
    lines.append("1. Start the backend.")
    lines.append("2. Open `/docs`.")
    lines.append("3. Click `Authorize` in Swagger UI.")
    lines.append("4. Enter your email or username in the `username` field and your password in the `password` field.")
    lines.append("5. Swagger will call `POST /api/v1/auth/token` automatically and store the bearer token.")
    lines.append("6. Expand endpoints by tag and test them directly from Swagger.")
    lines.append("")
    lines.append("Manual alternative: call `POST /api/v1/auth/login`, copy the `access_token`, and paste it into `Authorize`.")
    lines.append("")
    lines.append("## Tag Counts")
    lines.append("")
    lines.append("| Tag | Operations |")
    lines.append("| --- | ---: |")
    for tag, count in sorted(tag_counts.items()):
        lines.append(f"| {escape_cell(tag)} | {count} |")
    lines.append("")

    for tag in sorted(grouped):
        lines.append(f"## {tag}")
        lines.append("")
        lines.append("| Method | Path | Feature | Auth | Request Body | Success Response |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for item in grouped[tag]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        item["method"],
                        f"`{escape_cell(item['path'])}`",
                        escape_cell(item["feature"]),
                        escape_cell(item["auth"]),
                        f"`{escape_cell(item['request'])}`",
                        f"`{escape_cell(item['response'])}`",
                    ]
                )
                + " |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()

    OPENAPI_JSON_PATH.write_text(
        json.dumps(schema, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    CATALOG_MD_PATH.write_text(build_catalog(schema), encoding="utf-8")

    total_paths = len(schema.get("paths", {}))
    total_operations = sum(len(methods) for methods in schema.get("paths", {}).values())
    print(f"Wrote {OPENAPI_JSON_PATH}")
    print(f"Wrote {CATALOG_MD_PATH}")
    print(f"Paths: {total_paths}")
    print(f"Operations: {total_operations}")


if __name__ == "__main__":
    main()
