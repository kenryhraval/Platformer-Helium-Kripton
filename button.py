import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800,800))
pygame.display.set_caption("Button")
main_font = pygame.font.SysFont("Paradox King Script", 36)

class Button():
    def __init__(self, image, pos, text_input):
        self.image = image
        self.x_pos = pos[0]
        self.y_pos = pos[1]
        self.font = pygame.font.SysFont("Paradox King Script", 30)
        self.base_color, self.hovering_color = (100,100,100), (0,0,0)
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.text_input = text_input
        self.text = main_font.render(self.text_input, True, self.base_color)
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))
        if self.image is None:
            self.image = self.text
    def update(self, screen):
        if self.image is not None:    
            screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

    def checkForInput(self, position):
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            return True
        else: return False

    def changeColor(self, position):
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            self.text = main_font.render(self.text_input, True, self.hovering_color)
        else:
            self.text = main_font.render(self.text_input, True, self.base_color)

# button_surface = pygame.image.load("button.png")
# button_surface = pygame.transform.scale(button_surface, (250,50))

# button = Button(button_surface, (400, 300), "LOAD GAME")

# while True:
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             sys.exit()
#         if event.type == pygame.MOUSEBUTTONDOWN:
#             button.checkForInput(pygame.mouse.get_pos())

#     screen.fill((200,200,200))
#     button.update()
#     button.changeColor(pygame.mouse.get_pos())

#     pygame.display.update()