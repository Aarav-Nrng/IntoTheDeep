import pygame

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self, surface):
        do_action = False

        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos) and pygame.mouse.get_pressed()[0]: #Hovering over the button and clicked
            do_action = True
        
        surface.blit(self.image, self.rect)

        return do_action