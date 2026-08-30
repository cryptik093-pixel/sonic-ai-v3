from datetime import datetime
from typing import Optional


class Asset:
    def __init__(
        self,
        id: int,
        project_id: int,
        filename: str,
        filepath: str,
        file_type: str,
        duration: Optional[float] = None,
        bpm: Optional[int] = None,
        key: Optional[str] = None,
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
    ):
        self.id = id
        self.project_id = project_id
        self.filename = filename
        self.filepath = filepath
        self.file_type = file_type
        self.duration = duration
        self.bpm = bpm
        self.key = key
        self.sample_rate = sample_rate
        self.channels = channels
        self.created_at = datetime.utcnow()