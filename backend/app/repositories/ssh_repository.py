from pathlib import Path
from app.repositories.base import GridRepository


class SSHRepository(GridRepository):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir, "SSH", ("sla", "ssh", "adt", "sea_level_anomaly"))
