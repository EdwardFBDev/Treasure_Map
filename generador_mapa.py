from __future__ import annotations
import os
import random
from typing import List

# ---------- Tipos ----------
Matrix = List[List[str]]

# ---------- Creacion y utilidades de matriz ----------
def new_matrix(rows, cols, fill = ".") :
    """Crea una matriz rows x cols llena con 'fill'."""
    return [[fill for _ in range(cols)] for _ in range(rows)]

def clone_matrix(matrix):
    """Copia  de la matriz."""
    return [row[:] for row in matrix]

# ---------- Archivo <-> Matriz ----------
def read_lines(path):
    """Lee todas las lineas de un txt y las devuelve como lista de strings."""
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()

def write_lines(path, lines):
    """Escribe la lista de strings en el txt"""
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
def load_map(path):
    """Lee un mapa de un .txt y lo devuelve como matriz."""
    with open(path, "r", encoding="utf-8") as f:
        return [list(line.rstrip("\n")) for line in f]

def save_map(path, mapa) :
    """Guarda la matriz en un .txt, una fila por línea."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for fila in mapa:
            f.write("".join(fila) + "\n")

def list_maps(dir_path, ext= ".txt") :
    """Devuelve una lista de archivos de mapas en el directorio dado."""
    if not os.path.isdir(dir_path):
        return []
    return [f for f in os.listdir(dir_path) if f.endswith(ext)]


# ---------- Edición de la matriz ----------
def in_bounds(matrix, x, y):
    return 0 <= x < len(matrix) and 0 <= y < len(matrix[0])

def set_cell(matrix, x, y, ch):
    """Coloca un carácter en (x,y) si está dentro del rango."""
    if in_bounds(matrix, x, y):
        matrix[x][y] = ch


#   segmento horizonatal o vertical                                                 
def paint_segment(matrix, x1, y1, x2, y2, ch="#"):
    if x1 == x2:  # vertical (mismo x → columnas cambian)
        paso = 1 if y2 >= y1 else -1
        for y in range(y1, y2 + paso, paso):
            if in_bounds(matrix, x1, y):
                matrix[x1][y] = ch
    elif y1 == y2:  # horizontal (mismo y → filas cambian)
        paso = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + paso, paso):
            if in_bounds(matrix, x, y1):
                matrix[x][y1] = ch
    else:
        raise ValueError("Solo se permiten segmentos rectos (H o V)")



# ---------- Generación aleatoria ----------
def random_map(rows, cols, density= 0.15, ensure_treasure = True):
    
    random_map = new_matrix(rows, cols, ".")
    for i in range(rows):
        for j in range(cols):
            random_map[i][j] = "#" if random.random() < density else "."
    if ensure_treasure:
        tx, ty = random.randrange(rows), random.randrange(cols)
        random_map[tx][ty] = "T"
    return random_map



