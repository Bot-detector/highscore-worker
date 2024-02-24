from database.database import Base
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    func,
)
from sqlalchemy.dialects.mysql import BIGINT, SMALLINT
from sqlalchemy.schema import UniqueConstraint


# CREATE TABLE scraper_data (
#   scraper_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
#   created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
#   player_id SMALLINT UNSIGNED NOT NULL,
#   record_date DATE AS (DATE(created_at)) STORED,
#   UNIQUE KEY unique_player_per_day (player_id, record_date)
# );
class ScraperData(Base):
    __tablename__ = "scraper_data"

    scraper_id = Column(BIGINT, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    player_id = Column(SMALLINT, nullable=False)
    record_date = Column(Date, nullable=True, server_onupdate=func.current_date())

    __table_args__ = (
        UniqueConstraint("player_id", "record_date", name="unique_player_per_day"),
    )