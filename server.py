import asyncio
import websockets
import json
import os

connected_clients = set()
world_state_file = "worlds/.json"

# Load the initial world state from the JSON file
def load_world_state():
    if os.path.exists(world_state_file):
        with open(world_state_file, "r") as file:
            content = file.read().strip()
            if content:  # Check if the file is not empty
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {world_state_file}: {e}")
                    return {}
    return {}

# Save the world state to the JSON file
def save_world_state(world_state):
    with open(world_state_file, "w") as file:
        json.dump(world_state, file, indent=4)

world_state = load_world_state()

async def handle_connection(websocket):
    connected_clients.add(websocket)
    try:
        # Send the initial world state to the new client
        await websocket.send(json.dumps({"action": "initial_state", "world_state": world_state}))
        
        async for message in websocket:
            data = json.loads(message)
            print(f"Received data: {data}")

            action = data["action"]
            position = tuple(data["position"])

            if action == "place":
                texture = data["texture"]
                world_state[str(position)] = texture
                save_world_state(world_state)
            
            elif action == "destroy":
                if str(position) in world_state:
                    del world_state[str(position)]
                    save_world_state(world_state)

            # Broadcast the message to all connected clients
            if len(connected_clients) > 1:
                await asyncio.gather(*[client.send(message) for client in connected_clients if client != websocket])
    
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)

async def main():
    port = 8765
    addr = "localhost"
    start_server = await websockets.serve(handle_connection, addr, port)
    print("""

          PyCraft Multiplayer Server

                rainnysword
          
Github: https://github.com/rainnysword/PyCraft

Create a server for you and your friends to play!
    Feel free to edit this however you want.
          
Built on top https://github.com/Spyder-0/Minecraft-with-Python
""")
    print(f"Server started at ws://{addr}:{port}")
    await start_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
