import pygame

from config import window_size, window_width, window_height, FPS, tile_size, level_width, level_height, GAME_OVER_EVENT, LEVEL_FINISHED, PARTICLE_EVENT

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, x_d, y_d, image):
        super(Bullet, self).__init__()
        self.image = image
        self.x_d = x_d
        self.y_d = y_d
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = 5

    def update(self, collidable):
        self.rect.x += self.speed * self.x_d
        self.rect.y += self.speed * self.y_d

        collision_list = pygame.sprite.spritecollide(self, collidable, False)
        for collided_object in collision_list:
            if collided_object.effects != "wooden_crate" and collided_object.effects != "shooterbox":
                self.kill() 

        if self.rect.left > window_width * 2 or self.rect.top > window_height or self.rect.right < -window_width or self.rect.bottom < 0:
            self.kill()