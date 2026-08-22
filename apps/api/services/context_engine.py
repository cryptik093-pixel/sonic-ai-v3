"""Context Engine — assembles typed, provenance-aware AI context."""

from __future__ import annotations

from schemas.context import (
    AssetContext,
    ChatContext,
    ContextArea,
    ContextObservation,
    ContextPackage,
    ContextSourceType,
    MemoryContext,
    ProjectContext,
    SourceRef,
    utc_now,
)
from repositories.memory_repository import memory_store
from repositories.project_repository import project_store
from services.asset_service import asset_service
from repositories.chat_repository import chat_store


class ContextEngine:
    def build_context(
        self,
        user_message: str,
        project_id: int | None = None,
        session_id: int | None = None,
    ) -> tuple[str, list[str]]:
        """Return the legacy rendered context contract for existing callers."""
        package = self.build_context_package(
            user_message=user_message,
            project_id=project_id,
            session_id=session_id,
        )
        return self.render_context_package(package), package.context_labels

    def build_context_package(
        self,
        user_message: str,
        project_id: int | None = None,
        session_id: int | None = None,
    ) -> ContextPackage:
        observations: list[ContextObservation] = []
        project_context = self._build_project_package(project_id, observations)
        asset_contexts = self._build_asset_packages(project_id, observations)
        memory_contexts = self._build_memory_packages(user_message, project_id, observations)
        chat_context = self._build_chat_package(session_id, observations)

        labels: list[str] = []
        if project_context is not None:
            labels.append("project")
        if asset_contexts:
            labels.append("assets")
        if memory_contexts:
            labels.append("memory")
        return ContextPackage(
            task_query=user_message,
            project=project_context,
            assets=asset_contexts,
            memories=memory_contexts,
            chat=chat_context,
            observations=observations,
            context_labels=labels,
            retrieved_at=utc_now(),
        )

    def render_context_package(self, package: ContextPackage) -> str:
        sections: list[str] = []

        if package.project:
            lines = ["### Active Project"]
            values = {item.field: item.value for item in package.project.observations}
            for field in ("name", "artist", "genre", "bpm", "key", "status", "notes"):
                if field in values:
                    label = field.capitalize()
                    lines.append(f"- {label}: {values[field] or 'None'}")
            sections.append("\n".join(lines))

        if package.assets:
            lines = ["### Project Assets"]
            for asset in package.assets:
                values = {item.field: item.value for item in asset.observations}
                meta_parts = []
                if values.get("bpm"):
                    meta_parts.append(f"{values['bpm']} BPM")
                if values.get("key"):
                    meta_parts.append(str(values["key"]))
                if values.get("duration"):
                    meta_parts.append(f"{float(values['duration']):.1f}s")
                meta = ", ".join(meta_parts) if meta_parts else "no metadata"
                lines.append(f"- {values.get('filename', 'Unknown')} ({values.get('file_type', 'unknown')}, {meta})")
            sections.append("\n".join(lines))

        if package.memories:
            lines = ["### Studio Memory"]
            for memory in package.memories:
                values = {item.field: item.value for item in memory.observations}
                confidence = memory.confidence
                confidence_label = "high" if confidence >= 0.7 else "medium" if confidence >= 0.4 else "low"
                lines.append(f"- [{memory.category.value}, {confidence_label} confidence] {values.get('content', '')}")
            sections.append("\n".join(lines))

        if not sections:
            return ""

        return "\n\n".join(sections)

    def _build_project_package(
        self,
        project_id: int | None,
        observations: list[ContextObservation],
    ) -> ProjectContext | None:
        if project_id is None:
            return None
        project = next((item for item in project_store.list_projects() if item.id == project_id), None)
        if project is None:
            return None
        fields = {
            "name": project.name,
            "artist": project.artist,
            "genre": project.genre,
            "bpm": project.bpm,
            "key": project.key,
            "status": project.status.value,
            "notes": project.notes,
        }
        items = [self._observation(ContextArea.PROJECT, field, value, ContextSourceType.PROJECT, str(project.id), "project repository", project.updated_at) for field, value in fields.items()]
        observations.extend(items)
        return ProjectContext(project_id=project.id, observations=items)

    def _build_asset_packages(
        self,
        project_id: int | None,
        observations: list[ContextObservation],
    ) -> list[AssetContext]:
        assets = asset_service.list_assets()
        if project_id is not None:
            assets = [asset for asset in assets if asset.project_id == project_id]
        contexts: list[AssetContext] = []
        for asset in assets[:12]:
            fields = {
                "filename": asset.filename,
                "file_type": asset.file_type,
                "duration": asset.duration,
                "bpm": asset.bpm,
                "key": asset.key,
            }
            items = [self._observation(ContextArea.ASSET, field, value, ContextSourceType.ASSET, str(asset.id), "asset repository", asset.created_at) for field, value in fields.items() if value is not None]
            observations.extend(items)
            contexts.append(AssetContext(asset_id=asset.id, observations=items))
        return contexts

    def _build_memory_packages(
        self,
        user_message: str,
        project_id: int | None,
        observations: list[ContextObservation],
    ) -> list[MemoryContext]:
        memories = memory_store.search_relevant(user_message, project_id=project_id, limit=6)
        if not memories:
            memories = memory_store.list_memories(project_id=project_id, limit=4)
        contexts: list[MemoryContext] = []
        for memory in memories:
            items = [self._observation(ContextArea.MEMORY, "content", memory.content, ContextSourceType.MEMORY, str(memory.id), memory.source, memory.updated_at, memory.confidence)]
            observations.extend(items)
            contexts.append(MemoryContext(memory_id=memory.id, observations=items, memory_type=memory.memory_type, category=memory.category, source=memory.source, confidence=memory.confidence))
        return contexts

    def _build_chat_package(
        self,
        session_id: int | None,
        observations: list[ContextObservation],
    ) -> ChatContext | None:
        if session_id is None:
            return None
        messages = chat_store.get_recent_messages(session_id, limit=20)
        for message in messages:
            observations.append(self._observation(ContextArea.CHAT, "content", message.content, ContextSourceType.CHAT_MESSAGE, str(message.id), "chat repository", message.created_at))
        return ChatContext(session_id=session_id, messages=messages)

    def _observation(self, area, field, value, source_type, source_id, provenance, observed_at, reliability=1.0):
        return ContextObservation(
            context_area=area,
            field=field,
            value=value,
            source=SourceRef(source_type=source_type, source_id=source_id, field=field, provenance=provenance, observed_at=observed_at, reliability=reliability),
            confidence=reliability,
        )

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


def render_context_package(package: ContextPackage) -> str:
    return context_engine.render_context_package(package)
