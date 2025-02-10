import json
from uuid import uuid4

import aio_pika


class CeleryRMQConnector:
    def __init__(self, conn_str: str):
        if not conn_str.startswith("amqp://") and not conn_str.startswith("amqps://"):
            raise ValueError("CeleryRMQConnector can use only AMQP broker")
        self.conn_str = conn_str
        self._rmq = None
        self._rmq_channel = None

    async def _get_connection_channel(self):
        if not self._rmq:
            self._rmq = await aio_pika.connect_robust(
                self.conn_str,
            )
            self._rmq_channel = await self._rmq.channel()
        return self._rmq_channel

    async def send_task(self, task_name, queue_name, task_kwargs, expires=None):
        task_id = uuid4().hex
        channel = await self._get_connection_channel()

        headers = {
            "argsrepr": "[]",
            "kwargsrepr": str(task_kwargs),
            "group": None,
            "origin": "gen@blablabla",
            "retries": 0,
            "expires": expires,
            "id": task_id,
            "root_id": task_id,
            "task": task_name,
            "lang": "py",
        }

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(
                    [
                        [],
                        task_kwargs,
                        {
                            "callbacks": None,
                            "errbacks": None,
                            "chain": None,
                            "chord": None,
                        },
                    ]
                ).encode(),
                correlation_id=task_id,
                priority=0,
                delivery_mode=2,
                # reply_to=self.result_queue_name,
                reply_to=None,
                content_type="application/json",
                content_encoding="utf-8",
                message_id=None,
                expiration=expires or 60 * 60,
                headers=headers,
            ),
            routing_key=queue_name,
        )
        return task_id
