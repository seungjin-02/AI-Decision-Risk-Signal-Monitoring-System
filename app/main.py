from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.schemas import EvaluateRequest, EvaluateResponse, ErrorResponse
from app.services.evaluation_service import CoreValidationException, evaluate_request
from app.utils.trace import generate_trace_id

app = FastAPI(
    title="AI Decision Risk Signal Monitoring API",
    version="0.1.0",
)

def get_trace_id(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    if trace_id is None:
        trace_id = generate_trace_id()
        request.state.trace_id = trace_id

    return trace_id

@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    request.state.trace_id = generate_trace_id()
    response = await call_next(request)
    response.headers["X-Trace-Id"] = request.state.trace_id

    return response

@app.exception_handler(RequestValidationError)
async def api_validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    trace_id = get_trace_id(request)

    return JSONResponse(
        status_code=422,
        content={
            "trace_id": trace_id,
            "error_type": "api_validation_error",
            "message": "Request format or type is invalid.",
            "details": exc.errors()
        }
    )

@app.exception_handler(CoreValidationException)
async def core_validation_exception_handler(
    request: Request,
    exc: CoreValidationException
):
    trace_id = get_trace_id(request)

    return JSONResponse(
        status_code=400,
        content={
            "trace_id": trace_id,
            "error_type": "core_validation_error",
            "message": str(exc),
            "details": []
        },
    )

@app.exception_handler(Exception)
async def system_exception_handler(
    request: Request,
    exc: Exception
):
    trace_id = get_trace_id(request)

    return JSONResponse(
        status_code=500,
        content={
            "trace_id": trace_id,
            "error_type": "system_error",
            "message": "Unexpected internal server error.",
            "details": []
        }
    )

@app.get("/health")
async def health(request: Request):
    return {
        "trace_id": get_trace_id(request),
        "status": "ok"
    }

@app.post(
    "/evaluate",
    response_model=EvaluateResponse,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def evaluate(payload: EvaluateRequest, request: Request):
    trace_id = get_trace_id(request)

    return evaluate_request(payload, trace_id)