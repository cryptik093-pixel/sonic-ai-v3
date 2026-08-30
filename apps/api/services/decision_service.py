from ..schemas.decision import DecisionCreate, Decision
from ..repositories.decision_repository import decision_store


class DecisionService:
    def list_decisions(self, project_id: int | None = None):
        return decision_store.list_decisions(project_id=project_id)

    def create_decision(self, payload: DecisionCreate) -> Decision:
        return decision_store.create_decision(payload)


decision_service = DecisionService()
