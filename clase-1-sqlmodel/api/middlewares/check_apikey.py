import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class CheckApikeyMW:
    async def verify_header_middleware(self, request: Request, call_next):
        # Let the docs UI through without an API key
        if request.url.path in ("/docs", "/openapi.json"):
            return await call_next(request)

        # Retrieve the header value (FastAPI normalizes headers to lowercase)
        api_key = request.headers.get("x-api-key")

        # Check if the header matches your validation rules
        if api_key != "123":
            # Block the request and return an error response immediately
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Missing or invalid API Key"}
            )
        
        # If valid, pass the request to the next route or middleware
        response = await call_next(request)
        return response