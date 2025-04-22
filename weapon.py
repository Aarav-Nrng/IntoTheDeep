import pygame
import math
import random
import constants as cons
import logging

logger = logging.getLogger(__name__)

class Weapon():
    def __init__(self, image, arrow_image):
        self.orignal_image = image
        self.angle = 0
        self.image = pygame.transform.rotate(self.orignal_image,self.angle)
        self.rect = self.image.get_rect()
        self.arrow_image = arrow_image
        self.fired = False      #Mouse Trigger for arrow(One per click)
        self.last_shot = pygame.time.get_ticks()

    def update_weapon(self,player):
        arrow = None
        self.rect.center = player.rect.center
        shot_cooldown = 450

        #get mouse position
        mouse_pos = pygame.mouse.get_pos()
        x_dist = (mouse_pos[0] - self.rect.centerx)
        y_dist = (mouse_pos[1] - self.rect.centery)*-1 #Change the sign as y co-ord increases when going down the screen
        self.angle = math.degrees(math.atan2(y_dist,x_dist))

        #get mouse_click
        if pygame.mouse.get_pressed()[0] and self.fired == False and (pygame.time.get_ticks() - self.last_shot) > shot_cooldown:
            arrow = Arrow(self.arrow_image,self.rect.centerx,self.rect.centery,self.angle)
            self.fired = True
            self.last_shot = pygame.time.get_ticks()
        #get mouse_release
        if pygame.mouse.get_pressed()[0] == False:
            self.fired = False
        
        return arrow

    def draw(self,surface):
        self.image = pygame.transform.rotate(self.orignal_image,self.angle)
        surface.blit(self.image, ((self.rect.centerx - int(self.image.get_width()/2),(self.rect.centery - int(self.image.get_height()/2)))))


class Arrow(pygame.sprite.Sprite):
    def __init__(self, image, x, y, angle):
        pygame.sprite.Sprite.__init__(self)
        self.orignal_image = image
        self.angle = angle
        self.image = pygame.transform.rotate(self.orignal_image,self.angle - 90)
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        #Calculation of the speed of arrow depending on the angle
        self.dx = math.cos(math.radians(self.angle)) * cons.arrow_speed
        self.dy = -(math.sin(math.radians(self.angle)) * cons.arrow_speed)
        self.collideWall = False
        self.collisionCounter = 0

    def update(self, screen_scroll, enemy_list, obstacle_tiles):
        #default variables
        damage = 0
        damage_pos = None
        
        # Check if arrow has been colliding too long
        if(self.collisionCounter >= 120):
            self.kill()
            return damage, damage_pos
            
        # Update position based on screen scroll
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]
        
        # If already collided with wall, just count and return
        if self.collideWall:
            self.collisionCounter += 1
            return damage, damage_pos
        
        # Move the arrow based on its velocity
        self.rect.x += self.dx
        self.rect.y += self.dy
        
        # Check if arrow is off screen
        if (self.rect.right < 0 or self.rect.left > cons.SCREEN_WIDTH or 
            self.rect.bottom < 0 or self.rect.top > cons.SCREEN_HEIGHT):
            self.kill()
            return damage, damage_pos
        
        # Check for collision with obstacles
        for obstacle in obstacle_tiles:
            if obstacle[1].colliderect(self.rect):
                self.collideWall = True
                return damage, damage_pos

        # Check for collision with enemies - only check alive enemies
        for enemy in enemy_list:
            if enemy.alive and enemy.rect.colliderect(self.rect):
                enemy.hit = True
                damage = 15 + random.randint(-2, 2)
                damage_pos = enemy.rect
                enemy.health -= damage
                self.kill()
                break
                
        return damage, damage_pos

    def draw(self,surface):
        arrow_x = self.rect.centerx - int(self.image.get_width()/2)
        arrow_y = self.rect.centery - int(self.image.get_height()/2)
        surface.blit(self.image, (arrow_x,arrow_y)) 

class Fireball(pygame.sprite.Sprite):
    def __init__(self, image, x, y, target):
        pygame.sprite.Sprite.__init__(self)
        self.orignal_image = image
        x_dist = (target.rect.centerx - x)
        y_dist = (target.rect.centery - y) * -1
        self.angle = math.degrees(math.atan2(y_dist,x_dist))
        self.image = pygame.transform.rotate(self.orignal_image,self.angle - 90)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        #Calculation of the speed of arrow depending on the angle
        self.dx = (math.cos(math.radians(self.angle)) * cons.fireball_speed)
        self.dy = (math.sin(math.radians(self.angle)) * cons.fireball_speed) * -1 #-ve because y co-ords are reversed
        self.collideWall = False
        self.collisionCounter = 0

    def update(self, screen_scroll, player, obstacle_tiles):
        # Update position based on screen scroll
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]
        
        # Check if fireball has been active too long
        if(self.collisionCounter >= 500):
            self.kill()
            return
        
        # Check for collision with player
        if player.rect.colliderect(self.rect) and player.hit == False:
            player.hit = True
            player.last_hit = True
            player.health -= 5
            self.kill()
            return

        # If already collided with wall, just count and return
        if self.collideWall:
            self.collisionCounter += 1
            return

        # Move the fireball based on its velocity
        self.rect.x += self.dx
        self.rect.y += self.dy
        
        # Check for collision with obstacles
        for obstacle in obstacle_tiles:
            if obstacle[1].colliderect(self.rect):
                self.collideWall = True
                return

        # Check if fireball is off screen
        if (self.rect.right < 0 or self.rect.left > cons.SCREEN_WIDTH or 
            self.rect.bottom < 0 or self.rect.top > cons.SCREEN_HEIGHT):
            self.kill()

    def draw(self,surface):
        arrow_x = self.rect.centerx - int(self.image.get_width()/2)
        arrow_y = self.rect.centery - int(self.image.get_height()/2)
        surface.blit(self.image, (arrow_x,arrow_y))    