# let's make llama spitter!
import pygame

# Initialize the game
pygame.init()
screen = pygame.display.set_mode((609, 791))
clock = pygame.time.Clock()
running = True

# Load assets
player_sheet = pygame.image.load('assets/player_sheet.png')
background_image = pygame.image.load('assets/background.png')

# Player settings
player_rect = pygame.Rect(300, 360, 80, 80)
player_speed = 3
player_direction = 'down'
player_frame = 3
player_animation_speed = 0.1

def get_player_image(direction, frame):
    row = {'up': 0, 'left': 1, 'down': 2, 'right': 3}[direction]
    col = frame % 4
    return player_sheet.subsurface(pygame.Rect(col * 80, row * 80, 80, 80))

# Game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

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

    # Draw everything
    screen.blit(background_image, (0, 0))
    player_image = get_player_image(player_direction, int(player_frame))
    screen.blit(player_image, player_rect.topleft)
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()