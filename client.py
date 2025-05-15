import asyncio
import websockets
import threading
import time

def input_loop(send_queue):
    while True:
        msg = input()
        send_queue.put_nowait(msg)

async def connect_client(name):
    uri = "ws://localhost:8765"
    last_activity_time = time.time()
    heartbeat_interval = 20  # Send heartbeat every 20 seconds
    inactivity_timeout = 60  # Disconnect after 60 seconds of server inactivity
    
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(name)
            
            initial_response = await websocket.recv()
            
            if initial_response.startswith("Server is full"):
                print(f"\n{initial_response}")
                print("Will try again in 10 seconds...")
                await asyncio.sleep(10)
                return True 
            
            print(f"Connected to server as {name}.")
            print("To send a message, type: !chat your message")
            print("To check connection latency, type: !ping")
            
            send_queue = asyncio.Queue()
            ping_time = None
            
            threading.Thread(target=input_loop, args=(send_queue,), daemon=True).start()
            
            last_activity_time = time.time()
            
            async def send():
                nonlocal ping_time, last_activity_time
                while True:
                    current_time = time.time()
                    if current_time - last_activity_time >= heartbeat_interval:
                        print("[DEBUG] Sending heartbeat...")
                        try:
                            await websocket.send("!heartbeat")
                            last_activity_time = current_time 
                        except websockets.ConnectionClosed:
                            return 
                    
                    try:
                        msg = await asyncio.wait_for(send_queue.get(), timeout=1.0)
                        last_activity_time = time.time()
                        
                        if msg.startswith("!chat "):
                            actual_message = msg[6:]
                            await websocket.send(actual_message)
                        elif msg == "!ping":
                            ping_time = time.time()
                            await websocket.send("!ping")
                        await asyncio.sleep(0.01)
                    except asyncio.TimeoutError:
                        pass
                    except websockets.ConnectionClosed:
                        return 
            
            async def receive():
                nonlocal ping_time, last_activity_time
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=inactivity_timeout)
                        
                        last_activity_time = time.time()
                        
                        if message == "PONG":
                            if ping_time:
                                latency = (time.time() - ping_time) * 1000
                                print(f"\nPing: {latency:.2f}ms")
                                ping_time = None
                        elif message == "HEARTBEAT_ACK":
                            pass
                        else:
                            print(f"\n{message}")
                    except asyncio.TimeoutError:
                        print("\nConnection timed out due to inactivity.")
                        print("Attempting to reconnect...")
                        return 
                    except websockets.ConnectionClosed:
                        print("\nDisconnected from server.")
                        return 

            try:
                await websocket.send("!heartbeat")
                await asyncio.gather(send(), receive())
            except Exception as e:
                print(f"Error in connection: {e}")
                
    except Exception as e:
        print(f"Connection error: {e}")
    
    print("Waiting 5 seconds before reconnecting...")
    await asyncio.sleep(5)
    return True

async def main():
    name = input("Enter your name: ")
    
    while True:
        retry = await connect_client(name)
        if not retry:
            break

asyncio.run(main())
