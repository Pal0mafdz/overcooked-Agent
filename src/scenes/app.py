import pygame

from config import TAM_CELDA, ANCHO_GRID, ALTO_GRID
from src.scenes.game_scene import GameScene


def run_app(ordenes: int):
    pygame.init()
    ventana = pygame.display.set_mode((ANCHO_GRID * TAM_CELDA, ALTO_GRID * TAM_CELDA))
    pygame.display.set_caption("Agente Inteligente - Presiona 'R' para reiniciar")
    reloj = pygame.time.Clock()

    juego_activo = True
    while juego_activo:
        escena = GameScene(ventana, reloj, ordenes=ordenes)
        juego_activo = escena.run()

    pygame.quit()
