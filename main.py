# let's make llama spitter!
import pygame
import random

# Modify screen size and add world size
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
WORLD_WIDTH = 3000
WORLD_HEIGHT = 3000

pygame.init()
pygame.font.init()
score_font = pygame.font.Font(None, 36)  # Default font, size 36
score = 0
pygame.mixer.music.load('assets/background-music.mp3')
pygame.mixer.music.play(-1)  # -1 means loop indefinitely
pygame.mixer.music.set_volume(0.5)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Llama Spitter")
clock = pygame.time.Clock()
running = True

# Load assets
player_sheet = pygame.image.load('assets/player_sheet.png')
enemy_sheet = pygame.image.load('assets/player_sheet.png')  # Using same sheet for now
background_image = pygame.image.load('assets/background.png')
spit_image = pygame.image.load('assets/spit.png')
spit_sounds = [
    pygame.mixer.Sound('assets/spit1.mp3'),
    pygame.mixer.Sound('assets/spit2.mp3'),
    pygame.mixer.Sound('assets/spit3.mp3')
]
death_sounds = [
    pygame.mixer.Sound('assets/llama_death1.mp3'),
    pygame.mixer.Sound('assets/llama_death2.mp3'),
    pygame.mixer.Sound('assets/llama_death3.mp3')
]

# Add after loading background_image
# Create the large world surface with tiled background
world = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
bg_width = background_image.get_width()
bg_height = background_image.get_height()

# Tile the background
for x in range(0, WORLD_WIDTH, bg_width):
    for y in range(0, WORLD_HEIGHT, bg_height):
        world.blit(background_image, (x, y))

# Add camera position
camera_x = 0
camera_y = 0

def update_camera(target_rect):
    """Update camera position to follow target"""
    global camera_x, camera_y
    
    # Center the camera on the target
    camera_x = target_rect.centerx - SCREEN_WIDTH // 2
    camera_y = target_rect.centery - SCREEN_HEIGHT // 2
    
    # Keep camera within world bounds
    camera_x = max(0, min(camera_x, WORLD_WIDTH - SCREEN_WIDTH))
    camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_HEIGHT))

def world_to_screen(rect):
    """Convert world coordinates to screen coordinates"""
    return pygame.Rect(rect.x - camera_x, rect.y - camera_y, rect.width, rect.height)

# Add after other sound loading
player_death_sound = pygame.mixer.Sound('assets/llama-death.mp3')
sad_trombone = pygame.mixer.Sound('assets/sadtrombone.mp3')
death_sound_played = False
death_sound_timer = 0
game_over_font = pygame.font.Font(None, 74)
game_over = False

# After pygame.init()
pygame.mixer.set_num_channels(16)  # Increase number of available sound channels
available_channels = [pygame.mixer.Channel(i) for i in range(8, 16)]  # Reserve channels 8-15 for death sounds

# Add to font/game state variables
restart_font = pygame.font.Font(None, 36)
trombone_played = False

def get_random_spit_sound():
    return random.choice(spit_sounds)

# Replace get_random_death_sound function
def play_random_death_sound():
    sound = random.choice(death_sounds)
    # Find first available channel
    for channel in available_channels:
        if not channel.get_busy():
            channel.play(sound)
            break

def reset_game():
    global player_health, player_alive, game_over, score
    global death_sound_played, trombone_played, enemies, spits, enemy_spits
    player_health = player_max_health
    player_alive = True
    game_over = False
    death_sound_played = False
    trombone_played = False
    score = 0
    enemies.clear()
    spits.clear()
    enemy_spits.clear()

class Spit:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y, 32, 32)  # Adjust size as needed
        self.direction = direction
        self.speed = 7
        # Add rotation angles for each direction
        self.rotation = {
            'up': 180,
            'right': 90,
            'down': 0,
            'left': 270
        }[direction]
        # Rotate image once when created
        self.image = pygame.transform.rotate(spit_image, self.rotation)
    def update(self):
        if self.direction == 'right':
            self.rect.x += self.speed
        elif self.direction == 'left':
            self.rect.x -= self.speed
        elif self.direction == 'up':
            self.rect.y -= self.speed
        elif self.direction == 'down':
            self.rect.y += self.speed
            
    def is_off_screen(self, world_width, world_height):
        # Check against world boundaries instead of screen boundaries
        return (self.rect.right < 0 or self.rect.left > world_width or
                self.rect.bottom < 0 or self.rect.top > world_height)

class EnemySpit(Spit):
    def __init__(self, x, y, direction):
        super().__init__(x, y, direction)
        # Tint the spit red for enemy shots
        self.image = self.image.copy()
        self.image.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)

class Enemy:
    def __init__(self, x, y, target_rect):
        self.rect = pygame.Rect(x, y, 80, 80)
        self.speed = 1
        self.frame = 0
        self.animation_speed = 0.1
        self.target = target_rect
        self.direction = 'down'
        self.shoot_delay = random.randint(120, 240)  # Random delay between shots
        self.shoot_timer = random.randint(0, self.shoot_delay)  # Random initial timer
        
    def can_shoot(self):
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0
            return True
        return False

    def get_spit_position(self):
        spit_x = self.rect.centerx
        spit_y = self.rect.centery
        
        # Adjust spit position based on direction
        if self.direction == 'right':
            spit_x += 4
            spit_y -= 32
        elif self.direction == 'left':
            spit_x -= 32
            spit_y -= 30
        elif self.direction == 'down':
            spit_x -= 15
            spit_y -= 15
        elif self.direction == 'up':
            spit_x -= 15
            spit_y -= 45
            
        return spit_x, spit_y

    def update(self):
        # Move towards player
        dx = self.target.centerx - self.rect.centerx
        dy = self.target.centery - self.rect.centery
        dist = max(abs(dx), abs(dy))
        
        if dist != 0:
            dx = dx / dist * self.speed
            dy = dy / dist * self.speed
            
            self.rect.x += dx
            self.rect.y += dy
            
            # Update direction based on movement
            if abs(dx) > abs(dy):
                self.direction = 'right' if dx > 0 else 'left'
            else:
                self.direction = 'down' if dy > 0 else 'up'
        
        # Update animation
        self.frame = (self.frame + self.animation_speed) % 4

    def get_image(self):
        row = {'up': 0, 'left': 1, 'down': 2, 'right': 3}[self.direction]
        col = int(self.frame)
        surface = enemy_sheet.subsurface(pygame.Rect(col * 80, row * 80, 80, 80))
        # Tint the enemy 
        tinted_surface = surface.copy()
        tinted_surface.fill((139, 69, 19), special_flags=pygame.BLEND_MULT)
        return tinted_surface

# Player settings
player_rect = pygame.Rect(300, 360, 80, 80)
player_speed = 3
player_direction = 'down'
player_frame = 3
player_animation_speed = 0.1
spits = []  # Add this after player settings
enemies = []
spawn_timer = 0
spawn_delay = 120  # Frames between enemy spawns
enemy_spits = []
player_alive = True

# Add after player settings
player_max_health = 100
player_health = player_max_health
player_alive = True

def get_player_image(direction, frame):
    row = {'up': 0, 'left': 1, 'down': 2, 'right': 3}[direction]
    col = frame % 4
    return player_sheet.subsurface(pygame.Rect(col * 80, row * 80, 80, 80))

def get_collision_rect(rect):
    """Returns a smaller rectangle for collision detection"""
    return pygame.Rect(rect.x + 10, rect.y + 10, rect.width - 20, rect.height - 20)

# In check_collisions function, replace death sound line:
def check_collisions(spits, enemies):
    global score
    spits_to_remove = set()
    enemies_to_remove = set()
    
    for spit_idx, spit in enumerate(spits):
        for enemy_idx, enemy in enumerate(enemies):
            # Use smaller collision rect for enemy
            enemy_collision_rect = get_collision_rect(enemy.rect)
            if spit.rect.colliderect(enemy_collision_rect):
                spits_to_remove.add(spit_idx)
                enemies_to_remove.add(enemy_idx)
                score += 100
                play_random_death_sound()  # Changed this line
    
    # Remove collided objects
    return (
        [spit for idx, spit in enumerate(spits) if idx not in spits_to_remove],
        [enemy for idx, enemy in enumerate(enemies) if idx not in enemies_to_remove]
    )

# Replace check_player_hit function
def check_player_hit(player_rect, enemy_spits):
    global player_health, player_alive, game_over, death_sound_played
    was_hit = False
    player_collision_rect = get_collision_rect(player_rect)
    
    for spit in enemy_spits:
        if spit.rect.colliderect(player_collision_rect):
            player_health -= 10
            was_hit = True
            enemy_spits.remove(spit)
            
    if player_health <= 0 and player_alive:
        player_alive = False
        game_over = True
        death_sound_played = False  # Reset death sound flag
        player_death_sound.play()
    return False  # Don't end the game, just return false

def draw_health_bar(surface, x, y, width, height, health, max_health):
    ratio = health / max_health
    rectangle = pygame.Rect(x, y, width, height)
    health_rect = pygame.Rect(x, y, width * ratio, height)
    
    # Draw background (red)
    pygame.draw.rect(surface, (255, 0, 0), rectangle)
    # Draw health (green)
    if health > 0:
        pygame.draw.rect(surface, (0, 255, 0), health_rect)
    # Draw border
    pygame.draw.rect(surface, (0, 0, 0), rectangle, 1)

# Game loop
while running:
    # Update spawn timer and create new enemies
    spawn_timer += 1
    if spawn_timer >= spawn_delay:
        spawn_timer = 0
        # Spawn from random edge of screen
        side = random.choice(['top', 'right', 'bottom', 'left'])
        if side == 'top':
            x = random.randint(0, WORLD_WIDTH)
            y = -80
        elif side == 'right':
            x = WORLD_WIDTH
            y = random.randint(0, WORLD_HEIGHT)
        elif side == 'bottom':
            x = random.randint(0, WORLD_WIDTH)
            y = WORLD_HEIGHT
        else:  # left
            x = -80
            y = random.randint(0, WORLD_HEIGHT)
        enemies.append(Enemy(x, y, player_rect))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over and trombone_played:
                reset_game()
            elif not game_over and event.key == pygame.K_SPACE:
                # Create new spit
                spit_x = player_rect.centerx
                spit_y = player_rect.centery

                # Adjust spit position based on player direction
                if player_direction == 'right':
                    spit_x += 4
                    spit_y -= 32
                elif player_direction == 'left':
                    spit_x -= 32
                    spit_y -= 30
                elif player_direction == 'down':
                    spit_x -= 15
                    spit_y -= 15
                elif player_direction == 'up':
                    spit_x -= 15
                    spit_y -= 45

                spits.append(Spit(spit_x, spit_y, player_direction))
                get_random_spit_sound().play()

    # Get keys - only process movement if player is alive
    keys = pygame.key.get_pressed()
    moving = False
    if not game_over:  # Add this check for movement controls
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player_rect.x -= player_speed
            player_direction = 'left'
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player_rect.x += player_speed
            player_direction = 'right'
            moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            player_rect.y -= player_speed
            player_direction = 'up'
            moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            player_rect.y += player_speed
            player_direction = 'down'
            moving = True

    # Prevent player from leaving the screen
    if player_rect.left < 0:
        player_rect.left = 0
    if player_rect.right > WORLD_WIDTH:
        player_rect.right = WORLD_WIDTH
    if player_rect.top < 0:
        player_rect.top = 0
    if player_rect.bottom > WORLD_HEIGHT:
        player_rect.bottom = WORLD_HEIGHT

    # Update animation frame
    if moving:
        player_frame -= player_animation_speed
        if player_frame <= 0:
            player_frame = 4    # Update and remove off-screen spits
    spits = [spit for spit in spits if not spit.is_off_screen(WORLD_WIDTH, WORLD_HEIGHT)]
    for spit in spits:
        spit.update()

    # Update enemies
    for enemy in enemies:
        enemy.update()
        if enemy.can_shoot():
            spit_x, spit_y = enemy.get_spit_position()
            enemy_spits.append(EnemySpit(spit_x, spit_y, enemy.direction))

    # Update enemy spits
    enemy_spits = [spit for spit in enemy_spits if not spit.is_off_screen(WORLD_WIDTH, WORLD_HEIGHT)]
    for spit in enemy_spits:
        spit.update()

    # Check if player is hit (remove the running = False part)
    check_player_hit(player_rect, enemy_spits)

    # Check collisions
    spits, enemies = check_collisions(spits, enemies)

    # Handle death sound sequence
    if game_over and not death_sound_played:
        if not pygame.mixer.get_busy():  # If no sounds are playing
            sad_trombone.play()
            death_sound_played = True
            trombone_played = False
    elif game_over and death_sound_played and not trombone_played:
        if not pygame.mixer.get_busy():  # If trombone finished playing
            trombone_played = True

    # In game loop, before drawing, add camera update
    update_camera(player_rect)

    # Draw everything
    screen.fill((0, 0, 0))  # Clear screen
    
    # Draw visible portion of world
    visible_area = pygame.Rect(camera_x, camera_y, SCREEN_WIDTH, SCREEN_HEIGHT)
    screen.blit(world, (0, 0), visible_area)
    
    # Draw score (in screen coordinates)
    score_text = score_font.render(f"Score: {score}", True, (255, 255, 255))
    score_rect = score_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
    screen.blit(score_text, score_rect)
    
    player_image = get_player_image(player_direction, int(player_frame))
    screen.blit(player_image, world_to_screen(player_rect))
    
    # Draw health bar above player
    health_bar_width = 60
    health_bar_height = 8
    health_bar_x = world_to_screen(player_rect).centerx - health_bar_width // 2
    health_bar_y = world_to_screen(player_rect).top - 15
    draw_health_bar(screen, health_bar_x, health_bar_y, 
                   health_bar_width, health_bar_height, 
                   player_health, player_max_health)
    
    # Draw spits
    for spit in spits:
        screen.blit(spit.image, world_to_screen(spit.rect))
    
    # Draw enemies
    for enemy in enemies:
        screen.blit(enemy.get_image(), world_to_screen(enemy.rect))
    
    # Draw enemy spits
    for spit in enemy_spits:
        screen.blit(spit.image, world_to_screen(spit.rect))
    
    # Draw game over text if player is dead
    if game_over:
        game_over_text = game_over_font.render("You Have Died!", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(screen.get_width()/2, screen.get_height()/2))
        screen.blit(game_over_text, text_rect)
        
        if trombone_played:
            restart_text = restart_font.render("To play again hit the R key", True, (255, 255, 255))
            restart_rect = restart_text.get_rect(center=(screen.get_width()/2, screen.get_height()/2 + 50))
            screen.blit(restart_text, restart_rect)
    
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()