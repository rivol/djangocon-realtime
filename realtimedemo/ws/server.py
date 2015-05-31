import asyncio
import json
import logging

import websockets


logger = logging.getLogger('ws.server')

client_queues = []


@asyncio.coroutine
def handle_client_messages(websocket):
    while True:
        msg = yield from websocket.recv()
        logger.info("Socket %x <=! %s", id(websocket), msg)
        if msg is None:
            # Socket has closed
            return

        # Send the message to all clients
        for q in client_queues:
            yield from q.put(msg)


@asyncio.coroutine
def push_messages(websocket, q):
    while True:
        msg = yield from q.get()

        if not websocket.open:
            return

        logger.info("WS %x: pushing message %s", id(websocket), msg)
        yield from websocket.send(msg)


@asyncio.coroutine
def client_handler(websocket, uri):
    logger.info("New client, websocket %x", id(websocket))
    q = asyncio.Queue()
    client_queues.append(q)

    yield from websocket.send(json.dumps({
        "_event": "showMessage",
        "_data": {
            "message": "Welcome to the chat!"
        },
    }))

    tasks = [
        handle_client_messages(websocket),
        push_messages(websocket, q),
    ]

    yield from asyncio_wait(tasks)
    logger.info("client_handler() done")


def run_server(host, port):
    logger.info("Starting control server on %s:%d", host, port)

    start_server = websockets.serve(client_handler, host, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


def asyncio_wait(coros):
    """ Helper that augments asyncio.wait with better exception handling
    """
    done, pending = yield from asyncio.wait(
        [asyncio.Task(coro) for coro in coros],
        return_when=asyncio.FIRST_EXCEPTION,
    )

    failed = list(filter(lambda task: task.exception(), done))
    if failed:
        raise failed[0].exception()
