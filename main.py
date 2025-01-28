# let's make llama spitter!
import pygame
import random

# Initialize the game
pygame.init()
pygame.mixer.music.load('assets/background-music.mp3')
pygame.mixer.music.play(-1)  # -1 means loop indefinitely
pygame.mixer.music.set_volume(0.5)
screen = pygame.display.set_mode((609, 791))
pygame.display.set_caption("Llama Spitter")
clock = pygame.time.Clock()
running = True

# Load assets
player_sheet = pygame.image.load('assets/player_sheet.png')
background_image = pygame.image.load('assets/background.png')
spit_image = pygame.image.load('assets/spit.png')
spit_sounds = [
    pygame.mixer.Sound('assets/spit1.mp3'),
    pygame.mixer.Sound('assets/spit2.mp3'),
    pygame.mixer.Sound('assets/spit3.mp3')
]

def get_random_spit_sound():
    return random.choice(spit_sounds)

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

# Player settings
player_rect = pygame.Rect(300, 360, 80, 80)
player_speed = 3
player_direction = 'down'
player_frame = 3
player_animation_speed = 0.1
spits = []  # Add this after player settings

def get_player_image(direction, frame):
    row = {'up': 0, 'left': 1, 'down': 2, 'right': 3}[direction]
    col = frame % 4
    return player_sheet.subsurface(pygame.Rect(col * 80, row * 80, 80, 80))

# Game loop
while running:
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

    # Draw everything
    screen.blit(background_image, (0, 0))
    player_image = get_player_image(player_direction, int(player_frame))
    screen.blit(player_image, player_rect.topleft)
    
    # Draw spits
    for spit in spits:
        screen.blit(spit.image, spit.rect)
    
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()