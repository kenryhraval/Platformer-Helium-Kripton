import pygame

from bullets import Bullet

from config import window_size, window_width, window_height, FPS, tile_size, level_width, level_height, GAME_OVER_EVENT, LEVEL_FINISHED, PARTICLE_EVENT


class Mushrooms(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        self.bottomleft = position
        self.effects = "trampoline"
        self.image = pygame.image.load("assets/mushroom.png") # .convert_alpha()
        self.rect = self.image.get_rect(bottomleft = self.bottomleft)
        self.mask = pygame.mask.from_surface(self.image)  
        self.timer = 0 
        self.jumping = False 
        self.start_time = 0
    
    def update(self):
        if pygame.time.get_ticks() - self.start_time > 600:
            self.image = pygame.image.load("assets/mushroom.png") # .convert_alpha()

    def jump(self):
        self.image = pygame.image.load("assets/mushroom2.png") # .convert_alpha()
        self.start_time = pygame.time.get_ticks()
        
class Block (pygame.sprite.Sprite):
    
    def __init__(self, x, y, width, height, number = 2, effects = None):
        
        super(Block, self).__init__()
        self.number = number
        self.effects = effects
        self.image = pygame.Surface((width, height))

        if self.number == "4":
            self.effects = 'wall'
            self.image = pygame.image.load("assets/wall1.png")
        elif self.number == "3":
            self.effects = 'platform'
            self.image = pygame.image.load("assets/platform2.png")
        elif self.number == "2":
            self.image.fill((0,0,0))

        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        
        self.rect.x = x 
        self.rect.y = y 

class MovingBlock(pygame.sprite.Sprite):
    def __init__(self, position, direction_x, direction_y):
        super().__init__()
        self.image = pygame.image.load("assets/wall1.png")
        self.rect = self.image.get_rect(topleft=position)
        self.mask = pygame.mask.from_surface(self.image)
        self.direction = pygame.math.Vector2(direction_x, direction_y)
        self.effects = "moving"
        self.collision_image = pygame.Surface((50, 70))
        self.collision_image.fill((0, 0, 0))
        self.collision_sprite = pygame.sprite.Sprite()
        self.collision_sprite.image = self.collision_image
        self.collision_sprite.rect = self.collision_image.get_rect(center=self.rect.center)

    def update(self, blocks):
        self.rect.x += self.direction.x
        self.collision_sprite.rect.x += self.direction.x
        self.rect.y += self.direction.y
        self.collision_sprite.rect.y += self.direction.y    
            
        collision_list = pygame.sprite.spritecollide(self.collision_sprite, blocks, False)
        
        for block in collision_list:
            if block != self:
                self.direction.x = -self.direction.x
                self.direction.y = - self.direction.y

        if self.rect.bottom > window_height - 30 or self.rect.top < 30:
            self.direction.y = -self.direction.y

class ShooterBox(pygame.sprite.Sprite):
    def __init__(self, position, speed, bullet_direction_x, bullet_direction_y, image):
        super().__init__()
        self.speed = speed
        self.bullet_direction_x = bullet_direction_x
        self.bullet_direction_y = bullet_direction_y
        self.shooting_timer = 0
        self.image = pygame.image.load(image) # .convert_alpha()
        self.rect = self.image.get_rect(topleft = position)
        self.mask = pygame.mask.from_surface(self.image)
        self.timer = speed
        self.effects = "shooterbox"

    def update(self, bullet_list):
        self.timer += 1
        if self.timer > self.speed:
            bullet = Bullet(self.rect.centerx, self.rect.centery, self.bullet_direction_x, self.bullet_direction_y, pygame.image.load("assets/cannon_ball.png"))
            bullet_list.add(bullet)
            self.timer = 0