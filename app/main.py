from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import EvaluateRequest
from app.services.evaluation_service import CoreValidationException, evaluate_request
from app.utils.trace import generate_trace_id

app = FastAPI(
    title="AI Decision Risk Signal Monitoring API",
    version="0.1.0",
)

@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    request.state.trace_id = generate_trace_id()
    response = await call_next(request)
    response.headers["X-Trace-Id"] = request.state.trace_id
    return response

@app.exception_handler(RequestValidationError)
async def api_validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "trace_id", generate_trace_id())

    return JSONResponse(
        status_code=422,
        content={
            "trace_id": trace_id,
            "error_type": "api_validation_error",
            "message": "Request format or type is invalid.",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def system_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", generate_trace_id())

    return JSONResponse(
        status_code=500,
        content={
            "trace_id": trace_id,
            "error_type": "system_error",
            "message": "Unexpected internal server error.",
            "details": [],
        },
    )


@app.get("/health")
async def health(request: Request):
    return {
        "trace_id": request.state.trace_id,
        "status": "ok",
    }


@app.post("/evaluate")
async def evaluate(payload: EvaluateRequest, request: Request):
    trace_id = request.state.trace_id

    try:
        return evaluate_request(payload, trace_id)
    except CoreValidationException as exc:
        return JSONResponse(
            status_code=400,
            content={
                "trace_id": trace_id,
                "error_type": "core_validation_error",
                "message": exc.message,
                "details": [],
            },
        )