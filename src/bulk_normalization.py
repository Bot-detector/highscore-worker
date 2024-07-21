# import logging
import logging
import traceback
from asyncio import Queue
from dataclasses import asdict, dataclass
from datetime import date, datetime

import sqlalchemy as sqla
from app.schemas.input.highscore import PlayerHiscoreData
from app.schemas.input.message import Message
from database.database import SessionFactory
from database.models.player import Player as PlayerDB
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

skill_map = {}
activity_map = {}


@dataclass
class ScraperPlayerSkill:
    skill_id: int
    skill_value: int
    scrape_ts: datetime
    scrape_date: date
    player_id: int


@dataclass
class ScraperPlayerActivity:
    activity_id: int
    activity_value: int
    scrape_ts: datetime
    scrape_date: date
    player_id: int


@dataclass
class ScraperRecord:
    skill_id: int
    skill_value: int
    activity_id: int
    activity_value: int
    scrape_ts: datetime
    scrape_date: date
    player_id: int


async def get_session():
    return SessionFactory()


async def bulk_normalized_insert(
    session: Session,
    skills: list[ScraperPlayerSkill],
    activities: list[ScraperPlayerActivity],
):
    # create temp (staging) tables
    sql_create_temp_skills = """
        CREATE TEMPORARY TABLE temp_skill (
            skill_id TINYINT, 
            skill_value INT, 
            scrape_ts DATETIME, 
            scrape_date DATE, 
            player_id INT
        ) ENGINE=MEMORY;
    """
    sql_create_temp_activities = """
        CREATE TEMPORARY TABLE temp_activity (
            activity_id TINYINT, 
            activity_value INT, 
            scrape_ts DATETIME, 
            scrape_date DATE, 
            player_id INT
        ) ENGINE=MEMORY;
    """
    # insert into temp (staging) tables
    sql_insert_temp_skills = """
        INSERT INTO temp_skill (skill_id, skill_value, scrape_ts, scrape_date, player_id) 
        VALUES (:skill_id, :skill_value, :scrape_ts, :scrape_date, :player_id);
    """
    sql_insert_temp_activities = """
        INSERT INTO temp_activity (activity_id, activity_value, scrape_ts, scrape_date, player_id) 
        VALUES (:activity_id, :activity_value, :scrape_ts, :scrape_date, :player_id);
    """

    # insert into the normalized tables
    sql_insert_pl_skill = """
        INSERT IGNORE INTO player_skill (skill_id, skill_value)
        SELECT DISTINCT skill_id, skill_value FROM temp_skill tp
        WHERE NOT EXISTS (
            SELECT 1 FROM player_skill ps
            WHERE 1
                AND tp.skill_id = ps.skill_id
                AND tp.skill_value = ps.skill_value
        );
    """
    sql_insert_pl_activity = """
        INSERT IGNORE INTO player_activity (activity_id, activity_value)
        SELECT DISTINCT activity_id, activity_value FROM temp_activity tp
        WHERE NOT EXISTS (
            SELECT 1 FROM player_activity pa
            WHERE 1
                AND tp.activity_id = pa.activity_id
                AND tp.activity_value = pa.activity_value
        );
    """

    sql_insert_sc_data = """
        INSERT IGNORE INTO scraper_data_v3 (scrape_ts, scrape_date, player_id)
        select DISTINCT scrape_ts, scrape_date, player_id from (
            SELECT scrape_ts, scrape_date, player_id FROM temp_skill ts
            UNION
            SELECT scrape_ts, scrape_date, player_id FROM temp_activity ta
        ) tp
        WHERE NOT EXISTS (
            SELECT 1 FROM scraper_data_v3 sd
            WHERE 1
                AND tp.scrape_date = sd.scrape_date
                AND tp.player_id = sd.player_id
        )
        ;
    """

    # insert into the joinging tables
    sql_insert_sc_pl_skill = """
        INSERT IGNORE INTO scraper_player_skill (scrape_id, player_skill_id)
        SELECT sd.scrape_id, ps.player_skill_id FROM temp_skill tp
        join scraper_data_v3 sd ON (
            tp.scrape_date = sd.scrape_date AND 
            tp.player_id = sd.player_id
        )
        JOIN player_skill ps ON (
            tp.skill_id = ps.skill_id AND
            tp.skill_value = ps.skill_value
        )
        WHERE NOT EXISTS (
            SELECT 1 FROM scraper_player_skill sps
            WHERE 1
                AND sps.scrape_id = sd.scrape_id
                AND sps.player_skill_id = ps.player_skill_id
        );
    """
    sql_insert_sc_pl_activity = """
        INSERT IGNORE INTO scraper_player_activity (scrape_id, player_activity_id)
        SELECT sd.scrape_id, pa.player_activity_id FROM temp_activity tp
        join scraper_data_v3 sd ON (
            tp.scrape_date = sd.scrape_date AND 
            tp.player_id = sd.player_id
        )
        JOIN player_activity pa ON (
            tp.activity_id = pa.activity_id AND
            tp.activity_value = pa.activity_value
        )
        WHERE NOT EXISTS (
            SELECT 1 FROM scraper_player_activity spa
            WHERE 1
                AND spa.scrape_id = sd.scrape_id
                AND spa.player_activity_id = pa.player_activity_id
        );
    """
    # cleanup
    await session.execute(sqla.text("DROP TABLE IF EXISTS temp_skill"))
    await session.execute(sqla.text("DROP TABLE IF EXISTS temp_activity"))
    # create temp (staging) tables
    await session.execute(sqla.text(sql_create_temp_skills))
    await session.execute(sqla.text(sql_create_temp_activities))

    # parse data into dict
    _skills = [asdict(s) for s in skills]
    _activities = [asdict(a) for a in activities]

    # insert into temp (staging) tables
    if len(_skills) > 0:
        await session.execute(sqla.text(sql_insert_temp_skills), params=_skills)
    if len(_activities) > 0:
        await session.execute(sqla.text(sql_insert_temp_activities), params=_activities)

    # insert data into normalized table
    await session.execute(sqla.text(sql_insert_sc_data))
    await session.execute(sqla.text(sql_insert_pl_skill))
    await session.execute(sqla.text(sql_insert_pl_activity))

    # insert data into linking table
    await session.execute(sqla.text(sql_insert_sc_pl_skill))
    await session.execute(sqla.text(sql_insert_sc_pl_activity))
    # cleanup
    await session.execute(sqla.text("DROP TABLE IF EXISTS temp_skill"))
    await session.execute(sqla.text("DROP TABLE IF EXISTS temp_activity"))


async def update_skill_map() -> dict:
    sql = """
        SELECT skill_id, skill_name from skill;
    """
    async with await get_session() as session:
        session: AsyncSession
        result = await session.execute(sqla.text(sql))
    data = result.mappings().all()
    data_map = {d["skill_name"]: d["skill_id"] for d in data}
    return data_map


async def update_activity_map() -> dict:
    sql = """
        SELECT activity_id, activity_name from activity;
    """
    async with await get_session() as session:
        session: AsyncSession
        result = await session.execute(sqla.text(sql))
    data = result.mappings().all()
    data_map = {d["activity_name"]: d["activity_id"] for d in data}
    return data_map


def parse_hiscore_records(
    records: list[PlayerHiscoreData],
) -> tuple[list[ScraperPlayerSkill], list[ScraperPlayerActivity]]:
    global skill_map
    global activity_map

    assert skill_map != {}
    assert activity_map != {}

    skills = []
    activities = []

    # iterate over batch records
    for record in records:
        for key, value in record.model_dump().items():
            if key in ["total", "Player_id", "timestamp"]:
                continue
            skill_id = skill_map.get(key)
            activity_id = activity_map.get(key)

            if skill_id is None and activity_id is None:
                logger.warning(f"Unkown key: {key=}")
                continue

            if value == 0:
                continue

            if skill_id is not None:
                _skill = ScraperPlayerSkill(
                    skill_id=skill_id,
                    skill_value=value,
                    scrape_ts=record.timestamp,
                    scrape_date=record.timestamp.date(),
                    player_id=record.Player_id,
                )
                # print(f"appending, {_skill=}")
                skills.append(_skill)
            elif activity_id is not None:
                _activity = ScraperPlayerActivity(
                    activity_id=activity_id,
                    activity_value=value,
                    scrape_ts=record.timestamp,
                    scrape_date=record.timestamp.date(),
                    player_id=record.Player_id,
                )
                # print(f"appending, {_activity=}")
                activities.append(_activity)
            else:
                logger.warning(
                    msg=f"something is wrong: {skill_id=}, {activity_id=}, {key=}, {value=}, {record=}"
                )
                continue
    return skills, activities


async def insert_data_v3(batch: list[Message], error_queue: Queue):
    global skill_map
    global activity_map

    if skill_map == {}:
        skill_map = await update_skill_map()
    if activity_map == {}:
        activity_map = await update_activity_map()
    try:
        highscores = [msg.hiscores for msg in batch if msg.hiscores]
        players = [
            msg.player for msg in batch if msg.player and len(msg.player.name) < 13
        ]

        skills, activities = parse_hiscore_records(highscores)
        logger.info(
            f"Received: {len(players)=}, {len(highscores)=}, {len(skills)=}, {len(activities)=}"
        )
        async with await get_session() as session:
            session: AsyncSession  # Type annotation for clarity
            # insert highscore data
            await bulk_normalized_insert(
                session=session,
                skills=skills,
                activities=activities,
            )
            # update player
            for player in players:
                await session.execute(
                    update(PlayerDB)
                    .values(player.model_dump())
                    .where(PlayerDB.id == player.id)
                )
            await session.commit()
    except (OperationalError, IntegrityError) as e:
        for message in batch:
            await error_queue.put(message.model_dump())

        logger.error({"error": e})
        logger.info(f"error_qsize={error_queue.qsize()}, {message=}")
    except Exception as e:
        for message in batch:
            await error_queue.put(message.model_dump())

        logger.error({"error": e})
        logger.debug(f"Traceback: \n{traceback.format_exc()}")
        logger.info(f"error_qsize={error_queue.qsize()}, {message=}")


# class BenchMark(BenchmarkABC):
#     def insert_many_records(self, records: list[HiscoreRecord]) -> None:
#         skills, activities = parse_hiscore_records(records=records)

#         with get_session() as session:
#             bulk_normalized_insert(
#                 session=session,
#                 skills=skills,
#                 activities=activities,
#             )
#             session.commit()
