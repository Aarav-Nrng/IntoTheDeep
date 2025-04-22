import pygame
import constants as cons
import weapon
import math
import random
import logging

logger = logging.getLogger(__name__)

class Character():
    def __init__(self, x, y, health, mob_animations, char_type, boss, size):
        self.char_type = char_type
        self.score = 0      #Player Score variable
        self.health = health
        self.alive = True
        self.boss = boss
        self.size = size
        logger.debug(f"Created {'boss' if boss else 'enemy'} character at ({x}, {y}) with health {health}")
        
        self.hit = False
        self.last_hit = pygame.time.get_ticks()
        self.attack_damage = cons.enemy_damage[char_type - 1]
        self.attack_cooldown = cons.enemy_attack_cooldown[char_type - 1]
        self.attacked = False
        self.last_attack = pygame.time.get_ticks()
        self.stunned = False
        self.last_pos = (x, y)  # Store last position
        self.stuck_counter = 0   # Counter for when enemy might be stuck

        self.death_counter = 0
        self.death_update_time = pygame.time.get_ticks()

        self.animationList = mob_animations[self.char_type]
        self.flipper = False
        self.frame_index = 0
        self.action_type = 0    # 0:Idle , 1:Run 
        self.update_time = pygame.time.get_ticks()
        self.isRunning = False
        
        self.image = self.animationList[self.action_type][self.frame_index]
        self.rect = pygame.rect.Rect(0, 0, cons.TILE_SIZE * size - 4, cons.TILE_SIZE * size - 4) 
        self.rect.center = (x,y)
        
    def move(self, dx, dy, obstacles_tiles, exit_tile = None, interact_check = None):
        screen_scroll = [0, 0]
        level_complete = False

        #Check to see if moving left or right
        if dx < 0:
            self.flipper = True
        if dx > 0:
            self.flipper = False

        #Check for Movement
        if dx == 0 and dy == 0:
            #No Movement     
            self.isRunning = False
        else:
            self.isRunning = True
        
        #Diagonal Movement(Pythogoras Theorem)
        if dx != 0 and dy != 0:
            dx = dx * (math.sqrt(2)/2)
            dy = dy * (math.sqrt(2)/2)
        
        self.rect.x += dx
        for obstacle in obstacles_tiles:
            #check for collisions on the x axis
            if obstacle[1].colliderect(self.rect):
                #check for direction
                if dx > 0:  #collision when moving right
                    self.rect.right = obstacle[1].left
                if dx < 0:  #collision when moving left
                    self.rect.left = obstacle[1].right
        
        self.rect.y += dy
        for obstacle in obstacles_tiles:
            #check for collisions on the y axis
            if obstacle[1].colliderect(self.rect):
                #check for direction
                if dy > 0:  #collision when moving down
                    self.rect.bottom = obstacle[1].top
                if dy < 0:  #collision when moving up
                    self.rect.top = obstacle[1].bottom

        #(Logic only applicable to player character)
        if self.char_type == 0:
            #check collision with exit tile
            if self.rect.collidepoint(exit_tile[1].centerx,exit_tile[1].centery) and interact_check == True:
                level_complete = True

            #SCROLL CAMERA
            #move camera left or right based on player position
            if self.rect.right > (cons.SCREEN_WIDTH - cons.SCREEN_THRESHOLD):
                #move camera right
                screen_scroll[0] =  (cons.SCREEN_WIDTH - cons.SCREEN_THRESHOLD) - self.rect.right
                self.rect.right = (cons.SCREEN_WIDTH - cons.SCREEN_THRESHOLD)
            if self.rect.left < (cons.SCREEN_THRESHOLD):
                #move camera left
                screen_scroll[0] = (cons.SCREEN_THRESHOLD) - self.rect.left
                self.rect.left = (cons.SCREEN_THRESHOLD)

            #move the camera up or down based on player position
            if self.rect.bottom > (cons.SCREEN_HEIGHT - cons.SCREEN_THRESHOLD):
                #move camera down
                screen_scroll[1] = (cons.SCREEN_HEIGHT - cons.SCREEN_THRESHOLD) - self.rect.bottom
                self.rect.bottom = (cons.SCREEN_HEIGHT - cons.SCREEN_THRESHOLD)
            if self.rect.top < (cons.SCREEN_THRESHOLD):
                #move camera up
                screen_scroll[1] = (cons.SCREEN_THRESHOLD) - self.rect.top
                self.rect.top = cons.SCREEN_THRESHOLD


        return screen_scroll, level_complete

    def ai(self, player, obstacle_tiles, screen_scroll, fireball_image):
        if not self.alive:
            return None

        ai_dx = 0
        ai_dy = 0
        fireball = None
        stun_cooldown = 70

        #reposition based on screen scroll
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]

        #create line of sight
        line_of_sight = ((self.rect.centerx, self.rect.centery), (player.rect.centerx, player.rect.centery))
        
        #check for walls blocking sight
        wall_in_sight = False
        for obstacle in obstacle_tiles:
            if obstacle[1].clipline(line_of_sight):
                wall_in_sight = True
                break

        #check distance to player
        dist = math.sqrt(((self.rect.centerx - player.rect.centerx) ** 2) + ((self.rect.centery - player.rect.centery) ** 2))
        
        if not self.stunned and dist > cons.RANGE and not wall_in_sight:
            # Calculate direction to player
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist > 0:
                dx = dx / dist
                dy = dy / dist
                ai_dx = dx * cons.enemy_speed
                ai_dy = dy * cons.enemy_speed

            # Check if enemy is stuck
            new_pos = (self.rect.centerx, self.rect.centery)
            if (abs(new_pos[0] - self.last_pos[0]) < 1 and 
                abs(new_pos[1] - self.last_pos[1]) < 1):
                self.stuck_counter += 1
                if self.stuck_counter > 60:  # If stuck for 1 second
                    logger.debug(f"Enemy stuck at {self.rect.center}, attempting unstuck")
                    ai_dx = random.choice([-1, 1]) * cons.enemy_speed
                    ai_dy = random.choice([-1, 1]) * cons.enemy_speed
                    self.stuck_counter = 0
            else:
                self.stuck_counter = 0
            self.last_pos = new_pos

            #move towards player
            self.move(ai_dx, ai_dy, obstacle_tiles)
            
            #attack player
            if dist < cons.ATTACK_RANGE and not self.attacked and not player.hit and not wall_in_sight:
                player.health -= self.attack_damage + random.randint(-1,1)
                player.hit = True
                player.last_hit = pygame.time.get_ticks()
                self.attacked = True
                self.last_attack = pygame.time.get_ticks()
            
            #boss enemy fireball
            if self.boss:
                fireball_cooldown = 1000
                if (dist < 400 and dist > 50 and 
                    (pygame.time.get_ticks() - self.last_attack > fireball_cooldown) and 
                    not wall_in_sight and not self.attacked):
                    fireball = weapon.Fireball(fireball_image, self.rect.centerx, self.rect.centery, player)
                    self.last_attack = pygame.time.get_ticks()
        
        #handle stun
        if self.hit and not self.boss:
            self.hit = False
            self.last_hit = pygame.time.get_ticks()
            self.stunned = True
            self.isRunning = False
            self.update_action(0)
        
        if (pygame.time.get_ticks() - self.last_hit > stun_cooldown):
            self.stunned = False

        if self.attacked and (pygame.time.get_ticks() - self.last_attack) > self.attack_cooldown:
            self.attacked = False

        return fireball

    def death_flash(self):
        update_cooldown = 60
        #no bar if died a long time ago
        if self.death_counter >= 15:
            return 15  # Return max value to ensure cleanup
        #check if enough time has passed since last update
        if pygame.time.get_ticks() - self.death_update_time > update_cooldown:
            self.death_counter += 1
            self.death_update_time = pygame.time.get_ticks()
        return self.death_counter

    def update_sprite(self):
        #check if the character has died
        if self.health <= 0:
            self.health = 0  # Ensure health doesn't go negative
            if self.alive:  # Only log once when character dies
                logger.debug(f"Character died at {self.rect.center}")
                self.alive = False
            self.update_action(0) #idle
            self.image = self.animationList[self.action_type][self.frame_index]
            if self.flipper:
                self.image = pygame.transform.flip(self.image, True, False)
            return False

        #update animation
        update_cooldown = 100
        self.image = self.animationList[self.action_type][self.frame_index]
        
        if pygame.time.get_ticks() - self.update_time > update_cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            if self.frame_index >= len(self.animationList[self.action_type]):
                self.frame_index = 0

        if self.flipper:
            self.image = pygame.transform.flip(self.image, True, False)
        return True

    def update_action(self,new_action):
        #Check if action has changed from the previous one
        if new_action != self.action_type:
            self.action_type = new_action
            #Restart animations
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self,surface):
        flipped_image = pygame.transform.flip(self.image, self.flipper, False)
        if self.char_type == 0:
            surface.blit(flipped_image, (self.rect.x,self.rect.y - cons.global_scale * cons.OFFSET))
        else:
            surface.blit(flipped_image, self.rect) 