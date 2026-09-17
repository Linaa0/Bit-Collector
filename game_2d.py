import argparse
import threading
import time
import pygame
try:
    import serial
except ImportError:
    serial = None

# Game Configurations
WIDTH, HEIGHT = 900, 600
PLAYER_SPEED = 260
PLAYER_SIZE = 34
COIN_RADIUS = 12
BACKGROUND = (19, 36, 51)

# Command-line arguments to allow hardware bridging later
parser = argparse.ArgumentParser()
parser.add_argument('--port', help='Arduino serial port; omit for keyboard control')
args = parser.parse_args()

# Threading state variables for hardware serial readings
controller = [512, 512, 0]
controller_lock = threading.Lock()
last_packet = 0.0

def read_controller(port_name):
    global last_packet
    if serial is None: return
    try:
        with serial.Serial(port_name, 115200, timeout=.2) as device:
            while True:
                line = device.readline().decode('ascii', errors='ignore').strip()
                parts = line.split(',')
                if len(parts) != 3: continue
                try:
                    values = [int(part) for part in parts]
                except ValueError: continue
                if not (0 <= values[0] <= 1023 and 0 <= values[1] <= 1023): continue
                if values[2] not in (0, 1): continue
                with controller_lock:
                    controller[:] = values
                    last_packet = time.monotonic()
    except Exception as error:
        print(f'Controller unavailable: {error}')

def axis(raw):
    value = max(-1.0, min(1.0, (raw - 512) / 511))
    return 0.0 if abs(value) < .12 else value  # 0.12 is the Dead Zone

if args.port:
    threading.Thread(target=read_controller, args=(args.port,), daemon=True).start()

# Initialize Pygame Window
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Keyboard First 2D Coin Game')
clock = pygame.time.Clock()
font = pygame.font.Font(None, 34)

# Game Entities
player = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
coin_positions = [(100, 100), (800, 100), (100, 500), (800, 500), (450, 130)]
coins = [pygame.Vector2(pos) for pos in coin_positions]
previous_reset = False

def reset_game():
    global coins
    player.update(WIDTH / 2, HEIGHT / 2)
    coins = [pygame.Vector2(pos) for pos in coin_positions]

# Engine Main Loop
running = True
while running:
    dt = min(clock.tick(60) / 1000, .05)  # Delta time capped at 60 FPS frame ticks
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Process Inputs (Choose between Hardware Serial Port or Keyboard)
    if args.port:
        with controller_lock:
            values = controller.copy()
        fresh = time.monotonic() - last_packet < .3
        movement = pygame.Vector2(axis(values[0]), axis(values[1])) if fresh else pygame.Vector2()
        reset_pressed = fresh and values[2] == 1
    else:
        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(
            int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a]),
            int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w]),
        )
        reset_pressed = bool(keys[pygame.K_SPACE])

    # Physics & Bounds Check
    if movement.length_squared() > 1:
        movement = movement.normalize()
    player += movement * PLAYER_SPEED * dt
    player.x = max(PLAYER_SIZE / 2, min(WIDTH - PLAYER_SIZE / 2, player.x))
    player.y = max(PLAYER_SIZE / 2, min(HEIGHT - PLAYER_SIZE / 2, player.y))

    # Reset Handle
    if reset_pressed and not previous_reset:
        reset_game()
    previous_reset = reset_pressed

    # Collision Logic
    coins = [coin for coin in coins if player.distance_to(coin) > PLAYER_SIZE / 2 + COIN_RADIUS]

    # Render Graphics
    screen.fill(BACKGROUND)
    for coin in coins:
        pygame.draw.circle(screen, (255, 213, 79), coin, COIN_RADIUS)
    player_rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
    player_rect.center = player
    pygame.draw.rect(screen, (41, 182, 246), player_rect, border_radius=6)

    # UI Messaging
    collected = len(coin_positions) - len(coins)
    message = f'Coins: {collected}/5' if coins else 'You win! Press Space or joystick SW to reset'
    screen.blit(font.render(message, True, (255, 255, 255)), (20, 18))
    pygame.display.flip()

pygame.quit()
