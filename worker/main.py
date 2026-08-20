import asyncio
import json
import logging
import uuid
from contextlib import suppress
import aio_pika
from aio_pika import DeliveryMode, Message
from sqlalchemy import select, update
from app.core.config import settings
from app.db.db_session import SessionLocal
from app.models.models import OutboxEvent, Task, TaskStatus
from app.repositories.crud import TaskCrud


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('worker')


class TaskProcessor:
    async def process(self, task: Task) -> dict:

        return {
            'message': f'Task {task.title} processed successfully',
            'task_id': str(task.id),
        }


async def publish_outbox_once(channel):
    async with SessionLocal() as session:
        events = (await session.scalars(
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.created_at)
            .limit(100)
            .with_for_update(skip_locked=True)
        )).all()

        for event in events:
            body = json.dumps(event.payload).encode()

            await channel.default_exchange.publish(
                Message(
                    body,
                    delivery_mode=DeliveryMode.PERSISTENT,
                    priority=_priority_from_payload(event.payload.get('priority')),
                    message_id=str(event.id),
                    content_type='application/json',
                ),
                routing_key=settings.rabbitmq_queue,
            )

            await session.execute(
                update(OutboxEvent)
                .where(OutboxEvent.id == event.id)
                .values(published_at=__import__('sqlalchemy').func.now(),
                        attempts=OutboxEvent.attempts + 1)
            )

        await session.commit()


def _priority_from_payload(priority: str | None) -> int:
    return {'LOW': 1, 'MEDIUM': 5, 'HIGH': 10}.get(priority, 5)


async def outbox_publisher(channel):
    while True:
        try:
            await publish_outbox_once(channel)
        except Exception:
            logger.exception('Outbox publisher failed')
        await asyncio.sleep(settings.outbox_poll_interval)


async def handle_message(message: aio_pika.IncomingMessage, processor: TaskProcessor):
    async with message.process(requeue=True):
        payload = json.loads(message.body)
        task_id = uuid.UUID(payload['task_id'])

        async with SessionLocal() as session:
            repo = TaskCrud(session)
            task = await repo.get(task_id)

            if not task or task.status == TaskStatus.CANCELLED:
                return

            claimed = await repo.claim_for_processing(task_id)

            if not claimed:
                return

            await session.commit()

        try:
            async with SessionLocal() as session:
                task = await TaskCrud(session).get(task_id)

                if not task:
                    return

                result = await processor.process(task)

                await TaskCrud(session).complete(task_id, result)
                await session.commit()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception('Task %s failed', task_id)

            async with SessionLocal() as session:
                repo = TaskCrud(session)
                await repo.fail(task_id, {'type': type(exc).__name__, 'message': str(exc)})
                await session.commit()


async def main():
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()

    await channel.set_qos(prefetch_count=settings.rabbitmq_prefetch)

    await channel.declare_queue(
        settings.rabbitmq_queue,
        durable=True,
        arguments={'x-max-priority': 10},
    )

    publisher_task = asyncio.create_task(outbox_publisher(channel))
    processor = TaskProcessor()
    queue = await channel.declare_queue(settings.rabbitmq_queue, durable=True, arguments={'x-max-priority': 10})

    await queue.consume(lambda message: handle_message(message, processor))
    logger.info('Worker started')

    try:
        await asyncio.Future()
    finally:
        publisher_task.cancel()
        with suppress(asyncio.CancelledError):
            await publisher_task
        await connection.close()


if __name__ == '__main__':
    asyncio.run(main())
