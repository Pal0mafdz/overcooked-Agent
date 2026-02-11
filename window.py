import pygame
from sys import exit
import os 

GAME_WIDTH = 950
GAME_HEIGHT = 650

#imagenes
#background = pygame.image.load("assets/ambiente01.png")
background = pygame.image.load(os.path.join("assets", "ambiente01.png"))

pygame.init()
window = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_icon(pygame.image.load(os.path.join("assets", "icono.png")))
pygame.display.set_caption("Overcooked agent game!")

#estos son los frames
clock = pygame.time.Clock()

def draw():
    window.blit(background, (0,0))
   


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    draw()

    pygame.display.update()
    clock.tick(60)
    #son 60 frames por segundo