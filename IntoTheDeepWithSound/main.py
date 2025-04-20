import pygame
from pygame import mixer
import csv
import json
from pathlib import Path

import constants as cons
from world import World
from character import Character
from weapon import Weapon
from items import Item
from button import Button

pygame.init()

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

#Function to help find and get paths to load assets
def find_relative_path(file_name) -> Path | None:
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
#Function to help load in sounds

def load_sound(sound,volume):
    sound_fx = mixer.Sound(find_relative_path(sound))
    sound_fx.set_volume(volume)
    return sound_fx

#load game music and sounds
#music
mixer.music.load(find_relative_path("assets/audio/music.wav"))
mixer.music.set_volume(cons.MUSIC_VOLUME)
mixer.music.play(-1, 0.0, 4000)
#sound effects
arrow_shot_fx = load_sound("assets/audio/arrow_shot.mp3",cons.SOUND_EFFECT_VOLUME)
arrow_hit_fx = load_sound("assets/audio/arrow_hit.wav",cons.SOUND_EFFECT_VOLUME)
coin_collect_fx = load_sound("assets/audio/coin.wav",cons.SOUND_EFFECT_VOLUME)
heal_fx = load_sound("assets/audio/heal.wav",cons.SOUND_EFFECT_VOLUME)

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

#Function to reset level data
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

#Class that handles screen fades
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

#create an empty world
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

#pause menu
resume_button = Button(cons.SCREEN_WIDTH // 2 - 450, cons.SCREEN_HEIGHT // 2 - 120, resume_button_img)
pause_restart_button = Button(cons.SCREEN_WIDTH // 2 - 50, cons.SCREEN_HEIGHT // 2 -120 , restart_button_img)
back_button = Button(cons.SCREEN_WIDTH // 2 + 150, cons.SCREEN_HEIGHT // 2 -120 , back_button_img)

#death screen
restart_button = Button(cons.SCREEN_WIDTH // 2 - 50, cons.SCREEN_HEIGHT // 2 - 50, restart_button_img)

#main game loop
running = True
while running:
    #FPS control
    CLOCK.tick(cons.FPS)

    if start_game == False:
        frame_counter = 0
        screen.blit(menu_background_image, (0,0))
        mixer.music.pause()
        draw_text("INTO THE DEEP", font, cons.WHITE, cons.SCREEN_WIDTH // 2 - 348, 120, 3)
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
            arrow_group,health_text_group,damage_text_group,item_group,fireball_group = make_groups(world)
        if exit_button.draw(screen):
            running = False
    elif pause_game == True:
        frame_counter = 0
        screen.blit(pause_background_image, (0,0))
        mixer.music.pause()
        draw_text("PAUSED", font, cons.WHITE, cons.SCREEN_WIDTH // 2 - 166, 120, 3)
        if resume_button.draw(screen):
            mixer.music.unpause()
            pause_game = False
        if back_button.draw(screen):
            mixer.music.rewind()
            pause_game = False
            start_game = False
        if pause_restart_button.draw(screen):
            mixer.music.rewind()
            mixer.music.unpause()
            pause_game = False
            start_intro = True
            intro_fade.fade_counter = 0

            world, player, enemy_list, score_coin = load_level(level,player_health,player_score)
            arrow_group,health_text_group,damage_text_group,item_group,fireball_group = make_groups(world)
    else:
        screen.fill(cons.BackGround)
        mixer.music.unpause()
        if frame_counter <= 10:
            frame_counter += 1

        if player.alive:
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

            #update all objects
            world.update(screen_scroll)
            player.update_sprite()
            for enemy in enemy_list:
                fireball = enemy.ai(player, world.obstacle_tiles, screen_scroll, fireball_image)
                if fireball:
                    fireball_group.add(fireball)
                enemy.update_sprite()
                if enemy.alive == True:
                    health_level = calc_health(enemy)
                    enemy_health = HealthBar(enemy.rect.centerx , enemy.rect.bottom + 18 , health_level, enemy)
                    health_text_group.add(enemy_health)
                if enemy.alive == False:
                    death_counter = enemy.death_flash()
                    if death_counter % 2 == 0:  #0: show bar 1: dont show bar
                        enemy_health = HealthBar(enemy.rect.centerx , enemy.rect.bottom + 18 , 0, enemy)
                        health_text_group.add(enemy_health)
            arrow = bow.update_weapon(player)
            if arrow != None and frame_counter >= 8:
                arrow_group.add(arrow)
                arrow_shot_fx.play() #play sound
            for arrow in arrow_group:
                damage, damage_pos = arrow.update(screen_scroll, enemy_list, world.obstacle_tiles)
                if damage != 0:
                    damage_text = DamageText(damage_pos.centerx , damage_pos.y, str(damage), cons.RED)
                    damage_text_group.add(damage_text)
                    arrow_hit_fx.play() #play sound
            for fireball in fireball_group:
                fireball.update(screen_scroll, player, world.obstacle_tiles)
            item_group.update(screen_scroll, player, coin_collect_fx, heal_fx)
            health_text_group.update(screen_scroll)
            damage_text_group.update(screen_scroll)
            score_coin.update(screen_scroll,player, coin_collect_fx, heal_fx)
        
        #Draw all objects
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
        
    interact_check = False #get only 1 instance of button press
    #event handler
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
    
    pygame.display.update()

with open ("saves/into_the_deep_save_data.json","w") as save_file:
    save_data = {
        "level":level,
        "health":player_health,
        "score":player_score,
    }
    json.dump(save_data,save_file)  
  
pygame.quit()