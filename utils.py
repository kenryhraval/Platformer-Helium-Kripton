import pygame

def create_overlay(window, color, transparency):
    overlay = pygame.Surface(window.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, transparency))
    return overlay