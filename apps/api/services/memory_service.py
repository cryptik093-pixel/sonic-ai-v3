from repositories.memory_repository import memory_store
from schemas.memory import Memory, MemoryCategory, MemoryCreate


class MemoryService:
    def list_memories(self, project_id: int | None = None) -> list[Memory]:
        return memory_store.list_memories(project_id=project_id)

    def create_memory(self, payload: MemoryCreate) -> Memory:
        if not payload.content.strip():
            raise ValueError("Memory content is required.")
        return memory_store.create_memory(payload)

    def extract_memory_candidates(self, user_message: str, assistant_reply: str) -> list[MemoryCreate]:
        """Detect decisions or preferences worth persisting as studio memory."""
        candidates: list[MemoryCreate] = []
        combined = f"{user_message} {assistant_reply}".lower()

        preference_signals = [
            "i prefer", "i always", "my go-to", "my workflow", "i usually",
            "my chain", "my template", "my standard",
        ]
        if any(signal in combined for signal in preference_signals):
            candidates.append(
                MemoryCreate(
                    content=user_message.strip()[:500],
                    category=MemoryCategory.PREFERENCE,
                    source="conversation",
                    confidence=0.6,
                )
            )

        return candidates


memory_service = MemoryService()
