# Swagger Testing Guide

Use this when someone asks for "API testing in Swagger" for the backend.

## What Already Exists

- FastAPI Swagger UI: `http://localhost:8000/docs`
- ReDoc view: `http://localhost:8000/redoc`
- Generated OpenAPI schema file: [openapi.json](./openapi.json)
- Generated endpoint catalog: [API_ENDPOINT_CATALOG.md](./API_ENDPOINT_CATALOG.md)

## How To Test APIs In Swagger

1. Start the backend server.
2. Open `http://localhost:8000/docs`.
3. Click `Authorize` in Swagger.
4. Enter your email or username in the `username` field.
5. Enter your password.
6. Swagger will call `POST /api/v1/auth/token` automatically and store the bearer token.
7. Test endpoints by tag.

If you want to log in manually instead, you can still use `POST /api/v1/auth/login` and copy the `access_token` yourself.

## Recommended Testing Order

1. `Health`
2. `Authentication`
3. Role-specific modules:
   `Orders`, `Warehouses`, `Warehouse Operations`, `Inventory`, `Labourers`, `Logistics Manager`, `Live Tracking`, `Customer`, `Vendor`, `Finance`, `AI`

## Notes For Your Team

- You do not need to hand-write all endpoint docs one by one.
- FastAPI already generates Swagger from the router definitions and schemas.
- If routes change, regenerate docs with:

```powershell
cd backend
python export_api_docs.py
```

## Deliverables Created

- [openapi.json](./openapi.json)
- [API_ENDPOINT_CATALOG.md](./API_ENDPOINT_CATALOG.md)
- [SWAGGER_TESTING_GUIDE.md](./SWAGGER_TESTING_GUIDE.md)
