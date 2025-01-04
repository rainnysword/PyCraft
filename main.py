# Minecraft with Python (PyCraft) Multiplayer
#
# If you do want to player single player, you'd still need to run the server.py on your machine.
# If you want to make this available for everyone inside and outside your network, you'd need to port forward.
#
#
# Created by rainnysword


import asyncio
import json
import threading
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import websockets

app = Ursina()
grass_texture = load_texture("Assets/Textures/Grass_Block.png")
stone_texture = load_texture("Assets/Textures/Stone_Block.png")
brick_texture = load_texture("Assets/Textures/Brick_Block.png")
dirt_texture = load_texture("Assets/Textures/Dirt_Block.png")
wood_texture = load_texture("Assets/Textures/Wood_Block.png")
sky_texture = load_texture("Assets/Textures/Skybox.png")
arm_texture = load_texture("Assets/Textures/Arm_Texture.png")
gravel_texture = load_texture('Assets/Textures/Gravel_Block.png')
punch_sound = Audio("Assets/SFX/Punch_Sound.wav", loop=False, autoplay=False)
window.exit_button.visible = False
block_pick = 1
is_crouching = False
is_sprinting = False

# Load textures into a dictionary
textures = {
    "Grass_Block.png": grass_texture,
    "Stone_Block.png": stone_texture,
    "Brick_Block.png": brick_texture,
    "Dirt_Block.png": dirt_texture,
    "Wood_Block.png": wood_texture,
    "Gravel_Block.png": gravel_texture
}

async def send_block_data(action, position, texture):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        data = {"action": action, "position": (position.x, position.y, position.z), "texture": texture}
        await websocket.send(json.dumps(data))

async def receive_data():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received data from server: {data}")
            action = data['action']

            if action == "initial_state":
                world_state = data['world_state']
                for pos, tex in world_state.items():
                    position = Vec3(*map(float, pos.strip('()').split(',')))
                    texture = textures[tex]
                    Voxel(position=position, texture=texture)

            elif action == "place" or action == "destroy":
                position = Vec3(*data['position'])
                texture = textures[data['texture']]

                if action == "place":
                    Voxel(position=position, texture=texture)
                elif action == "destroy":
                    for voxel in scene.entities:
                        if isinstance(voxel, Voxel) and voxel.position == position:
                            destroy(voxel)
                            break

def update():
    global block_pick, is_crouching, is_sprinting

    if held_keys["left mouse"] or held_keys["right mouse"]:
        hand.active()
    else:
        hand.passive()

    if held_keys["1"]: block_pick = 1
    if held_keys["2"]: block_pick = 2
    if held_keys["3"]: block_pick = 3
    if held_keys["4"]: block_pick = 4
    if held_keys["5"]: block_pick = 5
    if held_keys["6"]: block_pick = 6

    if held_keys["shift"] and not is_crouching:
        is_crouching = True
        player.speed = 2  # Reduce speed while crouching
        player.gravity = 0  # Disable gravity while crouching
        player.collider = None  # Disable collider to prevent falling

    elif not held_keys["shift"] and is_crouching:
        is_crouching = False
        player.speed = 5  # Restore normal speed
        player.gravity = 1  # Restore gravity
        player.collider = "box"  # Restore collider

    if held_keys["control"] and not is_sprinting:
        is_sprinting = True
        player.speed = 10  # Increase speed while sprinting

    elif not held_keys["control"] and is_sprinting:
        is_sprinting = False
        player.speed = 5  # Restore normal speed

class Voxel(Button):
    def __init__(self, position=(0, 0, 0), texture=grass_texture):
        super().__init__(
            parent=scene,
            position=position,
            model="Assets/Models/Block",
            origin_y=0.5,
            texture=texture,
            color=color.color(0, 0, random.uniform(0.9, 1)),
            highlight_color=color.light_gray,
            scale=0.5
        )

    def input(self, key):
        if self.hovered:
            if key == "left mouse down":
                punch_sound.play()
                if block_pick == 1: voxel = Voxel(position=self.position + mouse.normal, texture=grass_texture)
                if block_pick == 2: voxel = Voxel(position=self.position + mouse.normal, texture=stone_texture)
                if block_pick == 3: voxel = Voxel(position=self.position + mouse.normal, texture=brick_texture)
                if block_pick == 4: voxel = Voxel(position=self.position + mouse.normal, texture=dirt_texture)
                if block_pick == 5: voxel = Voxel(position=self.position + mouse.normal, texture=wood_texture)
                if block_pick == 6: voxel = Voxel(position=self.position + mouse.normal, texture=gravel_texture)
                asyncio.run(send_block_data("place", voxel.position, voxel.texture.name))

            if key == "right mouse down":
                punch_sound.play()
                position = self.position
                texture = self.texture.name
                destroy(self)
                asyncio.run(send_block_data("destroy", position, texture))

class Sky(Entity):
    def __init__(self):
        super().__init__(
            parent=scene,
            model="Sphere",
            texture=sky_texture,
            scale=150,
            double_sided=True
        )

class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model="Assets/Models/Arm",
            texture=arm_texture,
            scale=0.2,
            rotation=Vec3(150, -10, 0),
            position=Vec2(0.4, -0.6)
        )
    
    def active(self):
        self.position = Vec2(0.3, -0.5)

    def passive(self):
        self.position = Vec2(0.4, -0.6)

# Loads a flat plain to start your build with.
#for z in range(20): 
#    for x in range(20): 
#       voxel = Voxel(position=(x, 0, z))

player = FirstPersonController()
sky = Sky()
hand = Hand()

# Start receiving data in a background thread
threading.Thread(target=lambda: asyncio.run(receive_data()), daemon=True).start()

app.run()
