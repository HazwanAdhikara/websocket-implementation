import asyncio
import websockets

clients = {}

async def handler(websocket):
    name = await websocket.recv()
    clients[websocket] = name
    print(f"{name} has connected.")

    try:
        async for message in websocket:
            print(f"{name}: {message}")
            formatted_message = f"{name} : {message}"
            for client in clients:
                if client != websocket:
                    await client.send(formatted_message)
    except websockets.ConnectionClosed:
        print(f"{name} disconnected.")
    finally:
        del clients[websocket]

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Server started on ws://localhost:8765")
        await asyncio.Future()

asyncio.run(main())
