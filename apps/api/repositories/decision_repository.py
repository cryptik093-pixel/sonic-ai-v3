from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..database import DecisionORM, SessionLocal
from ..schemas.decision import Decision, DecisionCreate


class SQLAlchemyDecisionRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session or SessionLocal()

    def list_decisions(self, project_id: int | None = None, limit: int = 50) -> list[Decision]:
        query = self._session.query(DecisionORM).order_by(DecisionORM.created_at.desc())
        if project_id is not None:
            query = query.filter(DecisionORM.project_id == project_id)
        records = query.limit(limit).all()
        return [self._to_schema(record) for record in records]

    def create_decision(self, payload: DecisionCreate) -> Decision:
        now = datetime.utcnow().replace(microsecond=0)
        record = DecisionORM(
            project_id=payload.project_id,
            asset_id=payload.asset_id,
            timestamp=now,
            observation=payload.observation,
            evidence=payload.evidence,
            interpretation=payload.interpretation,
            confidence=payload.confidence,
            recommendation=payload.recommendation,
            selected_option=payload.selected_option,
            reason=payload.reason,
            action=payload.action,
            outcome=payload.outcome,
            producer_response=payload.producer_response,
            created_at=now,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return self._to_schema(record)

    def _to_schema(self, record: DecisionORM) -> Decision:
        return Decision(
            id=record.id,
            project_id=record.project_id,
            asset_id=record.asset_id,
            timestamp=record.timestamp,
            observation=record.observation,
            evidence=record.evidence,
            interpretation=record.interpretation,
            confidence=record.confidence,
            recommendation=record.recommendation,
            selected_option=record.selected_option,
            reason=record.reason,
            action=record.action,
            outcome=record.outcome,
            producer_response=record.producer_response,
            created_at=record.created_at,
        )


decision_store = SQLAlchemyDecisionRepository()
