# CargoCore API Documentation (Offline)

This folder contains offline/downloadable versions of the CargoCore API documentation.

## 📁 Files

### 1. **openapi.json**
- **Format:** JSON (OpenAPI 3.0 Specification)
- **Use for:**
  - Import into Postman or Insomnia
  - Generate client SDKs
  - API testing tools
  - CI/CD integration

**How to use:**
- **Postman:** Import > Link > `file:///.../openapi.json`
- **Insomnia:** Create > Import From > File

---

### 2. **swagger-ui.html**
- **Format:** Interactive HTML (Swagger UI)
- **Use for:**
  - Browse API endpoints visually
  - Try API calls directly from browser
  - Share with team members

**How to use:**
1. Open `swagger-ui.html` in your browser
2. All 188 endpoints will be displayed
3. Click any endpoint to see details
4. ⚠️ Note: Authentication won't work in offline mode, but you can see all request/response schemas

---

### 3. **API_DOCUMENTATION.md**
- **Format:** Markdown (Text)
- **Use for:**
  - Read in VS Code, Notion, or any markdown viewer
  - Search through all endpoints with Ctrl+F
  - Copy/paste into documentation
  - Print-friendly version

**How to use:**
- Open in VS Code: Right-click > "Open Preview"
- Or view in GitHub, GitLab, etc.

---

## 🚀 Quick Start

### View Offline Swagger UI
```bash
# Just open this file in your browser:
backend/docs/swagger-ui.html
```

### Import into Postman
1. Open Postman
2. Import > File > Select `openapi.json`
3. You'll get all 188 endpoints organized by tag

### Search All Endpoints
```bash
# Search in markdown file
code API_DOCUMENTATION.md
# Then press Ctrl+F and search for endpoint names
```

---

## 📊 Documentation Stats

- **Total Endpoints:** 188
- **API Version:** 1.0.0
- **Last Generated:** 2026-03-26

---

## 🔄 Regenerate Documentation

If the API changes, regenerate the docs:

```bash
cd backend/docs

# Download latest OpenAPI spec
curl http://127.0.0.1:8000/openapi.json -o openapi.json

# Regenerate markdown
python generate_markdown_docs.py
```

---

## 📝 Notes

- The offline Swagger UI requires internet for CDN resources (Swagger UI library)
- For fully offline use, view the markdown or JSON files
- Authentication in offline mode won't work - use the live docs at http://127.0.0.1:8000/docs for testing
