import pygame, random

from config import window_size, window_width, window_height, FPS, tile_size, level_width, level_height, GAME_OVER_EVENT, LEVEL_FINISHED, PARTICLE_EVENT
class Particles:
    def __init__(self):
        self.particles = []

    def emit(self, window):
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
                pygame.draw.circle(window, (255, 255, 255), (int(particle[0][0]), int(particle[0][1])), int(particle[1]))

    def add_particles(self, x, y, direction):
        radius = 5
        particle_circle = [[x, y], radius, [-direction.x, -direction.y]]
        self.particles.append(particle_circle)

    def delete_particles(self):
        self.particles = [particle for particle in self.particles if particle[1] > 0.05]
