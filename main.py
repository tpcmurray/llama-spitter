# let's make llama spitter!
import pygame
import random

# Initialize the game
pygame.init()
pygame.font.init()
score_font = pygame.font.Font(None, 36)  # Default font, size 36
score = 0
pygame.mixer.music.load('assets/background-music.mp3')
pygame.mixer.music.play(-1)  # -1 means loop indefinitely
pygame.mixer.music.set_volume(0.5)
screen = pygame.display.set_mode((609, 791))
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

def get_random_spit_sound():
    return random.choice(spit_sounds)

def get_random_death_sound():
    return random.choice(death_sounds)

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

    def is_off_screen(self, screen_width, screen_height):
        return (self.rect.right < 0 or self.rect.left > screen_width or
                self.rect.bottom < 0 or self.rect.top > screen_height)

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

def check_collisions(spits, enemies):
    global score
    spits_to_remove = set()
    enemies_to_remove = set()
    
    for spit_idx, spit in enumerate(spits):
        for enemy_idx, enemy in enumerate(enemies):
            if spit.rect.colliderect(enemy.rect):
                spits_to_remove.add(spit_idx)
                enemies_to_remove.add(enemy_idx)
                score += 100  # Add 100 points for each enemy hit
                get_random_death_sound().play()  # Play random death sound
    
    # Remove collided objects
    return (
        [spit for idx, spit in enumerate(spits) if idx not in spits_to_remove],
        [enemy for idx, enemy in enumerate(enemies) if idx not in enemies_to_remove]
    )

def check_player_hit(player_rect, enemy_spits):
    global player_health, player_alive
    was_hit = False
    for spit in enemy_spits:
        if spit.rect.colliderect(player_rect):
            player_health -= 10  # Decrease health by 10 for each hit
            was_hit = True
            enemy_spits.remove(spit)  # Remove spit that hit player
            
    if player_health <= 0:
        player_alive = False
        return True
    return False

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
            x = random.randint(0, screen.get_width())
            y = -80
        elif side == 'right':
            x = screen.get_width()
            y = random.randint(0, screen.get_height())
        elif side == 'bottom':
            x = random.randint(0, screen.get_width())
            y = screen.get_height()
        else:  # left
            x = -80
            y = random.randint(0, screen.get_height())
        enemies.append(Enemy(x, y, player_rect))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
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

    # Get keys
    keys = pygame.key.get_pressed()
    moving = False
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
    if player_rect.right > screen.get_width():
        player_rect.right = screen.get_width()
    if player_rect.top < 0:
        player_rect.top = 0
    if player_rect.bottom > screen.get_height():
        player_rect.bottom = screen.get_height()

    # Update animation frame
    if moving:
        player_frame -= player_animation_speed
        if player_frame <= 0:
            player_frame = 4

    # Update and remove off-screen spits
    spits = [spit for spit in spits if not spit.is_off_screen(screen.get_width(), screen.get_height())]
    for spit in spits:
        spit.update()

    # Update enemies
    for enemy in enemies:
        enemy.update()
        if enemy.can_shoot():
            spit_x, spit_y = enemy.get_spit_position()
            enemy_spits.append(EnemySpit(spit_x, spit_y, enemy.direction))

    # Update enemy spits
    enemy_spits = [spit for spit in enemy_spits if not spit.is_off_screen(screen.get_width(), screen.get_height())]
    for spit in enemy_spits:
        spit.update()

    # Check if player is hit
    if check_player_hit(player_rect, enemy_spits):
        running = False  # End game when player is hit

    # Check collisions
    spits, enemies = check_collisions(spits, enemies)

    # Draw everything
    screen.blit(background_image, (0, 0))
    
    # Draw score
    score_text = score_font.render(f"Score: {score}", True, (255, 255, 255))
    score_rect = score_text.get_rect(topright=(screen.get_width() - 10, 10))
    screen.blit(score_text, score_rect)
    
    player_image = get_player_image(player_direction, int(player_frame))
    screen.blit(player_image, player_rect.topleft)
    
    # Draw health bar above player
    health_bar_width = 60
    health_bar_height = 8
    health_bar_x = player_rect.centerx - health_bar_width // 2
    health_bar_y = player_rect.top - 15
    draw_health_bar(screen, health_bar_x, health_bar_y, 
                   health_bar_width, health_bar_height, 
                   player_health, player_max_health)
    
    # Draw spits
    for spit in spits:
        screen.blit(spit.image, spit.rect)
    
    # Draw enemies
    for enemy in enemies:
        screen.blit(enemy.get_image(), enemy.rect.topleft)
    
    # Draw enemy spits
    for spit in enemy_spits:
        screen.blit(spit.image, spit.rect)
    
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()