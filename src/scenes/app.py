import pygame
import sys
from config import ANCHO_GRID, ALTO_GRID, TAM_CELDA
from src.scenes.game_scene import GameScene

def run_app(ordenes: int):
    pygame.init()
    
    ventana = pygame.display.set_mode((ANCHO_GRID * TAM_CELDA, ALTO_GRID * TAM_CELDA))
    pygame.display.set_caption("Agente Inteligente - Overcooked")
    
    try:
        icono = pygame.image.load("assets/icono_overcooked.png")
        pygame.display.set_icon(icono)
    except:
        pass
        
    reloj = pygame.time.Clock()
    
    juego_activo = True
    while juego_activo:
        escena = GameScene(ventana, reloj, ordenes)
        juego_activo = escena.run()
        
    pygame.quit()
    sys.exit()