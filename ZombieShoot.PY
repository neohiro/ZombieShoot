import pygame
import random
import math
import numpy as np

# --- Game Constants ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
DARK_RED = (139, 0, 0)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255) # Brighter color for the Gatling gun
BARRIER_COLOR = (120, 120, 120)

# New colors for the floor with eight gradients
FLOOR_GRAY_1 = (20, 20, 20)
FLOOR_GRAY_2 = (40, 40, 40)
FLOOR_GRAY_3 = (60, 60, 60)
FLOOR_GRAY_4 = (80, 80, 80)
FLOOR_GRAY_5 = (100, 100, 100)
FLOOR_GRAY_6 = (120, 120, 120)
FLOOR_GRAY_7 = (140, 140, 140)
FLOOR_COLORS = [FLOOR_GRAY_1, FLOOR_GRAY_2, FLOOR_GRAY_3, FLOOR_GRAY_4, FLOOR_GRAY_5, FLOOR_GRAY_6, FLOOR_GRAY_7]


# Hexagon dimensions
HEX_SIDE = 60
# Recalculated based on a proper hex grid
HEX_WIDTH = HEX_SIDE * 2
HEX_HEIGHT = int(HEX_SIDE * math.sqrt(3))

# --- Initialize Pygame ---
pygame.init()
pygame.mixer.init() # Initialize the mixer for sound
# Set the game to run in fullscreen mode and get dimensions after initialization
SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Python Zombie Shooter")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 72)

# Global variables for top scores and audio settings
top_scores = []
global_volume = 0.5
is_muted = False
# Default keybinds, now a global dictionary
keybinds = {
    'move_up': pygame.K_w,
    'move_down': pygame.K_s,
    'move_left': pygame.K_a,
    'move_right': pygame.K_d
}


# --- Sound Generation ---
def generate_sound(frequency, duration, volume):
    """
    Generates a sound wave and returns a Pygame Sound object.
    frequency: The frequency of the sine wave in Hz.
    duration: The duration of the sound in milliseconds.
    volume: The volume (0.0 to 1.0).
    
    This version has a corrected calculation for the sound's volume envelope
    to prevent the ValueError from mismatched array sizes.
    """
    sample_rate = 44100
    n_samples = int(round(duration * sample_rate / 1000))
    
    # Define a simple fade-in/out length (e.g., 10% of the total duration)
    fade_len = int(n_samples * 0.1)
    
    # Calculate the length of the sustained (middle) portion
    sustain_len = n_samples - (fade_len * 2)
    
    # Handle cases where the sound is too short for a fade
    if sustain_len < 0:
        fade_len = n_samples // 2
        sustain_len = 0
    
    # Generate the fade-in, sustain, and fade-out arrays
    fade_in = np.linspace(0, 1, fade_len)
    sustain = np.ones(sustain_len)
    fade_out = np.linspace(1, 0, n_samples - fade_len - sustain_len) # Correct length calculation
    
    # Concatenate them to create the full volume envelope array
    full_arr = np.concatenate([fade_in, sustain, fade_out])
    
    buf = np.zeros((n_samples, 2), dtype=np.int16)
    max_sample = 32767
    
    # Generate the sine wave
    sine_wave = np.sin(2 * np.pi * np.arange(n_samples) * frequency / sample_rate)
    
    # Multiply the sine wave by the volume envelope
    scaled_wave = np.array(sine_wave * max_sample * volume * full_arr, dtype=np.int16)
    
    for channel in range(2):
        buf[:, channel] = scaled_wave
    
    sound = pygame.sndarray.make_sound(buf)
    return sound

# Generate our sound effects internally
shoot_sound = generate_sound(500, 50, 0.25) # The volume has been lowered from 0.375 to 0.25
hit_sound = generate_sound(300, 100, 0.3)
zombie_death_sound = generate_sound(150, 200, 0.6)

# --- Classes ---
class Player(pygame.sprite.Sprite):
    """
    Represents the player character.
    Handles movement, health, and shooting.
    """
    def __init__(self):
        super().__init__()
        # Create a circular player icon
        self.image = pygame.Surface([50, 50], pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (25, 25), 25)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed = 5
        self.health = 100
        self.max_health = 100
        # New attributes for weapon upgrade
        self.current_weapon = 'pistol' # pistol, machine_gun, gatling_gun
        self.last_shot_time = 0
        self.fire_rate = 500 # milliseconds between shots (for pistol)

    def update(self):
        """
        Updates player position based on key presses.
        Now uses the global keybinds dictionary for movement.
        """
        keys = pygame.key.get_pressed()
        # Movement with WASD
        if keys[keybinds['move_left']] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[keybinds['move_right']] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        if keys[keybinds['move_up']] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[keybinds['move_down']] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed
            
        # Movement with Arrow Keys
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed


    def draw(self):
        """
        Draws the player on the screen.
        """
        screen.blit(self.image, self.rect)

    def shoot(self, mouse_pos, all_sprites, bullets):
        """
        Creates a new bullet instance and adds it to the bullet group.
        Fires only if the fire rate cooldown has passed.
        """
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.fire_rate:
            shoot_sound.play()
            direction = math.atan2(mouse_pos[1] - self.rect.centery, mouse_pos[0] - self.rect.centerx)
            # Change bullet color based on weapon
            if self.current_weapon == 'machine_gun':
                bullet_color = YELLOW
            elif self.current_weapon == 'gatling_gun':
                bullet_color = MAGENTA
            else:
                bullet_color = RED

            bullet = Bullet(self.rect.center, direction, bullet_color)
            all_sprites.add(bullet)
            bullets.add(bullet)
            self.last_shot_time = current_time
        
    def restore_health(self, amount):
        """
        Restores player's health up to the maximum.
        """
        self.health = min(self.max_health, self.health + amount)


class Zombie(pygame.sprite.Sprite):
    """
    Represents a zombie enemy.
    Moves towards the player.
    Initial speed is slower, but increases when hit by a bullet.
    """
    def __init__(self, initial_health):
        super().__init__()
        # Create a circular zombie icon
        self.image = pygame.Surface([40, 40], pygame.SRCALPHA)
        pygame.draw.circle(self.image, GREEN, (20, 20), 20)
        self.rect = self.image.get_rect()
        # Spawn zombie at a random position outside the screen
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = -50
        elif side == 'bottom':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = SCREEN_HEIGHT + 50
        elif side == 'left':
            self.rect.x = -50
            self.rect.y = random.randint(0, SCREEN_HEIGHT)
        else: # side == 'right'
            self.rect.x = SCREEN_WIDTH + 50
            self.rect.y = random.randint(0, SCREEN_HEIGHT)

        # Zombies start slow and speed up when hit
        self.speed = random.uniform(0.5, 1.5)
        self.health = initial_health

    def update(self, player_rect):
        """
        Moves the zombie towards the player's current position.
        """
        dx = player_rect.x - self.rect.x
        dy = player_rect.y - self.rect.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.rect.x += self.speed * dx / dist
            self.rect.y += self.speed * dy / dist
            
    def speed_up(self, amount):
        """
        Increases the zombie's speed.
        """
        self.speed += amount

    def draw(self):
        """
        Draws the zombie on the screen.
        """
        screen.blit(self.image, self.rect)

class WanderingZombie(Zombie):
    """
    A zombie that wanders aimlessly on the screen.
    Used for the background of the menu.
    """
    def __init__(self):
        super().__init__(initial_health=1) # A wandering zombie has minimal health
        self.speed = random.uniform(0.5, 1.5)
        # Give a random direction at the start
        self.vel_x = random.uniform(-1, 1) * self.speed
        self.vel_y = random.uniform(-1, 1) * self.speed
        
        # Reset position to a random edge of the screen
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = -50
        elif side == 'bottom':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = SCREEN_HEIGHT + 50
        elif side == 'left':
            self.rect.x = -50
            self.rect.y = random.randint(0, SCREEN_HEIGHT)
        else: # side == 'right'
            self.rect.x = SCREEN_WIDTH + 50
            self.rect.y = random.randint(0, SCREEN_HEIGHT)
    
    def update(self):
        """
        Moves the zombie and resets its position if it goes off-screen.
        """
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Reset zombie if it goes off screen
        if self.rect.right < -50 or self.rect.left > SCREEN_WIDTH + 50 or \
           self.rect.bottom < -50 or self.rect.top > SCREEN_HEIGHT + 50:
            self.__init__() # Re-initialize to a new random position and direction

class Bullet(pygame.sprite.Sprite):
    """
    Represents a bullet fired by the player.
    """
    def __init__(self, pos, direction, color):
        super().__init__()
        self.image = pygame.Surface([5, 5])
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        self.speed = 10
        self.vel_x = self.speed * math.cos(direction)
        self.vel_y = self.speed * math.sin(direction)

    def update(self):
        """
        Moves the bullet and kills it if it goes off-screen.
        """
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or \
           self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def draw(self):
        """
        Draws the bullet on the screen.
        """
        screen.blit(self.image, self.rect)
        
class PowerUp(pygame.sprite.Sprite):
    """
    Represents a health-restoring power-up.
    """
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([20, 20], pygame.SRCALPHA)
        pygame.draw.circle(self.image, DARK_RED, (10, 10), 10)
        self.rect = self.image.get_rect(center=(random.randint(50, SCREEN_WIDTH - 50), random.randint(50, SCREEN_HEIGHT - 50)))
        
    def update(self):
        # The power-up doesn't move, so this method is empty.
        pass
        
class Particle:
    """
    Represents a single particle for a visual effect.
    """
    def __init__(self, pos, color):
        self.pos = list(pos)
        self.color = color
        self.velocity = [random.uniform(-3, 3), random.uniform(-3, 3)]
        self.lifespan = random.randint(10, 30)
        self.size = 5

    def update(self):
        # Update particle position
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        # Decrease lifespan
        self.lifespan -= 1
        # Decrease size slightly for a fading effect
        self.size = max(0, self.size - 0.2)

    def draw(self, screen_surface):
        if self.lifespan > 0 and self.size > 0:
            pygame.draw.circle(screen_surface, self.color, (int(self.pos[0]), int(self.pos[1])), int(self.size))

class Barrier(pygame.sprite.Sprite):
    """
    Represents a barrier that blocks movement.
    """
    def __init__(self, pos):
        super().__init__()
        self.width = random.randint(50, 200)
        self.height = random.randint(50, 200)
        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(BARRIER_COLOR)
        self.rect = self.image.get_rect(topleft=pos)

# --- Helper Functions ---
def draw_floor_background():
    """
    Draws a tiled hexagonal floor pattern on the screen.
    This version uses a correct alignment algorithm for flat-topped hexagons
    and eight shades of gray for the tiles.
    """
    hex_radius = HEX_SIDE
    hex_width = hex_radius * 2
    hex_height = hex_radius * math.sqrt(3)

    # Calculate number of hexes to draw
    num_cols = int(SCREEN_WIDTH / (hex_width * 0.75)) + 2
    num_rows = int(SCREEN_HEIGHT / hex_height) + 2

    for row in range(num_rows):
        for col in range(num_cols):
            # Calculate the center of the hexagon
            x_pos = col * hex_width * 0.75
            y_pos = row * hex_height
            
            # Apply offset for every other column
            if col % 2 != 0:
                y_pos += hex_height / 2

            # Determine color based on a more robust pattern
            # The (row * 2 + col) % 7 pattern provides a better distribution for hex grids.
            color_index = (row * 2 + col) % 7
            color = FLOOR_COLORS[color_index]

            # Vertices for a flat-topped hexagon
            vertices = [
                (x_pos + hex_radius, y_pos),
                (x_pos + hex_radius * 0.5, y_pos + hex_height * 0.5),
                (x_pos - hex_radius * 0.5, y_pos + hex_height * 0.5),
                (x_pos - hex_radius, y_pos),
                (x_pos - hex_radius * 0.5, y_pos - hex_height * 0.5),
                (x_pos + hex_radius * 0.5, y_pos - hex_height * 0.5),
            ]
            
            pygame.draw.polygon(screen, color, vertices)

# --- Menu Functions ---
def show_start_menu():
    """
    Displays the game's main menu, with New Game, Options, and Quit buttons.
    """
    menu_running = True
    
    # Create a group for the zombies wandering in the background
    wandering_zombies = pygame.sprite.Group()
    for _ in range(5):
        wandering_zombies.add(WanderingZombie())

    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if new_game_rect.collidepoint(event.pos):
                    return "new_game"
                if options_rect.collidepoint(event.pos):
                    return "options_menu"
                if quit_rect.collidepoint(event.pos):
                    pygame.quit()
                    quit()
        
        # Draw the tiled floor background first
        draw_floor_background()
        
        # Draw zombies in the background
        wandering_zombies.update()
        wandering_zombies.draw(screen)

        # Draw the menu text and buttons on top
        title_text = large_font.render("ZOMBIE SHOOTER", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)

        new_game_text = font.render("New Game", True, WHITE)
        new_game_rect = new_game_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        
        options_text = font.render("Options", True, WHITE)
        options_rect = options_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        quit_text = font.render("Quit", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))

        screen.blit(new_game_text, new_game_rect)
        screen.blit(options_text, options_rect)
        screen.blit(quit_text, quit_rect)
        
        pygame.display.flip()

def show_options_menu():
    """
    Displays the options menu with buttons for Audio and Controls.
    """
    options_running = True
    while options_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if audio_rect.collidepoint(event.pos):
                    return "audio_menu"
                if controls_rect.collidepoint(event.pos):
                    return "controls_menu"
                if back_rect.collidepoint(event.pos):
                    return "start_menu"

        draw_floor_background()

        # Title
        title_text = large_font.render("OPTIONS", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)
        
        # Audio button
        audio_text = font.render("Audio", True, WHITE)
        audio_rect = audio_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(audio_text, audio_rect)
        
        # Controls button
        controls_text = font.render("Controls", True, WHITE)
        controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(controls_text, controls_rect)

        # Back button
        back_text = font.render("Back", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(back_text, back_rect)

        pygame.display.flip()

def show_audio_menu():
    """
    Displays the audio options menu with controls for volume and mute.
    """
    global global_volume, is_muted, shoot_sound, hit_sound, zombie_death_sound
    audio_running = True
    slider_dragging = False

    # Define slider dimensions and position
    slider_x = SCREEN_WIDTH // 2 - 100
    slider_y = SCREEN_HEIGHT // 2 - 50
    slider_width = 200
    slider_height = 20
    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)

    # Mute button dimensions and position
    mute_button_x = SCREEN_WIDTH // 2 - 100
    mute_button_y = SCREEN_HEIGHT // 2
    mute_button_width = 200
    mute_button_height = 50
    mute_button_rect = pygame.Rect(mute_button_x, mute_button_y, mute_button_width, mute_button_height)

    while audio_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            
            # Handle mouse events for the slider and buttons
            if event.type == pygame.MOUSEBUTTONDOWN:
                if slider_rect.collidepoint(event.pos):
                    slider_dragging = True
                if mute_button_rect.collidepoint(event.pos):
                    is_muted = not is_muted
                    # Set volume on individual sound objects instead of the mixer module
                    if is_muted:
                        shoot_sound.set_volume(0)
                        hit_sound.set_volume(0)
                        zombie_death_sound.set_volume(0)
                    else:
                        shoot_sound.set_volume(global_volume)
                        hit_sound.set_volume(global_volume)
                        zombie_death_sound.set_volume(global_volume)
                if back_rect.collidepoint(event.pos):
                    return "options_menu"

            if event.type == pygame.MOUSEBUTTONUP:
                slider_dragging = False

            if event.type == pygame.MOUSEMOTION and slider_dragging:
                # Update volume based on mouse position
                mouse_x = event.pos[0]
                # Clamp the position to the slider's boundaries
                slider_knob_x = max(slider_x, min(mouse_x, slider_x + slider_width))
                global_volume = (slider_knob_x - slider_x) / slider_width
                
                # Set volume on individual sound objects instead of the mixer module
                shoot_sound.set_volume(global_volume)
                hit_sound.set_volume(global_volume)
                zombie_death_sound.set_volume(global_volume)
                
                is_muted = (global_volume == 0)

        draw_floor_background()

        # Title
        title_text = large_font.render("AUDIO", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)

        # Volume label and slider
        volume_text = font.render("Volume", True, WHITE)
        volume_rect = volume_text.get_rect(center=(SCREEN_WIDTH // 2, slider_y - 25))
        screen.blit(volume_text, volume_rect)
        
        # Draw the slider track
        pygame.draw.rect(screen, (100, 100, 100), slider_rect)
        
        # Convert slider knob position to an integer to prevent crash
        slider_knob_x = slider_x + (global_volume * slider_width)
        pygame.draw.circle(screen, GREEN, (int(slider_knob_x), slider_y + slider_height // 2), 10)
        
        # Mute button
        mute_button_text = font.render("Mute" if not is_muted else "Unmute", True, WHITE)
        pygame.draw.rect(screen, (50, 50, 50), mute_button_rect)
        screen.blit(mute_button_text, mute_button_text.get_rect(center=mute_button_rect.center))

        # Back button
        back_text = font.render("Back", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(back_text, back_rect)

        pygame.display.flip()

def show_controls_menu():
    """
    Displays the controls menu with a list of keybindings, now with remapping.
    """
    global keybinds
    controls_running = True
    remap_mode = False
    current_key_to_remap = None
    
    # Calculate button positions
    button_y_start = SCREEN_HEIGHT // 2 - 100
    button_spacing = 60
    button_width = 100
    button_height = 40
    
    # Define a list of actions and their button positions
    actions = [
        ('move_up', "Move Up"),
        ('move_down', "Move Down"),
        ('move_left', "Move Left"),
        ('move_right', "Move Right")
    ]
    
    action_rects = {}

    while controls_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN and not remap_mode:
                if back_rect.collidepoint(event.pos):
                    return "options_menu"
                # Check if a remap button was clicked
                for action, rect in action_rects.items():
                    if rect.collidepoint(event.pos):
                        remap_mode = True
                        current_key_to_remap = action
            
            # If in remap mode, wait for a key press
            if event.type == pygame.KEYDOWN and remap_mode:
                if event.key not in keybinds.values():
                    keybinds[current_key_to_remap] = event.key
                    remap_mode = False
                    current_key_to_remap = None
                else:
                    # Inform the user the key is already in use
                    # A small message box or console message is fine for now
                    print("Key is already in use!")

        draw_floor_background()

        # Title
        title_text = large_font.render("CONTROLS", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)
        
        # Display the current keybindings and change buttons
        for i, (key_action, key_text) in enumerate(actions):
            # Display action text
            action_label = font.render(f'{key_text}:', True, WHITE)
            action_rect = action_label.get_rect(center=(SCREEN_WIDTH // 2 - 100, button_y_start + i * button_spacing))
            screen.blit(action_label, action_rect)

            # Display the currently bound key
            current_key_name = pygame.key.name(keybinds[key_action]).upper()
            key_name_label = font.render(current_key_name, True, YELLOW)
            key_name_rect = key_name_label.get_rect(center=(SCREEN_WIDTH // 2, button_y_start + i * button_spacing))
            screen.blit(key_name_label, key_name_rect)

            # Draw the Change button
            change_button_rect = pygame.Rect(
                SCREEN_WIDTH // 2 + 50,
                button_y_start + i * button_spacing - button_height // 2,
                button_width,
                button_height
            )
            pygame.draw.rect(screen, (50, 50, 50), change_button_rect, border_radius=10)
            change_text = font.render("Change", True, WHITE)
            change_text_rect = change_text.get_rect(center=change_button_rect.center)
            screen.blit(change_text, change_text_rect)
            action_rects[key_action] = change_button_rect
        
        # Display shooting control, which is not remappable
        shoot_text = font.render("Shoot: Left Mouse Button", True, WHITE)
        shoot_rect = shoot_text.get_rect(center=(SCREEN_WIDTH // 2, button_y_start + len(actions) * button_spacing + 20))
        screen.blit(shoot_text, shoot_rect)

        # Prompt for key change
        if remap_mode:
            prompt_text = font.render(f"Press a new key for '{current_key_to_remap.replace('_', ' ').title()}'", True, MAGENTA)
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200))
            screen.blit(prompt_text, prompt_rect)

        # Back button
        back_text = font.render("Back", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(back_text, back_rect)

        pygame.display.flip()

def show_pause_menu():
    """
    Displays the pause menu with Resume and Main Menu buttons.
    """
    pause_running = True
    while pause_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_rect.collidepoint(event.pos):
                    return "resume"
                if main_menu_rect.collidepoint(event.pos):
                    return "start_menu"

        # Draw the tiled floor background first
        draw_floor_background()

        # Draw a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Draw the menu text and buttons
        pause_text = large_font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(pause_text, pause_rect)

        resume_text = font.render("Resume", True, WHITE)
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        
        main_menu_text = font.render("Main Menu", True, WHITE)
        main_menu_rect = main_menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        screen.blit(resume_text, resume_rect)
        screen.blit(main_menu_text, main_menu_rect)

        pygame.display.flip()
        
def show_game_over_screen(final_score):
    """
    Displays the game over screen with the final score and top scores.
    """
    global top_scores
    top_scores.append(final_score)
    top_scores.sort(reverse=True)
    top_scores = top_scores[:5] # Keep only the top 5 scores

    game_over_running = True
    while game_over_running:
        draw_floor_background()
        
        # Game Over Title
        game_over_text = large_font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(game_over_text, game_over_rect)

        # Final Score
        final_score_text = font.render(f"Final Score: {final_score}", True, WHITE)
        final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(final_score_text, final_score_rect)

        # Top Scores
        top_scores_title = font.render("Top Scores:", True, WHITE)
        top_scores_title_rect = top_scores_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(top_scores_title, top_scores_title_rect)
        
        for i, score in enumerate(top_scores):
            score_text = font.render(f"{i + 1}. {score}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30 + i * 30))
            screen.blit(score_text, score_rect)

        # Return to Menu Button
        return_text = font.render("Return to Menu", True, WHITE)
        return_rect = return_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(return_text, return_rect)

        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if return_rect.collidepoint(event.pos):
                    return "start_menu"

def main_game_loop():
    """
    Contains the main game logic and drawing loop.
    """
    # --- Sprite Groups ---
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    zombies = pygame.sprite.Group()
    powerups = pygame.sprite.Group() # New group for power-ups
    barriers = pygame.sprite.Group() # New group for barriers
    particles = [] # A list to hold the new particle effects

    # --- Game Variables ---
    player = Player()
    all_sprites.add(player)
    score = 0
    last_zombie_spawn_time = pygame.time.get_ticks()
    zombie_spawn_rate = 1250 # in milliseconds, changed from 1000
    last_powerup_spawn_time = pygame.time.get_ticks()
    powerup_spawn_rate = 15000 # in milliseconds, a new power-up every 15 seconds
    is_game_over = False
    is_paused = False # New state variable for pausing the game
    is_shooting = False # New state variable to track if the mouse button is held down

    # Generate a random number of barriers and place them on the screen
    num_barriers = random.randint(3, 7)
    for _ in range(num_barriers):
        while True:
            # Pick a random position for the new barrier
            x = random.randint(50, SCREEN_WIDTH - 250)
            y = random.randint(50, SCREEN_HEIGHT - 250)
            new_barrier = Barrier((x, y))
            
            # Check for overlaps with other barriers and the player's starting position
            # This is a simple but effective way to ensure no overlaps
            overlap = False
            if pygame.sprite.spritecollide(new_barrier, barriers, False):
                overlap = True
            
            # Also ensure it doesn't spawn too close to the player
            player_start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 100, 200, 200)
            if new_barrier.rect.colliderect(player_start_rect):
                overlap = True

            if not overlap:
                all_sprites.add(new_barrier)
                barriers.add(new_barrier)
                break

    # --- Main Game Loop ---
    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Check for escape key to toggle pause
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                is_paused = not is_paused
            
            # Track if the mouse button is pressed for rapid fire
            if not is_paused and not is_game_over:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left mouse button
                        is_shooting = True
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        is_shooting = False
        
        # --- Game Logic ---
        if not is_game_over and not is_paused:
            # Check for score thresholds to upgrade gun and increase fire rate
            if score >= 500 and player.current_weapon != 'gatling_gun':
                player.current_weapon = 'gatling_gun'
                player.fire_rate = 50 # Base fire rate for gatling gun
            elif score >= 250 and player.current_weapon == 'pistol':
                player.current_weapon = 'machine_gun'
                player.fire_rate = 100 # Base fire rate for machine gun
            
            # Increase fire rate progressively based on score tiers
            fire_rate_modifier = score // 250
            if player.current_weapon == 'machine_gun':
                player.fire_rate = max(50, 100 - (fire_rate_modifier - 1) * 10)
            elif player.current_weapon == 'gatling_gun':
                player.fire_rate = max(20, 50 - (fire_rate_modifier - 2) * 5)


            # Fire the weapon if the player is holding the mouse button
            if is_shooting:
                player.shoot(pygame.mouse.get_pos(), all_sprites, bullets)

            # Store the player's old position before updating
            player_old_rect = player.rect.copy()
            
            # Update player and zombies separately to avoid the TypeError
            player.update()
            zombies.update(player.rect)
            bullets.update()
            powerups.update()
            
            # Update and clean up particles
            for particle in particles:
                particle.update()
            particles = [p for p in particles if p.lifespan > 0]
            
            # Collision detection for player and barriers
            if pygame.sprite.spritecollide(player, barriers, False):
                player.rect = player_old_rect
            
            # Collision detection for zombies and barriers
            for zombie in zombies:
                if pygame.sprite.spritecollide(zombie, barriers, False):
                    # For a simple bounce, reverse the movement direction
                    zombie.rect.x -= zombie.speed
                    zombie.rect.y -= zombie.speed

            # Spawn new zombies
            now = pygame.time.get_ticks()
            if now - last_zombie_spawn_time > zombie_spawn_rate:
                zombie_health = 1 + (score // 100) # Difficulty scales with score
                new_zombie = Zombie(zombie_health)
                all_sprites.add(new_zombie)
                zombies.add(new_zombie)
                last_zombie_spawn_time = now
                # Increase difficulty over time by reducing spawn rate
                zombie_spawn_rate = max(200, zombie_spawn_rate - 5)

            # Spawn a new power-up if one isn't on screen
            now = pygame.time.get_ticks()
            if len(powerups) == 0 and now - last_powerup_spawn_time > powerup_spawn_rate:
                new_powerup = PowerUp()
                all_sprites.add(new_powerup)
                powerups.add(new_powerup)
                last_powerup_spawn_time = now

            # Check for collisions between bullets and zombies, and bullets and barriers
            # Bullets are destroyed on impact with either
            pygame.sprite.groupcollide(bullets, barriers, True, False)
            hits = pygame.sprite.groupcollide(zombies, bullets, False, True)
            for zombie, bullet_hit_list in hits.items():
                hit_sound.play() # Play sound on hit
                zombie.health -= len(bullet_hit_list)
                # Speed up the zombie when it's hit
                zombie.speed_up(0.5)
                if zombie.health <= 0:
                    zombie_death_sound.play() # Play sound on zombie death
                    # Create a burst of particles when the zombie is destroyed
                    for _ in range(20):
                        particles.append(Particle(zombie.rect.center, GREEN))
                    zombie.kill()
                    score += 10
                    
            # Check for collisions between bullets and power-ups
            powerup_hits = pygame.sprite.groupcollide(powerups, bullets, True, True)
            if powerup_hits:
                player.restore_health(25) # Restore 25 health

            # Check for collisions between player and zombies
            player_hits = pygame.sprite.spritecollide(player, zombies, True)
            if player_hits:
                player.health -= 25
                if player.health <= 0:
                    is_game_over = True

        # --- Drawing ---
        draw_floor_background()
        
        # Draw all sprites including barriers
        all_sprites.draw(screen)
        
        # Draw the particles after all sprites
        for particle in particles:
            particle.draw(screen)

        # Display score and health
        score_text = font.render(f'Score: {score}', True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Display weapon name
        weapon_name = player.current_weapon.replace('_', ' ').title()
        weapon_surf = font.render(f'Weapon: {weapon_name}', True, WHITE)
        screen.blit(weapon_surf, (10, 80))

        # Health bar drawing
        # Determine health bar color based on current health
        if player.health > 75:
            health_color = GREEN
        elif player.health > 50:
            health_color = (255, 255, 0) # Yellow
        elif player.health > 25:
            health_color = (255, 165, 0) # Orange
        else:
            health_color = RED

        # Draw the background for the health bar
        health_bar_rect_bg = pygame.Rect(10, 50, 150, 20)
        pygame.draw.rect(screen, (50, 50, 50), health_bar_rect_bg, border_radius=5)

        # Calculate the width of the health bar
        health_bar_width = (player.health / player.max_health) * 150
        health_bar_rect = pygame.Rect(10, 50, health_bar_width, 20)
        pygame.draw.rect(screen, health_color, health_bar_rect, border_radius=5)
        
        if is_game_over:
            # Return final score to main loop
            return score
        
        # If the game is paused, display the pause menu
        if is_paused:
            action = show_pause_menu()
            if action == "resume":
                is_paused = False
            elif action == "start_menu":
                return "start_menu"

        pygame.display.flip()

        # --- Frame Rate Control ---
        clock.tick(60)

    # This part is technically unreachable in this version, but good practice
    return score

# --- Main Program Entry ---
if __name__ == "__main__":
    current_screen = "start_menu"
    while True:
        if current_screen == "start_menu":
            action = show_start_menu()
            if action == "new_game":
                current_screen = "game"
            elif action == "options_menu":
                current_screen = "options"
        elif current_screen == "options":
            action = show_options_menu()
            if action == "start_menu":
                current_screen = "start_menu"
            elif action == "audio_menu":
                current_screen = "audio"
            elif action == "controls_menu":
                current_screen = "controls"
        elif current_screen == "audio":
            action = show_audio_menu()
            if action == "options_menu":
                current_screen = "options"
        elif current_screen == "controls":
            action = show_controls_menu()
            if action == "options_menu":
                current_screen = "options"
        elif current_screen == "game":
            result = main_game_loop()
            if result == "start_menu":
                current_screen = "start_menu"
            else:
                final_score = result
                current_screen = show_game_over_screen(final_score)
