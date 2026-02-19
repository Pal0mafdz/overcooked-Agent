import pygame
import sys
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement

TAM_CELDA = 64
ANCHO_GRID = 17
ALTO_GRID = 11

# Colores
COLOR_SUELO = (139, 115, 85)     # Café (Suelo)
COLOR_MURO = (50, 50, 50)        # Gris Oscuro (Paredes)
COLOR_REJILLA = (80, 80, 80)     # Gris guía
COLOR_RUTA = (100, 200, 100)     # Verde (Camino A*)
COLOR_CHEF = (255, 63, 63)       # Azul (Representación del Chef)

# --- MATRIZ DE LA COCINA (17x11) ---
# 1 = Caminable, 0 = Obstáculo
mapa_cocinas_chef = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

# --- INICIALIZACIÓN ---
pygame.init()
ventana = pygame.display.set_mode((ANCHO_GRID * TAM_CELDA, ALTO_GRID * TAM_CELDA))
pygame.display.set_caption("Overcooked 2D")
reloj = pygame.time.Clock()

# Preparar Pathfinding
grid = Grid(matrix=mapa_cocinas_chef)
finder = AStarFinder(diagonal_movement=DiagonalMovement.never)

# Estado inicial del Agente
chef_pos = [1, 3] # Columna, Fila
ruta_dibujable = []

def obtener_ruta(start_pos, end_pos):
    grid.cleanup()
    start_node = grid.node(start_pos[0], start_pos[1])
    end_node = grid.node(end_pos[0], end_pos[1])
    path, _ = finder.find_path(start_node, end_node, grid)
    return [(n.x, n.y) for n in path]

# --- BUCLE PRINCIPAL ---
ejecutando = True
while ejecutando:
    
    # 1. EVENTOS
    for evento in pygame.event.get():
        if evento.type == pygame.KEYDOWN:
            ejecutando = False
            
        if evento.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            cx, cy = mx // TAM_CELDA, my // TAM_CELDA
            
            # Validar que el clic esté dentro de la matriz
            if 0 <= cx < ANCHO_GRID and 0 <= cy < ALTO_GRID:
                if mapa_cocinas_chef[cy][cx] == 1:
                    if evento.button == 3: # CLICK IZQUIERDO: Trazar ruta
                        ruta_dibujable = obtener_ruta(chef_pos, (cx, cy))
                        
                    elif evento.button == 1: # CLICK DERECHO: Mover Chef
                        chef_pos = [cx, cy]
                        ruta_dibujable = [] # Limpiamos ruta al teletransportar
                else:
                    print("Posición no válida (Obstáculo)")

    # 2. DIBUJO
    ventana.fill((0, 0, 0))

    # Dibujar Escenario
    for fila in range(ALTO_GRID):
        for col in range(ANCHO_GRID):
            x, y = col * TAM_CELDA, fila * TAM_CELDA
            
            # Color según matriz
            color_celda = COLOR_SUELO if mapa_cocinas_chef[fila][col] == 1 else COLOR_MURO
            pygame.draw.rect(ventana, color_celda, (x, y, TAM_CELDA, TAM_CELDA))
            
            # Guía visual (rejilla)
            pygame.draw.rect(ventana, COLOR_REJILLA, (x, y, TAM_CELDA, TAM_CELDA), 3)

    # Dibujar la ruta (si existe)
    for (rx, ry) in ruta_dibujable:
        # Dibujamos un cuadro pequeño centrado en la celda
        pygame.draw.rect(ventana, COLOR_RUTA, (rx * TAM_CELDA + 2, ry * TAM_CELDA + 2, 60, 60))

    # Dibujar al Chef (Representado por un círculo por ahora)
    centro_chef = (chef_pos[0] * TAM_CELDA + TAM_CELDA // 2, 
                   chef_pos[1] * TAM_CELDA + TAM_CELDA // 2)
    pygame.draw.circle(ventana, COLOR_CHEF, centro_chef, 22)


    # 3. ACTUALIZACIÓN
    pygame.display.flip()
    reloj.tick(60)

pygame.quit()
sys.exit()