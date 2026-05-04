from pydantic import BaseModel
from fastapi.responses import HTMLResponse


class BaseHTTPResponse(HTMLResponse):
    status_code: str = 200
    message: str = "OK"


class BaseHTTPRequeest(BaseModel):
    pass
