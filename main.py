import pygame
import random
import os

# Constants and settings
class Settings:
    # Screen settings
    SCREEN_WIDTH = 1200
    SCREEN_HEIGHT = 900
    WORLD_WIDTH = 3000
    WORLD_HEIGHT = 3000
    FPS = 60
    
    # Player settings
    PLAYER_SPEED = 3
    PLAYER_MAX_HEALTH = 100
    PLAYER_SIZE = 80
    PLAYER_ANIMATION_SPEED = 0.1
    
    # Spit settings
    SPIT_SPEED = 7
    SPIT_SIZE = 32
    
    # Enemy settings
    ENEMY_SPEED = 1
    ENEMY_SPAWN_DELAY = 120
    ENEMY_SHOOT_DELAY_MIN = 120
    ENEMY_SHOOT_DELAY_MAX = 240
    
    # Sprint settings
    SPRINT_COOLDOWN = 90  # 1.5 seconds (60 frames per second * 1.5)
    SPRINT_DURATION = 18  # 0.3 seconds (60 frames per second * 0.3)
    SPRINT_SPEED_MULTIPLIER = 3.0
    
    # Item settings
    COIN_VALUE = 50
    POTION_HEAL_AMOUNT = 30
    ITEM_SIZE = 32

    # Score settings
    ENEMIES_FOR_POTION = 20
    ENEMY_KILL_SCORE = 100
    
    # Difficulty settings
    DIFFICULTY_INCREASE_TIME = 1200  # 20 seconds (60 frames * 20)
    DIFFICULTY_INCREASE_RATE = 0.8  # 20% faster (multiply by 0.8)


class AssetManager:
    """Class to manage and load all game assets"""
    def __init__(self):
        self.player_sheet = None
        self.enemy_sheet = None
        self.background_image = None
        self.spit_image = None
        self.coin_image = None
        self.potion_image = None
        self.spit_sounds = []
        self.death_sounds = []
        self.player_death_sound = None
        self.sad_trombone = None
        self.bg_music = None
        
    def load_assets(self):
        """Load all game assets"""
        # Load images
        self.player_sheet = pygame.image.load('assets/player_sheet.png')
        self.enemy_sheet = pygame.image.load('assets/player_sheet.png')  # Using same sheet for now
        self.background_image = pygame.image.load('assets/background.png')
        self.spit_image = pygame.image.load('assets/spit.png')
        self.coin_image = pygame.image.load('assets/goldcoin.png')
        self.potion_image = pygame.image.load('assets/potion.png')
        
        # Load sounds
        self.spit_sounds = [
            pygame.mixer.Sound('assets/spit1.mp3'),
            pygame.mixer.Sound('assets/spit2.mp3'),
            pygame.mixer.Sound('assets/spit3.mp3')
        ]
        self.death_sounds = [
            pygame.mixer.Sound('assets/llama_death1.mp3'),
            pygame.mixer.Sound('assets/llama_death2.mp3'),
            pygame.mixer.Sound('assets/llama_death3.mp3')
        ]
        self.player_death_sound = pygame.mixer.Sound('assets/llama-death.mp3')
        self.sad_trombone = pygame.mixer.Sound('assets/sadtrombone.mp3')
        self.bg_music = 'assets/background-music.mp3'
        
    def get_random_spit_sound(self):
        """Return a random spit sound"""
        return random.choice(self.spit_sounds)
    
    def get_random_death_sound(self):
        """Return a random death sound"""
        return random.choice(self.death_sounds)


class Camera:
    """Camera to follow player and display only part of world"""
    def __init__(self):
        self.x = 0
        self.y = 0
        
    def update(self, target_rect):
        """Update camera position to follow target"""
        # Center the camera on the target
        self.x = target_rect.centerx - Settings.SCREEN_WIDTH // 2
        self.y = target_rect.centery - Settings.SCREEN_HEIGHT // 2
        
        # Keep camera within world bounds
        self.x = max(0, min(self.x, Settings.WORLD_WIDTH - Settings.SCREEN_WIDTH))
        self.y = max(0, min(self.y, Settings.WORLD_HEIGHT - Settings.SCREEN_HEIGHT))
        
    def world_to_screen(self, rect):
        """Convert world coordinates to screen coordinates"""
        return pygame.Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)
        
    def is_visible(self, rect):
        """Check if a rect is visible in the camera view"""
        viewport = pygame.Rect(self.x, self.y, Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT)
        return viewport.colliderect(rect)


class World:
    """Class for the game world"""
    def __init__(self, asset_manager):
        self.surface = pygame.Surface((Settings.WORLD_WIDTH, Settings.WORLD_HEIGHT))
        self.assets = asset_manager
        self.create_world()
        
    def create_world(self):
        """Create the large world surface with tiled background"""
        bg_width = self.assets.background_image.get_width()
        bg_height = self.assets.background_image.get_height()
        
        # Tile the background
        for x in range(0, Settings.WORLD_WIDTH, bg_width):
            for y in range(0, Settings.WORLD_HEIGHT, bg_height):
                self.surface.blit(self.assets.background_image, (x, y))


class Entity:
    """Base class for game entities with common properties"""
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        
    def get_collision_rect(self):
        """Returns a smaller rectangle for collision detection"""
        return pygame.Rect(
            self.rect.x + 10, 
            self.rect.y + 10, 
            self.rect.width - 20, 
            self.rect.height - 20
        )


class Player(Entity):
    """Player class with player functionality"""
    def __init__(self, x, y, assets):
        super().__init__(x, y, Settings.PLAYER_SIZE, Settings.PLAYER_SIZE)
        self.assets = assets
        self.speed = Settings.PLAYER_SPEED
        self.direction = 'down'
        self.frame = 3
        self.animation_speed = Settings.PLAYER_ANIMATION_SPEED
        self.health = Settings.PLAYER_MAX_HEALTH
        self.alive = True
        
        # Sprint properties
        self.sprint_available = True
        self.sprint_active = False
        self.sprint_timer = 0
        
    def update(self, keys):
        """Update player position and animation based on input"""
        if not self.alive:
            return False
            
        moving = False
        
        # Handle sprint logic
        if self.sprint_active:
            self.sprint_timer += 1
            if self.sprint_timer >= Settings.SPRINT_DURATION:
                self.sprint_active = False
                self.sprint_timer = 0
        elif not self.sprint_available:
            self.sprint_timer += 1
            if self.sprint_timer >= Settings.SPRINT_COOLDOWN:
                self.sprint_available = True
                self.sprint_timer = 0
        
        # Check for sprint activation
        current_speed = self.speed
        if (keys[pygame.K_LSHIFT] and self.sprint_available and not self.sprint_active and 
            (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or 
             keys[pygame.K_UP] or keys[pygame.K_DOWN] or
             keys[pygame.K_a] or keys[pygame.K_d] or
             keys[pygame.K_w] or keys[pygame.K_s])):
            self.sprint_active = True
            self.sprint_available = False
            self.sprint_timer = 0
            
        # Apply sprint multiplier if active
        if self.sprint_active:
            current_speed *= Settings.SPRINT_SPEED_MULTIPLIER
        
        # Track movement in each direction
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        move_up = keys[pygame.K_UP] or keys[pygame.K_w]
        move_down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        
        # Update player position based on movement
        if move_left:
            self.rect.x -= current_speed
            moving = True
        if move_right:
            self.rect.x += current_speed
            moving = True
        if move_up:
            self.rect.y -= current_speed
            moving = True
        if move_down:
            self.rect.y += current_speed
            moving = True
            
        # Set player direction based on combination of keys pressed
        if move_up and move_right:
            self.direction = 'up-right'
        elif move_up and move_left:
            self.direction = 'up-left'
        elif move_down and move_right:
            self.direction = 'down-right'
        elif move_down and move_left:
            self.direction = 'down-left'
        elif move_left:
            self.direction = 'left'
        elif move_right:
            self.direction = 'right'
        elif move_up:
            self.direction = 'up'
        elif move_down:
            self.direction = 'down'
            
        # Prevent player from leaving the world
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > Settings.WORLD_WIDTH:
            self.rect.right = Settings.WORLD_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > Settings.WORLD_HEIGHT:
            self.rect.bottom = Settings.WORLD_HEIGHT
            
        # Update animation frame
        if moving:
            self.frame -= self.animation_speed
            if self.frame <= 0:
                self.frame = 4
                
        return moving
        
    def take_damage(self, amount):
        """Handle player taking damage"""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.die()
        return self.alive
        
    def heal(self, amount):
        """Heal the player by the specified amount"""
        self.health = min(self.health + amount, Settings.PLAYER_MAX_HEALTH)
        
    def die(self):
        """Handle player death"""
        self.alive = False
        self.assets.player_death_sound.play()
        
    def get_spit_position(self):
        """Calculate the position to spawn a spit based on player direction"""
        spit_x = self.rect.centerx
        spit_y = self.rect.centery

        # Adjust spit position based on player direction
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
        # Add diagonal spit positions
        elif self.direction == 'up-right':
            spit_x += 0
            spit_y -= 40
        elif self.direction == 'up-left':
            spit_x -= 25
            spit_y -= 40
        elif self.direction == 'down-right':
            spit_x += 0
            spit_y -= 25
        elif self.direction == 'down-left':
            spit_x -= 25
            spit_y += 25
            
        return spit_x, spit_y
        
    def get_image(self):
        """Get the appropriate player image based on direction and animation frame"""
        # For diagonal directions, use the primary direction's animation
        base_direction = self.direction
        if '-' in self.direction:
            # Extract primary direction (first part of diagonal)
            base_direction = self.direction.split('-')[0]
        
        row = {'up': 0, 'left': 1, 'down': 2, 'right': 3}[base_direction]
        col = int(self.frame) % 4
        return self.assets.player_sheet.subsurface(pygame.Rect(col * 80, row * 80, 80, 80))


class Spit(Entity):
    """Projectile class for player spits"""
    def __init__(self, x, y, direction, assets):
        super().__init__(x, y, Settings.SPIT_SIZE, Settings.SPIT_SIZE)
        self.direction = direction
        self.assets = assets
        self.speed = Settings.SPIT_SPEED
        
        # Add rotation angles for each direction including diagonals
        self.rotation = {
            'up': 180,
            'up-right': 135,
            'right': 90,
            'down-right': 45,
            'down': 0,
            'down-left': 315,
            'left': 270,
            'up-left': 225
        }[direction]
        
        # Rotate image once when created
        self.image = pygame.transform.rotate(assets.spit_image, self.rotation)
        
    def update(self):
        """Update spit position based on direction"""
        if 'right' in self.direction and 'up' not in self.direction and 'down' not in self.direction:
            self.rect.x += self.speed
        elif 'left' in self.direction and 'up' not in self.direction and 'down' not in self.direction:
            self.rect.x -= self.speed
        elif 'up' in self.direction and 'left' not in self.direction and 'right' not in self.direction:
            self.rect.y -= self.speed
        elif 'down' in self.direction and 'left' not in self.direction and 'right' not in self.direction:
            self.rect.y += self.speed
        # Add diagonal movement
        elif self.direction == 'up-right':
            self.rect.x += self.speed * 0.7071  # cos(45°)
            self.rect.y -= self.speed * 0.7071  # sin(45°)
        elif self.direction == 'up-left':
            self.rect.x -= self.speed * 0.7071
            self.rect.y -= self.speed * 0.7071
        elif self.direction == 'down-right':
            self.rect.x += self.speed * 0.7071
            self.rect.y += self.speed * 0.7071
        elif self.direction == 'down-left':
            self.rect.x -= self.speed * 0.7071
            self.rect.y += self.speed * 0.7071
            
    def is_off_screen(self):
        """Check if spit is off the world boundaries"""
        return (self.rect.right < 0 or self.rect.left > Settings.WORLD_WIDTH or
                self.rect.bottom < 0 or self.rect.top > Settings.WORLD_HEIGHT)


class EnemySpit(Spit):
    """Enemy projectile class"""
    def __init__(self, x, y, direction, assets):
        super().__init__(x, y, direction, assets)
        # Tint the spit red for enemy shots
        self.image = self.image.copy()
        self.image.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)


class Enemy(Entity):
    """Enemy class with AI behavior"""
    def __init__(self, x, y, assets, target):
        super().__init__(x, y, Settings.PLAYER_SIZE, Settings.PLAYER_SIZE)
        self.assets = assets
        self.speed = Settings.ENEMY_SPEED
        self.frame = 0
        self.animation_speed = 0.1
        self.target = target
        self.direction = 'down'
        self.shoot_delay = random.randint(Settings.ENEMY_SHOOT_DELAY_MIN, Settings.ENEMY_SHOOT_DELAY_MAX)
        self.shoot_timer = random.randint(0, self.shoot_delay)  # Random initial timer
        
    def can_shoot(self):
        """Check if enemy can shoot based on timer"""
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0
            return True
        return False

    def get_spit_position(self):
        """Calculate the position to spawn a spit based on enemy direction"""
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
        """Update enemy position and direction based on target"""
        # Move towards player
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
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
        """Get the appropriate enemy image based on direction and animation frame"""
        row = {'up': 0, 'left': 1, 'down': 2, 'right': 3}[self.direction]
        col = int(self.frame)
        surface = self.assets.enemy_sheet.subsurface(pygame.Rect(col * 80, row * 80, 80, 80))
        # Tint the enemy 
        tinted_surface = surface.copy()
        tinted_surface.fill((139, 69, 19), special_flags=pygame.BLEND_MULT)
        return tinted_surface


class FloatingItem(Entity):
    """Base class for floating items like coins and potions"""
    def __init__(self, x, y, size, image):
        super().__init__(x, y, size, size)
        self.image = image
        self.collected = False
        self.animation_timer = 0
        self.float_offset = 0
        self.float_direction = 1
        
    def update(self):
        """Update floating animation"""
        self.animation_timer += 1
        if self.animation_timer % 5 == 0:
            self.float_offset += 0.2 * self.float_direction
            if abs(self.float_offset) >= 3:
                self.float_direction *= -1
    
    def draw(self, screen, camera):
        """Draw item with floating animation"""
        draw_rect = self.rect.copy()
        draw_rect.y += self.float_offset
        screen.blit(self.image, camera.world_to_screen(draw_rect))


class Coin(FloatingItem):
    """Coin item that player can collect for points"""
    def __init__(self, x, y, assets):
        super().__init__(x, y, Settings.ITEM_SIZE, assets.coin_image)
        self.value = Settings.COIN_VALUE


class Potion(FloatingItem):
    """Potion item that heals the player"""
    def __init__(self, x, y, assets):
        super().__init__(x, y, Settings.ITEM_SIZE, assets.potion_image)
        self.heal_amount = Settings.POTION_HEAL_AMOUNT


class UI:
    """Class to handle all UI elements"""
    def __init__(self):
        self.score_font = pygame.font.Font(None, 36)
        self.game_over_font = pygame.font.Font(None, 74)
        self.restart_font = pygame.font.Font(None, 36)
        
    def draw_score(self, screen, score):
        """Draw score in the top-right corner"""
        score_text = self.score_font.render(f"Score: {score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(topright=(Settings.SCREEN_WIDTH - 10, 10))
        screen.blit(score_text, score_rect)
    
    def draw_difficulty(self, screen, difficulty_level):
        """Draw difficulty level in the top-left corner"""
        difficulty_text = self.score_font.render(f"Difficulty: {difficulty_level}", True, (255, 255, 255))
        difficulty_rect = difficulty_text.get_rect(topleft=(10, 10))
        screen.blit(difficulty_text, difficulty_rect)
        
    def draw_health_bar(self, screen, x, y, width, height, health, max_health):
        """Draw health bar with specified dimensions"""
        ratio = health / max_health
        rectangle = pygame.Rect(x, y, width, height)
        health_rect = pygame.Rect(x, y, width * ratio, height)
        
        # Draw background (red)
        pygame.draw.rect(screen, (255, 0, 0), rectangle)
        # Draw health (green)
        if health > 0:
            pygame.draw.rect(screen, (0, 255, 0), health_rect)
        # Draw border
        pygame.draw.rect(screen, (0, 0, 0), rectangle, 1)
        
    def draw_game_over(self, screen, can_restart):
        """Draw game over screen"""
        game_over_text = self.game_over_font.render("You Have Died!", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(screen.get_width()/2, screen.get_height()/2))
        screen.blit(game_over_text, text_rect)
        
        if can_restart:
            restart_text = self.restart_font.render("To play again hit the R key", True, (255, 255, 255))
            restart_rect = restart_text.get_rect(center=(screen.get_width()/2, screen.get_height()/2 + 50))
            screen.blit(restart_text, restart_rect)


class SoundManager:
    """Class to handle sound playback and management"""
    def __init__(self, assets):
        self.assets = assets
        # Configure mixer
        pygame.mixer.set_num_channels(16)
        self.available_channels = [pygame.mixer.Channel(i) for i in range(8, 16)]
        
    def play_random_death_sound(self):
        """Play a random death sound on an available channel"""
        sound = self.assets.get_random_death_sound()
        # Find first available channel
        for channel in self.available_channels:
            if not channel.get_busy():
                channel.play(sound)
                break
                
    def play_background_music(self):
        """Start playing background music"""
        pygame.mixer.music.load(self.assets.bg_music)
        pygame.mixer.music.play(-1)  # -1 means loop indefinitely
        pygame.mixer.music.set_volume(0.5)


class Game:
    """Main game class that manages the game state and components"""
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT))
        pygame.display.set_caption("Llama Spitter")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize components
        self.assets = AssetManager()
        self.assets.load_assets()
        
        self.sound_manager = SoundManager(self.assets)
        self.camera = Camera()
        self.ui = UI()
        
        # Game state
        self.game_over = False
        self.death_sound_played = False
        self.trombone_played = False
        self.score = 0
        self.enemies_killed = 0
        
        # Game objects
        self.world = None
        self.player = None
        self.spits = []
        self.enemies = []
        self.enemy_spits = []
        self.coins = []
        self.potions = []
        
        # Timers
        self.spawn_timer = 0
        self.spawn_delay = Settings.ENEMY_SPAWN_DELAY
        
        # Difficulty progression
        self.difficulty_timer = 0
        self.difficulty_level = 1  # Starting at level 1
        
        self.init_game()
        
    def init_game(self):
        """Initialize or reset the game state"""
        # Create world
        self.world = World(self.assets)
        
        # Create player at center of world
        self.player = Player(
            Settings.WORLD_WIDTH // 2, 
            Settings.WORLD_HEIGHT // 2,
            self.assets
        )
        
        # Clear all game objects
        self.spits = []
        self.enemies = []
        self.enemy_spits = []
        self.coins = []
        self.potions = []
        
        # Reset game state
        self.score = 0
        self.enemies_killed = 0
        self.game_over = False
        self.death_sound_played = False
        self.trombone_played = False
        
        # Reset difficulty
        self.difficulty_timer = 0
        self.difficulty_level = 1
        self.spawn_delay = Settings.ENEMY_SPAWN_DELAY
        
        # Start background music
        self.sound_manager.play_background_music()
        
    def reset_game(self):
        """Reset the game after player death"""
        self.init_game()
        
    def spawn_enemy(self):
        """Spawn a new enemy at the edge of the world"""
        # Choose a random edge
        side = random.choice(['top', 'right', 'bottom', 'left'])
        
        if side == 'top':
            x = random.randint(0, Settings.WORLD_WIDTH)
            y = -80
        elif side == 'right':
            x = Settings.WORLD_WIDTH
            y = random.randint(0, Settings.WORLD_HEIGHT)
        elif side == 'bottom':
            x = random.randint(0, Settings.WORLD_WIDTH)
            y = Settings.WORLD_HEIGHT
        else:  # left
            x = -80
            y = random.randint(0, Settings.WORLD_HEIGHT)
            
        self.enemies.append(Enemy(x, y, self.assets, self.player))
        
    def handle_events(self):
        """Process all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over and self.trombone_played:
                    self.reset_game()
                elif not self.game_over and event.key == pygame.K_SPACE:
                    # Create new spit
                    spit_x, spit_y = self.player.get_spit_position()
                    self.spits.append(Spit(spit_x, spit_y, self.player.direction, self.assets))
                    self.assets.get_random_spit_sound().play()
                    
    def update(self):
        """Update game state"""
        if not self.game_over:
            # Update difficulty timer
            self.difficulty_timer += 1
            if self.difficulty_timer >= Settings.DIFFICULTY_INCREASE_TIME:
                # Reset timer
                self.difficulty_timer = 0
                
                # Increase difficulty
                self.difficulty_level += 1
                self.spawn_delay = int(self.spawn_delay * Settings.DIFFICULTY_INCREASE_RATE)
                self.spawn_delay = max(10, self.spawn_delay)  # Ensure it doesn't go too low
                
            # Update spawn timer and create new enemies
            self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_timer = 0
                self.spawn_enemy()
                
            # Update player
            keys = pygame.key.get_pressed()
            self.player.update(keys)
                
            # Update spits
            self.spits = [spit for spit in self.spits if not spit.is_off_screen()]
            for spit in self.spits:
                spit.update()

            # Update enemies
            for enemy in self.enemies:
                enemy.update()
                # Only allow enemies that are visible in the viewport to shoot
                if enemy.can_shoot() and self.camera.is_visible(enemy.rect):
                    spit_x, spit_y = enemy.get_spit_position()
                    self.enemy_spits.append(EnemySpit(spit_x, spit_y, enemy.direction, self.assets))

            # Update enemy spits
            self.enemy_spits = [spit for spit in self.enemy_spits if not spit.is_off_screen()]
            for spit in self.enemy_spits:
                spit.update()
                
            # Update items
            for coin in self.coins:
                coin.update()
                
            for potion in self.potions:
                potion.update()
                
            # Check collisions
            self.check_collisions()
        else:
            # Handle death sounds
            self.handle_death_sounds()
            
        # Update camera to follow player
        self.camera.update(self.player.rect)
        
    def check_collisions(self):
        """Check all collisions between game objects"""
        self.check_player_enemy_spit_collision()
        self.check_player_item_collision()
        self.check_spit_enemy_collision()
        
    def check_player_enemy_spit_collision(self):
        """Check if player is hit by enemy spits"""
        player_collision_rect = self.player.get_collision_rect()
        
        for spit in self.enemy_spits[:]:
            if spit.rect.colliderect(player_collision_rect):
                self.player.take_damage(10)
                self.enemy_spits.remove(spit)
                
        if self.player.health <= 0 and self.player.alive:
            self.player.alive = False
            self.game_over = True
            self.death_sound_played = False
            
    def check_player_item_collision(self):
        """Check if player collects coins or potions"""
        player_collision_rect = self.player.get_collision_rect()
        
        # Check coin collisions
        for coin in self.coins[:]:
            if player_collision_rect.colliderect(coin.rect) and not coin.collected:
                coin.collected = True
                self.score += coin.value
                self.coins.remove(coin)
        
        # Check potion collisions
        for potion in self.potions[:]:
            if player_collision_rect.colliderect(potion.rect) and not potion.collected:
                potion.collected = True
                self.player.heal(potion.heal_amount)
                self.potions.remove(potion)
                
    def check_spit_enemy_collision(self):
        """Check if player spits hit enemies"""
        spits_to_remove = set()
        enemies_to_remove = set()
        
        for spit_idx, spit in enumerate(self.spits):
            for enemy_idx, enemy in enumerate(self.enemies):
                enemy_collision_rect = enemy.get_collision_rect()
                if spit.rect.colliderect(enemy_collision_rect):
                    spits_to_remove.add(spit_idx)
                    enemies_to_remove.add(enemy_idx)
                    self.score += Settings.ENEMY_KILL_SCORE
                    self.enemies_killed += 1
                    self.sound_manager.play_random_death_sound()
                    
                    # Drop a coin or potion
                    if self.enemies_killed % Settings.ENEMIES_FOR_POTION == 0:
                        # Every 20th kill drops a potion
                        self.potions.append(Potion(enemy.rect.centerx, enemy.rect.centery, self.assets))
                    else:
                        # All other kills drop a coin
                        self.coins.append(Coin(enemy.rect.centerx, enemy.rect.centery, self.assets))
        
        # Remove collided objects
        self.spits = [spit for idx, spit in enumerate(self.spits) if idx not in spits_to_remove]
        self.enemies = [enemy for idx, enemy in enumerate(self.enemies) if idx not in enemies_to_remove]
        
    def handle_death_sounds(self):
        """Handle the sequence of sounds played on death"""
        if not self.death_sound_played:
            if not pygame.mixer.get_busy():  # If no sounds are playing
                self.assets.sad_trombone.play()
                self.death_sound_played = True
                self.trombone_played = False
        elif not self.trombone_played:
            if not pygame.mixer.get_busy():  # If trombone finished playing
                self.trombone_played = True
                
    def draw(self):
        """Draw all game elements"""
        # Clear the screen
        self.screen.fill((0, 0, 0))
        
        # Draw visible portion of world
        visible_area = pygame.Rect(self.camera.x, self.camera.y, Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT)
        self.screen.blit(self.world.surface, (0, 0), visible_area)
        
        # Draw player
        if self.player.alive:
            player_image = self.player.get_image()
            self.screen.blit(player_image, self.camera.world_to_screen(self.player.rect))
            
            # Draw health bar above player
            health_bar_width = 60
            health_bar_height = 8
            health_bar_x = self.camera.world_to_screen(self.player.rect).centerx - health_bar_width // 2
            health_bar_y = self.camera.world_to_screen(self.player.rect).top - 15
            self.ui.draw_health_bar(
                self.screen, health_bar_x, health_bar_y, 
                health_bar_width, health_bar_height, 
                self.player.health, Settings.PLAYER_MAX_HEALTH
            )
        
        # Draw spits
        for spit in self.spits:
            self.screen.blit(spit.image, self.camera.world_to_screen(spit.rect))
            
        # Draw enemies and their spits
        for enemy in self.enemies:
            self.screen.blit(enemy.get_image(), self.camera.world_to_screen(enemy.rect))
            
        for spit in self.enemy_spits:
            self.screen.blit(spit.image, self.camera.world_to_screen(spit.rect))
            
        # Draw items
        for coin in self.coins:
            coin.draw(self.screen, self.camera)
            
        for potion in self.potions:
            potion.draw(self.screen, self.camera)
            
        # Draw UI elements
        self.ui.draw_score(self.screen, self.score)
        self.ui.draw_difficulty(self.screen, self.difficulty_level)
        
        # Draw game over screen if needed
        if self.game_over:
            self.ui.draw_game_over(self.screen, self.trombone_played)
            
        # Update the display
        pygame.display.flip()
        
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(Settings.FPS)
            
        pygame.quit()


# Start the game when this script is run
if __name__ == "__main__":
    game = Game()
    game.run()
