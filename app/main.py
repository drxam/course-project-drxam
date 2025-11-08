from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="SecDev Course App", version="0.1.0")


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Example minimal entity (for tests/demo)
_DB = {"items": []}


def validate_item_name(name: str) -> str:
    """Валидация имени элемента с детальными сообщениями об ошибках"""
    if not name:
        raise ApiError(code="validation_error", message="name is required", status=422)
    if len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    if len(name.strip()) == 0:
        raise ApiError(
            code="validation_error",
            message="name cannot be empty or whitespace only",
            status=422,
        )
    return name.strip()


@app.post("/items")
def create_item(name: str):
    # Используем функцию валидации для переиспользования
    validated_name = validate_item_name(name)

    item = {"id": len(_DB["items"]) + 1, "name": validated_name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)
