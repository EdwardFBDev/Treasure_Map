from __future__ import annotations
from typing import List, Tuple, Generator

try:
    from generador_mapa import clone_matrix, load_map , in_bounds 
except ImportError:
    clone_matrix = lambda m: [row[:] for row in m]  # fallback simple
    def load_map(path: str):
        with open(path, "r", encoding="utf-8") as f:
            return [list(line.strip()) for line in f]

Matrix = List[List[str]]

WALL      = "#"
EMPTY     = "."
TREASURE  = "T"
PATH_MARK = "*"

# Funcion principal 

def search_treasure(mapa, start_x, start_y):
    rows, cols = len(mapa), len(mapa[0])
    isVisited = [[False]*cols for _ in range(rows)]                         #-->> 	marca celdas ya exploradas
    memo      = [[False]*cols for _ in range(rows)]                         #-->>   “memorización” / caching:
    result    = clone_matrix(mapa)

    found = _resolver_backtracking(mapa, start_x, start_y, isVisited, memo, result)
    return found, result


def _resolver_backtracking(matrix, x, y, vis, memo, res) :
    rows, cols = len(matrix), len(matrix[0])

    # Fuera de rango
    if x < 0 or y < 0 or x >= rows or y >= cols:
        return False

    # Obstáculo o visitado
    if matrix[x][y] == WALL or vis[x][y]:
        return False

    # Ya sabemos que no hay solución desde aquí
    if memo[x][y]:
        return False

    # Tesoro encontrado
    if matrix[x][y] == TREASURE:
        res[x][y] = PATH_MARK
        return True

    # Marcar visitado
    vis[x][y] = True

    # Explorar 4 direcciones
    if (_resolver_backtracking(matrix, x-1, y, vis, memo, res) or  # -->> arriba
        _resolver_backtracking(matrix, x+1, y, vis, memo, res) or  # -->> abajo
        _resolver_backtracking(matrix, x, y-1, vis, memo, res) or  # -->> izquierda
        _resolver_backtracking(matrix, x, y+1, vis, memo, res)):   # -->> derecha
        res[x][y] = PATH_MARK
        return True

    # No hay solución desde aquí
    memo[x][y] = True
    return False


# ------------------------------------------------------------
# Versión para animación: genera pasos
# ------------------------------------------------------------
def search_with_steps(mapa, x, y):
    rows, cols = len(mapa), len(mapa[0])
    visited = [[False]*cols for _ in range(rows)]

    def backtrack(cx, cy):
        if not in_bounds(mapa, cx, cy): return
        if mapa[cx][cy] == "#" or visited[cx][cy]: return
        visited[cx][cy] = True
        yield (cx, cy, [row[:] for row in mapa])

        if mapa[cx][cy] == "T":
            mapa[cx][cy] = "*"
            yield True
            return

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            for step in backtrack(cx + dx, cy + dy):
                yield step
                if step is True:
                    mapa[cx][cy] = "*"
                    yield (cx, cy, [row[:] for row in mapa])
                    return

    yield from backtrack(x, y)



# ------------------------------------------------------------
# Utilidades archivo error
# ------------------------------------------------------------
def escribir_error_no_solucion(path, x, y):
    """Crea/reescribe un archivo con el mensaje de mapa sin solución."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Error: mapa sin solución iniciando en la coordenada x={x}, y={y}\n")