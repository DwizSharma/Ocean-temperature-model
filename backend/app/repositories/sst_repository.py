from pathlib import Path
from app.repositories.base import GridRepository


class SSTRepository(GridRepository):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir, "SST", ("sst", "analysed_sst", "sea_surface_temperature"))
