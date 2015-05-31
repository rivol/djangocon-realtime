# Django Real-time Demo

This demo is for my talk at DjangoCon Europe 2015.

There are two different implementation of simple real-time chat - one with Pusher and one with websockets.

## Installation

Django Real-time Demo uses Python 3.4
It can be locally run with SQLite and uses PostgreSQL in production.

For WebSocket demo to work, you need to also run the local WebSocket server: `./manage.py runwsserver 8080`
