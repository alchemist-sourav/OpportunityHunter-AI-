from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.application_models import UserApplication
from app.repositories.application_repository import ApplicationRepository


class ApplicationService:
    """Service layer for application tracking."""

    def save_opportunity(
        self,
        session: Session,
        user_id: str,
        opportunity_id: str,
        status: str | None = None,
        notes: str | None = None,
        deadline: datetime | None = None,
    ) -> UserApplication:
        """Save an opportunity to a user's application tracker.

        If an application already exists for this user and opportunity,
        it is updated; otherwise a new application is created.
        """
        repo = ApplicationRepository(session)
        existing = repo.get_by_user_and_opportunity(user_id, opportunity_id)
        if existing:
            return repo.update(existing, status=status or existing.status,
                               notes=notes, deadline=deadline)
        return repo.create(user_id, opportunity_id, status=status or "interested",
                           notes=notes, deadline=deadline)

    def get_user_applications(
        self,
        session: Session,
        user_id: str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, object]:
        """List applications with pagination and filters for a user."""
        repo = ApplicationRepository(session)
        items = repo.get_by_user(user_id, status=status, limit=limit, offset=offset)
        count_stmt = select(func.count()).select_from(UserApplication).where(
            UserApplication.user_id == user_id
        )
        total = session.scalar(count_stmt) or 0
        return {"total": total, "items": items, "limit": limit, "offset": offset}

    def get_application(self, session: Session, user_id: str, application_id: str) -> UserApplication | None:
        """Get a specific application, ensuring ownership."""
        repo = ApplicationRepository(session)
        application = repo.get_by_id(application_id)
        if not application or application.user_id != user_id:
            return None
        return application

    def update_application(
        self,
        session: Session,
        user_id: str,
        application_id: str,
        status: str | None = None,
        notes: str | None = None,
        deadline: datetime | None = None,
    ) -> UserApplication | None:
        """Update an application status and/or notes."""
        repo = ApplicationRepository(session)
        application = repo.get_by_id(application_id)
        if not application or application.user_id != user_id:
            return None
        return repo.update(application, status=status, notes=notes, deadline=deadline)

    def delete_application(self, session: Session, user_id: str, application_id: str) -> bool:
        """Delete an application."""
        repo = ApplicationRepository(session)
        application = repo.get_by_id(application_id)
        if not application or application.user_id != user_id:
            return False
        repo.delete(application)
        return True