from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db.alert_repository import AlertRepository, PersistenceError
from app.db.connection import init_db
from app.services.evaluation_service import CoreValidationException, evaluate_request
from app.utils.trace import generate_trace_id
from app.schemas import EvaluateRequest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "alert.db"

def get_alert_repository() -> AlertRepository:
    return AlertRepository(DATABASE_PATH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(DATABASE_PATH)
    yield

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = generate_trace_id()
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id

    return response

@app.exception_handler(RequestValidationError)
async def api_validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = request.state.trace_id

    return JSONResponse(
        status_code=422,
        content={
            "trace_id": trace_id,
            "error_type": "api_validation_error",
            "message": "Request format or type is invalid.",
            "details": exc.errors(),
        }
    )

@app.exception_handler(CoreValidationException)
async def core_validation_exception_handler(request: Request, exc: CoreValidationException):
    trace_id = request.state.trace_id

    return JSONResponse(
        status_code=400,
        content={
            "trace_id": trace_id,
            "error_type": "core_validation_error",
            "message": str(exc),
            "details": [],
        },
    )

@app.exception_handler(PersistenceError)
async def persistence_exception_handler(request: Request, exc: PersistenceError):
    trace_id = request.state.trace_id

    return JSONResponse(
        status_code=500,
        headers={"X-Trace-ID": trace_id},
        content={
            "trace_id": trace_id,
            "error_type": "persistence_error",
            "message": "Failed to persist evaluation result",
            "details": [],
        },
    )

@app.exception_handler(Exception)
async def system_exception_handler(request: Request, exc: Exception):
    trace_id = request.state.trace_id

    return JSONResponse(
        status_code=500,
        headers={"X-Trace-ID": trace_id},
        content={
            "trace_id": trace_id,
            "error_type": "system_error",
            "message": "Unexpected internal server error",
            "details": [],
        },
    )

@app.post("/evaluate")
def evaluate_endpoint(payload: EvaluateRequest, request: Request, repository: AlertRepository = Depends(get_alert_repository)):
    trace_id = request.state.trace_id

    return evaluate_request(payload, trace_id, repository)
