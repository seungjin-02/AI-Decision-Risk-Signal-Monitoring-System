from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db.alert_repository import AlertRepository
from app.db.connection import init_db
from app.schemas import EvaluateRequest, EvaluateResponse, ErrorResponse
from app.services.evaluation_service import (
    CoreValidationException,
    evaluate_request,
)
from app.utils.trace import generate_trace_id


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "alerts.db"


def get_trace_id(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)

    if trace_id is None:
        trace_id = generate_trace_id()
        request.state.trace_id = trace_id

    return trace_id


async def add_trace_id(request: Request, call_next):
    request.state.trace_id = generate_trace_id()

    response = await call_next(request)

    response.headers["X-Trace-Id"] = request.state.trace_id

    return response


async def api_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    trace_id = get_trace_id(request)

    return JSONResponse(
        status_code=422,
        content={
            "trace_id": trace_id,
            "error_type": "api_validation_error",
            "message": "Request format or type is invalid.",
            "details": exc.errors(),
        },
    )


async def core_validation_exception_handler(
    request: Request,
    exc: CoreValidationException,
):
    trace_id = get_trace_id(request)

    return JSONResponse(
        status_code=400,
        content={
            "trace_id": trace_id,
            "error_type": "core_validation_error",
            "message": str(exc),
            "details": [],
        },
    )


async def system_exception_handler(
    request: Request,
    exc: Exception,
):
    trace_id = get_trace_id(request)

    return JSONResponse(
        status_code=500,
        content={
            "trace_id": trace_id,
            "error_type": "system_error",
            "message": "Unexpected internal server error.",
            "details": [],
        },
    )


async def health(request: Request):
    return {
        "trace_id": get_trace_id(request),
        "status": "ok",
    }


async def evaluate(
    payload: EvaluateRequest,
    request: Request,
):
    trace_id = get_trace_id(request)

    return evaluate_request(
        payload,
        trace_id,
    )


def create_app(
    db_path: str | Path = DEFAULT_DB_PATH,
) -> FastAPI:
    db_path = Path(db_path)

    db_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    init_db(db_path)

    application = FastAPI(
        title="AI Decision Risk Signal Monitoring API",
        version="0.1.0",
    )

    application.state.alert_repository = AlertRepository(db_path)

    application.middleware("http")(add_trace_id)

    application.add_exception_handler(
        RequestValidationError,
        api_validation_exception_handler,
    )

    application.add_exception_handler(
        CoreValidationException,
        core_validation_exception_handler,
    )

    application.add_exception_handler(
        Exception,
        system_exception_handler,
    )

    application.add_api_route(
        "/health",
        health,
        methods=["GET"],
    )

    application.add_api_route(
        "/evaluate",
        evaluate,
        methods=["POST"],
        response_model=EvaluateResponse,
        responses={
            400: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
        },
    )

    return application


app = create_app()