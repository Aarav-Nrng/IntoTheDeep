import pygame
import constants as cons
import weapon
import math
import random

class Character():
    def __init__(self, x, y, health, mob_animations, char_type, boss, size):
        self.char_type = char_type
        self.score = 0      #Player Score variable
        self.health = health
        self.alive = True
        self.boss = boss
        self.size = size
        
        self.hit = False
        self.last_hit = pygame.time.get_ticks() # This functions is used to get the no. of ticks that have passed since last update
        self.attack_damage = cons.enemy_damage[char_type - 1]
        self.attack_cooldown = cons.enemy_attack_cooldown[char_type - 1]
        self.attacked = False
        self.last_attack = pygame.time.get_ticks() # This functions is used to get the no. of ticks that have passed since last update
        self.stunned = False

        self.death_counter = 0
        self.death_update_time = pygame.time.get_ticks() # This functions is used to get the no. of ticks that have passed since last update

        self.animationList = mob_animations[self.char_type]
        self.flipper = False
        self.frame_index = 0
        self.action_type = 0    # 0:Idle , 1:Run 
        self.update_time = pygame.time.get_ticks()  # This functions is used to get the no. of ticks that have passed since last update
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
        ai_dx = 0
        ai_dy = 0
        clipped_line = ()
        stun_cooldown = 70
        fireball = None

        #reposition the enemy based on screen scroll
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]

        #check if the enemy is alive
        if self.alive == False:
            return 

        #create a line of sight from enemy to player
        line_of_sight = ((self.rect.centerx, self.rect.centery), (player.rect.centerx, player.rect.centery))

        #check if there is a wall between the enemy and the player (Can the enemy see the player)
        for obstacle in obstacle_tiles:
            if obstacle[1].clipline(line_of_sight):
                clipped_line = obstacle[1].clipline(line_of_sight)

        #check distance to player
        dist = math.sqrt(((self.rect.centerx - player.rect.centerx) ** 2) + ((self.rect.centery - player.rect.centery) ** 2))
        #change dy and dx depending on player position
        if dist > cons.RANGE and not clipped_line:
            if player.rect.centerx > self.rect.centerx:
                ai_dx = cons.enemy_speed
            if player.rect.centerx < self.rect.centerx:
                ai_dx = cons.enemy_speed * -1
            if player.rect.centery > self.rect.centery:
                ai_dy = cons.enemy_speed
            if player.rect.centery < self.rect.centery:
                ai_dy = cons.enemy_speed * -1

        if not self.stunned:
            #move towards player
            self.move(ai_dx,ai_dy, obstacle_tiles)
            #attack the player if (in range, not behind a wall, attack_cooldown, and player hit cooldown)
            if dist < cons.ATTACK_RANGE and self.attacked == False and player.hit == False and not clipped_line:
                player.health -= self.attack_damage + random.randint(-1,1)
                player.hit = True
                player.last_hit = pygame.time.get_ticks()
                self.attacked = True
                self.last_attack = pygame.time.get_ticks()
            #make boss enemy shoot fireballs
            fireball_cooldown = 1250
            if self.boss:
                if dist < 500 and dist > 50 and (pygame.time.get_ticks() - self.last_attack > fireball_cooldown) and not clipped_line: 
                    fireball = weapon.Fireball(fireball_image, self.rect.centerx, self.rect.centery, player)
                    self.last_attack = pygame.time.get_ticks()

        
        #check if the enemy should be stunned
        if self.hit == True and not self.boss:
            self.hit = False
            self.last_hit = pygame.time.get_ticks()
            self.stunned = True
            self.isRunning = False
            self.update_action(0)
        
        #check if stun-timer is complete
        if (pygame.time.get_ticks() - self.last_hit > stun_cooldown):
            self.stunned = False

        #check for enemy attack cooldown
        if self.attacked == True and (pygame.time.get_ticks() - self.last_attack) > self.attack_cooldown:
            self.attacked = False

        return fireball

    def death_flash(self):
        update_cooldown = 60
        #no bar if died a long time ago
        if self.death_counter >= 15:
            return 1
        #check if enough time has passed since last update
        if pygame.time.get_ticks() - self.death_update_time > update_cooldown:
            self.death_counter += 1
            self.death_update_time = pygame.time.get_ticks()
        return self.death_counter

    def update_sprite(self):
        #check if the character has died
        if self.health <= 0 or self.alive == False: #pause animation if dead
            self.health = 0
            self.alive = False
            return
        
        #check to see if enough time has passed since last hit
        hit_cooldown = 400
        if self.char_type == 0:
            if self.hit == True and (pygame.time.get_ticks() - self.last_hit) > hit_cooldown:
                self.hit = False
        
        #check for movement
        if self.isRunning:
            self.update_action(1)
            #run
        else:
            self.update_action(0)
            #idle

        update_cooldown = 80
        self.image = self.animationList[self.action_type][self.frame_index]

        #check if enough time has passed since last update
        if pygame.time.get_ticks() - self.update_time > update_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
            #Restart animation if animation is complete
            if self.frame_index >= len(self.animationList[self.action_type]):
                self.frame_index = 0

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