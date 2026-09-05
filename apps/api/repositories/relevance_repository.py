"""Read existing persisted checkpoints; do not synthesize intelligence."""
from pydantic import BaseModel, ConfigDict
from ..database import RelevanceCheckpointORM, SessionLocal


class Checkpoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_id: int | None
    project_id: int | None
    persistence_decision: str
    reason: str
    confidence_score: float


class RelevanceRepository:
    def list_checkpoints(self, project_id: int | None = None, limit: int = 20):
        with SessionLocal() as session:
            query = session.query(RelevanceCheckpointORM)
            if project_id is not None:
                query = query.filter_by(project_id=project_id)
            return [Checkpoint.model_validate(row) for row in
                    query.order_by(RelevanceCheckpointORM.id.desc()).limit(limit).all()]


relevance_store = RelevanceRepository()
