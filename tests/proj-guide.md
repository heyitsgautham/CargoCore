# Sprint 2 Deliverables

1. Changes made based on user feedback
2. **Updated** documentation of API’s in a Swagger-compatible YAML file.
3. Backend code of the implemented API’s
   *Note: YAML file must have all the error handling, User stories mapping and description of each API listed.*
4. Proper test cases to test an **Updated API**
5. Submit pytest code for the **Updated API**

---

# Do & Don’t Checklist

| Do | Don’t |
| :--- | :--- |
| Design each endpoint in **Swagger/YAML first**; confirm parameters & responses with the team. | “Prototype” in code without updating the YAML spec. |
| Follow **consistent URL naming** (`/api/v1/...`), HTTP verbs, status codes, and error format. | Return 200 for everything or mix snake_case and camelCase randomly. |
| Use **meaningful error messages** and document them in the spec. | Throw generic “Internal Server Error” without detail. |
| Write basic unit tests (pytest) immediately after coding an endpoint. | Plan to add tests after integration. |
| Record any discovered bugs as GitHub Issues to be showcased in Milestone 5. | Fix silently without a trace—loses learning evidence. |
| Create a **test matrix** listing endpoints, positive & negative cases, and integration flows. | Test ad-hoc in Postman and hope coverage is “good enough.” |
| Automate repeatable tests with **pytest + requests** (or similar). | Rely solely on manual clicking through the UI. |
| Document **input, expected output, actual output** for each showcased API in the PDF. | Paste raw console logs with no explanation. |
| Highlight at least one case where **expected ≠ actual** and explain the fix. | Hide failures to make the report look “perfect.” |
| Take **screenshots** (or terminal grabs) of pytest results for 4–5 key APIs. | Submit **.py** files or huge test dumps, the grader can’t read quickly. |