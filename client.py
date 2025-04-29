import asyncio
import websockets
import threading

def input_loop(send_queue):
    while True:
        msg = input()
        send_queue.put_nowait(msg)

async def main():
    uri = "ws://localhost:8765"
    name = input("Enter your name: ")

    async with websockets.connect(uri) as websocket:
        await websocket.send(name)
        print(f"Connected to server as {name}.")
        print("To send a message, type: !chat your message")

        send_queue = asyncio.Queue()

        threading.Thread(target=input_loop, args=(send_queue,), daemon=True).start()

        async def send():
            while True:
                msg = await send_queue.get()
                if msg.startswith("!chat "):
                    actual_message = msg[6:]
                    await websocket.send(actual_message)

        async def receive():
            while True:
                try:
                    message = await websocket.recv()
                    print(f"\n{message}")
                except websockets.ConnectionClosed:
                    print("Disconnected from server.")
                    break

        await asyncio.gather(send(), receive())

asyncio.run(main())
