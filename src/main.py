import asyncio
import logging
import time
from asyncio import Queue

import _kafka as _kafka
from _kafka import consumer, producer

# schemas import
from app.schemas.input.message import Message

# from bulk_normalization import insert_data_v3
from core.config import settings

# from insert_data import insert_data_v1
# from insert_data import insert_data_v2
from insert_data import insert_data_v4

logger = logging.getLogger(__name__)


async def process_data(receive_queue: Queue, error_queue: Queue):
    # Initialize counter and start time
    start_time = time.time()
    max_insert_wait = 60  # seconds
    max_batch_size = 10

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
                logger.warning(f"{settings.ENV}, skipping: {player_id}")
                continue

        # batch message
        batch.append(message)

        now = time.time()

        # insert data in batches of N or interval of N
        if len(batch) > max_batch_size or now - start_time > max_insert_wait:
            start_time = time.time()
            async with semaphore:
                # await insert_data_v1(batch=batch, error_queue=error_queue)
                # await insert_data_v2(batch=batch, error_queue=error_queue)
                # await insert_data_v3(batch=batch, error_queue=error_queue)
                await insert_data_v4(batch=batch, error_queue=error_queue)
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
