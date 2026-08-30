"""Context Engine — assembles project, asset, and memory context for AI sessions."""

from ..repositories.memory_repository import memory_store
from ..repositories.project_repository import project_store
from ..services.asset_service import asset_service


class ContextEngine:
    def build_context(
        self,
        user_message: str,
        project_id: int | None = None,
    ) -> tuple[str, list[str]]:
        sections: list[str] = []
        context_labels: list[str] = []

        if project_id is not None:
            project_section = self._build_project_context(project_id)
            if project_section:
                sections.append(project_section)
                context_labels.append("project")

        asset_section = self._build_asset_context(project_id)
        if asset_section:
            sections.append(asset_section)
            context_labels.append("assets")

        memory_section = self._build_memory_context(user_message, project_id)
        if memory_section:
            sections.append(memory_section)
            context_labels.append("memory")

        if not sections:
            return "", context_labels

        return "\n\n".join(sections), context_labels

    def _build_project_context(self, project_id: int) -> str | None:
        projects = project_store.list_projects()
        project = next((item for item in projects if item.id == project_id), None)
        if project is None:
            return None

        return (
            f"### Active Project\n"
            f"- Name: {project.name}\n"
            f"- Artist: {project.artist}\n"
            f"- Genre: {project.genre}\n"
            f"- BPM: {project.bpm}\n"
            f"- Key: {project.key}\n"
            f"- Status: {project.status.value}\n"
            f"- Notes: {project.notes or 'None'}"
        )

    def _build_asset_context(self, project_id: int | None) -> str | None:
        assets = asset_service.list_assets()
        if project_id is not None:
            assets = [asset for asset in assets if asset.project_id == project_id]

        if not assets:
            return None

        lines = ["### Project Assets"]
        for asset in assets[:12]:
            meta_parts = []
            if asset.bpm:
                meta_parts.append(f"{asset.bpm} BPM")
            if asset.key:
                meta_parts.append(asset.key)
            if asset.duration:
                meta_parts.append(f"{asset.duration:.1f}s")
            meta = ", ".join(meta_parts) if meta_parts else "no metadata"
            lines.append(f"- {asset.filename} ({asset.file_type}, {meta})")

        return "\n".join(lines)

    def _build_memory_context(self, user_message: str, project_id: int | None) -> str | None:
        memories = memory_store.search_relevant(user_message, project_id=project_id, limit=6)
        if not memories:
            memories = memory_store.list_memories(project_id=project_id, limit=4)

        if not memories:
            return None

        lines = ["### Studio Memory"]
        for memory in memories:
            confidence_label = "high" if memory.confidence >= 0.7 else "medium" if memory.confidence >= 0.4 else "low"
            lines.append(
                f"- [{memory.category.value}, {confidence_label} confidence] {memory.content}"
            )

        return "\n".join(lines)


context_engine = ContextEngine()
