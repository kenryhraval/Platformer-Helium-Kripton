import pygame, math, random

from items import ItemBar, HealthBar, ItemForBarDisplay, Item, WoodenCrate
from particles import Particles
from utils import create_overlay
from bullets import Bullet

from config import window_size, window_width, window_height, FPS, tile_size, level_width, level_height, GAME_OVER_EVENT, LEVEL_FINISHED, PARTICLE_EVENT
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

    def update(self, player_collide_list, potion1_list, potion2_list, ammo_list, events, window):
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
                self.overlay = create_overlay(window, (127, 0, 200), 100)
            else:
                self.jump_boost = 0
                self.double_jump = 1
                self.overlay = None

            self.experience_gravity()
            self.collision_detection(player_collide_list, potion1_list, potion2_list, ammo_list)
            self.moving(events)

            if self.direction.x < 0 and self.action != "wall":
                self.change_action("run")
                self.flip = True
            elif self.direction.x > 0 and self.action != "wall":
                self.change_action("run")
                self.flip = False
            elif self.direction.x == 0:
                self.change_action("idle")

            if self.on_ground and (self.direction.y < 0) or (self.direction.y > 1):
                self.on_ground = False
            if self.on_ceiling and self.direction.y > 0:
                self.on_ceiling = False

            if self.on_left and (self.rect.left < self.current_x) or (self.direction.x >= 0):
                self.on_left = False
            if self.on_right and (self.rect.right > self.current_x) or (self.direction.x <= 0):
                self.on_right = False

            if self.on_platform and (self.direction.y != 0):
                self.on_platform = False

            if self.on_ground and self.on_right:
                self.rect = self.image.get_rect(bottomright = self.rect.bottomright)
            elif self.on_ground and self.on_left:
                self.rect = self.image.get_rect(bottomleft = self.rect.bottomleft)
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
            self.change_action("finished")
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

    def moving(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    self.direction.x = -self.speed
                elif event.key == pygame.K_d:
                    self.direction.x = self.speed
                elif event.key == pygame.K_w:
                    if self.jumps_left > 0:
                        self.direction.y = -2 * self.speed - self.jump_boost
                        self.jumps_left -= 1
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a and self.direction.x < 0:
                    self.direction.x = 0
                elif event.key == pygame.K_d and self.direction.x > 0:
                    self.direction.x = 0

    
    def experience_gravity(self, gravity = .35):
        if (self.direction.y == 0): self.direction.y = 1
        else: self.direction.y += gravity
        