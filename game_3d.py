"""Keyboard-first 3D coin game; add --port later for two joysticks."""
import argparse
import math
import threading
import time as wall_time
import serial
from ursina import Ursina, Entity, Text, Vec3, camera, color, held_keys, time

# Set up terminal options to handle the 2-joystick hardware setup later
parser = argparse.ArgumentParser()
parser.add_argument('--port', help='Arduino serial port (omit for keyboard demo)')
args = parser.parse_args()

# State mapping contract: J1_X, J1_Y, J1_SW, J2_X, J2_Y, J2_SW
state = [512, 512, 0, 512, 512, 0]
last_packet = 0.0
lock = threading.Lock()

def read_controller(port_name):
    global last_packet
    try:
        with serial.Serial(port_name, 115200, timeout=0.2) as port:
            while True:
                raw = port.readline().decode('ascii', errors='ignore').strip()
                parts = raw.split(',')
                if len(parts) != 6: continue
                try:
                    values = [int(item) for item in parts]
                except ValueError: continue
                if any(not 0 <= values[i] <= 1023 for i in (0, 1, 3, 4)): continue
                if values[2] not in (0, 1) or values[5] not in (0, 1): continue
                with lock:
                    state[:] = values
                    last_packet = wall_time.monotonic()
    except serial.SerialException as exc:
        print(f'Serial connection failed: {exc}')

if args.port:
    threading.Thread(target=read_controller, args=(args.port,), daemon=True).start()

def axis(raw):
    value = (raw - 512) / 511
    return 0.0 if abs(value) < 0.12 else max(-1.0, min(1.0, value))

# 1. Initialize the 3D Engine App context
app = Ursina()

# 2. Spawn 3D Geometry Entities (Ground plane & Player cube)
ground = Entity(model='cube', color=color.gray, scale=(14, .2, 14), y=-.1)
player = Entity(model='cube', color=color.azure, scale=(.8, .8, .8), y=.4)

# 3. Position the 5 3D yellow collectible spheres
coin_positions = [(-4, -3), (4, -3), (-4, 3), (4, 3), (0, 0)]
coins = [Entity(model='sphere', color=color.yellow, scale=.55, position=(x, .55, z))
         for x, z in coin_positions]

score = 0
score_text = Text(text='Coins: 0/5', position=(-.85, .45), scale=1.4)
help_text = Text(text=('J1 move J2 camera SW1 jump SW2 reset' if args.port
                       else 'WASD move Arrows camera Space jump R reset'),
                 position=(-.85, -.46), scale=.8)

camera_yaw = 0.0
camera_pitch = 45.0
vertical_speed = 0.0
previous_jump = False
previous_reset = False

def reset_game():
    global score, vertical_speed
    player.position = Vec3(0, .4, 0)
    vertical_speed = 0.0
    score = 0
    for coin in coins:
        coin.enabled = True
    score_text.text = 'Coins: 0/5'

# 4. Engine Frame update loop (runs automatically every frame)
def update():
    global camera_yaw, camera_pitch, vertical_speed, score
    global previous_jump, previous_reset
    
    with lock:
        values = state.copy()
        fresh = wall_time.monotonic() - last_packet < .3
    
    # Check if we use Keyboard mapping or Serial data packets
    if args.port:
        mx, mz = (axis(values[0]), -axis(values[1])) if fresh else (0, 0)
        cx, cy = (axis(values[3]), axis(values[4])) if fresh else (0, 0)
        jump, reset = (bool(values[2]), bool(values[5])) if fresh else (False, False)
    else:
        mx = held_keys['d'] - held_keys['a']
        mz = held_keys['w'] - held_keys['s']
        cx = held_keys['right arrow'] - held_keys['left arrow']
        cy = held_keys['up arrow'] - held_keys['down arrow']
        jump, reset = bool(held_keys['space']), bool(held_keys['r'])
        
    dt = min(time.dt, .05)  # Frame-independent delta time scale
    length = max(1.0, math.hypot(mx, mz))
    
    # Update Player 3D Position
    player.x = max(-6.5, min(6.5, player.x + 5 * mx / length * dt))
    player.z = max(-6.5, min(6.5, player.z + 5 * mz / length * dt))
    
    # Calculate Camera Orbit values
    camera_yaw += 80 * cx * dt
    camera_pitch = max(25, min(70, camera_pitch + 50 * cy * dt))
    
    # 3D Physics Jump Vector tracking
    if jump and not previous_jump and player.y <= .401:
        vertical_speed = 5.0
    previous_jump = jump
    vertical_speed -= 12 * dt
    player.y = max(.4, player.y + vertical_speed * dt)
    if player.y == .4:
        vertical_speed = 0.0
        
    if reset and not previous_reset:
        reset_game()
    previous_reset = reset
    
    # Collision detection using hypotenuse geometric bounds
    for coin in coins:
        if coin.enabled and math.hypot(player.x - coin.x, player.z - coin.z) < .7:
            coin.enabled = False
            score += 1
            score_text.text = (f'Coins: {score}/5' if score < 5
                               else f'You win! {"SW2" if args.port else "R"} to reset')
            
    # Calculate Orbit Camera trigonometry projection matrix tracking
    yaw = math.radians(camera_yaw)
    pitch = math.radians(camera_pitch)
    radius = 11
    camera.position = Vec3(player.x + radius * math.sin(yaw) * math.cos(pitch),
                           radius * math.sin(pitch),
                           player.z - radius * math.cos(yaw) * math.cos(pitch))
    camera.look_at(Vec3(player.x, 0, player.z))

app.run()
