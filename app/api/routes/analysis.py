import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import get_settings
from app.rag.generation.llm_factory import LLMConfigurationError
from app.schemas.analysis import AnalysisDocument, CompareRequest, CompareResponse
from app.services.financial_analysis import (
    FinancialAnalysisError,
    compare_user_reports,
    list_user_documents,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["financial analysis"])


@router.get("/documents", response_model=list[AnalysisDocument])
def get_analysis_documents(
    current_user: User = Depends(get_current_user),
) -> list[AnalysisDocument]:
    try:
        return list_user_documents(str(current_user.id), get_settings())
    except Exception as exc:
        logger.exception("Could not list analysis documents for user_id=%s", current_user.id)
        raise HTTPException(status_code=503, detail="Document index is unavailable") from exc


@router.post("/compare", response_model=CompareResponse)
def compare_reports(
    request: CompareRequest,
    current_user: User = Depends(get_current_user),
) -> CompareResponse:
    settings = get_settings()
    try:
        reports = compare_user_reports(
            request.document_ids,
            user_id=str(current_user.id),
            settings=settings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FinancialAnalysisError as exc:
        logger.exception("Financial report comparison failed for user_id=%s", current_user.id)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Financial report comparison failed for user_id=%s", current_user.id)
        raise HTTPException(status_code=503, detail="Financial analysis is unavailable") from exc

    return CompareResponse(
        reports=reports,
        note=(
            "Figures are extracted only when a matching source quote and page can be verified. "
            "A blank value means the report did not provide a clear, verifiable figure. "
            "Year-over-year growth is calculated only for annual reports from the same company with matching currency and units."
        ),
    )
