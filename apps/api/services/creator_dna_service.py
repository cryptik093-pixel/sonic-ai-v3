"""Expose persisted signals for the existing context snapshot consumer."""
from ..database import CreatorDNASignalORM, SessionLocal


class CreatorDNAService:
    def build_profile(self, project_id: int | None = None):
        with SessionLocal() as session:
            query = session.query(CreatorDNASignalORM)
            if project_id is not None:
                query = query.filter_by(project_id=project_id)
            return {"project_id": project_id, "signals": [
                {"category": row.category, "signal": row.signal,
                 "strength": row.strength, "confidence": row.confidence,
                 "evidence_count": row.evidence_count}
                for row in query.order_by(CreatorDNASignalORM.id).all()
            ]}


creator_dna_service = CreatorDNAService()
