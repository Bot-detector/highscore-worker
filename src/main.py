from AioKafkaEngine.AioKafkaEngine import AioKafkaEngine
from asyncio import Queue
import asyncio
import json

async def consume(queue:Queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        print(json.dumps(item))
        queue.task_done()

async def main():
    kafka_engine = AioKafkaEngine(bootstrap_servers=["localhost:9094"], topic="scraper")
    await kafka_engine.start_consumer(group_id="test")
    await kafka_engine.consume_messages()
    
    await consume(kafka_engine.receive_queue)


if __name__ == "__main__":
    asyncio.run(main())