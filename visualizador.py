import sys
import os
import pygame
import random
import time

# ---------- IMPORTAR LÓGICA ----------
from generador_mapa import (
    new_matrix, clone_matrix, load_map, save_map, list_maps,
    set_cell, paint_segment, random_map,
)
from buscador_tesoros import (
    search_treasure, search_with_steps, escribir_error_no_solucion
)

# ============================================================
# ---------- PANEL CONFIGURACIONES GLOBAL ----------
# ============================================================
WIDTH, HEIGHT = 900, 700                                                                # Dimensiones de la ventana
MIN_SIZE, MAX_SIZE = 15, 25                                                             # Tamaño mínimo Y máximo 

START_CHAR  = '@'                                                                       # inicial del explorador
STEP_DELAY   = 500                                                                     # ms entre pasos animados

FPS = 60

# ============================================================
# ---------- RUTAS CONST DE ARCHIVOS ----------
# ============================================================

# Ruta base del proyecto
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
# Ruta a la carpeta de imágenes
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Ruta de las imagenes intro, menu, sgn intro
IMG_INTRO  = os.path.join(ASSETS_DIR, "images", "Logo_intro.png")   # img intro
IMG_MENU   = os.path.join(ASSETS_DIR, "images", "Portada_menu.png") # img intro
SND_INTRO  = os.path.join(ASSETS_DIR, "audio",  "8bits_Davy_Jones.wav")        # sng intro

# crea la carpeta "MAPS" y evitga error 
MAPS_DIR   = os.path.join(BASE_DIR, "MAPS")     
os.makedirs(MAPS_DIR, exist_ok=True)

# Crea la subcarpeta "MAPS_Animate" y evota error
ANIM_DIR   = os.path.join(MAPS_DIR, "MAPS_Animate")
os.makedirs(ANIM_DIR, exist_ok=True)


# ============================================================
# ---------- PALETA ----------
# ============================================================
PALETTE = {
    "bg":           (18, 26, 34),     # azul marino muy oscuro
    "panel":        (40, 48, 56),     # gris petróleo oscuro
    "grid":         (80, 90, 100),    # gris pizarra
    "empty":        (240, 240, 240),  # gris casi blanco
    "wall":         (55, 55, 55),     # gris grafito
    "treasure":     (255, 215, 0),    # dorado / oro vibrante
    "accent":       (0, 200, 120),    # verde menta / turquesa
    "text":         (230, 230, 230),  # gris claro (texto)
    "dorado":       (239, 184, 16),   # dorado clásico
    "negro":        (0, 0, 0),        # negro puro
    "gris_claro":   (120, 120, 120),  # gris medio
    "START_COLOR":  (0, 255, 0),      # verde brillante (inicio @)
    "HILITE_COLOR": (255, 0, 0)       # rojo puro (resalte)
}


# ============================================================
#  ---------- WIDGETS BÁSICOS ----------
# ============================================================

class Button:
    def __init__(self, rect, text, font, callback):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.hover = False

    def draw(self, screen):
        col = PALETTE["accent"] if self.hover else PALETTE["panel"]
        pygame.draw.rect(screen, col, self.rect, border_radius=6)
        pygame.draw.rect(screen, PALETTE["negro"], self.rect, 2, border_radius=6)
        txt = self.font.render(self.text, True, PALETTE["text"])
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(e.pos)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            return self.callback()


class InputBox:
    """Caja de texto simple."""
    def __init__(self, rect, font, text=""):
        self.rect   = pygame.Rect(rect)
        self.font   = font
        self.text   = text
        self.active = False
        self.color_inactive = PALETTE["gris_claro"]
        self.color_active   = PALETTE["accent"]
        self.txt_surface    = font.render(text, True, PALETTE["text"])

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = self.font.render(self.text, True, PALETTE["text"])

    def draw(self, screen):
        pygame.draw.rect(screen, self.color_active if self.active else self.color_inactive,
                         self.rect, 2, border_radius=4)
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))

    def get_value(self):
        return self.text.strip()


class OptionBox:
    """Selector de opciones (#/T, V/H). Click para cambiar."""
    def __init__(self, rect, font, options, index=0):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.options = options
        self.index = index
        self.hover = False

    def current(self):
        return self.options[self.index]

    def draw(self, screen):
        col = PALETTE["accent"] if self.hover else PALETTE["panel"]
        pygame.draw.rect(screen, col, self.rect, border_radius=4)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=4)
        txt = self.font.render(self.current(), True, PALETTE["text"])
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(e.pos)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            self.index = (self.index + 1) % len(self.options)


# ============================================================
#  ----------DIBUJOS Y UTILIDADES DE UI----------
# ============================================================

def draw_map_preview(screen, mapa, top_left, cell=20):
    """Dibuja el mapa prewiew"""
    x0, y0 = top_left
    rows, cols = len(mapa), len(mapa[0])
    for i in range(rows):
        for j in range(cols):
            ch = mapa[i][j]
            if ch == '.':
                color = PALETTE["empty"]
            elif ch == '#':
                color = PALETTE["wall"]
            elif ch == 'T':
                color = PALETTE["treasure"]
            elif ch == '*':
                color = (0, 180, 255)      # camino
            elif ch == START_CHAR:
                color = PALETTE["START_COLOR"]        # inicio / tesoro final
            else:
                color = (200, 200, 200)
            pygame.draw.rect(screen, color, (x0 + j*cell, y0 + i*cell, cell, cell))
            pygame.draw.rect(screen, PALETTE["grid"],  (x0 + j*cell, y0 + i*cell, cell, cell), 1)


def calc_preview_origin(rows, cols, cell, left, right, top, bottom):
    """Centra el mapa dentro del rectángulo disponible"""
    avail_w = right - left
    avail_h = bottom - top
    map_w   = cols * cell
    map_h   = rows * cell
    x = left + max((avail_w - map_w) // 2, 0)
    y = top  + max((avail_h - map_h) // 2, 0)
    return x, y

def draw_centered(surface, screen):
    rect = surface.get_rect(center=screen.get_rect().center)
    screen.blit(surface, rect)

def fade_in(surface, screen, duration_ms=2000):
    clock = pygame.time.Clock()
    start = pygame.time.get_ticks()
    overlay = pygame.Surface(screen.get_size())
    overlay.fill(PALETTE["negro"])

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                return False  # skip

        elapsed = pygame.time.get_ticks() - start
        alpha   = max(255 - int(255 * (elapsed / duration_ms)), 0)

        screen.fill(PALETTE["negro"])
        draw_centered(surface, screen)
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))
        pygame.display.flip()

        if alpha == 0:
            return True
        clock.tick(FPS)

# ============================================================
#  ---------- ARCHIVOS *_Solved.txt ----------
# ============================================================

def list_solved_maps(folder = ANIM_DIR):
    "para ver la lista de mapas resueltos"
    return [f for f in os.listdir(folder) if f.endswith("_Solved.txt")]

def save_steps_file(base_name, steps, final_map, folder= ANIM_DIR):
    name = os.path.splitext(base_name)[0] + "_Solved.txt"
    path = os.path.join(folder, name)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write("#STEPS\n")
        for (x, y) in steps:
            f.write(f"{x},{y}\n")
        f.write("#MAP\n")
        for row in final_map:
            f.write("".join(row) + "\n")
    return path

def load_steps_file(path):
    steps = []
    final_map = []
    with open(path, "r", encoding="utf-8") as f:
        mode = None
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line == "#STEPS":
                mode = "steps"; continue
            if line == "#MAP":
                mode = "map"; continue
            if mode == "steps":
                x_str, y_str = line.split(",")
                steps.append((int(x_str), int(y_str)))
            elif mode == "map":
                final_map.append(list(line))
    return steps, final_map

# ============================================================
#  ---------- LAYOUT CONFIG – COORDINATES ----------
# ============================================================

LAYOUT = {
    # Medidas del PANEL IZQUIERDO (donde van los inputs y botones)
    "panel": {
        "x": 20,                  # margen izquierdo de todo el panel
        "y": 20,                  # margen superior
        "w": 300,                 # ancho fijo del panel
        "h": HEIGHT - 30          # alto → casi toda la ventana
    },

    # Parámetros generales de la cuadrícula de preview
    "cell": 22,                   # tamaño del lado de cada celda (px)
    "preview_margin": 20,         # separación panel <<-->>  preview (derecha)


    # Columnas dentro del panel  (coordenada X para cada tipo de widget)
    "col": {
        "lbl":  40,               # columna de las etiquetas de texto
        "inp1": 70,               # primera columna de InputBox   (X)
        "inp2": 160,              # segunda  columna de InputBox  (Y)
        "opt":  230               # columna de OptionBox / dropdown
    },

    # Filas (coordenada Y) donde empieza cada “bloque” de opciones
    "row": {
        "size":     60,           # • Sección  tamaño del mapa
        "obj":      155,          # • Sección  ingresar objeto   (# / T)
        "range":    250,          # • Sección  rango de obstáculos
        "rand":     340,          # • Botón    random generator
        "name":     385,          # • Input    nombre del mapa
        "list":     450,          # • Lista    mapas disponibles
        "buttons":  630           # • Botones  Volver / OK
    },

    # Tamaño estándar para los Button del panel
    "btn": {
        "w": 120,                 # ancho del botón
        "h": 32                   # alto  del botón
    }
}


# ============================================================
#  ---------- PANTALLAS ----------
# ============================================================

def intro_screen(screen):
    """Intro con transicion lenta  + audio// bucar 8 bits."""
    try:
        img = pygame.image.load(IMG_INTRO).convert()
        img = pygame.transform.smoothscale(img, (int(WIDTH-25), int(HEIGHT-25)))
    except Exception:
        img = pygame.Surface(screen.get_size()); img.fill(PALETTE["negro"])
    try:
        pygame.mixer.music.load(SND_INTRO)
        pygame.mixer.music.play()
    except Exception:
        pass # para que no falle si no se encuentra el sng o si lo eliminan. 
    fade_in(img, screen, duration_ms=3000) # coordinarlo con la musica


def menu_screen(screen):
    """Menú principal."""
    font_title = pygame.font.SysFont("Georgia", 55, True)
    font_opt   = pygame.font.SysFont("Georgia", 25)

    opts = [
        "1- Generar / Editar Mapa",
        "2- Buscar Tesoro",
        "3- Salir"
    ]
    try:
        bg = pygame.image.load(IMG_MENU).convert()
        bg = pygame.transform.smoothscale(bg, (int(WIDTH-25), int(HEIGHT-25)))
    except Exception:
        bg = pygame.Surface(screen.get_size()); bg.fill(PALETTE["bg"])

    clock = pygame.time.Clock()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_1: return 1
                if e.key == pygame.K_2: return 2
                if e.key == pygame.K_3: return 3

        screen.fill(PALETTE["bg"])
        draw_centered(bg, screen)

        title_surf = font_title.render("TREASURE MAP", True, PALETTE["dorado"])
        screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 40))

        x = WIDTH//2.5 - 260
        y = HEIGHT//2 - 20
        for i, txt in enumerate(opts):
            surf = font_opt.render(txt, True, (255,255,255))
            screen.blit(surf, (x, y + i*50))

        pygame.display.flip()
        clock.tick(FPS)


def generator_screen(screen):
    """GUI Map Generator (UI)"""
    clock      = pygame.time.Clock()
    font_title = pygame.font.SysFont("consolas", 22)
    font_txt   = pygame.font.SysFont("consolas", 18)

    # Estado
    rows, cols = 15, 15
    mapa = new_matrix(rows, cols, '.')

    # Alias layout
    PX, PY = LAYOUT["panel"]["x"], LAYOUT["panel"]["y"]
    PW, PH = LAYOUT["panel"]["w"], LAYOUT["panel"]["h"]
    CELL   = LAYOUT["cell"]

    prev_left  = PX + PW + LAYOUT["preview_margin"]
    prev_right = WIDTH - 20
    prev_top   = 60
    prev_bot   = HEIGHT - 40

    # Inputs TAM
    inp_rows = InputBox((LAYOUT["col"]["inp1"], PY + LAYOUT["row"]["size"] + 10, 50, 28), font_txt, "")
    inp_cols = InputBox((LAYOUT["col"]["inp2"], PY + LAYOUT["row"]["size"] + 10, 50, 28), font_txt, "")
    
    # OBJ 
    inp_y    = InputBox((LAYOUT["col"]["inp1"], PY + LAYOUT["row"]["obj"] + 10, 50, 28), font_txt, "")
    inp_x    = InputBox((LAYOUT["col"]["inp2"], PY + LAYOUT["row"]["obj"] + 10, 50, 28), font_txt, "")
    opt_obj  = OptionBox((LAYOUT["col"]["opt"],  PY + LAYOUT["row"]["obj"] + 10, 50, 28), font_txt, ["#", "T"], 0)
    
    # rango
    inp_xy1 = InputBox((LAYOUT["col"]["inp1"] + 70, PY + LAYOUT["row"]["range"] + 10, 70, 28), font_txt, "")
    inp_xy2 = InputBox((LAYOUT["col"]["inp1"] + 70, PY + LAYOUT["row"]["range"] + 50, 70, 28), font_txt, "")
    
    # name
    inp_name = InputBox((LAYOUT["col"]["lbl"] + 100, PY + LAYOUT["row"]["name"] - 5, 160, 28), font_txt, "")

    # Lista mapas
    maps_list = list_maps(MAPS_DIR)
    selected_map_idx = -1
    list_rect = pygame.Rect(LAYOUT["col"]["lbl"], PY + LAYOUT["row"]["list"] + 15, PW - 40, 150)

    def parse_coord(texto):
        """
        Convierte un string 'x,y' o '(x,y)' en una tupla (x, y).
        """
        texto = texto.strip().replace("(", "").replace(")", "")
        partes = texto.split(",")
        if len(partes) != 2:
            raise ValueError("Formato inválido")
        return int(partes[0]), int(partes[1])
    
    def refresh_list():
        nonlocal maps_list
        maps_list = list_maps(MAPS_DIR)
    # Callbacks
    def apply_size():
        nonlocal rows, cols, mapa
        try:
            r = int(inp_rows.get_value())
            c = int(inp_cols.get_value())
            if MIN_SIZE <= r <= MAX_SIZE and MIN_SIZE <= c <= MAX_SIZE:
                rows, cols = r, c
                mapa = new_matrix(rows, cols, '.')
            else:
                print(f"Tamaño invalido. Debe ser entre {MIN_SIZE} y {MAX_SIZE}")
        except ValueError:
            pass

    def add_single():
        try:
            x = int(inp_x.get_value()); y = int(inp_y.get_value())
            ch = opt_obj.current()
            set_cell(mapa, x, y, ch)
        except ValueError:
            pass

    def add_range():
        try:
            x1, y1 = parse_coord(inp_xy1.get_value())
            x2, y2 = parse_coord(inp_xy2.get_value())
            paint_segment(mapa, y1, x1, y2, x2, "#")  # OJO: y=fila, x=col
        except Exception as e:
            print(f"Error: {e}")

    def random_gen():
        nonlocal mapa, rows, cols
        mapa = random_map(rows, cols, 0.15, True)

    def save_current():
        name = inp_name.get_value() or "MAPS"
        path = os.path.join(MAPS_DIR, f"{name}.txt")
        save_map(path, mapa)
        refresh_list()
        return path

    def ok_and_back():
        global CURRENT_MAP_PATH
        CURRENT_MAP_PATH = save_current()
        return "back"

    def go_back():
        return "back"

    def load_selected():
        nonlocal mapa, rows, cols, selected_map_idx
        if 0 <= selected_map_idx < len(maps_list):
            path = os.path.join(MAPS_DIR, maps_list[selected_map_idx])
            mapa = load_map(path)
            rows, cols = len(mapa), len(mapa[0])

    # Botones
    btns = []
    def add_btn(x, y, txt, cb):
        btns.append(Button((x, y, LAYOUT["btn"]["w"], LAYOUT["btn"]["h"]), txt, font_txt, cb))

    add_btn(LAYOUT["col"]["lbl"],       PY + LAYOUT["row"]["size"]  + 45, "Aplicar", apply_size)
    add_btn(LAYOUT["col"]["lbl"],       PY + LAYOUT["row"]["obj"]   + 45, "Aplicar", add_single)
    #segmento x,y
    add_btn(LAYOUT["col"]["lbl"], PY + LAYOUT["row"]["range"] + 90, "Aplicar", add_range) 

    add_btn(LAYOUT["col"]["lbl"] + 150,       PY + LAYOUT["row"]["rand"],       "Random", random_gen)
    add_btn(LAYOUT["col"]["lbl"] + 150, PY + LAYOUT["row"]["name"]  + 35, "Guardar map", save_current)
    add_btn(LAYOUT["col"]["lbl"],       PY + LAYOUT["row"]["buttons"],    "Volver menú", go_back)
    add_btn(LAYOUT["col"]["lbl"] + 150, PY + LAYOUT["row"]["buttons"],    "OK/Enter",    ok_and_back)

    last_click = 0
    DOUBLE_MS  = 350

    # Loop
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return

            # Inputs
            for inp in [inp_rows, inp_cols, inp_x, inp_y, inp_xy1, inp_xy2, inp_name]:
                inp.handle_event(e)

            # Options
            opt_obj.handle_event(e)
           
            # Botones
            for b in btns:
                ret = b.handle_event(e)
                if ret == "back":
                    return

            # Lista
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if list_rect.collidepoint(e.pos):
                    rel_y = e.pos[1] - list_rect.y
                    idx = rel_y // 24
                    if 0 <= idx < len(maps_list):
                        now = pygame.time.get_ticks()
                        if idx == selected_map_idx and (now - last_click) <= DOUBLE_MS:
                            load_selected()
                        else:
                            selected_map_idx = idx
                        last_click = now

        # Dibujo panel_izq
        screen.fill(PALETTE["bg"])
        pygame.draw.rect(screen, PALETTE["panel"], (PX, PY, PW, PH), border_radius=12)
        # Título centrado
        title = font_title.render("MAP GENERATOR", True, PALETTE["text"])
        screen.blit(title, title.get_rect(center=(PX + PW//2, PY + 30)))

        # Tamaño
        screen.blit(font_txt.render("15 <= TAM <= 25:", True, PALETTE["text"]), (LAYOUT["col"]["lbl"], PY + LAYOUT["row"]["size"] - 10))
        screen.blit(font_txt.render("X=", True, PALETTE["text"]), (LAYOUT["col"]["lbl"],      PY + LAYOUT["row"]["size"] + 15))
        screen.blit(font_txt.render("Y=", True, PALETTE["text"]), (LAYOUT["col"]["lbl"] + 90, PY + LAYOUT["row"]["size"] + 15))
        inp_rows.draw(screen); inp_cols.draw(screen)

        # Obj
        screen.blit(font_txt.render("Ingresar obj", True, PALETTE["text"]), (LAYOUT["col"]["lbl"], PY + LAYOUT["row"]["obj"]- 10))
        screen.blit(font_txt.render("X=", True, PALETTE["text"]), (LAYOUT["col"]["lbl"],      PY + LAYOUT["row"]["obj"] + 15))
        screen.blit(font_txt.render("Y=", True, PALETTE["text"]), (LAYOUT["col"]["lbl"] + 90, PY + LAYOUT["row"]["obj"] + 15))
        inp_x.draw(screen); inp_y.draw(screen); opt_obj.draw(screen)

        # Rango
        screen.blit(font_txt.render("Obstáculo rango", True, PALETTE["text"]), (LAYOUT["col"]["lbl"], PY + LAYOUT["row"]["range"]-10))
        screen.blit(font_txt.render("X= (x,y):", True, PALETTE["text"]), (LAYOUT["col"]["lbl"], PY + LAYOUT["row"]["range"] + 15))
        inp_xy1.draw(screen)

        screen.blit(font_txt.render("Y= (x,y):", True, PALETTE["text"]), (LAYOUT["col"]["lbl"], PY + LAYOUT["row"]["range"] + 55))
        inp_xy2.draw(screen)


        # Name
        screen.blit(font_txt.render("Map name:", True, PALETTE["text"]), (LAYOUT["col"]["lbl"], PY + LAYOUT["row"]["name"]))
        inp_name.draw(screen)

        # Lista
        screen.blit(font_txt.render("CARGAR MAPA", True, PALETTE["text"]),
                    (LAYOUT["col"]["lbl"], PY + LAYOUT["row"]["list"] - 25))
        pygame.draw.rect(screen, (100,100,100), list_rect, 2)
        for i, fname in enumerate(maps_list):
            col = PALETTE["accent"] if i == selected_map_idx else PALETTE["text"]
            txt = font_txt.render(fname, True, col)
            screen.blit(txt, (list_rect.x + 6, list_rect.y + i*24 + 4))

        # Botones
        for b in btns:
            b.draw(screen)

        # Preview
        px, py = calc_preview_origin(rows, cols, CELL, prev_left, prev_right, prev_top, prev_bot)
        draw_map_preview(screen, mapa, (px, py), CELL)

        pygame.display.flip()
        clock.tick(FPS)


def solver_screen(screen):
    

    #  OBJETOS BÁSICOS DE PYGAME

    clock    = pygame.time.Clock()                 # controla FPS y tiempos
    font_tit = pygame.font.SysFont("consolas", 22) # fuente títulos
    font_txt = pygame.font.SysFont("consolas", 18) # fuente texto normal


    #  ESTADO DE LA PANTALLA “RESOLVER MAPA”

    maps_list   = list_maps(MAPS_DIR)              # .txt crudos en /MAPS
    solved_list = list_solved_maps(MAPS_DIR)       # *_Solved.txt en /MAPS

    selected_map_idx    = -1  # índice del mapa crudo seleccionado
    selected_solved_idx = -1  # índice del mapa resuelto seleccionado

    mapa_original = None       # copia sin modificar, cargada de disco
    mapa_mostrado = None       # lo que se dibuja cada frame (puede cambiar)
    rows = cols = 0            # dimensiones del mapa cargado

    start_x = start_y = 0      # coordenadas de inicio que ingresa el usuario
    start_fijado = False       # True después de pulsar “Fijar inicio”

    result_map = None          # matriz final con ‘*’ si ya se resolvió
    found = None               # True/False si se halló tesoro, None sin intentar

    # ------------------ Animación EN VIVO (generator paso a paso) -----
    step_gen        = None     # generator devuelto por search_with_steps()
    last_step_time  = 0        # timestamp del último frame aplicado
    animating_live  = False    # bandera: animación en curso
    current_pos     = None     # (x,y) celda actual, para pintar borde rojo

    # ------------------ Animación DESDE ARCHIVO -----------------------
    file_steps      = []       # lista [(x1,y1), (x2,y2), …] cargada de *_Solved.txt
    file_anim_index = 0        # posición actual dentro de file_steps
    animating_file  = False    # bandera: reproduciendo archivo grabado


    #  PARAMETROS DE LAYOUT — coordenadas útiles

    PX, PY = LAYOUT["panel"]["x"], LAYOUT["panel"]["y"]   # esquina panel
    PW, PH = LAYOUT["panel"]["w"], LAYOUT["panel"]["h"]   # ancho/alto panel
    CELL   = LAYOUT["cell"]                               # tamaño de celda

    # Área disponible a la derecha para el preview del mapa
    prev_left  = PX + PW + LAYOUT["preview_margin"]       # borde izq. preview
    prev_right = WIDTH - 20                               # borde der.
    prev_top   = 60                                       # margen sup.
    prev_bot   = HEIGHT - 40                              # margen inf.


    # ----- Widgets -----
    list_rect_maps   = pygame.Rect(LAYOUT["col"]["lbl"], PY + 80,  PW - 40, 150)
    list_rect_solved = pygame.Rect(LAYOUT["col"]["lbl"], PY + 390, PW - 40, 150)

    inp_start_x = InputBox((LAYOUT["col"]["inp1"], PY + 260, 50, 28), font_txt, "0")
    inp_start_y = InputBox((LAYOUT["col"]["inp2"], PY + 260, 50, 28), font_txt, "0")

    buttons = []
    def add_btn(x, y, w, txt, cb):
        buttons.append(Button((x, y, w, 32), txt, font_txt, cb))

    def refresh_lists():
        nonlocal maps_list, solved_list
        maps_list   = list_maps(MAPS_DIR)
        solved_list = list_solved_maps(ANIM_DIR)

    def load_selected_map():
        nonlocal mapa_original, mapa_mostrado, rows, cols, result_map, found
        nonlocal step_gen, animating_live, current_pos, start_fijado, animating_file
        if 0 <= selected_map_idx < len(maps_list):
            path = os.path.join(MAPS_DIR, maps_list[selected_map_idx])
            mapa_original = load_map(path)
            rows, cols = len(mapa_original), len(mapa_original[0])
            mapa_mostrado = clone_matrix(mapa_original)
            result_map = None; found = None
            step_gen = None; animating_live = False; animating_file = False
            current_pos = None
            start_fijado = False

    def fijar_inicio():
        nonlocal mapa_mostrado, start_x, start_y, start_fijado
        if mapa_original is None:
            return
        try:
            start_x = int(inp_start_x.get_value())
            start_y = int(inp_start_y.get_value())
        except ValueError:
            return
        if not (0 <= start_x < rows and 0 <= start_y < cols):
            return
        mapa_mostrado = clone_matrix(mapa_original)
        mapa_mostrado[start_x][start_y] = START_CHAR
        start_fijado = True

    def resolver_rapido():
        nonlocal result_map, found, mapa_mostrado
        nonlocal step_gen, animating_live, current_pos, animating_file
        if mapa_original is None: return
        if not start_fijado: fijar_inicio()
        sx, sy = start_x, start_y
        found, result_map = search_treasure(mapa_original, sx, sy)
        result_map[sx][sy] = START_CHAR
        mapa_mostrado = result_map
        # apagar animaciones
        step_gen = None; animating_live = False; animating_file = False
        current_pos = None

    def generar_animate_file():
        """Ejecuta solver con pasos y guarda *_Solved.txt"""
        nonlocal result_map, found
        if mapa_original is None: return
        if not start_fijado: fijar_inicio()
        sx, sy = start_x, start_y

        pasos = []
        for step in search_with_steps(mapa_original, sx, sy):
            if step is True:
                break
            x, y, partial = step
            pasos.append((x, y))

        ok, final_map = search_treasure(mapa_original, sx, sy)
        final_map[sx][sy] = START_CHAR
        found = ok
        result_map = final_map

        base = maps_list[selected_map_idx] if 0 <= selected_map_idx < len(maps_list) else "MAPS"
        save_steps_file(base, pasos, final_map, folder=ANIM_DIR)
        refresh_lists()

    def animar_desde_archivo():
        nonlocal file_steps, file_anim_index, animating_file
        nonlocal mapa_mostrado, result_map, found, rows, cols
        nonlocal animating_live, current_pos, start_fijado

        if 0 <= selected_solved_idx < len(solved_list):
            path = os.path.join(ANIM_DIR, solved_list[selected_solved_idx])
            steps, final_map = load_steps_file(path)

            file_steps = steps
            file_anim_index = 0
            animating_file = True
            animating_live = False
            current_pos = None

            
            rows, cols = len(final_map), len(final_map[0])
            mapa_mostrado = clone_matrix(final_map)
            result_map = final_map
            found = any("*" in "".join(row) for row in final_map)

            # Repinta la @ si ya se había fijado
            if start_fijado and 0 <= start_x < rows and 0 <= start_y < cols:
                mapa_mostrado[start_x][start_y] = START_CHAR

                
    def save_error():
        if found is False:
            escribir_error_no_solucion(os.path.join(BASE_DIR, "mapa_err.txt"), start_x, start_y)

    def go_back():
        return "back"

    # Botones
    add_btn(LAYOUT["col"]["lbl"] + 185, PY + 260, 60,  "Fijar",      fijar_inicio)
    add_btn(LAYOUT["col"]["lbl"],       PY + 310, 120, "Resolver",   resolver_rapido)
    add_btn(LAYOUT["col"]["lbl"]+140,   PY + 310, 120, "G.Animate",  generar_animate_file)
    add_btn(LAYOUT["col"]["lbl"],       PY + 620, 120, "Volver",          go_back)
    add_btn(LAYOUT["col"]["lbl"]+125,   PY + 620, 150, "Ver Recorrido", animar_desde_archivo) 

    DOUBLE = 350
    last_click_maps   = 0
    last_click_solved = 0

    refresh_lists()

    # -------- Loop --------
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return

            inp_start_x.handle_event(e)
            inp_start_y.handle_event(e)

            for b in buttons:
                ret = b.handle_event(e)
                if ret == "back":
                    return

            # listas
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # disponibles
                if list_rect_maps.collidepoint(e.pos):
                    rel_y = e.pos[1] - list_rect_maps.y
                    idx   = rel_y // 24
                    if 0 <= idx < len(maps_list):
                        now = pygame.time.get_ticks()
                        if idx == selected_map_idx and (now - last_click_maps) <= DOUBLE:
                            load_selected_map()
                        else:
                            selected_map_idx = idx
                        last_click_maps = now
                # resueltos
                if list_rect_solved.collidepoint(e.pos):
                    rel_y = e.pos[1] - list_rect_solved.y
                    idx   = rel_y // 24
                    if 0 <= idx < len(solved_list):
                        now = pygame.time.get_ticks()
                        if idx == selected_solved_idx and (now - last_click_solved) <= DOUBLE:
                            animar_desde_archivo()
                        else:
                            selected_solved_idx = idx
                        last_click_solved = now

        # --- Animación en vivo ---
        if animating_live and step_gen is not None:
            now = pygame.time.get_ticks()
            if now - last_step_time >= STEP_DELAY:
                try:
                    step = next(step_gen)
                    if step is True:
                        animating_live = False
                        return
                    x, y, partial = step
                    mapa_mostrado = clone_matrix(partial)
                    mapa_mostrado[start_x][start_y] = START_CHAR
                    current_pos = (x, y)
                    last_step_time = now
                except StopIteration:
                    animating_live = False
                    step_gen = None


        # --- Animación desde archivo ---
        if animating_file and file_steps:
            now = pygame.time.get_ticks()
            if now - last_step_time >= STEP_DELAY:
                if file_anim_index < len(file_steps):
                    # Base: mapa original si existe, si no el final (al que le quitamos * temporalmente)
                    if mapa_original:
                        base_map = clone_matrix(mapa_original)
                    else:
                        base_map = clone_matrix(result_map)
                        # limpiar '*' del final para reconstruir
                        for i in range(rows):
                            for j in range(cols):
                                if base_map[i][j] == '*':
                                    base_map[i][j] = '.'

                    # Pintar todos los pasos hasta el actual
                    for k in range(file_anim_index + 1):
                        px, py = file_steps[k]
                        if base_map[px][py] == '.':
                            base_map[px][py] = '*'

                    # Reponer el inicio
                    if start_fijado and 0 <= start_x < rows and 0 <= start_y < cols:
                        base_map[start_x][start_y] = START_CHAR

                    mapa_mostrado = base_map
                    current_pos   = file_steps[file_anim_index]

                    file_anim_index += 1
                    last_step_time  = now
                else:
                    animating_file = False
                    current_pos    = None



        # Dibujo
        screen.fill(PALETTE["bg"])
        pygame.draw.rect(screen, PALETTE["panel"], (PX, PY, PW, PH), border_radius=12)

        # Título
        title = font_tit.render("RESOLVER MAPA", True, PALETTE["text"])
        screen.blit(title, title.get_rect(center=(PX + PW//2, PY + 30)))

        # Lista mapas disponibles
        screen.blit(font_txt.render("Mapas disponibles:", True, PALETTE["text"]),
                    (LAYOUT["col"]["lbl"], PY + 60))
        pygame.draw.rect(screen, (100,100,100), list_rect_maps, 2)
        for i, fname in enumerate(maps_list):
            col = PALETTE["accent"] if i == selected_map_idx else PALETTE["text"]
            txt = font_txt.render(fname, True, col)
            screen.blit(txt, (list_rect_maps.x + 6, list_rect_maps.y + i*24 + 4))

        # Coords inicio
        screen.blit(font_txt.render("Coordenadas de inicio", True, PALETTE["text"]),
                    (LAYOUT["col"]["lbl"], PY + 235))
        screen.blit(font_txt.render("X:", True, PALETTE["text"]), (LAYOUT["col"]["lbl"],      PY + 265))
        screen.blit(font_txt.render("Y:", True, PALETTE["text"]), (LAYOUT["col"]["lbl"] + 90, PY + 265))
        inp_start_x.draw(screen); inp_start_y.draw(screen)

        # Botones
        for b in buttons:
            b.draw(screen)

        # Lista mapas resueltos
        screen.blit(font_txt.render("Mapas Resueltos:", True, PALETTE["text"]),
                    (LAYOUT["col"]["lbl"], PY + 360))
        pygame.draw.rect(screen, (100,100,100), list_rect_solved, 2)
        for i, fname in enumerate(solved_list):
            col = PALETTE["accent"] if i == selected_solved_idx else PALETTE["text"]
            txt = font_txt.render(fname, True, col)
            screen.blit(txt, (list_rect_solved.x + 6, list_rect_solved.y + i*24 + 4))

        # Preview
        if mapa_mostrado:
            px, py = calc_preview_origin(rows, cols, CELL, prev_left, prev_right, prev_top, prev_bot)
            draw_map_preview(screen, mapa_mostrado, (px, py), CELL)

            # celda actual (anim)
            if current_pos is not None and (animating_live or animating_file):
                cx, cy = current_pos
                pygame.draw.rect(screen, PALETTE["HILITE_COLOR"], (px + cy*CELL, py + cx*CELL, CELL, CELL), 3)

            label = "Mapa" if (result_map is None and not animating_file and not animating_live) else "Resultado"
            screen.blit(font_txt.render(label, True, PALETTE["text"]), (px, py - 20))

            if found is not None and result_map is not None and not animating_live and not animating_file:
                msg = "Tesoro encontrado!" if found else "Sin solución"
                screen.blit(font_txt.render(msg, True, PALETTE["text"]), (px, py + 10 + CELL*rows))

        pygame.display.flip()
        clock.tick(FPS)


# ============================================================
#  ---------- Main start ----------
# ============================================================

def run_ui():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Treasure Map")

    intro_screen(screen)

    while True:
        op = menu_screen(screen)        
        if op == 1:
            generator_screen(screen)

        elif op == 2:
            solver_screen(screen)       

        elif op == 3:
            break                      

        else:
            print("Opción inválida — vuelve a intentarlo.")
            continue
            

    pygame.quit()
    sys.exit()
