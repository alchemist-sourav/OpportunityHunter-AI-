from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.exceptions import CredentialNotFoundError
from app.core.security import AuthUser
from app.database.engine import get_session
from app.schemas.credentials import (
    FirecrawlCredentialPut,
    FirecrawlCredentialStored,
    FirecrawlCredentialStatus,
)
from app.services import credential_service

router = APIRouter(prefix="/credentials/firecrawl", tags=["credentials"])

Session = Annotated[Session, Depends(get_session)]
AuthenticatedUser = Annotated[AuthUser, Depends(get_current_user)]


@router.get("/status", response_model=FirecrawlCredentialStatus)
def firecrawl_status(user: AuthenticatedUser, session: Session) -> FirecrawlCredentialStatus:
    credential = credential_service.get_firecrawl_credential(session, user.user_id)
    return FirecrawlCredentialStatus(**credential_service.credential_to_status(credential))


@router.put("", response_model=FirecrawlCredentialStored)
def firecrawl_put(
    payload: FirecrawlCredentialPut,
    user: AuthenticatedUser,
    session: Session,
) -> FirecrawlCredentialStored:
    credential, validation = credential_service.save_firecrawl_credential(session, user.user_id, payload.api_key)
    return FirecrawlCredentialStored(
        provider=credential.provider,
        configured=credential.is_active,
        updated_at=credential.updated_at,
        validation=validation,
    )


@router.delete("", response_model=FirecrawlCredentialStatus)
def firecrawl_delete(user: AuthenticatedUser, session: Session) -> FirecrawlCredentialStatus:
    if not credential_service.delete_firecrawl_credential(session, user.user_id):
        raise CredentialNotFoundError()
    return FirecrawlCredentialStatus(provider="firecrawl", configured=False)
