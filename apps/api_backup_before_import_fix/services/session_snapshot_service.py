from schemas.session_snapshot import SessionSnapshotCreate, SessionSnapshot
from repositories.session_snapshot_repository import snapshot_store


class SessionSnapshotService:
    def list_snapshots(self, project_id: int | None = None):
        return snapshot_store.list_snapshots(project_id=project_id)

    def create_snapshot(self, payload: SessionSnapshotCreate) -> SessionSnapshot:
        return snapshot_store.create_snapshot(payload)


snapshot_service = SessionSnapshotService()
