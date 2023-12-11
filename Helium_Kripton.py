import pygame, os, random, math, pickle
from pathfinding.core.grid import Grid
from button import Button
from SaveLoadManager import SaveLoadSystem
saveloadmanager = SaveLoadSystem(".save", "save_data")
FPS = 60
window_size = window_width, window_height = 640, 480
GAME_OVER_EVENT = pygame.USEREVENT + 1
LEVEL_FINISHED = pygame.USEREVENT + 2
PARTICLE_EVENT = pygame.USEREVENT + 3
pygame.time.set_timer(PARTICLE_EVENT, 50)
tile_size = 20
level_width = 2000 // tile_size
level_height = 480 // tile_size

class Particles():
    def __init__(self):
        self.particles = []
    
    def emit(self):
        if self.particles:
            self.delete_particles()
            for particle in self.particles:
                # move
                particle[0][0] += particle[2][0]
                particle[0][1] += particle[2][1]
                particle[2][1] += random.randint(-20, 25) * 0.05
                # shrink
                particle[1] *= 0.95
                # draw a circle
                pygame.draw.circle(window, (255,255,255), (particle[0]), int(particle[1]))

    def add_particles(self, x, y, direction):
        radius = 5
        particle_circle = [[x,y], radius, [-direction.x, -direction.y]]
        self.particles.append(particle_circle)

    def delete_particles(self):
        particle_copy = [particle for particle in self.particles if particle[1] > 0.05]
        self.particles = particle_copy

class Health_Bar():
    def __init__(self, player):
        self.max_health = player.max_health // 2
        self.heart_full_image = pygame.transform.rotate(pygame.transform.scale(pygame.image.load ("assets/heart_full.png"), (10, 10)), 0)
        self.heart_half_image = pygame.transform.rotate(pygame.transform.scale(pygame.image.load ("assets/heart_half.png"), (10, 10)), 0)
        self.heart_empty_image = pygame.transform.rotate(pygame.transform.scale(pygame.image.load ("assets/heart_empty.png"), (10, 10)), 0)
        self.heart_width = 10

    def draw(self, player):
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

    def draw(self):
        font = pygame.font.SysFont("Paradox King Script", 15)
        
        x = 220
        y = window_height - 40
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

class ItemForBarDisplay(pygame.sprite.Sprite):
    def __init__(self, image):
        self.image_path = image
        self.ammount = 1
        self.item_image = pygame.transform.scale(pygame.image.load(self.image_path), (15, 15))
        
class Player(pygame.sprite.Sprite):
    def __init__(self):
        self.bullet_list = pygame.sprite.Group()
        self.max_health = 40
        self.current_health = 40
        self.max_ammo = 30
        self.current_ammo = 30
        self.width = 20
        self.current_level_number = 1
        super(Player, self).__init__()        
        self.speed = 4        
        self.jump_boost = 0
        self.boost_time = -10000
        self.kill_ammount = 0    
        self.double_jump = 1 
        self.overlay = None
        self.animation_frames = {}
        self.animation_database = {}
        self.active = True
        self.death = False
        self.direction = pygame.math.Vector2(0, 0)
        self.particles = Particles()

        self.on_ground = False
        self.on_left = False
        self.on_right = False
        self.on_ceiling = False
        self.on_platform = False
        self.current_x = 0

        self.action = "idle"
        self.frame = 0
        self.flip = False

        self.animation_database["run"] = self.load_animations("player_animations/run", [15,15])
        self.animation_database["idle"] = self.load_animations("player_animations/idle", [15,15])
        self.animation_database["jump"] = self.load_animations("player_animations/jump", [30])
        self.animation_database["wall"] = self.load_animations("player_animations/wall", [15,15])
        self.animation_database["dead"] = self.load_animations("player_animations/dead", [15,15])
        self.animation_database["finished"] = self.load_animations("player_animations/finished", [15,15])
        
        self.image_id = self.animation_database[self.action][self.frame]
        self.image = self.animation_frames[self.image_id]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
    
    def particle_animation(self):
        if self.direction.x > 0:
            self.particles.add_particles(self.rect.bottomright[0], self.rect.centery + 20, self.direction)
        if self.direction.x < 0:
            self.particles.add_particles(self.rect.bottomleft[0], self.rect.centery + 20, self.direction)

    def death_event(self):
        self.active = False
        self.death = True
        self.death_time = pygame.time.get_ticks()

    def level_passed(self):
        self.active = False
        self.finish_time = pygame.time.get_ticks()

    def change_action(self, new_value):
        if self.action != new_value:
            self.action = new_value
            self.frame = 0

    def load_animations(self, path, frame_durations):
        animation_name = path.split("/")[-1]
        animation_frame_data = []
        n = 1
        for frame in frame_durations:
            animation_frame_id = animation_name + str(n)
            image_loc = path + "/" + animation_frame_id + ".png"
            animation_image = pygame.image.load(image_loc).convert()
            animation_image.set_colorkey((255,255,255))
            self.animation_frames[animation_frame_id] = animation_image.copy()
            for i in range (frame):
                animation_frame_data.append(animation_frame_id)
            n += 1
        return animation_frame_data

    def reset(self, level, player_start, kills, ammo, health):
        self.current_health = health
        self.current_ammo = ammo
        self.kill_ammount = kills
        self.current_level_number = level
        self.rect.bottomleft = player_start
    
    def shoot_bullet(self, mouse_x, mouse_y):
        if self.current_ammo > 0:
            # Calculate the angle between player's position and mouse click
            angle = math.atan2(mouse_y - self.rect.centery, mouse_x - self.rect.centerx)
            
            # Convert the angle to degrees and rotate the image accordingly
            angle_degrees = math.degrees(angle)
            bullet_image = pygame.transform.rotate(pygame.image.load("assets/bullet.png"), -angle_degrees)
            
            # Create the Bullet with the calculated angle
            bullet = Bullet(self.rect.centerx, self.rect.centery, math.cos(angle), math.sin(angle), bullet_image)
            self.bullet_list.add(bullet)
            self.change_ammo(-1) 

    def apply_jump_boost(self, amount):
        self.jump_boost = amount
        self.double_jump = 2
        self.boost_time = pygame.time.get_ticks()
        self.boost_duration = 10000

    def change_health(self, ammount):
        self.current_health += ammount
        if self.current_health > self.max_health:
            self.current_health = self.max_health
        if self.current_health <= 0:
            self.current_health = 0
            self.death_event()

    def change_ammo(self, ammount):
        self.current_ammo += ammount
        if self.current_ammo > self.max_ammo:
            self.current_ammo = self.max_ammo
        if self.current_ammo < 0:
            self.current_ammo = 0

    def update(self, collidable = pygame.sprite.Group(), potion1_list= pygame.sprite.Group(), potion2_list= pygame.sprite.Group(), ammo_list = pygame.sprite.Group(), event = None, ):
        self.frame += 1
        if self.frame >= len(self.animation_database[self.action]):
            self.frame = 0
        self.image_id = self.animation_database[self.action][self.frame]
        self.image = self.animation_frames[self.image_id]
        self.image = pygame.transform.flip(self.image, self.flip, False)
        self.image.set_colorkey((0,0,0))
        self.mask = pygame.mask.from_surface(self.image)


        if self.active:            
            if self.rect.top > window_height:
                self.death_event()
        
            if pygame.time.get_ticks() - self.boost_time < 10000:
                self.overlay = create_overlay((127, 0, 200), 100)
            else:
                self.jump_boost = 0
                self.double_jump = 1
                self.overlay = None

            self.experience_gravity()

            self.collision_detection(collidable, potion1_list, potion2_list, ammo_list)

            self.moving(event)
            self.bullet_shoot(event)
            
            if self.direction.x < 0 and self.action != "wall":
                self.change_action( "run")
                self.flip = True

            if self.direction.x > 0 and self.action != "wall":
                self.change_action( "run")
                self.flip = False

            if self.direction.x == 0:
                self.change_action( "idle")

            if self.on_ground and (self.direction.y < 0) or (self.direction.y > 1):
                self.on_ground = False
            if self.on_ceiling and self.direction.y > 0:
                self.on_ceiling = False

            if self.on_left and (self.rect.left < self.current_x) or (self.direction.x >= 0) :
                self.on_left = False
            if self.on_right and (self.rect.right > self.current_x) or (self.direction.x <= 0) :
                self.on_right = False

            if self.on_platform and (self.direction.y != 0):
                self.on_platform = False

            if self.on_ground and self.on_right:
                self.rect = self.image.get_rect(bottomright =self.rect.bottomright)
            elif self.on_ground and self.on_left:
                self.rect = self.image.get_rect(bottomleft =self.rect.bottomleft)
            elif self.on_ground:
                self.rect = self.image.get_rect(midbottom = self.rect.midbottom)
            elif self.on_ceiling and self.on_right:
                self.rect = self.image.get_rect(topright = self.rect.topright)
            elif self.on_ceiling and self.on_left:
                self.rect = self.image.get_rect(topleft = self.rect.topleft)
            elif self.on_ceiling:
                self.rect = self.image.get_rect(midtop = self.rect.midtop)
            elif self.on_left:
                self.rect = self.image.get_rect(midleft = self.rect.midleft)
            elif self.on_right:
                self.rect = self.image.get_rect(midright = self.rect.midright)
            else:
                self.rect = self.image.get_rect(center = self.rect.center)

        elif self.death:
            self.change_action("dead")
            self.direction.y = 0
            self.direction.x = 0
            self.rect.y -= 1
            if pygame.time.get_ticks() - self.death_time > 3000:
                pygame.event.post(pygame.event.Event(GAME_OVER_EVENT))
        else:
            self.change_action( "finished")
            self.direction.y = 0
            self.direction.x = 0
            self.rect.y -= 1
            self.rect.x += 1
            if pygame.time.get_ticks() - self.finish_time > 5000:
                pygame.event.post(pygame.event.Event(LEVEL_FINISHED))
        
    def bullet_shoot(self, event):    
        if not (event == None):
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.shoot_bullet(mouse_x, mouse_y)

    def collision_detection(self, collidable, potion1_list, potion2_list, ammo_list):
        self.rect.x += self.direction.x
        collision_list = pygame.sprite.spritecollide(self, collidable, False)   
        for collided_object in collision_list:
            if collided_object.effects != "background" and collided_object.effects != "platform" and not self.on_platform:
                offset = (collided_object.rect.x - self.rect.x, collided_object.rect.y - self.rect.y)
                if self.mask.overlap(collided_object.mask, offset):    
                    if (self.direction.x > 0):
                        self.rect.right = collided_object.rect.left
                        self.on_right = True
                        self.current_x = self.rect.right
                        if collided_object.effects == "wall":
                            self.direction.y *= 0.95
                            self.jumps_left = self.double_jump

                    elif (self.direction.x < 0 ):
                        self.rect.left = collided_object.rect.right
                        self.on_left = True
                        self.cuurent_x = self.rect.left 
                        if collided_object.effects == "wall":
                            self.direction.y *= 0.95 
                            self.jumps_left = self.double_jump                

        self.rect.y += self.direction.y
        collision_list = pygame.sprite.spritecollide(self, collidable, False)
        for collided_object in collision_list:
            offset = (collided_object.rect.x - self.rect.x, collided_object.rect.y - self.rect.y)
            if self.mask.overlap(collided_object.mask, offset):
                    if (self.direction.y > 0):
                        if collided_object.effects != "platform" or collided_object.rect.top >= self.rect.bottom - self.width / 2:
                            self.rect.bottom = collided_object.rect.top
                            self.direction.y = 0
                            self.jumps_left = self.double_jump
                            self.on_ground = True
                            
                            if collided_object.effects == "mystery_box":
                                print("myster")
                                choice = random.choice((1,2,3,4,5))
                                if choice == 1: potion1_list.add(Item("assets/jump_potion.png", collided_object.rect.bottomleft, None))
                                elif choice == 2: potion2_list.add(Item("assets/health_potion.png", collided_object.rect.bottomleft, None))
                                elif choice == 3: ammo_list.add(Item("assets/ammo.png", collided_object.rect.bottomleft, None))
                                else: pass
                                collided_object.kill() 

                            elif collided_object.effects == "trampoline":
                                self.direction.y =  -10 
                                collided_object.jump() 
                            elif collided_object.effects == "moving":
                                self.on_platform = True
                                if collided_object.direction.x != 0:
                                    self.rect.x += collided_object.direction.x

                    elif (self.direction.y < 0 ):
                        if collided_object.effects != "platform":
                            self.rect.top = collided_object.rect.bottom
                            self.direction.y = 0
                            self.on_ceiling = True
                            if collided_object.effects == "mystery_box":
                                print("myster")
                                choice = random.choice((1,2,3,4,5))
                                if choice == 1: potion1_list.add(Item("assets/jump_potion.png",collided_object.rect.bottomleft, None))
                                elif choice == 2: potion2_list.add(Item("assets/health_potion.png", collided_object.rect.bottomleft, None))
                                elif choice == 3: ammo_list.add(Item("assets/ammo.png", collided_object.rect.bottomleft, None))
                                else: pass
                                collided_object.kill() 

        
    def moving(self, event):
        if not (event == None):
            if (event.type == pygame.KEYDOWN):
                if (event.key == pygame.K_a):
                    self.direction.x = -(self.speed)
                if (event.key == pygame.K_d):
                    self.direction.x = (self.speed)
                if (event.key == pygame.K_w):
                    if self.jumps_left > 0:
                        self.direction.y = -(self.speed) * 2 - self.jump_boost
                        self.jumps_left -= 1
            if (event.type == pygame.KEYUP):
                if (event.key == pygame.K_a):
                    if (self.direction.x < 0): 
                        self.direction.x = 0
                if (event.key == pygame.K_d):
                    if (self.direction.x > 0): 
                        self.direction.x = 0
    
    def experience_gravity(self, gravity = .35):
        if (self.direction.y == 0): self.direction.y = 1
        else: self.direction.y += gravity

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
            

class Level( object ):
    def __init__(self, loaded, world_shift_x, player_start, current_level_number, mysterybox_coordinates, woodencrate_coordinates, potion1_coordinates, potion2_coordinates, player_kill_ammount, player_current_ammo , player_current_health):
        self.loaded = loaded
        self.current_level_number = current_level_number
        level_data = open(f"save_data/level_{current_level_number}.save", "rb")
        self.level = pickle.load(level_data)

        # # can be used for pathfinding
        # self.grid = Grid(self.level)

        self.world_shift_x = world_shift_x

        if loaded:
            self.player_start = self.player_start_x, self.player_start_y = player_start
            self.player_start_x += self.world_shift_x

        self.left_viewbox = window_width / 5
        self.right_viewbox = window_width - (window_width/4)

        # self.top_viewbox = window_height/10
        # self.bottom_viewbox = window_height * .9

        self.level_width = len(self.level[0])
        self.level_height = len(self.level)

        self.mysterybox_coordinates = mysterybox_coordinates
        self.woodencrate_coordinates = woodencrate_coordinates
        self.potion1_coordinates = potion1_coordinates
        self.potion2_coordinates = potion2_coordinates
        
        self.set_up()
        self.reset(self.player_start, player_kill_ammount, player_current_ammo , player_current_health )
        
    def set_up(self):
        self.object_list = pygame.sprite.Group()
        self.mushroom_list = pygame.sprite.Group()
        self.player_collide_list = pygame.sprite.Group()
        self.enemy_bullet_list = pygame.sprite.Group()
        self.bullet_list = pygame.sprite.Group()
        self.item_list = pygame.sprite.Group()
        self.potion1_list = pygame.sprite.Group()
        self.potion2_list = pygame.sprite.Group()
        self.wooden_crate_list = pygame.sprite.Group()
        self.ammo_list = pygame.sprite.Group()
        self.moving_enemies = pygame.sprite.Group()
        self.mystery_box_list = pygame.sprite.Group()
        self.laser_shooter_group = pygame.sprite.Group()
        self.decorative_item_group = pygame.sprite.Group()
        self.moving_blocks = pygame.sprite.Group()
        self.all_items_and_enemies = pygame.sprite.Group()
        self.finish_flag = pygame.sprite.GroupSingle()
        self.player_object = Player()
        self.active_object_list = pygame.sprite.GroupSingle()
        self.active_object_list.add(self.player_object)

        self.health_bar = Health_Bar(self.player_object)
        self.item_bar = ItemBar()

        self.enemy_coordinates = []
        self.coordinates = []
        self.objective = 0

        
        for row in range(self.level_height):
            for col in range(self.level_width):
                x = col * tile_size + self.world_shift_x
                y = row * tile_size
                if self.level[row][col] == "3" or self.level[row][col] == "4":
                    block = Block(x, y, tile_size, tile_size, self.level[row][col])
                    self.object_list.add(block)
                elif self.level[row][col] == "2":
                    self.moving_enemies.add(Enemy((random.randint(50, 100)), (x, y)))
                elif self.level[row][col] == "7":
                    self.laser_shooter_group.add(ShooterBox((x, y), random.randint(50,100), -1, 0, "assets/arrow_l.png"))
                elif self.level[row][col] == "8":
                    self.laser_shooter_group.add(ShooterBox((x, y), random.randint(50,100), 0, -1, "assets/arrow_u.png"))
                elif self.level[row][col] == "9":
                    self.laser_shooter_group.add(ShooterBox((x, y), random.randint(50,100), 0, 1, "assets/arrow_d.png"))
                elif self.level[row][col] == "6":
                    self.laser_shooter_group.add(ShooterBox((x, y), random.randint(50,100), 1, 0, "assets/arrow_r.png"))
                elif self.level[row][col] == "14":
                    self.mushroom_list.add(Mushrooms((x, y + tile_size)))
                elif self.level[row][col] == "15":
                    self.moving_blocks.add(MovingBlock((x, y + tile_size), 0, 1))
                elif self.level[row][col] == "16":
                    self.moving_blocks.add(MovingBlock((x, y + tile_size), 1, 0))
                elif self.level[row][col] == "17":
                    self.finish_flag.add(Item("assets/finish_flag.png", (x, y + tile_size), "finish"))
                elif self.level[row][col] == "1":
                    if not self.loaded:
                        self.player_start = (x, y + tile_size)
                    self.decorative_item_group.add(Item("assets/start_flag.png", (x, y + tile_size), "start"))
                
                if not self.loaded:
                    if self.level[row][col] == "11":
                        self.potion1_list.add(Item("assets/jump_potion.png", (x, y + tile_size), None))
                    elif self.level[row][col] == "12":
                        self.potion2_list.add(Item("assets/health_potion.png", (x, y + tile_size), None))
                    elif self.level[row][col] == "5":
                        self.wooden_crate_list.add(WoodenCrate("assets/wooden_crate.png", (x, y + tile_size), "wooden_crate"))
                    elif self.level[row][col] == "13":
                        self.mystery_box_list.add(Item("assets/mystery_box.png", (x, y + tile_size), "mystery_box"))
    
    def spawn_items(self):
        if self.loaded:
            self.spawn_something(self.mysterybox_coordinates, self.mystery_box_list, Item, "assets/mystery_box.png", "mystery_box")          
            self.spawn_something(self.woodencrate_coordinates, self.wooden_crate_list, WoodenCrate, "assets/wooden_crate.png", "wooden_crate")
            self.spawn_something(self.potion1_coordinates, self.potion1_list, Item, "assets/jump_potion.png", None)
            self.spawn_something(self.potion2_coordinates, self.potion2_list, Item, "assets/health_potion.png", None)      
        self.decorative_item_group.add(self.finish_flag)
        self.item_list.add(self.mystery_box_list, self.wooden_crate_list, self.potion1_list, self.potion2_list)
        self.player_collide_list.add(self.object_list, self.mystery_box_list, self.wooden_crate_list, self.mushroom_list, self.moving_blocks, self.laser_shooter_group)

    def spawn_something(self, some_coordinates, some_list, something, image, effects):
        for i in range(len(some_coordinates)):
            thing = something(image, (some_coordinates[i][0], some_coordinates[i][1] + tile_size), effects)
            some_list.add(thing)

    def reset(self, player_start, kills, ammo, health):
        self.spawn_items()      
        self.player_object.reset(self.current_level_number, player_start, kills, ammo, health)
    
    def update(self):
        self.item_list.add(self.potion1_list, self.potion2_list, self.ammo_list, self.mystery_box_list, self.wooden_crate_list)
        self.current_time = pygame.time.get_ticks() 
        self.object_list.update()
        self.wooden_crate_list.update(self.bullet_list)
        self.moving_enemies.update(self.player_object, self.player_collide_list, self.moving_enemies)
        self.laser_shooter_group.update(self.enemy_bullet_list)
        self.bullet_list.add(self.enemy_bullet_list)
        self.bullet_list.update(self.player_collide_list)
        self.mushroom_list.update()
        self.moving_blocks.update(self.player_collide_list)
        self.player_object.update(self.player_collide_list, self.potion1_list, self.potion2_list, self.ammo_list)
        self.managePlayerCollisions()
        self.run_viewbox()

    def managePlayerCollisions(self):
        if pygame.sprite.spritecollide(self.player_object, self.enemy_bullet_list, False):
            if pygame.sprite.spritecollide(self.player_object, self.enemy_bullet_list, True, pygame.sprite.collide_mask):
                self.player_object.change_health(-2)
        if pygame.sprite.spritecollide(self.player_object, self.moving_enemies, False):    
            for enemy in pygame.sprite.spritecollide(self.player_object, self.moving_enemies, False, pygame.sprite.collide_mask):
                if not enemy.has_done_damage:
                    self.player_object.change_health(-1)
                    enemy.deal_damage()
        if pygame.sprite.spritecollide(self.player_object, self.potion1_list, False):    
            if pygame.sprite.spritecollide(self.player_object, self.potion1_list, True, pygame.sprite.collide_mask):
                self.item_bar.add_item(ItemForBarDisplay("assets/jump_potion.png"))
                # self.player_object.apply_jump_boost(0.5)           
        if pygame.sprite.spritecollide(self.player_object, self.potion2_list, False):    
            if pygame.sprite.spritecollide(self.player_object, self.potion2_list, True, pygame.sprite.collide_mask):
                self.item_bar.add_item(ItemForBarDisplay("assets/health_potion.png"))
                # self.player_object.change_health(random.randint(2,5))
        if pygame.sprite.spritecollide(self.player_object, self.ammo_list, False):    
            if pygame.sprite.spritecollide(self.player_object, self.ammo_list, True, pygame.sprite.collide_mask):
                self.item_bar.add_item(ItemForBarDisplay("assets/ammo.png"))
                # self.player_object.change_ammo(random.randint(5,10))
        if pygame.sprite.spritecollide(self.player_object, self.finish_flag, False):
            if pygame.sprite.spritecollide(self.player_object, self.finish_flag, False, pygame.sprite.collide_mask):
                self.player_object.level_passed()

    def draw(self, window):

        window.fill ((0,0,255))
        self.decorative_item_group.draw(window)
        self.object_list.draw(window)
        self.item_list.draw(window)
        self.mushroom_list.draw(window)
        self.health_bar.draw(self.player_object)
        self.item_bar.draw()
        self.bullet_list.add(self.player_object.bullet_list)
        self.bullet_list.draw(window)        
        self.moving_enemies.draw(window)
        self.laser_shooter_group.draw(window)
        self.moving_blocks.draw(window)
        self.player_object.particles.emit() 
        self.active_object_list.draw(window)
        if self.player_object.overlay != None:
            window.blit(self.player_object.overlay, (0, 0))

        if self.item_bar.something_selected:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            pygame.draw.rect(window, (100,100,100,200), ((((mouse_x - 10)//tile_size) * tile_size + self.world_shift_x % tile_size, ((mouse_y - 10) // tile_size)* tile_size), (20, 20)))

    def shift_world(self, shift_x):
        self.world_shift_x += shift_x
        
        for each_object in self.player_collide_list:
            each_object.rect.x += shift_x
            if each_object.effects == "moving":
                each_object.collision_sprite.rect.x += shift_x

        for each in self.potion1_list:
            each.rect.x += shift_x

        for each in self.ammo_list:
            each.rect.x += shift_x

        for each in self.potion2_list:
            each.rect.x += shift_x

        for each in self.moving_enemies:
            each.rect.x += shift_x

        for each_bullet in self.bullet_list:
            each_bullet.rect.x += shift_x

        for decorative_item in self.decorative_item_group:
            decorative_item.rect.x += shift_x

    def run_viewbox(self):
        if (self.player_object.rect.x <= self.left_viewbox):
            view_difference = self.left_viewbox - self.player_object.rect.x
            self.player_object.rect.x = self.left_viewbox
            self.shift_world(view_difference)

        if (self.player_object.rect.x >= self.right_viewbox):
            view_difference = self.right_viewbox - self.player_object.rect.x
            self.player_object.rect.x = self.right_viewbox
            self.shift_world(view_difference)

        # if (self.player_object.rect.y <= self.top_viewbox):
        #     view_difference = self.top_viewbox - self.player_object.rect.y
        #     self.player_object.rect.y = self.top_viewbox
        #     self.shift_world(0, view_difference)

        # if (self.player_object.rect.y >= self.bottom_viewbox):
        #     view_difference = self.bottom_viewbox - self.player_object.rect.y
        #     self.player_object.rect.y = self.bottom_viewbox
        #     self.shift_world(0, view_difference)

def create_overlay(color, transparency):
    overlay = pygame.Surface(window.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, transparency))
    return overlay

running = True

class GameState():
    def __init__(self):
        self.state = "start_screen"
        self.running = True 
        self.max_achieved_level_number = 1
        self.current_level_number = 1
        self.current_level_whatever = "custom"
        self.level = [["0" for _ in range(level_width)] for _ in range(level_height)]
        self.selected_color = "4"
        self.dragging = False
        self.start_cell_x = 0
        self.start_cell_y = 0
        self.draw_options = False
        self.level_ammount = 21
        self.current_level_number_none = False

    def state_manager(self):
        if self.state == "start_screen":
            self.start_screen()
        if self.state == "main_game":
            self.main_game()
        if self.state == "custom_screen":
            self.custom_screen()
        if self.state == "game_over_screen":
            self.game_over_screen()
        if self.state == "customize":
            self.customize()
        if self.state == "next_level_screen":
            self.next_level_screen()
        if self.state == "level_menu":
            self.level_menu()

    def start_screen(self):
        window.fill((200, 200, 200))
        font = pygame.font.SysFont("Paradox King Script", 50)
        text = font.render("The Helium Kripton", True, (100, 0, 0))
        text_rect = text.get_rect(center=(window_width // 2, 75))
        window.blit(text, text_rect)
         
        button_surface = pygame.image.load("assets/button.png")
        button_surface = pygame.transform.scale(button_surface, (250,50))
        play_button = Button(button_surface, (window_width//2, 175), "NEW GAME")
        load_button = Button(button_surface, (window_width//2, 275), "LOAD GAME")
        custom_screen_button = Button(button_surface, (window_width//2, 375), "SANDBOX")
            
        for button in [play_button, load_button, custom_screen_button]:
            button.changeColor(pygame.mouse.get_pos())
            button.update(window)
        
        for event in pygame.event.get():     
            if (event.type == pygame.QUIT) or \
            (event.type == pygame.KEYDOWN) and \
            (event.key == pygame.K_ESCAPE or event.key == pygame.K_q):
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.checkForInput(pygame.mouse.get_pos()):
                    self.current_level = Level(False, world_shift_x = 0, player_start = None, current_level_number = self.current_level_number, mysterybox_coordinates= [], woodencrate_coordinates= [], potion1_coordinates= [], potion2_coordinates= [], player_kill_ammount = 0, player_current_ammo = 30, player_current_health = 40)
                    self.current_level_whatever = 1                                       
                    self.max_achieved_level_number = 1
                    self.state = "main_game"
                elif load_button.checkForInput(pygame.mouse.get_pos()):
                    self.max_achieved_level_number, self.world_shift_x, self.mysterybox_coordinates, self.woodencrate_coordinates, self.potion1_coordinates, self.potion2_coordinates, self.current_level_number, self.player_position, self.player_kill_ammount, self.player_current_ammo, self.player_current_health = saveloadmanager.Load_game_data(["max_achieved_level", "world_shift_x", "coordinates_mystery", "coordinates_wooden", "coordinates_potion1", "coordinates_potion2", "level", "position","kills", "ammo", "health"], [1, None, None, None, None, None, 1, 0, 20, 150])
                    if self.current_level_number_none:
                        self.current_level_number = 0
                    print(f'LOADED max_achieved_level_number {self.max_achieved_level_number}')
                    print(f'LOADED current_level_number {self.current_level_number}')
                    self.level_button_setup()
                    self.state = "level_menu"
                elif custom_screen_button.checkForInput(pygame.mouse.get_pos()):
                    self.state = "custom_screen"
    
    def saveGameProgress(self):
        saveloadmanager.save_game_data(
                        [
                            self.max_achieved_level_number,
                            self.current_level.world_shift_x,
                            self.current_level.mysterybox_coordinates,
                            self.current_level.woodencrate_coordinates,
                            self.current_level.potion1_coordinates,
                            self.current_level.potion2_coordinates,
                            self.current_level_number,
                            self.current_level.player_object.rect.bottomleft,
                            self.current_level.player_object.kill_ammount,
                            self.current_level.player_object.current_ammo,
                            self.current_level.player_object.current_health
                        ],
                        [
                            "max_achieved_level",
                            "world_shift_x",
                            "coordinates_mystery",
                            "coordinates_wooden",
                            "coordinates_potion1",
                            "coordinates_potion2",
                            "level",
                            "position",
                            "kills",
                            "ammo",
                            "health"
                        ]
                    )
    def level_button_setup(self):
        self.button_size = 50
        self.margin = 25
        self.row_size = 7
        self.level_buttons = []

        for i in range(self.level_ammount):
            row = i // self.row_size - 1
            col = i % self.row_size
            button_x = col * (self.button_size + self.margin) + 90
            button_y = row * (self.button_size + self.margin) + 250
            if i <= self.max_achieved_level_number - 1: 
                if i == self.current_level_number - 1: button_surface = pygame.transform.scale(pygame.image.load("assets/button_circle3.png"), (50,50))
                else: button_surface = pygame.transform.scale(pygame.image.load("assets/button_circle.png"), (50,50))
            else: button_surface = pygame.transform.scale(pygame.image.load("assets/button_circle2.png"), (50,50))
            self.level_buttons.append(Button(button_surface, (button_x, button_y), f'{i + 1}'))

    def level_menu(self):
        window.fill((200, 200, 200))
        font = pygame.font.SysFont("Paradox King Script", 50)
        text = font.render("The Helium Kripton", True, (100, 0, 0))
        text_rect = text.get_rect(center=(window_width // 2, 75))
        window.blit(text, text_rect)
        
        for button in self.level_buttons:
            button.changeColor(pygame.mouse.get_pos())
            button.update(window)

        for event in pygame.event.get():     
            if (event.type == pygame.QUIT) or \
            (event.type == pygame.KEYDOWN) and \
            (event.key == pygame.K_ESCAPE):
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in self.level_buttons:
                    if button.checkForInput(pygame.mouse.get_pos()):
                        if int(button.text_input) <= self.max_achieved_level_number:
                            if int(button.text_input) == self.current_level_number:
                                print("last played level")
                                self.current_level = Level(True, self.world_shift_x , self.player_position, self.current_level_number, self.mysterybox_coordinates, self.woodencrate_coordinates, self.potion1_coordinates, self.potion2_coordinates, self.player_kill_ammount, self.player_current_ammo, self.player_current_health)
                                self.current_level_whatever = int(button.text_input)                                      
                                self.state = "main_game"    
                            else:
                                print("unsaved level")
                                self.current_level = Level(False, world_shift_x = 0, player_start = None, current_level_number = int(button.text_input), mysterybox_coordinates= [], woodencrate_coordinates= [], potion1_coordinates= [], potion2_coordinates= [] , player_kill_ammount = 0, player_current_ammo =30, player_current_health = 40)
                                self.current_level_whatever = int(button.text_input)
                                self.current_level_number = int(button.text_input)
                                self.state = "main_game"                                                                      
                        else: pass

    def main_game(self):
        for event in pygame.event.get():    
            if (event.type == pygame.QUIT) or \
            (event.type == pygame.KEYDOWN) and \
            (event.key == pygame.K_ESCAPE):
                if self.current_level_whatever != "custom":    
                    
                    self.current_level.mysterybox_coordinates = []
                    self.current_level.woodencrate_coordinates = []
                    self.current_level.potion1_coordinates = []
                    self.current_level.potion2_coordinates = []
                    for item in self.current_level.mystery_box_list:
                        self.current_level.mysterybox_coordinates += [item.rect.topleft]
                    for item in self.current_level.wooden_crate_list:
                        self.current_level.woodencrate_coordinates += [item.rect.topleft]
                    for item in self.current_level.potion1_list:
                        self.current_level.potion1_coordinates += [item.rect.topleft]
                    for item in self.current_level.potion2_list:
                        self.current_level.potion2_coordinates += [item.rect.topleft]
                    print(f'SAVED max_achieved_level_number {self.max_achieved_level_number}')
                    print(f'SAVED current_level_number {self.current_level_number}')

                    # save current progress
                    self.saveGameProgress()

                self.running = False
            self.current_level.player_object.moving(event)
            self.current_level.player_object.bullet_shoot(event)
            if event.type == GAME_OVER_EVENT:
                self.state = "game_over_screen" 
            if event.type == LEVEL_FINISHED:
                self.state = "next_level_screen" 
            if event.type == PARTICLE_EVENT:
                self.current_level.player_object.particle_animation()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and self.current_level.item_bar.selected_index != self.current_level.item_bar.max_item_index - 1:
                    self.current_level.item_bar.selected_index += 1
                if event.key == pygame.K_LEFT and self.current_level.item_bar.selected_index != 0:
                    self.current_level.item_bar.selected_index -= 1

        # Update functions
        self.current_level.update()   
        # Logic testing

        # Draw everything
        
        self.current_level.draw(window)
        fps = int(clock.get_fps())
        pygame.display.set_caption(f"HELIUM KRIPTON the Game of Survival in a Geometric World. FPS is {fps}")


    def custom_screen(self):
        
        window.fill((200, 200, 200))
        font = pygame.font.SysFont("Paradox King Script", 50)
        text = font.render("The Helium Kripton", True, (100, 0, 0))
        text_rect = text.get_rect(center=(window_width // 2, 75))
        window.blit(text, text_rect)
            
        button_surface = pygame.image.load("assets/button.png")
        button_surface = pygame.transform.scale(button_surface, (250,50))
        new_button = Button(button_surface, (window_width//2, 175), "Create new")
        last_button = Button(button_surface, (window_width//2, 275), "last created")
        back_button = Button(button_surface, (window_width//2, 375), "back")
            
        for button in [new_button, last_button, back_button]:
            button.changeColor(pygame.mouse.get_pos())
            button.update(window)

        for event in pygame.event.get():     
            if (event.type == pygame.QUIT) or \
            (event.type == pygame.KEYDOWN) and \
            (event.key == pygame.K_ESCAPE):
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.checkForInput(pygame.mouse.get_pos()):
                        self.state = "start_screen"                                                
                    elif new_button.checkForInput(pygame.mouse.get_pos()):
                        self.state = "customize"
                    elif last_button.checkForInput(pygame.mouse.get_pos()):
                        self.current_level = Level(False, world_shift_x = 0, player_start = None, current_level_number = "custom", mysterybox_coordinates= [], woodencrate_coordinates= [], potion1_coordinates= [], potion2_coordinates= [] , player_kill_ammount = 0, player_current_ammo =30, player_current_health = 40)
                        self.current_level_whatever = "custom"
                        self.state = "main_game"

    def game_over_screen(self):
        window.fill((200, 200, 200))
        font = pygame.font.SysFont("Paradox King Script", 50)
        text = font.render("You've died", True, (100, 0, 0))
        text_rect = text.get_rect(center=(window_width // 2, 75))
        window.blit(text, text_rect)
            
        button_surface = pygame.image.load("assets/button.png")
        button_surface = pygame.transform.scale(button_surface, (250,50))
        play_again_button = Button(button_surface, (window_width//2, 175), "Play again")
        quit_button = Button(button_surface, (window_width//2, 275), "quit")
            
        for button in [play_again_button, quit_button]:
            button.changeColor(pygame.mouse.get_pos())
            button.update(window)
        
        for event in pygame.event.get():     
            if (event.type == pygame.QUIT) or \
            (event.type == pygame.KEYDOWN) and \
            (event.key == pygame.K_ESCAPE or event.key == pygame.K_q):
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                    if play_again_button.checkForInput(pygame.mouse.get_pos()):
                        self.current_level = Level(False, world_shift_x = 0, player_start = None, current_level_number = self.current_level_whatever, mysterybox_coordinates= [], woodencrate_coordinates= [], potion1_coordinates= [], potion2_coordinates= [] , player_kill_ammount = 0, player_current_ammo = 30, player_current_health = 40)
                        self.state = "main_game"
                    if quit_button.checkForInput(pygame.mouse.get_pos()):
                        self.state = "start_screen"

    def updateCurrentAndMaxLevel(self):
        self.current_level_number += 1
        self.current_level_whatever = self.current_level_number
        if self.max_achieved_level_number <= self.current_level_number:
            self.max_achieved_level_number = self.current_level_number
            print(self.max_achieved_level_number)
    
    def next_level_screen(self):
        window.fill((200, 200, 200))
        font = pygame.font.SysFont("Paradox King Script", 50)
        text = font.render(f'Level {self.current_level_number} completed!', True, (100, 0, 0))
        text_rect = text.get_rect(center=(window_width // 2, 75))
        window.blit(text, text_rect)
            
        button_surface = pygame.image.load("assets/button.png")
        button_surface = pygame.transform.scale(button_surface, (250,50))
        next_level_button = Button(button_surface, (window_width//2, 175), "Next Level")
        play_again_button = Button(button_surface, (window_width//2, 225), "Play Again")
        quit_button = Button(button_surface, (window_width//2, 300), "Quit")
            
        for button in [next_level_button, play_again_button, quit_button]:
            button.changeColor(pygame.mouse.get_pos())
            button.update(window)
        
        for event in pygame.event.get():     
            if (event.type == pygame.QUIT) or \
            (event.type == pygame.KEYDOWN) and \
            (event.key == pygame.K_ESCAPE or event.key == pygame.K_q):
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                    if next_level_button.checkForInput(pygame.mouse.get_pos()):
                        self.updateCurrentAndMaxLevel()
                        self.current_level = Level(False, world_shift_x = 0, player_start = None, current_level_number = self.current_level_number, mysterybox_coordinates= [], woodencrate_coordinates= [], potion1_coordinates= [], potion2_coordinates= [] , player_kill_ammount = 0, player_current_ammo = 30, player_current_health = 40)
                        self.state = "main_game"
                    if play_again_button.checkForInput(pygame.mouse.get_pos()):
                        self.current_level = Level(False, world_shift_x = 0, player_start = None, current_level_number = self.current_level_whatever, mysterybox_coordinates= [], woodencrate_coordinates= [], potion1_coordinates= [], potion2_coordinates= [] , player_kill_ammount = 0, player_current_ammo = 30, player_current_health = 40)
                        self.state = "main_game"
                    if quit_button.checkForInput(pygame.mouse.get_pos()):
                        self.current_level_number_none = True
                        self.updateCurrentAndMaxLevel()
                        # save the current progress
                        self.saveGameProgress()
                        self.state = "start_screen"

    def customize(self):        
        button_surface = pygame.transform.scale(pygame.image.load("assets/button.png"), (150,50))
        options_button = Button(button_surface, (window_width - 100, 40), "Options")
        save_button = Button(button_surface, (window_width - 100, 100), "Save")
        play_button = Button(button_surface, (window_width - 100, 160), "Play")
        quit_button = Button(button_surface, (window_width - 100, 220), "Quit")
        back_button = Button(button_surface, (window_width - 100, 40), "Back")
        window.fill((255,255,255))

        for event in pygame.event.get():     
            if (event.type == pygame.QUIT) or \
            (event.type == pygame.KEYDOWN) and \
            (event.key == pygame.K_ESCAPE):
                self.running = False            
            
            elif event.type == pygame.MOUSEBUTTONDOWN:

                if self.draw_options:
                    if save_button.checkForInput(pygame.mouse.get_pos()):
                        saveloadmanager.save_game_data([self.level], ["level_custom"])
                    if play_button.checkForInput(pygame.mouse.get_pos()):
                        saveloadmanager.save_game_data([self.level], ["level_custom"])
                        self.current_level = Level(False, world_shift_x = 0, player_start = None, current_level_number = "custom", mysterybox_coordinates= [], woodencrate_coordinates= [], potion1_coordinates= [], potion2_coordinates= [], player_kill_ammount = 0, player_current_ammo = 30, player_current_health = 40)
                        self.current_level_whatever = "custom"
                        self.state = "main_game"
                    if back_button.checkForInput(pygame.mouse.get_pos()):
                        self.draw_options = False
                    if quit_button.checkForInput(pygame.mouse.get_pos()):
                        self.state = "custom_screen"
                else:
                    if options_button.checkForInput(pygame.mouse.get_pos()):
                        self.draw_options = True

                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.start_cell_x = mouse_x // tile_size
                self.start_cell_y = mouse_y // tile_size

                if 0 <= self.start_cell_x < level_width and 0 <= self.start_cell_y < level_height:
                    self.level[self.start_cell_y][self.start_cell_x] = self.selected_color
                self.dragging = True

            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    current_cell_x = mouse_x // tile_size
                    current_cell_y = mouse_y // tile_size

                    if 0 <= current_cell_x < level_width and 0 <= current_cell_y < level_height:
                        min_cell_x = min(self.start_cell_x, current_cell_x)
                        max_cell_x = max(self.start_cell_x, current_cell_x)
                        min_cell_y = min(self.start_cell_y, current_cell_y)
                        max_cell_y = max(self.start_cell_y, current_cell_y)

                        for row in range(min_cell_y, max_cell_y + 1):
                            for col in range(min_cell_x, max_cell_x + 1):
                                self.level[row][col] = self.selected_color
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_2: self.selected_color = "2"
                elif event.key == pygame.K_1: self.selected_color = "1"
                elif event.key == pygame.K_3: self.selected_color = "3"
                elif event.key == pygame.K_4: self.selected_color = "4"
                elif event.key == pygame.K_5: self.selected_color = "5"
                elif event.key == pygame.K_6: self.selected_color = "6"
                elif event.key == pygame.K_7: self.selected_color = "7"
                elif event.key == pygame.K_8: self.selected_color = "8"
                elif event.key == pygame.K_9: self.selected_color = "9"
                elif event.key == pygame.K_0: self.selected_color = "0"
                elif event.key == pygame.K_h: self.selected_color = "13"
                elif event.key == pygame.K_d: self.selected_color = "11"
                elif event.key == pygame.K_z: self.selected_color = "12"
                elif event.key == pygame.K_c: self.selected_color = "14"
                elif event.key == pygame.K_i: self.selected_color = "15" 
                elif event.key == pygame.K_j: self.selected_color = "16"       
                elif event.key == pygame.K_f: self.selected_color = "17"       

        for row in range(level_height):
            for col in range(level_width):
                x = col * tile_size
                y = row * tile_size
                if self.level[row][col] == "1":
                    window.blit(pygame.image.load(os.path.join("assets/start_flag.png")), (x, y - tile_size))
                elif self.level[row][col] == "2":
                    window.blit(pygame.transform.scale(pygame.image.load(os.path.join("assets/spike_ball.png")), (20,20)), (x, y))
                elif self.level[row][col] == "3":
                    block = Block(x, y, tile_size, tile_size, self.level[row][col])
                    window.blit(block.image, (x, y))
                elif self.level[row][col] == "4" or self.level[row][col] == "15" or self.level[row][col] == "16":
                    block = Block(x, y, tile_size, tile_size, self.level[row][col])
                    window.blit(block.image, (x, y))
                elif self.level[row][col] == "5":
                    window.blit(pygame.image.load(os.path.join("assets/wooden_crate.png")), (x, y))
                elif self.level[row][col] == "6":
                    window.blit(pygame.image.load(os.path.join("assets/arrow_r.png")), (x, y))
                elif self.level[row][col] == "7":
                    window.blit(pygame.image.load(os.path.join("assets/arrow_l.png")), (x, y))
                elif self.level[row][col] == "8":
                    window.blit(pygame.image.load(os.path.join("assets/arrow_u.png")), (x, y))
                elif self.level[row][col] == "9":
                    window.blit(pygame.image.load(os.path.join("assets/arrow_d.png")), (x, y))
                elif self.level[row][col] == "13":
                    window.blit(pygame.image.load(os.path.join("assets/mystery_box.png")), (x, y))
                elif self.level[row][col] == "11":
                    window.blit(pygame.image.load(os.path.join("assets/jump_potion.png")), (x, y))
                elif self.level[row][col] == "12":
                    window.blit(pygame.image.load(os.path.join("assets/health_potion.png")), (x, y))

                elif self.level[row][col] == "14":
                    window.blit(pygame.image.load(os.path.join("assets/mushroom.png")), (x, y))
                elif self.level[row][col] == "17":
                    window.blit(pygame.image.load(os.path.join("assets/finish_flag.png")), (x, y - tile_size))

                elif self.level[row][col] == "0":
                    image = pygame.Surface((tile_size, tile_size))
                    image.fill((255,255,255))
                    rect = image.get_rect()
                    rect.x = x 
                    rect.y = y   
        
        if self.draw_options:
            save_button.changeColor(pygame.mouse.get_pos())
            save_button.update(window)
            play_button.changeColor(pygame.mouse.get_pos())
            play_button.update(window)
            quit_button.changeColor(pygame.mouse.get_pos())
            quit_button.update(window)
            back_button.changeColor(pygame.mouse.get_pos())
            back_button.update(window)
        else:
            options_button.changeColor(pygame.mouse.get_pos())
            options_button.update(window)


if (__name__ == "__main__"):
    pygame.init()
    
    pygame.display.set_caption(f"HELIUM KRIPTON the Game of Survival in a Geometric World.")
    clock = pygame.time.Clock()
    window = pygame.display.set_mode( window_size, pygame.RESIZABLE )    

    game_state = GameState()
    
    while game_state.running:
        game_state.state_manager()

        # Delay framerate
        clock.tick(FPS)
        
        # Update the screen
        pygame.display.update()

    pygame.quit()