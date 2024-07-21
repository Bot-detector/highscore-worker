import asyncio
import logging
import time
import traceback
from asyncio import Queue
from functools import wraps

import _kafka as _kafka
from _kafka import consumer, producer
from app.repositories.activities import ActivitiesRepo

# schemas import
from app.repositories.highscore import HighscoreRepo
from app.repositories.scraper_data import ScraperDataRepo
from app.repositories.skills import SkillsRepo
from app.schemas.input.activities import Activities, PlayerActivities
from app.schemas.input.message import Message
from app.schemas.input.skills import PlayerSkills, Skills
from app.schemas.scraper_data import ScraperCreate
from bulk_normalization import insert_data_v3
from core.config import settings
from sqlalchemy.exc import IntegrityError, OperationalError

logger = logging.getLogger(__name__)


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


async def process_data(receive_queue: Queue, error_queue: Queue):
    # Initialize counter and start time
    start_time = time.time()
    max_insert_wait = 60  # seconds
    max_batch_size = 1_000

    # limit the number of async insert_data calls
    semaphore = asyncio.Semaphore(5)

    batch = []
    # Run indefinitely
    while True:
        # Check if queue is empty
        if receive_queue.empty():
            await asyncio.sleep(1)
            continue

        # Get a message from the chosen queue
        message = await receive_queue.get()

        if not (isinstance(message, dict) or isinstance(message, list)):
            logger.debug(f"invalid type: {message=}")
            continue

        try:
            message = Message(**message)
        except Exception as e:
            logger.error(e)
            continue

        # TODO fix test data
        if settings.ENV != "PRD":
            player_id = message.player.id
            MIN_PLAYER_ID, MAX_PLAYER_ID = 0, 300
            if not (MIN_PLAYER_ID < player_id <= MAX_PLAYER_ID):
                continue

        # batch message
        batch.append(message)

        now = time.time()

        # insert data in batches of N or interval of N
        if len(batch) > max_batch_size or now - start_time > max_insert_wait:
            print(len(batch))
            start_time = time.time()
            async with semaphore:
                # await insert_data_v1(batch=batch, error_queue=error_queue)
                # await insert_data_v2(batch=batch, error_queue=error_queue)
                await insert_data_v3(batch=batch, error_queue=error_queue)
            batch = []

        receive_queue.task_done()


async def main():
    receive_queue = consumer.receive_queue
    send_queue = producer.send_queue

    await consumer.start_engine(topics=["scraper"])
    await producer.start_engine(topic="scraper")

    asyncio.create_task(
        process_data(receive_queue=receive_queue, error_queue=send_queue)
    )

    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
