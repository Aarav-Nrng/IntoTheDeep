import pygame

class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, item_type, animation_list, dummy_coin=False):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type  # 0:coin 1:potion
        self.animation_list = animation_list
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = animation_list[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.dummy_coin = dummy_coin

    def update(self, screen_scroll, player):
        #reposition the item based on screen scroll
        if not self.dummy_coin:
            self.rect.x += screen_scroll[0]
            self.rect.y += screen_scroll[1]

        #check if the item has been collected by the player
        if self.rect.colliderect(player.rect) and not(self.dummy_coin):
            #what item has been collected

            #a coin has been collected
            if self.item_type == 0:
                player.score += 1
            #a potion has been collected
            elif self.item_type == 1:
                player.health += 25
                if player.health > 100:
                    player.health = 100
            #score coin cannot be collected even if collided with

            #remove the item from the group
            self.kill()
            
        #handle item animation
        update_cooldown = 150
        #update image
        self.image = self.animation_list[self.frame_index]
        #check if enough time has passed since last animation
        if pygame.time.get_ticks() - self.update_time > update_cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            #Restart animation if animation is complete
            if self.frame_index >= len(self.animation_list):
                self.frame_index = 0
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)