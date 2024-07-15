import pygame, math

from config import window_size, window_width, window_height, FPS, tile_size, level_width, level_height, GAME_OVER_EVENT, LEVEL_FINISHED, PARTICLE_EVENT

class Enemy(pygame.sprite.Sprite):
    def __init__(self, health, position):
        super(Enemy, self).__init__()
        self.image = pygame.transform.rotate(pygame.transform.scale(pygame.image.load ("assets/spike_ball.png"), (20, 20)), 0) #.convert_alpha()
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.direction = pygame.math.Vector2(0, 0)  
        self.potential_direction = pygame.math.Vector2(0,0)    
        self.moving_towards_player_x = False
        self.moving_towards_player_y = False
        self.visability_distance = 100
        self.speed = 1 
        self.current_health = health
        self.effects = "enemy"
        self.has_done_damage = False
        self.last_damage_time = 0
        self.damage_cooldown = 1000
        self.rect.topleft = position
        # manage the pathfinding
        self.collision_image = pygame.Surface((50, 70))
        self.collision_image.fill((0, 0, 0))
        self.collision_sprite = pygame.sprite.Sprite()
        self.collision_sprite.image = self.collision_image
        self.collision_sprite.rect = self.collision_image.get_rect(center=self.rect.center)

    def update(self, player, blocks, moving_object_list):
        
        self.towards_player(player)
        self.collision_with_other_moving_objects(moving_object_list)
        self.experience_gravity()
        self.movement(blocks)

        self.collision_with_bullets(player)
        if pygame.time.get_ticks() - self.last_damage_time > self.damage_cooldown:
            self.has_done_damage = False

    def experience_gravity(self, gravity = .35):
        if (self.direction.y == 0): 
            self.direction.y = 1
        else: 
            self.direction.y += gravity

    def movement(self, blocks):           
        self.rect.x += self.direction.x

        for block in pygame.sprite.spritecollide(self, blocks, False):
            if (self.direction.x > 0):
                self.rect.right = block.rect.left

            elif (self.direction.x < 0 ):
                self.rect.left = block.rect.right

        self.rect.y += self.direction.y
                    
        for block in pygame.sprite.spritecollide(self, blocks, False):
            if (self.direction.y > 0):
                self.rect.bottom = block.rect.top
                self.direction.y = 0
                    
            elif (self.direction.y < 0 ):
                self.rect.top = block.rect.bottom
                self.direction.y = 0
    
    def towards_player(self, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        distance = math.sqrt(dx**2 + dy**2)

        if distance < self.visability_distance:
            if dx > 19: self.potential_direction.x = self.speed
            elif dx < -19: self.potential_direction.x = -self.speed
            else: self.potential_direction.x = 0
        else: self.potential_direction.x = 0

        if distance < self.visability_distance:
            if dy > 19: self.potential_direction.y = self.speed
            # elif dy < -19: self.potential_direction.y = -self.speed
            else: self.potential_direction.y = 0
        else: self.potential_direction.y = 0


    def collision_with_other_moving_objects(self, moving_objects_list):
        move_x = True
        move_y = True
        self.collision_sprite.rect.x += self.potential_direction.x
        if pygame.sprite.spritecollide(self.collision_sprite, moving_objects_list, False, pygame.sprite.collide_mask):
        # Filter out the current enemy from the collision list
            collisions = [obj for obj in pygame.sprite.spritecollide(self.collision_sprite, moving_objects_list, False, pygame.sprite.collide_mask) if obj != self]
            if collisions:
                move_x = False

        self.collision_sprite.rect.y += self.potential_direction.y
        if pygame.sprite.spritecollide(self.collision_sprite, moving_objects_list, False, pygame.sprite.collide_mask):
            # Filter out the current enemy from the collision list
            collisions = [obj for obj in pygame.sprite.spritecollide(self.collision_sprite, moving_objects_list, False, pygame.sprite.collide_mask) if obj != self]
            if collisions:
                move_y = False
        
        if move_x: self.direction.x = self.potential_direction.x
        else: self.collision_sprite.rect.x -= self.potential_direction.x

        if move_y: self.direction.y = self.potential_direction.y
        else: self.collision_sprite.rect.y -= self.potential_direction.y

        self.potential_direction.x = 0
        self.potential_direction.y = 0
    
    def collision_with_bullets(self, player):
        for bullet in player.bullet_list:
            if pygame.sprite.collide_rect(self, bullet):
                self.current_health -= 20
                bullet.kill()
                if self.current_health <= 0:
                    self.kill()
                    player.kill_ammount += 1  

    def deal_damage(self):
        self.has_done_damage = True
        self.last_damage_time = pygame.time.get_ticks()