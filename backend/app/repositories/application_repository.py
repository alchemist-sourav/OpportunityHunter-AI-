import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application_models import UserApplication


class ApplicationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: str, opportunity_id: str, status: str = "interested",
               notes: str | None = None, deadline: datetime | None = None) -> UserApplication:
        application = UserApplication(
            id=str(uuid.uuid4()),
            user_id=user_id,
            opportunity_id=opportunity_id,
            status=status,
            applied_date=datetime.now(timezone.utc) if status == "applied" else None,
            deadline=deadline,
            notes=notes,
        )
        self.session.add(application)
        self.session.flush()
        return application

    def get_by_id(self, application_id: str) -> UserApplication | None:
        return self.session.get(UserApplication, application_id)

    def get_by_user_and_opportunity(self, user_id: str, opportunity_id: str) -> UserApplication | None:
        stmt = select(UserApplication).where(
            UserApplication.user_id == user_id,
            UserApplication.opportunity_id == opportunity_id,
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_user(self, user_id: str, status: str | None = None, limit: int = 100, offset: int = 0) -> list[UserApplication]:
        stmt = select(UserApplication).where(UserApplication.user_id == user_id)
        if status:
            stmt = stmt.where(UserApplication.status == status)
        stmt = stmt.order_by(UserApplication.created_at.desc()).limit(limit).offset(offset)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def update(self, application: UserApplication, status: str | None = None,
               notes: str | None = None, deadline: datetime | None = None) -> UserApplication:
        if status is not None:
            application.status = status
        if notes is not None:
            application.notes = notes
        if deadline is not None:
            application.deadline = deadline
        application.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return application

    def delete(self, application: UserApplication) -> None:
        self.session.delete(application)
        self.session.flush()