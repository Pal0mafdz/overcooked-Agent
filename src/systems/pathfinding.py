from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement


class Pathfinder:
    def __init__(self, matrix: list[list[int]]):
        self.grid = Grid(matrix=matrix)
        self.finder = AStarFinder(diagonal_movement=DiagonalMovement.never)

    def set_matrix(self, matrix: list[list[int]]):
        self.grid = Grid(matrix=matrix)

    def obtener_ruta(self, start_pos: list[int] | tuple[int, int], end_pos: tuple[int, int]) -> list[tuple[int, int]]:
        self.grid.cleanup()
        sx, sy = start_pos
        start_node = self.grid.node(sx, sy)
        end_node = self.grid.node(end_pos[0], end_pos[1])
        path, _ = self.finder.find_path(start_node, end_node, self.grid)
        return [(n.x, n.y) for n in path][1:]
