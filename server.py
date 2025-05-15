import asyncio
import websockets
import time

clients = {}
client_activity = {}

MAX_CLIENTS = 5

async def handler(websocket):
    if len(clients) >= MAX_CLIENTS:
        print(f"Connection rejected: Maximum clients ({MAX_CLIENTS}) reached.")
        await websocket.send(f"Server is full. Maximum of {MAX_CLIENTS} clients allowed. Please try again later.")
        return
    
    name = await websocket.recv()
    clients[websocket] = name
    client_activity[websocket] = time.time()
    print(f"{name} has connected. ({len(clients)}/{MAX_CLIENTS} clients connected)")
    
    await websocket.send(f"Welcome to the chat, {name}!")
    
    monitor_task = asyncio.create_task(monitor_client_activity(websocket, name))

    try:
        async for message in websocket:
            client_activity[websocket] = time.time()
            
            if message == "!ping":
                print(f"{name}: Sent a ping request")
                await websocket.send("PONG")
            elif message == "!heartbeat":
                print(f"{name}: has gone AFK")
                await websocket.send("HEARTBEAT_ACK")
            else:
                print(f"{name}: {message}")
                formatted_message = f"{name} : {message}"
                for client in clients:
                    if client != websocket:
                        await client.send(formatted_message)
    except websockets.ConnectionClosed:
        print(f"{name} disconnected.")
    finally:
        del clients[websocket]
        if websocket in client_activity:
            del client_activity[websocket]
        monitor_task.cancel()
        print(f"Client count: {len(clients)}/{MAX_CLIENTS}")

async def monitor_client_activity(websocket, name):
    inactivity_threshold = 65 
    
    try:
        while True:
            await asyncio.sleep(20)
            
            if websocket not in client_activity:
                break
                
            time_since_last_activity = time.time() - client_activity[websocket]
            if time_since_last_activity > inactivity_threshold:
                print(f"{name} inactive for {time_since_last_activity:.1f} seconds, disconnecting.")
                await websocket.close(1000, "Inactivity timeout")
                break
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error monitoring {name}: {e}")

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print(f"Server started on ws://localhost:8765 (Max {MAX_CLIENTS} clients)")
        await asyncio.Future()

asyncio.run(main())
