import pygame
import pymunk
import pymunk.pygame_util
import mysql.connector
import sys
import math
import random

# ==========================================
# 1. CONSTANTS & HELPER FUNCTIONS
# ==========================================
COLLISION_TYPE_BALL = 1
COLLISION_TYPE_TARGET = 2

def get_parabola_equation(p1, p2, p3, screen_height):
    # Convert Pygame Y (0 at top) to Cartesian Y (0 at bottom)
    x1, y1 = p1[0], screen_height - p1[1]
    x2, y2 = p2[0], screen_height - p2[1]
    x3, y3 = p3[0], screen_height - p3[1]

    if x1 == x2 or x1 == x3 or x2 == x3:
        return None

    denom = (x1 - x2) * (x1 - x3) * (x2 - x3)
    a = (x3 * (y2 - y1) + x2 * (y1 - y3) + x1 * (y3 - y2)) / denom
    b = (x3**2 * (y1 - y2) + x2**2 * (y3 - y1) + x1**2 * (y2 - y3)) / denom
    c = y1 - a * x1**2 - b * x1
    return a, b, c

def spawn_targets(physics_space, num_targets):
    for _ in range(num_targets):
        # Constrain random coordinates to the 600x450 playable grid
        x = random.randint(50, 550)
        y = random.randint(50, 400)
        
        target_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        target_body.position = (x, y)
        target_shape = pymunk.Circle(target_body, 15)
        target_shape.elasticity = 0.8 
        target_shape.friction = 0.5
        target_shape.color = pygame.Color("green") 
        target_shape.collision_type = COLLISION_TYPE_TARGET 
        
        physics_space.add(target_body, target_shape)
        
    return num_targets

# ==========================================
# 2. FETCH CONFIGURATION FROM MYSQL
# ==========================================
if len(sys.argv) < 2:
    print("Error: No simulation ID provided. Please launch from Streamlit.")
    sys.exit()

sim_id = sys.argv[1]

conn = mysql.connector.connect(
    host="localhost",
    user="root",          # Change to your MySQL username
    password="1@Abhinav",  # Change to your MySQL password
    database="vedic_dynamics"
)
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM simulations WHERE id = %s", (sim_id,))
config = cursor.fetchone()
conn.close()

if not config:
    print("Error: Configuration not found.")
    sys.exit()

# ==========================================
# 3. PYGAME & PYMUNK SETUP
# ==========================================
pygame.init()
pygame.font.init()

width, height = 800, 500 
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption(f"Vedic Dynamics: {config['sim_name']}")
clock = pygame.time.Clock()
FPS = 60

ui_font = pygame.font.SysFont("Consolas", 14) 
draw_options = pymunk.pygame_util.DrawOptions(screen)

space = pymunk.Space()
space.gravity = (0, config['gravity'] * 100) 

# --- Create the Static Boundary Box ---
# Floor
floor_shape = pymunk.Segment(space.static_body, (0, 450), (width - 200, 450), 5)
# Ceiling
ceil_shape = pymunk.Segment(space.static_body, (0, 0), (width - 200, 0), 5)
# Left Wall
left_wall_shape = pymunk.Segment(space.static_body, (0, 0), (0, 450), 5)
# Right Wall (stops right before the HUD)
right_wall_shape = pymunk.Segment(space.static_body, (width - 200, 0), (width - 200, 450), 5)

for border in [floor_shape, ceil_shape, left_wall_shape, right_wall_shape]:
    border.elasticity = 1.0  
    border.friction = 0.5
    space.add(border)
# --- Create the Dynamic Ball ---
mass = 1.0
radius = 20
moment = pymunk.moment_for_circle(mass, 0, radius)

ball_body = pymunk.Body(mass, moment)
ball_body.position = (100, 100) 

ball_shape = pymunk.Circle(ball_body, radius)
ball_shape.elasticity = config['bounce'] 
ball_shape.friction = 0.5
ball_shape.color = pygame.Color("red")
ball_shape.collision_type = COLLISION_TYPE_BALL 
space.add(ball_body, ball_shape)

# --- Initial Target Spawning ---
active_targets = spawn_targets(space, 3)

# ==========================================
# 4. COLLISION HANDLING
# ==========================================
targets_to_remove = [] 

def target_hit(arbiter, physics_space, data):
    ball_shape, hit_target_shape = arbiter.shapes
    if hit_target_shape not in targets_to_remove:
        targets_to_remove.append(hit_target_shape)
    return True 

space.on_collision(COLLISION_TYPE_BALL, COLLISION_TYPE_TARGET, begin=target_hit)

# ==========================================
# 5. GAME LOOP & INTERACTION VARIABLES
# ==========================================
is_aiming = False
impulse_multiplier = 15.0 
trajectory_points = [] 
score = 0

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    # --- EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            dist = math.hypot(ball_body.position.x - mouse_pos[0], ball_body.position.y - mouse_pos[1])
            if dist <= radius:
                is_aiming = True
                ball_body.velocity = (0, 0)
                ball_body.angular_velocity = 0
                trajectory_points.clear() 

        elif event.type == pygame.MOUSEBUTTONUP:
            if is_aiming:
                dx = mouse_pos[0] - ball_body.position.x
                dy = mouse_pos[1] - ball_body.position.y
                
                impulse_vector = (dx * impulse_multiplier, dy * impulse_multiplier)
                ball_body.apply_impulse_at_local_point(impulse_vector, (0, 0))
                is_aiming = False

    # --- PHYSICS STEP ---
    space.step(1 / FPS)

    # --- PROCESS DESTROYED TARGETS ---
    for target_shape in targets_to_remove:
        if target_shape in space.shapes: 
            space.remove(target_shape, target_shape.body)
            score += 1
            active_targets -= 1 
            
    targets_to_remove.clear() 

    # --- WAVE RESPAWN LOGIC ---
    if active_targets <= 0:
        active_targets = spawn_targets(space, 3) 
        ball_body.position = (100, 100)
        ball_body.velocity = (0, 0)
        ball_body.angular_velocity = 0
        trajectory_points.clear()

    # --- TRAJECTORY RECORDING & MATH ---
    equation_text = "y = N/A"

    if abs(ball_body.velocity.x) > 0.1 or abs(ball_body.velocity.y) > 0.1:
        current_pos = (int(ball_body.position.x), int(ball_body.position.y))
        if not trajectory_points or trajectory_points[-1] != current_pos:
            trajectory_points.append(current_pos)

    if len(trajectory_points) >= 3:
        pt_start = trajectory_points[0]
        pt_mid = trajectory_points[len(trajectory_points) // 2]
        pt_end = trajectory_points[-1]
        
        coeffs = get_parabola_equation(pt_start, pt_mid, pt_end, height)
        if coeffs:
            a, b, c = coeffs
            equation_text = f"y={a:.4f}x²+{b:.2f}x+{c:.0f}"

    # ==========================================
    # 6. ADVANCED RENDERING & UI
    # ==========================================
    screen.fill((20, 24, 30))
    
    # Draw Graph Paper Grid
    grid_color = (40, 48, 60)
    axis_color = (80, 96, 120)
    for x in range(0, width - 200, 50): 
        pygame.draw.line(screen, grid_color, (x, 0), (x, height))
    for y in range(0, height, 50):
        pygame.draw.line(screen, grid_color, (0, y), (width - 200, y))
    
    pygame.draw.line(screen, axis_color, (50, 0), (50, height), 2)
    pygame.draw.line(screen, axis_color, (0, 450), (width - 200, 450), 2)

    # Draw Trajectory
    if len(trajectory_points) > 1:
        pygame.draw.lines(screen, (0, 200, 255), False, trajectory_points, 2)

    # Draw Physics Objects
    space.debug_draw(draw_options) 
    
    # Draw Aiming Line & Angle
    if is_aiming:
        pygame.draw.line(
            screen, (255, 100, 100), 
            (int(ball_body.position.x), int(ball_body.position.y)), 
            mouse_pos, 2
        )
        dx = ball_body.position.x - mouse_pos[0]
        dy = ball_body.position.y - mouse_pos[1]
        angle = math.degrees(math.atan2(dy, dx))
        
        angle_text = ui_font.render(f"Angle: {abs(angle):.1f}°", True, (255, 255, 255))
        screen.blit(angle_text, (mouse_pos[0] + 15, mouse_pos[1] - 15))

    # --- SIDEBAR HUD ---
    pygame.draw.rect(screen, (15, 18, 22), (width - 200, 0, 200, height)) 
    pygame.draw.line(screen, (60, 70, 90), (width - 200, 0), (width - 200, height), 2) 

    title_text = ui_font.render("VEDIC DYNAMICS", True, (150, 200, 255))
    screen.blit(title_text, (width - 170, 20))
    pygame.draw.line(screen, (150, 200, 255), (width - 180, 45), (width - 20, 45), 1)

    pos_x, pos_y = ball_body.position.x, ball_body.position.y
    vel_x, vel_y = ball_body.velocity.x, ball_body.velocity.y
    speed = math.hypot(vel_x, vel_y)

    data_lines = [
        ("Score:", f"{score}"),
        ("X Coord:", f"{pos_x:.1f}"),
        ("Y Coord:", f"{pos_y:.1f}"),
        ("V(x):", f"{vel_x:.1f}"),
        ("V(y):", f"{vel_y:.1f}"),
        ("Speed:", f"{speed:.1f}"),
        ("Eq:", equation_text),
        ("Gravity:", f"{config['gravity']:.2f}"),
        ("Bounce:", f"{config['bounce']:.2f}")
    ]

    y_offset = 70
    for label, val in data_lines:
        lbl_render = ui_font.render(label, True, (180, 190, 200))
        val_render = ui_font.render(val, True, (255, 255, 255))
        screen.blit(lbl_render, (width - 190, y_offset))
        screen.blit(val_render, (width - 110, y_offset))
        y_offset += 35

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()