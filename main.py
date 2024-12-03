# let's make llama spitter!
import pygame

# Initialize the game
pygame.init()
screen = pygame.display.set_mode((609, 791))
clock = pygame.time.Clock()
running = True

# Load assets
player_image = pygame.image.load('assets/player.png')
background_image = pygame.image.load('assets/background.png')

# Player settings
player_rect = player_image.get_rect()
player_rect.topleft = (300, 360)
player_speed = 15

# Game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get keys
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_rect.x -= player_speed
    if keys[pygame.K_RIGHT]:
        player_rect.x += player_speed
    if keys[pygame.K_UP]:
        player_rect.y -= player_speed
    if keys[pygame.K_DOWN]:
        player_rect.y += player_speed

    # Draw everything
    screen.blit(background_image, (0, 0))
    screen.blit(player_image, player_rect.topleft)
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()