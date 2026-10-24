from starlette.middleware.cors import CORSMiddleware

from app.main import app

# Find CORS middleware
for middleware in app.user_middleware:
    if middleware.cls == CORSMiddleware:
        print("CORS ALLOW_ORIGINS: ", middleware.kwargs.get("allow_origins"))
