import asyncio

from .websocket_server import TranslationServer


def main():
    server = TranslationServer()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        server.cleanup()
        print("Server stopped")


if __name__ == "__main__":
    main()
