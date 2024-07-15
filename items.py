import pygame

from config import window_size, window_width, window_height, FPS, tile_size, level_width, level_height, GAME_OVER_EVENT, LEVEL_FINISHED, PARTICLE_EVENT

class ItemBar():
    def __init__(self):
        self.max_item_index = 8
        self.items = [None for _ in range(self.max_item_index)]
        self.selected_index = 0 
        self.something_selected = False

    def add_item(self, itemToAdd):
        add = True
        for i in range(len(self.items)):
            if self.items[i] != None:    
                if self.items[i].image_path == itemToAdd.image_path:
                    self.items[i].ammount += 1
                    add = False
                    break
        if add:
            freeSpace = None
            for i in range(len(self.items)):
                if self.items[i] == None: 
                    freeSpace = i
                    break
            if freeSpace != None:
                self.items[freeSpace] = itemToAdd

    def draw(self, window):
        font = pygame.font.SysFont("Paradox King Script", 15)
        
        x = 220
        y = window.get_height() - 40
        for i in range(self.max_item_index):
            pygame.draw.rect(window, (100,100,100,200), ((x,y), (25, 25)))
            if self.items[i] != None:
                window.blit(self.items[i].item_image, (x+2, y+5))
                text = font.render(f'{self.items[i].ammount}', True, (50, 0, 0))
                text_rect = text.get_rect(bottomright=(x + 25, y + 27))
                window.blit(text, text_rect)
            x += 28
        
        x = 220 + 28 * self.selected_index -1
        pygame.draw.rect(window, (50,0, 0,200), ((x,y - 1), (27, 27)), 2)

        if self.items[self.selected_index] != None:
            self.something_selected = True
        else: self.something_selected = False


class HealthBar():
    def __init__(self, player):
        self.max_health = player.max_health // 2
        self.heart_full_image = pygame.transform.rotate(pygame.transform.scale(pygame.image.load ("assets/heart_full.png"), (10, 10)), 0)
        self.heart_half_image = pygame.transform.rotate(pygame.transform.scale(pygame.image.load ("assets/heart_half.png"), (10, 10)), 0)
        self.heart_empty_image = pygame.transform.rotate(pygame.transform.scale(pygame.image.load ("assets/heart_empty.png"), (10, 10)), 0)
        self.heart_width = 10

    def draw(self, player, window):
        current_health = player.current_health
        x = 5
        y = 5

        # Draw full hearts
        for i in range(current_health // 2):
            window.blit(self.heart_full_image, (x, y))
            x += self.heart_width + 2

        # Draw half-hearts if needed
        if current_health % 2 == 1: window.blit(self.heart_half_image, (x, y))
        elif current_health != self.max_health * 2: window.blit(self.heart_empty_image, (x, y))

        # Draw empty hearts for remaining health
        for i in range(self.max_health - current_health // 2 - 1):
            x += self.heart_width + 2
            window.blit(self.heart_empty_image, (x, y))

class ItemForBarDisplay(pygame.sprite.Sprite):
    def __init__(self, image):
        self.image_path = image
        self.ammount = 1
        self.item_image = pygame.transform.scale(pygame.image.load(self.image_path), (15, 15))


class Item(pygame.sprite.Sprite):
    def __init__(self, image, coordinates, effects): 
        super().__init__()
        self.image = pygame.image.load (image)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(bottomleft = coordinates)
        self.effects = effects

class WoodenCrate(Item):
    def __init__(self, image, coordinates, effects):
        super().__init__(image, coordinates, effects)
        self.image = pygame.image.load (image)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(bottomleft = coordinates)
        self.effects = effects

    def update(self, bullet_list):
        for bullet in bullet_list:
            if pygame.sprite.collide_rect(self, bullet):
                bullet.kill()          
                self.kill()