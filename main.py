from typing import Optional

import pygame
from pygame import mixer
import csv
import json
from pathlib import Path
import time  # Add time module for timing
import logging  # Add logging module
import sys
import gc  # For garbage collection control

import constants as cons
from world import World
from character import Character
from weapon import Weapon
from items import Item
from button import Button
from sound_manager import MinimalSoundManager

pygame.init()

# Set up logging - SIMPLIFIED
logging.basicConfig(
    level=logging.ERROR,  # Only show errors
    filename='game.log',
    filemode='w'
)
logger = logging.getLogger(__name__)

# Sound configuration - Individual toggles for different sound types
SOUND_MANAGER_ENABLED = False  # Master switch for sound system
MUSIC_ENABLED = False
ARROW_SHOT_SOUND_ENABLED = False
ARROW_HIT_SOUND_ENABLED = False
COIN_SOUND_ENABLED = True  # Let's start by enabling coin sounds
HEAL_SOUND_ENABLED = False

sound_manager = MinimalSoundManager()

# Initialize sound if any sound type is enabled
if SOUND_MANAGER_ENABLED or MUSIC_ENABLED or ARROW_SHOT_SOUND_ENABLED or ARROW_HIT_SOUND_ENABLED or COIN_SOUND_ENABLED or HEAL_SOUND_ENABLED:
    if not sound_manager.enable():
        print("WARNING: Sound system failed to initialize. Running without sound.")
        SOUND_MANAGER_ENABLED = False
        MUSIC_ENABLED = False
        ARROW_SHOT_SOUND_ENABLED = False
        ARROW_HIT_SOUND_ENABLED = False
        COIN_SOUND_ENABLED = False
        HEAL_SOUND_ENABLED = False

#Display section
monitor_res = (pygame.display.Info().current_w,pygame.display.Info().current_h)
screen = pygame.display.set_mode((cons.SCREEN_WIDTH,cons.SCREEN_HEIGHT))
pygame.display.set_caption("Into the Deep")
CLOCK = pygame.time.Clock()

#Define game variables
level = 1
screen_scroll = [0, 0]
start_game = False
pause_game = False
start_intro = False
fullscreen = False
player_health = 100
player_score = 0
frame_counter = 0

# Performance tracking
TRACK_PERFORMANCE = True
last_time = time.time()
frame_times = []
section_times = {}
current_section = None
frame_count = 0

# Memory tracking
def get_obj_count():
    """Get count of objects by type for memory tracking"""
    counts = {}
    for obj in gc.get_objects():
        obj_type = type(obj).__name__
        if obj_type not in counts:
            counts[obj_type] = 0
        counts[obj_type] += 1
    return counts

memory_snapshots = []
last_snapshot_time = time.time()

def take_memory_snapshot():
    """Take a snapshot of current memory usage"""
    global last_snapshot_time
    if time.time() - last_snapshot_time > 5.0:  # Every 5 seconds
        memory_snapshots.append(get_obj_count())
        if len(memory_snapshots) > 10:
            memory_snapshots.pop(0)  # Keep last 10 snapshots
        last_snapshot_time = time.time()

def print_memory_diff():
    """Print difference between first and last memory snapshot"""
    if len(memory_snapshots) < 2:
        print("Not enough memory snapshots collected")
        return
    
    first = memory_snapshots[0]
    last = memory_snapshots[-1]
    
    print("\nMemory Usage Changes:")
    diff_items = []
    
    # Calculate differences
    for obj_type, count in last.items():
        if obj_type in first:
            diff = count - first[obj_type]
            if abs(diff) > 10:  # Only show significant changes
                diff_items.append((obj_type, diff))
        else:
            diff_items.append((obj_type, count))
    
    # Sort by absolute difference
    diff_items.sort(key=lambda x: abs(x[1]), reverse=True)
    
    # Show top 20 changes
    for obj_type, diff in diff_items[:20]:
        print(f"  {obj_type}: {'+' if diff > 0 else ''}{diff}")

def start_section(name):
    """Start timing a section of code"""
    global current_section, last_time
    if TRACK_PERFORMANCE:
        current_section = name
        last_time = time.time()

def end_section():
    """End timing the current section"""
    global current_section, last_time
    if TRACK_PERFORMANCE and current_section:
        elapsed = time.time() - last_time
        if current_section not in section_times:
            section_times[current_section] = []
        section_times[current_section].append(elapsed)
        # Print warning if section took too long
        if elapsed > 0.05:  # More than 50ms is suspicious
            print(f"WARNING: Section {current_section} took {elapsed*1000:.1f}ms")
        current_section = None

def log_performance():
    """Log performance statistics"""
    if TRACK_PERFORMANCE and len(frame_times) > 0:
        avg_frame = sum(frame_times) / len(frame_times)
        print(f"\nPerformance Report:")
        print(f"Average frame time: {avg_frame*1000:.1f}ms ({1/avg_frame:.1f} FPS)")
        
        # Report on sections
        for section, times in section_times.items():
            if len(times) > 0:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                print(f"  {section}: avg={avg_time*1000:.1f}ms, max={max_time*1000:.1f}ms")
        
        # Print memory diff
        print_memory_diff()

#Function to help find and get paths to load assets
def find_relative_path(file_name) -> Optional[Path]:
    start_dir = Path.cwd()
    for path in start_dir.rglob(file_name):
        return str(path.relative_to(start_dir))
    return None

try:
    with open (find_relative_path("saves/into_the_deep_save_data.json"),"r") as save_file:
        save_data = json.load(save_file)
        level = save_data.get("level")
        player_health = save_data.get("health")
        player_score = save_data.get("score")
except:
    print("No file created:")

# Function to help load in sounds
def load_sound(sound_path, volume):
    """Safely load a sound file, returns None if sound is disabled"""
    if sound_manager.initialized:
        path = find_relative_path(sound_path)
        if path:
            return sound_manager.load_sound(path, volume)
    return None

def play_sound(sound, sound_type):
    """Play sound based on its type and whether that type is enabled"""
    if not sound:
        return
        
    if sound_type == 'arrow_shot' and ARROW_SHOT_SOUND_ENABLED:
        sound_manager.play_sound(sound)
    elif sound_type == 'arrow_hit' and ARROW_HIT_SOUND_ENABLED:
        sound_manager.play_sound(sound)
    elif sound_type == 'coin' and COIN_SOUND_ENABLED:
        sound_manager.play_sound(sound)
    elif sound_type == 'heal' and HEAL_SOUND_ENABLED:
        sound_manager.play_sound(sound)

def play_music(music_path, volume):
    """Safely play music, does nothing if music is disabled"""
    if MUSIC_ENABLED:
        path = find_relative_path(music_path)
        if path:
            sound_manager.play_music(path, volume)

def pause_music():
    """Safely pause music"""
    if MUSIC_ENABLED:
        sound_manager.pause_music()

def unpause_music():
    """Safely unpause music"""
    if MUSIC_ENABLED:
        sound_manager.unpause_music()

def stop_music():
    """Safely stop music"""
    if MUSIC_ENABLED:
        sound_manager.stop_music()

# Load sound effects - these will be None if sound is disabled
arrow_shot_fx = load_sound("assets/audio/arrow_shot.mp3", cons.SOUND_EFFECT_VOLUME)
arrow_hit_fx = load_sound("assets/audio/arrow_hit.wav", cons.SOUND_EFFECT_VOLUME)
coin_collect_fx = load_sound("assets/audio/coin.wav", cons.SOUND_EFFECT_VOLUME)
heal_fx = load_sound("assets/audio/heal.wav", cons.SOUND_EFFECT_VOLUME)

# Play background music if enabled
play_music("assets/audio/music.wav", cons.MUSIC_VOLUME)

#load game font
font = pygame.font.Font(find_relative_path("assets/fonts/AtariClassic.ttf"), 17)

#Function to help scale images
def scale_img(image,scale):
    w = image.get_width()
    h = image.get_height()
    trasformed_image = pygame.transform.scale(image,(w*scale, h*scale))
    return trasformed_image

#load backgounds
menu_background_image = scale_img(pygame.image.load(find_relative_path("assets/images/backgrounds/menu_background.png")).convert_alpha(), 1)
pause_background_image = scale_img(pygame.image.load(find_relative_path("assets/images/backgrounds/pause_background.png")).convert_alpha(), 1)

#load tile_map images
tile_list = []
for x in range(cons.TILE_TYPES):
    img = pygame.image.load(find_relative_path(f"assets/images/tiles/{x}.png")).convert_alpha()
    img = scale_img(img,cons.global_scale)
    tile_list.append(img)

#load character images
mob_types = ["elf", "imp", "skeleton", "goblin", "muddy", "tiny_zombie", "big_demon"]
mobs_animation_list = [] 
for mob in mob_types:
    #Creating a character
    animation_types = ["idle","run"]
    animation_list = []
    for animation in animation_types:
        temp_list = []
        for i in range(4):
            img = pygame.image.load(find_relative_path(f"assets/images/characters/{mob}/{animation}/{i}.png")).convert_alpha()
            img = scale_img(img,cons.global_scale)
            temp_list.append(img)
        #Adding temp list to main list (Creates sub list)
        animation_list.append(temp_list)
    mobs_animation_list.append(animation_list)

#load player health images
heart_empty = scale_img(pygame.image.load(find_relative_path("assets/images/items/heart_empty.png")).convert_alpha(),cons.item_scale)
heart_half = scale_img(pygame.image.load(find_relative_path("assets/images/items/heart_half.png")).convert_alpha(),cons.item_scale)
heart_full = scale_img(pygame.image.load(find_relative_path("assets/images/items/heart_full.png")).convert_alpha(),cons.item_scale)

#load enemy health images
enemy_health_list = []
for x in range(cons.HEALTH_BAR_TYPES):
    img = scale_img(pygame.image.load(find_relative_path(f"assets/images/health_bars/{x}.png")).convert_alpha(),cons.global_scale)
    enemy_health_list.append(img)

#load weapon images
bow_image = scale_img(pygame.image.load(find_relative_path("assets/images/weapons/bow.png")).convert_alpha(),cons.bow_scale)
arrow_image = scale_img(pygame.image.load(find_relative_path("assets/images/weapons/arrow.png")).convert_alpha(),cons.bow_scale)
fireball_image = scale_img(pygame.image.load(find_relative_path("assets/images/weapons/fireball.png")).convert_alpha(),cons.fireball_scale)

#load item images
coin_images = []
for i in range(4):
    img = pygame.image.load(find_relative_path(f"assets/images/items/coin_f{i}.png")).convert_alpha()
    img = scale_img(img,cons.item_scale)
    coin_images.append(img)

red_potion_image = scale_img(pygame.image.load(find_relative_path(f"assets/images/items/potion_red.png")).convert_alpha(), cons.potion_scale)

item_images = []
item_images.append(coin_images)
item_images.append([red_potion_image])

#load button images 
exit_button_img = scale_img(pygame.image.load(find_relative_path(f"assets/images/buttons/exit_button.png")).convert_alpha(), cons.button_scale)
restart_button_img = scale_img(pygame.image.load(find_relative_path(f"assets/images/buttons/restart_button.png")).convert_alpha(), cons.button_scale)
resume_button_img = scale_img(pygame.image.load(find_relative_path(f"assets/images/buttons/resume_button.png")).convert_alpha(), cons.button_scale)
start_button_img = scale_img(pygame.image.load(find_relative_path(f"assets/images/buttons/play_button.png")).convert_alpha(), cons.button_scale)
new_game_button_img = scale_img(pygame.image.load(find_relative_path(f"assets/images/buttons/new_game_button.png")).convert_alpha(), cons.button_scale)
back_button_img = scale_img(pygame.image.load(find_relative_path(f"assets/images/buttons/back_button.png")).convert_alpha(), cons.button_scale)

# Create a custom button image for sound toggle
def create_sound_button():
    """Create a custom button image for sound toggle"""
    # Create a Surface for the button with alpha channel
    button_width = 300
    button_height = 80
    button_surf = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
    
    # Draw the button background (black rectangle with white border)
    pygame.draw.rect(button_surf, (0, 0, 0, 255), (0, 0, button_width, button_height))
    pygame.draw.rect(button_surf, (255, 255, 255, 255), (0, 0, button_width, button_height), 2)
    
    # Add text to the button
    text = "SOUND ON" if SOUND_MANAGER_ENABLED else "SOUND OFF"
    # Use a larger font for the button text
    sound_font = pygame.font.Font(find_relative_path("assets/fonts/AtariClassic.ttf"), 24)
    text_surf = sound_font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=(button_width//2, button_height//2))
    button_surf.blit(text_surf, text_rect)
    
    return button_surf

# Initialize custom button images
sound_button_img = create_sound_button()

# Function to reset level data
def reset_level():
    arrow_group.empty()
    health_text_group.empty()
    damage_text_group.empty()
    item_group.empty()
    fireball_group.empty()

    #create an empty world
    empty_data = []
    for row in range(cons.ROWS):
        r = [-1]*cons.COLS
        empty_data.append(r)
    
    return empty_data

# Function to make sprite groups
#Function to make sprite groups
def make_groups(world):
    #make sprite groups
    arrow_group = pygame.sprite.Group()
    health_text_group = pygame.sprite.Group()
    damage_text_group = pygame.sprite.Group()
    item_group = pygame.sprite.Group()
    fireball_group = pygame.sprite.Group()

    for item in world.item_list:
        item_group.add(item)
    
    return arrow_group, health_text_group, damage_text_group, item_group, fireball_group

#Function to load a level
def load_level(level, health, score):
    world_data = reset_level()
    #load level file to create world
    with open(find_relative_path(f"levels/level{level}_data.csv"), newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter= ",")
        for x, row in enumerate(reader):
            for y, tile in enumerate(row):
                world_data[x][y] = int(tile)
            #Create the world
    world = World() 
    world.process_data(world_data, tile_list, mobs_animation_list, item_images)
        
    #Reset player to before death status
    player = world.player
    player.health = health
    player.score = score

    #Extract enemies from world data
    enemy_list = world.character_list
                    
    score_coin = Item(cons.SCREEN_WIDTH - 115, 23 , 0 , coin_images, True)

    return world, player, enemy_list, score_coin

#Function that calculates how much health an enemy has
def calc_health(enemy):
    if enemy.alive == False:
        return 0
    max_health_list = [100, 50, 125, 175, 75, 300]
    bar_percentages = [0, 8, 16, 25, 33, 41, 50, 58, 66, 75, 83, 91]
    max_health = max_health_list[enemy.char_type - 1]
    curr_health = enemy.health
    for x in range(12):
        if curr_health <= (bar_percentages[x] * max_health)/100:
            return x
    return 12

#Function that outputs text onto the screen
def draw_text(text, font, text_color, x, y, scale = 1):
    img = font.render(text, True, text_color)
    img = scale_img(img, scale)
    screen.blit(img, (x, y))

#Function that displays general game information
def draw_info():
    #draw panel
    pygame.draw.rect(screen, cons.Panel, (0, 0, cons.SCREEN_WIDTH + 100 , 50))
    pygame.draw.line(screen, cons.WHITE, (0, 50), (cons.SCREEN_WIDTH + 100, 50))

    #draw player lives
    half_heart_drawn = False
    for i in range(5):
        if player.health >= ((i + 1 ) * 20):
            screen.blit(heart_full , (10 + (i * 50), 0))
        elif player.health <= 0:
            screen.blit(heart_empty , (10 + (i * 50), 0))
        elif (player.health % 20 >= 5 or (player.health < 20)) and half_heart_drawn == False:
            screen.blit(heart_half , (10 + (i * 50), 0))
            half_heart_drawn = True
        else:
            screen.blit(heart_empty , (10 + (i * 50), 0))
    
    #draw player health
    draw_text(f"{player.health}%", font, cons.WHITE, 264, 16)

    #draw level info
    draw_text(f"LEVEL:{level}", font, cons.WHITE, cons.SCREEN_WIDTH // 2 - 76, 16)

    #draw the score
    draw_text(f"X{player.score}", font, cons.WHITE, cons.SCREEN_WIDTH-104, 16)

def draw_sound_status():
    """Display which sound types are enabled"""
    if SOUND_MANAGER_ENABLED:
        # Position the sound controls to the right edge of the screen
        x_pos = cons.SCREEN_WIDTH - 250
        y_pos = 180  # Start higher up on the screen
        text_color = cons.GREEN
        
        # Title
        draw_text("Sound Controls:", font, cons.WHITE, x_pos, y_pos - 30)
        
        if MUSIC_ENABLED:
            draw_text("1. Music: ON", font, text_color, x_pos, y_pos)
        else:
            draw_text("1. Music: OFF", font, cons.RED, x_pos, y_pos)
        y_pos += 30
            
        if ARROW_SHOT_SOUND_ENABLED:
            draw_text("2. Arrow Shot: ON", font, text_color, x_pos, y_pos)
        else:
            draw_text("2. Arrow Shot: OFF", font, cons.RED, x_pos, y_pos)
        y_pos += 30
            
        if ARROW_HIT_SOUND_ENABLED:
            draw_text("3. Arrow Hit: ON", font, text_color, x_pos, y_pos)
        else:
            draw_text("3. Arrow Hit: OFF", font, cons.RED, x_pos, y_pos)
        y_pos += 30
            
        if COIN_SOUND_ENABLED:
            draw_text("4. Coin: ON", font, text_color, x_pos, y_pos)
        else:
            draw_text("4. Coin: OFF", font, cons.RED, x_pos, y_pos)
        y_pos += 30
            
        if HEAL_SOUND_ENABLED:
            draw_text("5. Heal: ON", font, text_color, x_pos, y_pos)
        else:
            draw_text("5. Heal: OFF", font, cons.RED, x_pos, y_pos)

# Class that handles screen fades
class ScreenFade():
    def __init__(self, fade_type, color, speed):
        self.fade_type = fade_type
        self.color = color
        self.speed = speed
        self.fade_counter = 0
    
    def fade(self):
        fade_complete = False
        if cons.SCREEN_WIDTH > cons.SCREEN_HEIGHT:
            greater_resolution = cons.SCREEN_WIDTH
        else:
            greater_resolution = cons.SCREEN_HEIGHT
        
        self.fade_counter += self.speed
        if self.fade_type == 1: #Whole screen fade inside out
            pygame.draw.rect(screen, self.color, (0 - self.fade_counter, 0, cons.SCREEN_WIDTH // 2, cons.SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (cons.SCREEN_WIDTH // 2 + self.fade_counter, 0, cons.SCREEN_WIDTH, cons.SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (0, 0 - self.fade_counter, cons.SCREEN_WIDTH, cons.SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.color, (0, cons.SCREEN_HEIGHT // 2 + self.fade_counter, cons.SCREEN_WIDTH, cons.SCREEN_HEIGHT))

        if self.fade_type == 2: #Vertical screen fade top to bottom:
            pygame.draw.rect(screen, self.color, (0 , 0 , cons.SCREEN_WIDTH, 0 + self.fade_counter))
        
        #check if fade animation is completed for different type of fades
        if self.fade_counter >= greater_resolution and self.fade_type == 1:
            fade_complete = True
        if self.fade_counter >= cons.SCREEN_HEIGHT and self.fade_type == 2:
            fade_complete = True
            draw_text("GAME OVER", font, cons.WHITE,cons.SCREEN_WIDTH // 2 - 226, cons.SCREEN_HEIGHT // 2 - 120, 3)
        return fade_complete

#Class that keeps that tracks of enemy health
class HealthBar(pygame.sprite.Sprite):
    def __init__(self, x, y, health_level, enemy):
        pygame.sprite.Sprite.__init__(self)
        self.health_level = health_level
        self.image = enemy_health_list[health_level]
        if enemy.boss == True:
            #make health bar bigger if the enemy is a boss
            w = self.image.get_width()
            h = self.image.get_height()
            self.image = pygame.transform.scale(self.image,(w*2, h))

        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.counter = 0
    
    def update(self, screen_scroll):
        #reposition the bar based on screen scroll
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]
        
        #kill the bar so that the new one can replace it
        self.counter += 1
        if (self.counter >= 2):
            self.kill()

#Class that keeps that tracks of damage dealt to an enemy
class DamageText(pygame.sprite.Sprite):
    def __init__(self, x, y, damage, color):
        pygame.sprite.Sprite.__init__(self)
        self.image = font.render(damage, True, color)
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.counter = 0

    def update(self, screen_scroll):
        #reposition the text based on screen scroll
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]

        #make the text float upwards
        self.rect.y -= 1
        
        #remove the text after a few instances of update
        self.counter += 1
        if (self.counter >35):
            self.kill()

#Create an empty world
world_data = []
for row in range(cons.ROWS):
    r = [-1]*cons.COLS
    world_data.append(r)
#load level file to create world
with open(find_relative_path(f"levels/level{level}_data.csv"), newline="") as csvfile:
    reader = csv.reader(csvfile, delimiter= ",")
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)

#Create the world
world = World() 
world.process_data(world_data, tile_list, mobs_animation_list, item_images)

#Player event variables
move_Left = False 
move_Right = False
move_Up = False
move_Down = False
interact_check = False 

#Extract player character
player = world.player
player.health = player_health
player.score = player_score
bow = Weapon(bow_image,arrow_image)

#Extract enemies from world data
enemy_list = world.character_list

#Create score coin for panel
score_coin = Item(cons.SCREEN_WIDTH - 115, 23 , 0 , coin_images, True)

#make sprite groups
arrow_group = pygame.sprite.Group()
health_text_group = pygame.sprite.Group()
damage_text_group = pygame.sprite.Group()
item_group = pygame.sprite.Group()
fireball_group = pygame.sprite.Group()

for item in world.item_list:
    item_group.add(item)

#make level starting fade
intro_fade = ScreenFade(1, cons.BLACK, 4)
death_fade = ScreenFade(2, cons.GameOver, 4)

#make button instances
#intro menu
start_button = Button(cons.SCREEN_WIDTH // 2 - 150, cons.SCREEN_HEIGHT // 2 - 130, start_button_img)
new_game_button = Button(cons.SCREEN_WIDTH // 2 - 150, cons.SCREEN_HEIGHT // 2, new_game_button_img)
exit_button = Button(cons.SCREEN_WIDTH // 2 - 150, cons.SCREEN_HEIGHT // 2 + 130, exit_button_img)
sound_button = Button(cons.SCREEN_WIDTH // 2 - 150, cons.SCREEN_HEIGHT // 2 + 260, sound_button_img)

#pause menu
resume_button = Button(cons.SCREEN_WIDTH // 2 - 450, cons.SCREEN_HEIGHT // 2 - 120, resume_button_img)
pause_restart_button = Button(cons.SCREEN_WIDTH // 2 - 50, cons.SCREEN_HEIGHT // 2 -120, restart_button_img)
back_button = Button(cons.SCREEN_WIDTH // 2 + 150, cons.SCREEN_HEIGHT // 2 -120, back_button_img)

#death screen
restart_button = Button(cons.SCREEN_WIDTH // 2 - 50, cons.SCREEN_HEIGHT // 2 - 50, restart_button_img)

# Function to limit sprite counts to prevent memory issues
def limit_sprite_group(group, max_count):
    """Ensure a sprite group doesn't grow beyond a maximum size"""
    if len(group) > max_count:
        # Remove oldest sprites (first in list)
        sprites = list(group)
        for sprite in sprites[:len(group) - max_count]:
            sprite.kill()

# Function to cleanup offscreen sprites
def cleanup_offscreen_sprites(group, margin=100):
    """Remove sprites that are far offscreen"""
    screen_rect = pygame.Rect(-margin, -margin, 
                             cons.SCREEN_WIDTH + 2*margin, 
                             cons.SCREEN_HEIGHT + 2*margin)
    for sprite in list(group):
        if hasattr(sprite, 'rect') and not screen_rect.colliderect(sprite.rect):
            sprite.kill()

#main game loop
running = True
while running:
    #FPS control
    CLOCK.tick(cons.FPS)
    
    start_time = time.time()
    
    # Take memory snapshot every few frames
    if TRACK_PERFORMANCE:
        frame_count += 1
        if frame_count % 60 == 0:  # Every ~1 second at 60fps
            take_memory_snapshot()
            # Force garbage collection occasionally to reduce memory pressure
            if frame_count % 300 == 0:  # Every ~5 seconds
                gc.collect()
    
    if start_game == False:
        # Menu screen logic
        start_section("menu_screen")
        frame_counter = 0
        screen.blit(menu_background_image, (0,0))
        pause_music()
        draw_text("INTO THE DEEP", font, cons.WHITE, cons.SCREEN_WIDTH // 2 - 348, 120, 3)
        
        # Draw sound status
        draw_sound_status()
        
        # Draw sound toggle button
        if sound_button.draw(screen):
            # Toggle sound on/off
            SOUND_MANAGER_ENABLED = not SOUND_MANAGER_ENABLED
            # Update the button with new text
            sound_button.image = create_sound_button()
            
            if SOUND_MANAGER_ENABLED:
                if sound_manager.enable():
                    # Restart music if enabling sound
                    play_music("assets/audio/music.wav", cons.MUSIC_VOLUME)
            else:
                sound_manager.disable()
        
        if start_button.draw(screen):
            start_game = True
            start_intro = True
            intro_fade.fade_counter = 0
        if new_game_button.draw(screen):
            start_game = True
            level = 1
            player_health = 100
            player_score = 0
            start_intro = True
            intro_fade.fade_counter = 0
            world, player, enemy_list, score_coin = load_level(level,player_health,player_score)
            arrow_group, health_text_group, damage_text_group, item_group, fireball_group = make_groups(world)
        if exit_button.draw(screen):
            running = False
        end_section()
    elif pause_game == True:
        # Pause screen logic
        start_section("pause_screen")
        frame_counter = 0
        screen.blit(pause_background_image, (0,0))
        pause_music()
        draw_text("PAUSED", font, cons.WHITE, cons.SCREEN_WIDTH // 2 - 166, 120, 3)
        if resume_button.draw(screen):
            unpause_music()
            pause_game = False
        if back_button.draw(screen):
            stop_music()
            if SOUND_MANAGER_ENABLED:
                play_music("assets/audio/music.wav", cons.MUSIC_VOLUME)
            pause_game = False
            start_game = False
        if pause_restart_button.draw(screen):
            stop_music()
            if SOUND_MANAGER_ENABLED:
                play_music("assets/audio/music.wav", cons.MUSIC_VOLUME)
            pause_game = False
            start_intro = True
            intro_fade.fade_counter = 0

            world, player, enemy_list, score_coin = load_level(level,player_health,player_score)
            arrow_group, health_text_group, damage_text_group, item_group, fireball_group = make_groups(world)
        #update and draw groups
        start_section("pause_update_sprites")
        arrow_group.update(screen_scroll, enemy_list, world.obstacle_tiles)
        item_group.update(screen_scroll, player)
        fireball_group.update(screen_scroll, player, world.obstacle_tiles)
        damage_text_group.update(screen_scroll)
        health_text_group.update(screen_scroll)
        end_section()
    else:
        # Main game logic
        start_section("game_background")
        screen.fill(cons.BackGround)
        unpause_music()
        if frame_counter <= 10:
            frame_counter += 1
        end_section()

        if player.alive:
            # Player movement
            start_section("player_movement")
            delta_x = 0
            delta_y = 0
            if move_Left:
                delta_x -= cons.player_speed
            if move_Right:
                delta_x += cons.player_speed
            if move_Up:
                delta_y -= cons.player_speed
            if move_Down:
                delta_y += cons.player_speed

            #move all objects
            screen_scroll, level_complete = player.move(delta_x, delta_y, world.obstacle_tiles, world.exit_tile, interact_check)
            end_section()

            #update all objects
            start_section("world_update")
            world.update(screen_scroll)
            player.update_sprite()
            end_section()
            
            # Update enemies
            start_section("enemy_update")
            # Create a copy of the list to avoid modification during iteration
            safe_enemy_list = enemy_list.copy()
            for enemy in safe_enemy_list:
                if enemy.alive:
                    fireball = enemy.ai(player, world.obstacle_tiles, screen_scroll, fireball_image)
                    if fireball:
                        fireball_group.add(fireball)
                    enemy.update_sprite()
                    # Create health text for alive enemies
                    health_level = calc_health(enemy)
                    health_text = HealthBar(enemy.rect.centerx, enemy.rect.bottom + 18, health_level, enemy)
                    health_text_group.add(health_text)
                else:
                    # Handle dead enemy
                    death_counter = enemy.death_flash()
                    if death_counter % 2 == 0:  #0: show bar 1: dont show bar
                        health_text = HealthBar(enemy.rect.centerx, enemy.rect.bottom + 18, 0, enemy)
                        health_text_group.add(health_text)
                    if death_counter >= 15:  # Remove enemy after death animation
                        if enemy in enemy_list:
                            enemy_list.remove(enemy)
            end_section()
            
            # Update weapon and projectiles
            start_section("weapon_update")
            arrow = bow.update_weapon(player)
            if arrow and frame_counter > 8:  # Changed from >= to > for consistency
                arrow_group.add(arrow)
                play_sound(arrow_shot_fx, 'arrow_shot')
            end_section()
                
            # Update arrows
            start_section("arrow_update")
            for arrow in list(arrow_group):  # Use a copy to safely iterate
                damage, damage_pos = arrow.update(screen_scroll, enemy_list, world.obstacle_tiles)
                if damage:
                    damage_text = DamageText(damage_pos.centerx, damage_pos.y, str(damage), cons.RED)
                    damage_text_group.add(damage_text)
                    play_sound(arrow_hit_fx, 'arrow_hit')
            end_section()
            
            # Update other objects
            start_section("other_updates")
            # Sound-aware item collection
            for item in list(item_group):
                before_update = item.rect.copy()
                item.update(screen_scroll, player)
                # Check if item disappeared (was collected)
                if not item.alive() and before_update.colliderect(player.rect):
                    if item.item_type == 0:  # Coin
                        play_sound(coin_collect_fx, 'coin')
                    elif item.item_type == 1:  # Potion
                        play_sound(heal_fx, 'heal')
            
            # Update fireballs properly
            for fireball in list(fireball_group):  # Use a copy to safely iterate
                fireball.update(screen_scroll, player, world.obstacle_tiles)
            
            # Update UI elements
            for health_text in list(health_text_group):  # Use a copy to safely iterate
                health_text.update(screen_scroll)
            for damage_text in list(damage_text_group):  # Use a copy to safely iterate
                damage_text.update(screen_scroll)
            
            # Update score coin separately - no collection sounds needed
            score_coin.update(screen_scroll, player)
            end_section()
        
        # Drawing
        start_section("drawing")
        world.draw(screen)
        player.draw(screen)
        for enemy in enemy_list:
            enemy.draw(screen)
        bow.draw(screen)
        for arrow in arrow_group:
            arrow.draw(screen)
        for fireball in fireball_group:
            fireball.draw(screen)
        item_group.draw(screen)
        health_text_group.draw(screen)
        damage_text_group.draw(screen)
        draw_info()
        score_coin.draw(screen)
        end_section()

        # Level completion
        start_section("level_logic")
        if level_complete == True:
            level += 1
            start_intro = True
            player_health = player.health
            player_score = player.score
            world, player, enemy_list, score_coin = load_level(level,player_health,player_score)
            arrow_group, health_text_group, damage_text_group, item_group, fireball_group = make_groups(world)

        #show level intro
        if start_intro == True:
            if intro_fade.fade() == True:
                start_intro = False
                intro_fade.fade_counter = 0

        #show death screen
        if player.alive == False:
            if death_fade.fade():
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    world, player, enemy_list, score_coin = load_level(level,player_health,player_score)
                    arrow_group, health_text_group, damage_text_group, item_group, fireball_group = make_groups(world)
                if exit_button.draw(screen):
                    running = False
        end_section()
        
    # Event handling
    start_section("event_handling")
    interact_check = False #get only 1 instance of button press
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        #check keyboard press
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                move_Left = True
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                move_Right = True
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                move_Up = True
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                move_Down = True
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                interact_check = True
            if event.key == pygame.K_ESCAPE and start_game == True:
                pause_game = True
            if event.key == pygame.K_f:
                fullscreen = not fullscreen
                if fullscreen == True:
                    screen = pygame.display.set_mode((cons.SCREEN_WIDTH,cons.SCREEN_HEIGHT), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((cons.SCREEN_WIDTH,cons.SCREEN_HEIGHT))
            # Sound control shortcuts
            if event.key == pygame.K_m:
                # Toggle master sound
                SOUND_MANAGER_ENABLED = not SOUND_MANAGER_ENABLED
                sound_button.image = create_sound_button()
                if SOUND_MANAGER_ENABLED:
                    if sound_manager.enable():
                        # Restart music if enabling sound
                        play_music("assets/audio/music.wav", cons.MUSIC_VOLUME)
                else:
                    sound_manager.disable()
                    
            # Toggle individual sound types    
            if event.key == pygame.K_1:
                # Toggle music
                MUSIC_ENABLED = not MUSIC_ENABLED
                print(f"Music sounds: {'ON' if MUSIC_ENABLED else 'OFF'}")
                if MUSIC_ENABLED:
                    play_music("assets/audio/music.wav", cons.MUSIC_VOLUME)
                else:
                    stop_music()
                # Update sound button if we're in the menu
                if not start_game:
                    sound_button.image = create_sound_button()
            
            if event.key == pygame.K_2:
                # Toggle arrow shot sounds
                ARROW_SHOT_SOUND_ENABLED = not ARROW_SHOT_SOUND_ENABLED
                print(f"Arrow shot sounds: {'ON' if ARROW_SHOT_SOUND_ENABLED else 'OFF'}")
                # Update sound button if we're in the menu
                if not start_game:
                    sound_button.image = create_sound_button()
            
            if event.key == pygame.K_3:
                # Toggle arrow hit sounds
                ARROW_HIT_SOUND_ENABLED = not ARROW_HIT_SOUND_ENABLED
                print(f"Arrow hit sounds: {'ON' if ARROW_HIT_SOUND_ENABLED else 'OFF'}")
                # Update sound button if we're in the menu
                if not start_game:
                    sound_button.image = create_sound_button()
            
            if event.key == pygame.K_4:
                # Toggle coin sounds
                COIN_SOUND_ENABLED = not COIN_SOUND_ENABLED
                print(f"Coin sounds: {'ON' if COIN_SOUND_ENABLED else 'OFF'}")
                # Update sound button if we're in the menu
                if not start_game:
                    sound_button.image = create_sound_button()
            
            if event.key == pygame.K_5:
                # Toggle heal sounds
                HEAL_SOUND_ENABLED = not HEAL_SOUND_ENABLED
                print(f"Heal sounds: {'ON' if HEAL_SOUND_ENABLED else 'OFF'}")
                # Update sound button if we're in the menu
                if not start_game:
                    sound_button.image = create_sound_button()

        #check keyboard press release
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                move_Left = False
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                move_Right = False
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                move_Up = False
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                move_Down= False
    end_section()
    
    # Screen update
    start_section("screen_update")
    pygame.display.update()
    end_section()
    
    # Calculate frame time
    if TRACK_PERFORMANCE:
        frame_time = time.time() - start_time
        frame_times.append(frame_time)
        # Keep only last 100 frames
        if len(frame_times) > 100:
            frame_times.pop(0)
        # Print warning for slow frames
        if frame_time > 0.1:  # 100ms = 10fps
            print(f"WARNING: Slow frame: {frame_time*1000:.1f}ms")

    # Limit sprite counts to prevent memory issues
    start_section("sprite_management")
    # Limit each sprite group to reasonable numbers
    limit_sprite_group(arrow_group, 30)  # Maximum 30 arrows at once
    limit_sprite_group(fireball_group, 20)  # Maximum 20 fireballs at once 
    limit_sprite_group(health_text_group, 50)  # Maximum 50 health texts
    limit_sprite_group(damage_text_group, 30)  # Maximum 30 damage texts
    
    # Clean up offscreen sprites
    cleanup_offscreen_sprites(arrow_group)
    cleanup_offscreen_sprites(fireball_group)
    end_section()

# End of the game - cleanup
with open ("saves/into_the_deep_save_data.json","w") as save_file:
    save_data = {
        "level":level,
        "health":player_health,
        "score":player_score,
    }
    json.dump(save_data,save_file)  

# Clean up sound manager
if SOUND_MANAGER_ENABLED:
    sound_manager.shutdown()
  
pygame.quit()