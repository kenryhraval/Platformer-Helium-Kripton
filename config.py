import pygame

# Window dimensions
window_width = 640
window_height = 480
window_size = (window_width, window_height)

# FPS (Frames per second)
FPS = 60

# Custom events
GAME_OVER_EVENT = pygame.USEREVENT + 1
LEVEL_FINISHED = pygame.USEREVENT + 2
PARTICLE_EVENT = pygame.USEREVENT + 3

# Tile size and level dimensions
tile_size = 20
level_width = 2000 // tile_size
level_height = 480 // tile_size