# Created by Group Members :
# ====================================
# Dodik Kurniawan - s391213
# Binay Siwakoti - s387596
# Bibek Chhantyal - s390276
# Govinda Debnath - s388937
# ====================================

# Initialize Pygame modules
import pygame
import random
import math
from pygame.locals import *

pygame.init()
pygame.mixer.init()
# Horizontal camera offset for scrolling effect
camera_x = 0  

# Load and rotate background image to landscape
raw_image = pygame.image.load("background.png")
rotated_image = pygame.transform.rotate(raw_image, -90)
bg_width, bg_height = rotated_image.get_size()
SCREEN_WIDTH, SCREEN_HEIGHT = bg_width, bg_height

# Setup the main game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("TankStrike V1")
clock = pygame.time.Clock()

# Setup fonts for rendering text
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 80)
med_font = pygame.font.Font(None, 48)
rotated_image = rotated_image.convert()

# Set custom game icon
icon = pygame.image.load("icon.png").convert_alpha()
pygame.display.set_icon(icon)

# Load and scale CDU logo for title screen
logo_raw = pygame.image.load("cdu.png").convert_alpha()
logo_height = 50
scale_ratio = logo_height / logo_raw.get_height()
logo_width = int(logo_raw.get_width() * scale_ratio)
logo_cdu = pygame.transform.scale(logo_raw, (logo_width, logo_height))

# Try loading a custom font, fallback to default if not available
try:
    game_font = pygame.font.Font("arcade.ttf", 48)
except:
    game_font = pygame.font.Font(None, 48)

# Load game sound effects
collision_sound = pygame.mixer.Sound("collision.ogg")
explosion_sound = pygame.mixer.Sound("explosion.wav")
shield_sound = pygame.mixer.Sound("shield.wav")
shoot_sound = pygame.mixer.Sound("shoot.wav")
gameover_sound = pygame.mixer.Sound("gameover.wav")
gameover_sound.set_volume(0.5)

# Set volume for all sounds uniformly
for s in [collision_sound, explosion_sound, shield_sound, shoot_sound, gameover_sound]:
    s.set_volume(0.5)

# Define background music tracks for different stages
music_level1 = "musiclevel1.wav"
music_level2 = "musiclevel2.wav"
music_level3 = "musiclevel3.wav"
music_boss = "musicbossbattle.mp3"
music_ending = "musicending.wav"
music_title = "musictitle.wav"
# Track the currently playing music to avoid reloads
current_music = ""  

# Load explosion sprite sheet and define its properties
explosion_sheet = pygame.image.load("explosion.png").convert()
explosion_sheet.set_colorkey((0, 0, 0))
# Set black as transparent
EXPLOSION_SIZE = (32, 32)
EXPLOSION_FRAMES = 6

# Load player bullet image from sprite strip
bullet_sheet = pygame.image.load("spr_bullet_strip04.png").convert_alpha()
bullet_width = bullet_sheet.get_width() // 2
bullet_height = bullet_sheet.get_height()
player_bullet_img = bullet_sheet.subsurface(pygame.Rect(0, 0, bullet_width, bullet_height)).copy()

# Load enemy bullet frames from sprite strip
enemy_bullet_strip = pygame.image.load("spr_bullet_strip.png").convert_alpha()
enemy_bullet_frames = []
for i in range(3):
    frame = enemy_bullet_strip.subsurface(pygame.Rect(i * 39, 0, 39, 39))
    enemy_bullet_frames.append(frame)

# Load images for shield power-up
shield_img = pygame.image.load("shield_alpha.gif").convert_alpha()
spr_shield_img = pygame.image.load("spr_shield.png").convert_alpha()

# Define scrolling background class
class ScrollingBackground:
    def __init__(self, image_surface, speed=2):
        self.image = image_surface
        self.rect = self.image.get_rect()
        self.speed = speed
        self.x1 = 0
        self.x2 = self.rect.width

    # Update positions to simulate scrolling
    def update(self):
        self.x1 -= self.speed
        self.x2 -= self.speed
        if self.x1 + self.rect.width < 0:
            self.x1 = self.x2 + self.rect.width
        if self.x2 + self.rect.width < 0:
            self.x2 = self.x1 + self.rect.width

    # Draw the two background segments on screen
    def draw(self, surface):
        surface.blit(self.image, (self.x1, 0))
        surface.blit(self.image, (self.x2, 0))

# Create title screen background with slow scroll speed
title_background = ScrollingBackground(rotated_image, speed=1)

# Define class for player's bullet
class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, angle):
        super().__init__()
        self.image_orig = player_bullet_img
        self.image = pygame.transform.rotate(self.image_orig, angle)
        self.rect = self.image.get_rect(center=pos)
        self.angle = angle
        self.speed = 10
        self.direction = pygame.Vector2(1, 0).rotate(-angle)

    def update(self):
        # Move the bullet in its firing direction
        self.rect.centerx += self.direction.x * self.speed
        self.rect.centery += self.direction.y * self.speed

        # Remove bullet if it goes off-screen
        buffer = 100  
        if (self.rect.right < camera_x - buffer or
            self.rect.left > camera_x + SCREEN_WIDTH + buffer or
            self.rect.bottom < 0 or
            self.rect.top > SCREEN_HEIGHT):
            self.kill()
# Class for enemy bullets that follow the player
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, speed=4):
        super().__init__()
        self.frames = enemy_bullet_frames
    # Use animated frames
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=start_pos)

        # Calculate direction to player (target position)
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        distance = math.hypot(dx, dy)
        if distance == 0:
            distance = 1

        # Normalize velocity vector and apply speed
        self.velocity = pygame.Vector2((dx / distance) * speed, (dy / distance) * speed)
        self.animation_timer = 0

    def update(self):
        # Move bullet along its path
        self.rect.centerx += self.velocity.x
        self.rect.centery += self.velocity.y

        # Animate bullet sprite
        self.animation_timer += 1
        if self.animation_timer % 5 == 0:
            self.index = (self.index + 1) % len(self.frames)
            self.image = self.frames[self.index]

        # Remove bullet if it goes out of screen bounds
        buffer = 100
        if (self.rect.right < camera_x - buffer or
            self.rect.left > camera_x + SCREEN_WIDTH + buffer or
            self.rect.bottom < 0 or
            self.rect.top > SCREEN_HEIGHT):
            self.kill()


# Explosion class used for both enemies and player
class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, sheet, frame_size, frame_count):
        super().__init__()
        # Extract explosion frames from sprite sheet
        self.frames = [sheet.subsurface(pygame.Rect(i * frame_size[0], 0, frame_size[0], frame_size[1]))
                       for i in range(frame_count)]
        for frame in self.frames:
            frame.set_colorkey((0, 0, 0))
            # Set black as transparent
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=center)
        self.timer = 0

    def update(self):
        # Play explosion animation and destroy sprite when done
        self.timer += 1
        if self.timer % 5 == 0:
            self.index += 1
            if self.index >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[self.index]


# Shield power-up that moves from right to left
class ShieldPowerUp(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(shield_img, (32, 32))
        y_pos = random.randint(50, SCREEN_HEIGHT - 50)
        self.rect = self.image.get_rect(midleft=(SCREEN_WIDTH + 32, y_pos))
        self.speed = 2
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        self.rect.x -= self.speed
        # Remove power-up if it goes off-screen
        if self.rect.right < 0:
            self.kill()


# Helper function to extract and transform a specific tank sprite frame
def load_fighter_bottom_right(filename):
    sprite_sheet = pygame.image.load(filename).convert_alpha()
    sw, sh = sprite_sheet.get_size()
    fw, fh = sw // 2, sh // 2
    frame = sprite_sheet.subsurface(pygame.Rect(fw, fh, fw, fh))
    frame = pygame.transform.rotate(frame, -90)
    return pygame.transform.scale(frame, (50, int(50 * (frame.get_height() / frame.get_width()))))


# Player tank class controlled by user
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Load and rotate tank image
        self.original_image = pygame.image.load("tank.png").convert_alpha()
        self.original_image = pygame.transform.rotate(self.original_image, 90)  
        desired_width = 50
        aspect_ratio = self.original_image.get_height() / self.original_image.get_width()
        desired_height = int(desired_width * aspect_ratio)
        self.original_image = pygame.transform.scale(self.original_image, (desired_width, desired_height))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(100, SCREEN_HEIGHT // 2))

        # Movement and rotation settings
        self.angle = 0  
        self.speed = 0
        self.rotation_speed = 3
        self.max_speed = 5
        self.velocity = pygame.Vector2(0, 0)

        # Shield variables
        self.has_shield = False
        self.shield_hits = 0
        self.shield_angle = 0

    def update(self, keys):
        # Handle key input for rotation and movement
        if keys[K_LEFT]:
            self.angle += self.rotation_speed
        if keys[K_RIGHT]:
            self.angle -= self.rotation_speed
        if keys[K_UP]:
            self.speed = self.max_speed
        elif keys[K_DOWN]:
            self.speed = -self.max_speed / 2
        else:
            self.speed = 0

        # Apply movement based on angle
        direction = pygame.Vector2(1, 0).rotate(-self.angle)
        self.velocity = direction * self.speed
        self.rect.centerx += self.velocity.x
        self.rect.centery += self.velocity.y

        # Prevent player from going off-screen
        if self.rect.centerx < 0:
            self.rect.centerx = 0

        # Rotate image based on current angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        # Update shield angle if active
        if self.has_shield:
            self.shield_angle = (self.shield_angle + 2) % 360

        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def draw(self, surface, camera_x):
        # Draw player on screen (adjusted by camera)
        surface.blit(self.image, (self.rect.x - camera_x, self.rect.y))
        if self.has_shield:
            # Draw rotating shield around the player
            shield_size = int(self.rect.width * 1.4)
            resized_shield = pygame.transform.scale(spr_shield_img, (shield_size, shield_size))
            rotated = pygame.transform.rotate(resized_shield, self.shield_angle)
            rotated_rect = rotated.get_rect(center=(self.rect.centerx - camera_x, self.rect.centery))
            surface.blit(rotated, rotated_rect)


# Enemy tank with random movement and shooting behavior
class Enemy1(pygame.sprite.Sprite):
    def __init__(self, bullet_group, shoot_delay=3000, speed_mult=1.2):
        super().__init__()
        self.frames = []
        sheet = pygame.image.load("enemy1.png").convert_alpha()
        fw, fh = 42, 44
        for i in range(8):
            frame = sheet.subsurface(pygame.Rect(i * fw, 0, fw, fh))
            scale_width = 30
            scale_height = int(scale_width * (frame.get_height() / frame.get_width()))
            self.frames.append(pygame.transform.scale(frame, (scale_width, scale_height)))
        self.image = self.frames[0]

        # Start enemy at a random position to the right of screen
        self.rect = self.image.get_rect(midleft=(SCREEN_WIDTH + random.randint(20, 100), random.randint(50, SCREEN_HEIGHT - 50)))
        self.index = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_speed = 100

        # Movement logic
        self.move_timer = pygame.time.get_ticks()
        self.move_duration = 1000
        self.direction_x = -1
        self.direction_y = 1
        self.speed_mult = speed_mult

        self.bullets = bullet_group
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_delay = shoot_delay
        self.health = 1

    def update(self):
        now = pygame.time.get_ticks()

        # Animate enemy sprite
        if now - self.last_update > self.animation_speed:
            self.index = (self.index + 1) % len(self.frames)
            self.image = self.frames[self.index]
            self.last_update = now

        # Change direction randomly after move duration
        if now - self.move_timer > self.move_duration:
            self.move_timer = now
            self.move_duration = random.randint(800, 2000)

            # Decide X direction based on player position
            if self.rect.centerx < player.rect.centerx:
                self.direction_x = random.choice([1, 1, 0])
            elif self.rect.centerx > player.rect.centerx:
                self.direction_x = random.choice([-1, -1, 0])
            else:
                self.direction_x = random.choice([-1, 0, 1])

            # Decide Y direction based on player position
            if self.rect.centery < player.rect.centery:
                self.direction_y = random.choice([1, 1, 0])
            elif self.rect.centery > player.rect.centery:
                self.direction_y = random.choice([-1, -1, 0])
            else:
                self.direction_y = random.choice([-1, 0, 1])

        # Apply movement
        self.rect.x += self.direction_x * (2 * self.speed_mult)
        self.rect.y += self.direction_y * (2 * self.speed_mult)

        # Keep enemy within screen bounds
        if self.rect.left < camera_x:
            self.rect.left = camera_x
        if self.rect.right > camera_x + SCREEN_WIDTH:
            self.rect.right = camera_x + SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

        # Shoot bullet if close enough to player
        if self.alive() and now - self.last_shot_time > self.shoot_delay:
            if abs(self.rect.centerx - player.rect.centerx) < 800:
                bullet = EnemyBullet(self.rect.center, player.rect.center)
                self.bullets.add(bullet)
                self.last_shot_time = now

    def hit(self):
        # Enemy takes damage and dies after 1 hit
        self.health -= 1
        if self.health <= 0:
            boom = Explosion(self.rect.center, explosion_sheet, EXPLOSION_SIZE, EXPLOSION_FRAMES)
            explosions.add(boom)
            all_sprites.add(boom)
            explosion_sound.play()
            self.kill()
            global enemies_destroyed
            enemies_destroyed += 1
# Boss enemy class with health bar and explosion animation
class BossEnemy(pygame.sprite.Sprite):
    def __init__(self, bullet_group):
        super().__init__()
        self.frames = [pygame.image.load("planeboss.png").convert_alpha()]
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midleft=(SCREEN_WIDTH + 50, SCREEN_HEIGHT // 2))

        self.index = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_speed = 100

        # Initial horizontal movement until it enters screen
        self.speed_x = -2
        self.direction_y = 1

        self.move_timer = pygame.time.get_ticks()
        self.move_duration = 800

        self.bullets = bullet_group
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_delay = 700

        self.health = 100
        self.max_health = 100
        self.explosion_mode = False

        # Load explosion animation for boss
        sheet = pygame.image.load("planebossexplosion.png").convert_alpha()
        fw, fh = 228, 241
        self.explosion_frames = [
            sheet.subsurface(pygame.Rect(i * fw, 0, fw, fh)) for i in range(11)
        ]
        for frame in self.explosion_frames:
            frame.set_colorkey((0, 0, 0))

    def update(self):
        now = pygame.time.get_ticks()

        # If boss is in explosion mode, play animation and disappear
        if self.explosion_mode:
            if now - self.last_update > self.animation_speed:
                if self.index < len(self.explosion_frames):
                    self.image = self.explosion_frames[self.index]
                    self.index += 1
                    self.last_update = now
                else:
                    self.kill()
                    global boss_defeated
                    boss_defeated = True
            return

        # Movement logic
        self.rect.x += self.speed_x
        if self.rect.right < SCREEN_WIDTH:
            self.speed_x = 0
            # Stop horizontal movement after entry

        margin = 150
        if self.rect.centerx - player.rect.centerx < margin:
            self.rect.x += 2
            # Small adjustment toward player

        # Move vertically within screen bounds
        self.rect.y += self.direction_y * 2
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.direction_y *= -1
            # Bounce off top and bottom

        # Fire bullets at interval
        if now - self.last_shot_time > self.shoot_delay:
            bullet = EnemyBullet(self.rect.center, player.rect.center)
            self.bullets.add(bullet)
            self.last_shot_time = now

        # Trigger explosion animation when health is low
        if self.health <= 5 and not self.explosion_mode:
            self.explosion_mode = True
            self.index = 0
            self.last_update = now

    def hit(self):
        # Show small explosion on hit
        small_explosion = Explosion(self.rect.center, explosion_sheet, EXPLOSION_SIZE, EXPLOSION_FRAMES)
        explosions.add(small_explosion)
        all_sprites.add(small_explosion)
        explosion_sound.play()
        self.health -= 1

        # Trigger final explosion when health reaches zero
        if self.health <= 0 and not self.explosion_mode:
            final_boom = Explosion(self.rect.center, explosion_sheet, EXPLOSION_SIZE, EXPLOSION_FRAMES)
            explosions.add(final_boom)
            all_sprites.add(final_boom)
            explosion_sound.play()
            self.explosion_mode = True
            global boss_defeated
            boss_defeated = True


# Draw standard text on screen
def draw_text(text, x, y, color=(255, 255, 255)):
    screen.blit(font.render(text, True, color), (x, y))

# Draw health bar with red fill and white border
def draw_health_bar(x, y, pct):
    BAR_WIDTH = 200
    fill = max(0, (pct / 100) * BAR_WIDTH)
    pygame.draw.rect(screen, (255, 0, 0), (x, y, fill, 20))
    pygame.draw.rect(screen, (255, 255, 255), (x, y, BAR_WIDTH, 20), 2)


# Reset all game state and recreate player and enemies
def reset_game():
    global player, background, shields, bullets, enemy_bullets, explosions, all_sprites
    global score, lives, health, game_over, enemies, enemies_destroyed, level
    global boss, boss_defeated, show_victory, gameover_sound_played, shield_powerups

    # Initialize player and groups
    player = Player()
    shields = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    shield_powerups = pygame.sprite.Group()

    # Reset game values
    level = 1
    enemies_destroyed = 0
    boss_defeated = False
    show_victory = False
    boss = None
    gameover_sound_played = False

    # Add initial enemies to level 1
    for _ in range(5):
        enemy = Enemy1(enemy_bullets)
        enemy.rect.left = player.rect.centerx + SCREEN_WIDTH + random.randint(0, 200)
        enemy.rect.centery = random.randint(50, SCREEN_HEIGHT - 50)
        enemies.add(enemy)
        all_sprites.add(enemy)

    all_sprites.add(player)
    score = 0
    lives = 3
    health = 100
    game_over = False
# Draw centered text on screen using a given font
def draw_centered_text(text, font, y, color=(255, 255, 255)):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, y))
    screen.blit(rendered, rect)


# Draw animated title with gradient wave effect
def draw_animated_title(text, font, y):
    time_ms = pygame.time.get_ticks()
    gradient_colors = []
    color1 = (0, 100, 200)
    color2 = (0, 200, 255)

    # Create animated gradient per character
    for i in range(len(text)):
        wave = (math.sin(time_ms * 0.003 + i * 0.5) + 1) / 2
        color = interpolate_color(color1, color2, wave)
        gradient_colors.append(color)

    # Calculate total width to center text
    total_width = sum(font.render(ch, True, (0, 0, 0)).get_width() for ch in text)
    start_x = (SCREEN_WIDTH - total_width) // 2
    x = start_x

    # Render each character with gradient
    for i, ch in enumerate(text):
        shadow = font.render(ch, True, (0, 0, 0))
        screen.blit(shadow, (x + 2, y + 2))
        # Shadow effect
        surf = font.render(ch, True, gradient_colors[i])
        screen.blit(surf, (x, y))
        x += surf.get_width()


# General-purpose animated text function
def draw_animated_text(text, font, y, color1=(0, 100, 200), color2=(0, 200, 255)):
    time_ms = pygame.time.get_ticks()
    gradient_colors = []

    for i in range(len(text)):
        wave = (math.sin(time_ms * 0.003 + i * 0.5) + 1) / 2
        color = interpolate_color(color1, color2, wave)
        gradient_colors.append(color)

    total_width = sum(font.render(ch, True, (0, 0, 0)).get_width() for ch in text)
    start_x = (SCREEN_WIDTH - total_width) // 2
    x = start_x

    for i, ch in enumerate(text):
        shadow = font.render(ch, True, (0, 0, 0))
        screen.blit(shadow, (x + 2, y + 2))
        surf = font.render(ch, True, gradient_colors[i])
        screen.blit(surf, (x, y))
        x += surf.get_width()


# Play background music only if it's not already playing
def play_music(file_path, loop=True):
    global current_music
    if current_music != file_path:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play(-1 if loop else 0)
        current_music = file_path


# Create smooth gradient color between two given RGB colors
def interpolate_color(c1, c2, factor):
    return (
        int(c1[0] + (c2[0] - c1[0]) * factor),
        int(c1[1] + (c2[1] - c1[1]) * factor),
        int(c1[2] + (c2[2] - c1[2]) * factor)
    )


# Draw an animated button with hover effect and return its rectangle
def draw_button(text, center_pos, width=240, height=60,
                color1=(0, 100, 200), color2=(0, 200, 255),
                hover_color=(255, 128, 0)):

    time_ms = pygame.time.get_ticks()
    wave = (math.sin(time_ms * 0.003) + 1) / 2
    animated_color = interpolate_color(color1, color2, wave)

    mouse_pos = pygame.mouse.get_pos()
    rect = pygame.Rect(0, 0, width, height)
    rect.center = center_pos

    # Detect hover
    is_hovered = rect.collidepoint(mouse_pos)
    final_color = hover_color if is_hovered else animated_color
    border_thickness = 4 if is_hovered else 2

    # Draw button background and border
    pygame.draw.rect(screen, final_color, rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), rect, border_thickness, border_radius=10)

    # Render button text
    txt = game_font.render(text, True, (255, 255, 255))
    txt_rect = txt.get_rect(center=rect.center)
    screen.blit(txt, txt_rect)

    return rect
# Return rect for click detection


# Draw the main title screen with animated text and buttons
def draw_title_screen():
    title_background.update()
    title_background.draw(screen)

    # CDU logo
    screen.blit(logo_cdu, (10, 10))

    # Title text
    draw_animated_title("TankStrike V1", big_font, SCREEN_HEIGHT // 2 - 150)

    # Buttons: Play, Credit, Exit
    play_btn = draw_button("Play", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
    credit_btn = draw_button("Credit", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    exit_btn = draw_button("Exit", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
    return play_btn, credit_btn, exit_btn


# Draw the credit screen listing all group members
def draw_credit_screen():
    title_background.update()
    title_background.draw(screen)

    draw_animated_text("Created by:", med_font, SCREEN_HEIGHT // 2 - 150)
    draw_animated_text("Dodik Kurniawan - s391213", font, SCREEN_HEIGHT // 2 - 80)
    draw_animated_text("Binay Siwakoti - s387596", font, SCREEN_HEIGHT // 2 - 40)
    draw_animated_text("Bibek Chhantyal - s390276", font, SCREEN_HEIGHT // 2)
    draw_animated_text("Govinda Debnath - s388937", font, SCREEN_HEIGHT // 2 + 40)

    # Draw back button (not clickable directly here, just visual)
    draw_button("Back", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 125))
# Set initial screen states
title_screen = True
show_credit = False
running = True
# Main loop

while running:
    # Title screen logic
    if title_screen:
        # Play title screen music once
        if current_music != music_title:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(music_title)
            pygame.mixer.music.play(-1)
            current_music = music_title

        # Show credit or main menu
        if show_credit:
            draw_credit_screen()
        else:
            play_btn, credit_btn, exit_btn = draw_title_screen()

        pygame.display.flip()

        # Handle events on title screen
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == MOUSEBUTTONDOWN:
                if show_credit:
                    show_credit = False
                elif play_btn.collidepoint(event.pos):
                    title_screen = False
                    reset_game()
                elif credit_btn.collidepoint(event.pos):
                    show_credit = True
                elif exit_btn.collidepoint(event.pos):
                    running = False

        clock.tick(30)
        continue
    # Skip the rest of the loop when still in title screen

    # Handle ingame events
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            if event.key == K_r and (game_over or show_victory):
                reset_game()
                current_music = ""
            if event.key == K_SPACE and not game_over and not show_victory:
                # Fire bullet
                b = Bullet(player.rect.center, player.angle)
                bullets.add(b)
                all_sprites.add(b)
                shoot_sound.play()
            if event.key == K_b and not boss and not game_over and not show_victory:
                # Spawn boss instantly for testing < cheat code
                for enemy in enemies:
                    enemy.kill()
                enemies.empty()
                boss = BossEnemy(enemy_bullets)
                all_sprites.add(boss)
                level = 3
                enemies_destroyed = 0

    # Camera follows the player
    camera_x = max(0, player.rect.centerx - SCREEN_WIDTH // 3)

    # Handle scrolling background
    bg_width = rotated_image.get_width()
    x = -camera_x % bg_width
    zoom_factor = 1.5
    zoomed_bg = pygame.transform.scale(rotated_image, (int(rotated_image.get_width() * zoom_factor), int(rotated_image.get_height() * zoom_factor)))
    zoomed_bg_width = zoomed_bg.get_width()
    x = -camera_x % zoomed_bg_width
    screen.blit(zoomed_bg, (x - zoomed_bg_width, 0))
    screen.blit(zoomed_bg, (x, 0))

    # Play background music based on current level
    if level == 1:
        play_music(music_level1)
    elif level == 2:
        play_music(music_level2)
    elif level == 3 and not boss:
        play_music(music_level3)
    elif boss and current_music != music_boss:
        play_music(music_boss)

    # Main gameplay updates
    if not game_over and not show_victory:
        keys = pygame.key.get_pressed()
        player.update(keys)
        bullets.update()
        enemies.update()
        enemy_bullets.update()
        explosions.update()
        shield_powerups.update()
        if boss:
            boss.update()

        # Occasionally spawn shield power-ups
        if random.randint(1, 150) == 1:
            powerup = ShieldPowerUp()
            shield_powerups.add(powerup)
            all_sprites.add(powerup)

        # Handle shield pickup
        if pygame.sprite.spritecollide(player, shield_powerups, True):
            player.has_shield = True
            player.shield_hits = 5
            shield_sound.play()

        # Draw all sprites relative to camera
        for s in all_sprites:
            if s != player:
                draw_x = s.rect.x - camera_x
                screen.blit(s.surf if hasattr(s, "surf") else s.image, (draw_x, s.rect.y))

        # Draw player tank and shield
        player.draw(screen, camera_x)
        
        # Draw each enemy
        for e in enemies:
            screen.blit(e.image, (e.rect.x - camera_x, e.rect.y))

        # Draw enemy bullets
        for eb in enemy_bullets:
            screen.blit(eb.image, (eb.rect.x - camera_x, eb.rect.y))

        # Draw explosion effects
        for exp in explosions:
            screen.blit(exp.image, (exp.rect.x - camera_x, exp.rect.y))

        # Draw shield power-ups
        for p in shield_powerups:
            screen.blit(p.image, (p.rect.x - camera_x, p.rect.y))

        # Draw boss if active
        if boss:
            screen.blit(boss.image, (boss.rect.x - camera_x, boss.rect.y))

        # Handle collisions between bullets and enemies
        for b in bullets:
            for e in enemies:
                if e.alive() and b.rect.colliderect(e.rect):
                    b.kill()
                    e.hit()
                    score += 10
                    break
            if boss and boss.alive() and b.rect.colliderect(boss.rect):
                b.kill()
                hit_explosion = Explosion(b.rect.center, explosion_sheet, EXPLOSION_SIZE, EXPLOSION_FRAMES)
                explosions.add(hit_explosion)
                all_sprites.add(hit_explosion)
                explosion_sound.play()
                boss.hit()
                score += 50

        # Handle collision with enemy bullets
        if pygame.sprite.spritecollide(player, enemy_bullets, True):
            if player.has_shield:
                player.shield_hits -= 1
                if player.shield_hits <= 0:
                    player.has_shield = False
            else:
                collision_sound.play()
                hit_explosion = Explosion(player.rect.center, explosion_sheet, EXPLOSION_SIZE, EXPLOSION_FRAMES)
                explosions.add(hit_explosion)
                all_sprites.add(hit_explosion)
                health -= 25
                if health <= 0:
                    lives -= 1
                    health = 100
                    if lives <= 0:
                        player.kill()
                        game_over = True
                        pygame.mixer.music.stop()

        # Level progression logic
        if level == 1 and enemies_destroyed == 5:
            level = 2
            draw_text("LEVEL UP!", SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 20, (255, 255, 0))
            pygame.display.flip()
            pygame.time.delay(1500)
            enemies_destroyed = 0
            for _ in range(7):
                enemy = Enemy1(enemy_bullets, shoot_delay=1200, speed_mult=1.2)
                enemy.rect.left = player.rect.centerx + SCREEN_WIDTH + random.randint(0, 200)
                enemy.rect.centery = random.randint(50, SCREEN_HEIGHT - 50)
                enemies.add(enemy)
                all_sprites.add(enemy)

        elif level == 2 and enemies_destroyed == 7:
            level = 3
            draw_text("LEVEL 3!", SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 20, (255, 255, 255))
            pygame.display.flip()
            pygame.time.delay(1500)
            enemies_destroyed = 0
            for _ in range(10):
                enemy = Enemy1(enemy_bullets, shoot_delay=900, speed_mult=1.5)
                enemy.rect.left = player.rect.centerx + SCREEN_WIDTH + random.randint(0, 200)
                enemy.rect.centery = random.randint(50, SCREEN_HEIGHT - 50)
                enemies.add(enemy)
                all_sprites.add(enemy)

        elif level == 3 and enemies_destroyed == 10 and not boss:
            boss = BossEnemy(enemy_bullets)
            boss.rect.left = player.rect.centerx + SCREEN_WIDTH + 100
            boss.rect.centery = SCREEN_HEIGHT // 2
            all_sprites.add(boss)

        if boss_defeated:
            show_victory = True

        # Draw HUD: score, lives, level, health, boss health
        draw_text(f"Score: {score}", 10, 10, (0, 0, 0))
        draw_text(f"Lives: {lives}", 10, 40, (255, 0, 0))
        draw_text(f"Level: {level}", 10, 70, (0, 0, 0))
        draw_health_bar(10, 100, health)
        if boss:
            draw_text("", SCREEN_WIDTH - 250, 20)
            draw_health_bar(SCREEN_WIDTH - 250, 50, boss.health)

    # Display Game Over screen
    elif game_over:
        if not gameover_sound_played:
            gameover_sound.play()
            gameover_sound_played = True
        draw_centered_text("GAME OVER", big_font, SCREEN_HEIGHT // 2 - 60, (255, 0, 0))
        draw_centered_text("Press R to Try Again", med_font, SCREEN_HEIGHT // 2 + 10, (255, 255, 255))

    # Display Victory screen
    elif show_victory:
        draw_centered_text("VICTORY!", big_font, SCREEN_HEIGHT // 2 - 80, (0, 255, 0))
        draw_centered_text(f"Score: {score}", med_font, SCREEN_HEIGHT // 2 - 10, (255, 255, 255))
        draw_centered_text("Press R to Play Again", med_font, SCREEN_HEIGHT // 2 + 50, (255, 255, 255))

    # Refresh display and control frame rate
    pygame.display.flip()
    clock.tick(30)

# Exit game goodbye
pygame.quit()

