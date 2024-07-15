import pygame, os, random, math, pickle

from button import Button
from manager import SaveLoadSystem
from player import Player
from enemy import Enemy
from items import ItemBar, HealthBar, ItemForBarDisplay, Item, WoodenCrate
from blocks import MovingBlock, ShooterBox, Mushrooms, Block

from config import window_size, window_width, window_height, FPS, tile_size, level_width, level_height, GAME_OVER_EVENT, LEVEL_FINISHED, PARTICLE_EVENT

pygame.time.set_timer(PARTICLE_EVENT, 50)
saveloadmanager = SaveLoadSystem(".save", "save_data")            

class Level( object ):
    def __init__(self, loaded, world_shift_x, player_start, current_level_number, mysterybox_coordinates, woodencrate_coordinates, potion1_coordinates, potion2_coordinates, player_kill_ammount, player_current_ammo , player_current_health):
        self.loaded = loaded
        self.current_level_number = current_level_number
        level_data = open(f"save_data/level_{current_level_number}.save", "rb")
        self.level = pickle.load(level_data)

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

        self.health_bar = HealthBar(self.player_object)
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
    
    def update(self, events, window):
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
        self.player_object.update(self.player_collide_list, self.potion1_list, self.potion2_list, self.ammo_list, events, window)
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
        self.health_bar.draw(self.player_object, window)
        self.item_bar.draw(window)
        self.bullet_list.add(self.player_object.bullet_list)
        self.bullet_list.draw(window)        
        self.moving_enemies.draw(window)
        self.laser_shooter_group.draw(window)
        self.moving_blocks.draw(window)
        self.player_object.particles.emit(window) 
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
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                if self.current_level_whatever != "custom":
                    self.current_level.mysterybox_coordinates = [item.rect.topleft for item in self.current_level.mystery_box_list]
                    self.current_level.woodencrate_coordinates = [item.rect.topleft for item in self.current_level.wooden_crate_list]
                    self.current_level.potion1_coordinates = [item.rect.topleft for item in self.current_level.potion1_list]
                    self.current_level.potion2_coordinates = [item.rect.topleft for item in self.current_level.potion2_list]

                    print(f'SAVED max_achieved_level_number {self.max_achieved_level_number}')
                    print(f'SAVED current_level_number {self.current_level_number}')

                    self.saveGameProgress()

                self.running = False
                return

            if event.type == GAME_OVER_EVENT:
                self.state = "game_over_screen"
            elif event.type == LEVEL_FINISHED:
                self.state = "next_level_screen"
            elif event.type == PARTICLE_EVENT:
                self.current_level.player_object.particle_animation()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and self.current_level.item_bar.selected_index != self.current_level.item_bar.max_item_index - 1:
                    self.current_level.item_bar.selected_index += 1
                if event.key == pygame.K_LEFT and self.current_level.item_bar.selected_index != 0:
                    self.current_level.item_bar.selected_index -= 1

            self.current_level.player_object.bullet_shoot(event)

        movement_events = [event for event in events if event.type in (pygame.KEYDOWN, pygame.KEYUP)]
        self.current_level.player_object.update(self.current_level.player_collide_list, self.current_level.potion1_list, self.current_level.potion2_list, self.current_level.ammo_list, movement_events, window)

        self.current_level.update(events, window)

        self.current_level.draw(window)

        fps = int(clock.get_fps())
        pygame.display.set_caption(f"HELIUM KRIPTON the Game of Survival in a Geometric World. FPS is {fps}")
        pygame.display.update()


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
    window = pygame.display.set_mode(window_size, pygame.RESIZABLE )    

    game_state = GameState()
    
    while game_state.running:
        game_state.state_manager()

        # Delay framerate
        clock.tick(FPS)
        
        # Update the screen
        pygame.display.update()

    pygame.quit()