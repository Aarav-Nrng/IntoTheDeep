import constants as cons
from character import Character
from items import Item

class World():
   def __init__(self):
      self.map_tiles = []
      self.obstacle_tiles = []
      self.exit_tile = None
      self.item_list = []
      self.player = None
      self.character_list = []

   def process_data(self, data, tile_list, mob_animations, item_images):
      #iterate through each value of data file
      for y , row in enumerate(data):
         for x , tile in enumerate(row):
            image = tile_list[tile]        #get the tile from set which corresponds to given data
            image_rect = image.get_rect()
            image_x = x * cons.TILE_SIZE
            image_y = y * cons.TILE_SIZE
            image_rect.center = (image_x,image_y)
            tile_data = [image, image_rect, image_x, image_y]

            #perform actions based on the tile
            if tile == 7:
               #wall tile
               self.obstacle_tiles.append(tile_data)
            elif tile == 8:
               #ladder tile
               self.exit_tile = tile_data
            elif tile == 9 or tile == 10:
               #coin or potion
               item = Item(image_x, image_y, (tile-9), item_images[tile-9])
               self.item_list.append(item)
               tile_data[0] = tile_list[0]
            elif tile == 11:
               #player character
               player = Character(image_x, image_y, 100, mob_animations, 0, False, 1)
               self.player = player
               tile_data[0] = tile_list[0]
            elif tile >= 12 and tile<=16:
               #basic enemies
               enemy_health = [100,50,125,175,75]
               enemy = Character(image_x, image_y, enemy_health[tile-12], mob_animations, tile - 11, False, 1)
               self.character_list.append(enemy)
               tile_data[0] = tile_list[0]
            elif tile == 17:
               #boss enemy
               boss_enemy = Character(image_x, image_y, 400, mob_animations, 6, True, 2)
               self.character_list.append(boss_enemy)
               tile_data[0] = tile_list[0]
               
            #add image data to main tile list
            if tile >= 0:
               self.map_tiles.append(tile_data)

   def update(self,screen_scroll):
      for tile in self.map_tiles:
         tile[2] += screen_scroll[0]   #x_co-ordinate
         tile[3] += screen_scroll[1]   #y_co-ordinate
         tile[1].center = (tile[2],tile[3])

   def draw(self, surface):
      for tile in self.map_tiles:
         tile_image = tile[0]
         tile_rect = tile[1]
         surface.blit(tile_image, tile_rect) #tile 0 = image , tile 1 = image rect(position)