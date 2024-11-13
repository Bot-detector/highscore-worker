from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    PrimaryKeyConstraint,
)

from database.database import Base


class HighscoreData(Base):
    __tablename__ = "highscore_data"

    player_id = Column(Integer, nullable=False)
    scrape_ts = Column(DateTime, nullable=False, index=True)
    scrape_date = Column(Date, nullable=False)
    skills = Column(JSON, nullable=True, default={})
    activities = Column(JSON, nullable=True, default={})

    __table_args__ = (
        PrimaryKeyConstraint("player_id", "scrape_date"),
        Index("idx_scrape_ts", "scrape_ts"),
        {"mysql_partition_by": "HASH(player_id)", "mysql_num_partitions": 10},
    )
