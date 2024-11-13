import logging
import traceback
from asyncio import Queue

import sqlalchemy as sqla
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

import _kafka as _kafka
from app.repositories.activities import ActivitiesRepo

# schemas import
from app.repositories.highscore import HighscoreRepo
from app.repositories.scraper_data import ScraperDataRepo
from app.repositories.skills import SkillsRepo
from app.schemas.input.activities import Activities, PlayerActivities
from app.schemas.input.message import Message
from app.schemas.input.skills import PlayerSkills, Skills
from app.schemas.scraper_data import ScraperCreate
from database.database import SessionFactory
from database.models.player import Player as PlayerDB
from database.models.scraper_data_v4 import HighscoreData

logger = logging.getLogger(__name__)

SKILLS = [
    "attack",
    "defence",
    "strength",
    "hitpoints",
    "ranged",
    "prayer",
    "magic",
    "cooking",
    "woodcutting",
    "fletching",
    "fishing",
    "firemaking",
    "crafting",
    "smithing",
    "mining",
    "herblore",
    "agility",
    "thieving",
    "slayer",
    "farming",
    "runecraft",
    "hunter",
    "construction",
]


async def insert_data_v1(batch: list[Message], error_queue: Queue):
    try:
        highscores = [msg.hiscores for msg in batch if msg.hiscores]
        players = [msg.player for msg in batch if msg.player]

        logger.info(f"Received: {len(players)=}, {len(highscores)=}")

        repo = HighscoreRepo()
        await repo.create(highscore_data=highscores, player_data=players)
    except (OperationalError, IntegrityError) as e:
        for message in batch:
            await error_queue.put(message)

        logger.error({"error": e})
        logger.info(f"error_qsize={error_queue.qsize()}, {message=}")
    except Exception as e:
        for message in batch:
            await error_queue.put(message)

        logger.error({"error": e})
        logger.debug(f"Traceback: \n{traceback.format_exc()}")
        logger.info(f"error_qsize={error_queue.qsize()}, {message=}")


async def insert_data_v2(batch: list[Message], error_queue: Queue):
    try:
        highscores = [msg.hiscores for msg in batch if msg.hiscores]
        players = [
            msg.player for msg in batch if msg.player and len(msg.player.name) < 13
        ]

        logger.info(f"Received: {len(players)=}, {len(highscores)=}")

        scraper_repo = ScraperDataRepo()

        skills_repo = SkillsRepo()
        activities_repo = ActivitiesRepo()

        skills = {s.skill_name: s for s in await skills_repo.request()}

        activities = {a.activity_name: a for a in await activities_repo.request()}

        highscore_data = []
        scraper_data = []
        for highscore in highscores:
            player_skills: list[PlayerSkills] = []
            player_activities: list[PlayerActivities] = []
            scraper_data = ScraperCreate(
                player_id=highscore.Player_id, created_at=highscore.timestamp
            )
            _highscore = highscore.model_dump()
            assert isinstance(_highscore, dict)
            # logger.info(_highscore)
            for k, v in _highscore.items():
                if k in skills.keys():
                    skill = skills.get(k)
                    assert isinstance(skill, Skills)
                    player_skills.append(
                        PlayerSkills(
                            scraper_id=None, skill_id=skill.skill_id, skill_value=v
                        )
                    )
                if k in activities.keys():
                    activity = activities.get(k)
                    assert isinstance(activity, Activities)
                    player_activities.append(
                        PlayerActivities(
                            scraper_id=None,
                            activity_id=activity.activity_id,
                            activity_value=v,
                        )
                    )
            highscore_data.append((player_skills, player_activities, scraper_data))
            # logger.info(f"{highscore_data[0]}, {players[0]}")
        await scraper_repo.create(highscore_data=highscore_data, player_data=players)
    except (OperationalError, IntegrityError) as e:
        for message in batch:
            await error_queue.put(message)

        logger.error({"error": e})
        logger.info(f"error_qsize={error_queue.qsize()}, {message=}")
    except Exception as e:
        for message in batch:
            await error_queue.put(message)

        logger.error({"error": e})
        logger.debug(f"Traceback: \n{traceback.format_exc()}")
        logger.info(f"error_qsize={error_queue.qsize()}, {message=}")


async def insert_data_v4(batch: list[Message], error_queue: Queue):
    player_batch = [b.player for b in batch if b.player and len(b.player.name) < 13]

    hs_batch = []
    for b in batch:
        if not b.hiscores:
            continue

        hiscores = b.hiscores.model_dump()
        _ = hiscores.pop("total")
        _ = hiscores.pop("timestamp")

        skills = {k: v for k, v in hiscores.items() if k in SKILLS and v and v > 0}

        activities = {
            k: v for k, v in hiscores.items() if k not in SKILLS and v and v > 0
        }

        hs_batch.append(
            {
                "scrape_ts": b.hiscores.timestamp,
                "scrape_date": b.hiscores.timestamp.date(),
                "player_id": b.hiscores.Player_id,
                "skills": skills,
                "activities": activities,
            }
        )

        try:
            async with SessionFactory() as session:
                session: AsyncSession
                async with session.begin():
                    # update players
                    for player in player_batch:
                        await session.execute(
                            sqla.update(PlayerDB)
                            .values(player.model_dump())
                            .where(PlayerDB.id == player.id)
                        )
                    # insert hiscore
                    await session.execute(
                        sqla.insert(HighscoreData)
                        .values(hs_batch)
                        .prefix_with("ignore")
                    )
                    # commit data
                    await session.commit()
        except (OperationalError, IntegrityError) as e:
            for message in batch:
                await error_queue.put(message)

            logger.error({"error": e})
            logger.info(f"error_qsize={error_queue.qsize()}")
        except Exception as e:
            for message in batch:
                await error_queue.put(message)

            logger.error({"error": e})
            logger.debug(f"Traceback: \n{traceback.format_exc()}")
            logger.info(f"error_qsize={error_queue.qsize()}")
