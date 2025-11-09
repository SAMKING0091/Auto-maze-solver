"""
Auto Maze Solver - Fixed Window Layout
"""

import pygame
import random
import math
import heapq
from collections import deque

# ---------- Config ----------
WIDTH, HEIGHT = 1400, 900
FPS = 60

DIFFICULTIES = {
    "Easy": (25, 17, 8),
    "Medium": (40, 28, 5),
    "Hard": (60, 42, 3),
}
DEFAULT_DIFFICULTY = "Medium"

# Modern Color Palette
BG = (240, 242, 245)
PANEL = (255, 255, 255)
WALL = (30, 41, 59)
CELL = (255, 255, 255)
PATH = (239, 68, 68)
VISITED = (96, 165, 250)
START = (34, 197, 94)
END = (239, 68, 68)
BTN_ACTIVE = (59, 130, 246)
BTN_INACTIVE = (226, 232, 240)
BTN_HOVER = (147, 197, 253)
TEXT = (30, 41, 59)
TEXT_LIGHT = (100, 116, 139)
BORDER = (203, 213, 225)

# ---------- Maze Classes ----------
class Cell:
    def __init__(self, c, r):
        self.c = c
        self.r = r
        self.walls = [True, True, True, True]
        self.visited = False

class Maze:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.grid = [Cell(c, r) for r in range(rows) for c in range(cols)]
        self.stack = []

    def index(self, c, r):
        if c < 0 or r < 0 or c >= self.cols or r >= self.rows:
            return None
        return r * self.cols + c

    def get(self, c, r):
        idx = self.index(c, r)
        return self.grid[idx] if idx is not None else None

    def neighbors_with_walls(self, cell):
        res = []
        dirs = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for i, (dc, dr) in enumerate(dirs):
            n = self.get(cell.c + dc, cell.r + dr)
            if n and not n.visited:
                res.append((n, i))
        return res

    def remove_walls(self, a: Cell, b: Cell):
        dx = b.c - a.c
        dy = b.r - a.r
        if dx == 1:
            a.walls[1] = False
            b.walls[3] = False
        elif dx == -1:
            a.walls[3] = False
            b.walls[1] = False
        elif dy == 1:
            a.walls[2] = False
            b.walls[0] = False
        elif dy == -1:
            a.walls[0] = False
            b.walls[2] = False

    def generate_recursive_backtracker(self, animate_callback=None):
        for cell in self.grid:
            cell.visited = False
            cell.walls = [True, True, True, True]
        start = self.get(0, 0)
        start.visited = True
        self.stack = [start]
        while self.stack:
            current = self.stack[-1]
            neighbors = self.neighbors_with_walls(current)
            if neighbors:
                nxt, _dir = random.choice(neighbors)
                nxt.visited = True
                self.remove_walls(current, nxt)
                self.stack.append(nxt)
            else:
                self.stack.pop()
            if animate_callback:
                animate_callback()
        for cell in self.grid:
            cell.visited = False

# ---------- Pathfinding ----------
def reconstruct_path(came_from, end_idx):
    path = []
    current = end_idx
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

def cell_neighbors_walkable(maze: Maze, cell_idx):
    cell = maze.grid[cell_idx]
    c, r = cell.c, cell.r
    dirs = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    for i, (dc, dr) in enumerate(dirs):
        if not cell.walls[i]:
            n = maze.get(c + dc, r + dr)
            if n:
                yield maze.index(n.c, n.r)

def DFS_generator(maze: Maze, start_idx, end_idx):
    visited = set()
    stack = [(start_idx, None)]
    came_from = {}
    while stack:
        node, parent = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        if parent is not None:
            came_from[node] = parent
        yield ("visit", node, visited, came_from)
        if node == end_idx:
            yield ("found", reconstruct_path(came_from, end_idx))
            return
        neighbors = list(cell_neighbors_walkable(maze, node))
        random.shuffle(neighbors)
        for n in neighbors:
            if n not in visited:
                stack.append((n, node))
    yield ("notfound",)

def BFS_generator(maze: Maze, start_idx, end_idx):
    visited = set([start_idx])
    q = deque([(start_idx, None)])
    came_from = {}
    while q:
        node, parent = q.popleft()
        if parent is not None:
            came_from[node] = parent
        yield ("visit", node, visited, came_from)
        if node == end_idx:
            yield ("found", reconstruct_path(came_from, end_idx))
            return
        for n in cell_neighbors_walkable(maze, node):
            if n not in visited:
                visited.add(n)
                q.append((n, node))
    yield ("notfound",)

def dijkstra_generator(maze: Maze, start_idx, end_idx):
    dist = {start_idx: 0}
    came_from = {}
    visited = set()
    heap = [(0, start_idx, None)]
    while heap:
        d, node, parent = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if parent is not None:
            came_from[node] = parent
        yield ("visit", node, visited, came_from)
        if node == end_idx:
            yield ("found", reconstruct_path(came_from, end_idx))
            return
        for n in cell_neighbors_walkable(maze, node):
            nd = d + 1
            if n not in dist or nd < dist[n]:
                dist[n] = nd
                heapq.heappush(heap, (nd, n, node))
    yield ("notfound",)

def manhattan(a_idx, b_idx, maze: Maze):
    a = maze.grid[a_idx]
    b = maze.grid[b_idx]
    return abs(a.c - b.c) + abs(a.r - b.r)

def a_star_generator(maze: Maze, start_idx, end_idx):
    gscore = {start_idx: 0}
    fscore = {start_idx: manhattan(start_idx, end_idx, maze)}
    came_from = {}
    open_heap = [(fscore[start_idx], start_idx, None)]
    open_set = {start_idx}
    closed_set = set()
    while open_heap:
        f, node, parent = heapq.heappop(open_heap)
        if node in closed_set:
            continue
        open_set.discard(node)
        closed_set.add(node)
        if parent is not None:
            came_from[node] = parent
        yield ("visit", node, closed_set, came_from)
        if node == end_idx:
            yield ("found", reconstruct_path(came_from, end_idx))
            return
        for n in cell_neighbors_walkable(maze, node):
            tentative_g = gscore[node] + 1
            if n in closed_set and tentative_g >= gscore.get(n, math.inf):
                continue
            if tentative_g < gscore.get(n, math.inf):
                came_from[n] = node
                gscore[n] = tentative_g
                fscore[n] = tentative_g + manhattan(n, end_idx, maze)
                heapq.heappush(open_heap, (fscore[n], n, node))
                open_set.add(n)
    yield ("notfound",)

ALGORITHM_MAP = {
    "DFS": DFS_generator,
    "BFS": BFS_generator,
    "Dijkstra": dijkstra_generator,
    "A*": a_star_generator,
}

# ---------- Button Class ----------
class Button:
    def __init__(self, x, y, w, h, text, action, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.font = font
        self.hovered = False
        self.active = False
        
    def draw(self, screen):
        if self.active:
            color = BTN_ACTIVE
        elif self.hovered:
            color = BTN_HOVER
        else:
            color = BTN_INACTIVE
            
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        
        text_color = (255, 255, 255) if self.active else TEXT
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def handle_event(self, event, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered:
            self.action()
            return True
        return False

# ---------- Visualizer ----------
class Visualizer:
    def __init__(self, difficulty_name=DEFAULT_DIFFICULTY):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Auto Maze Solver")
        self.clock = pygame.time.Clock()
        self.width = WIDTH
        self.height = HEIGHT
        
        try:
            self.font = pygame.font.SysFont("arial", 14, bold=True)
            self.font_title = pygame.font.SysFont("arial", 26, bold=True)
            self.font_label = pygame.font.SysFont("arial", 11, bold=True)
        except:
            self.font = pygame.font.Font(None, 18)
            self.font_title = pygame.font.Font(None, 34)
            self.font_label = pygame.font.Font(None, 14)
        
        self.algorithm_name = "A*"
        self.running_search = False
        self.search_generator = None
        self.search_visited = set()
        self.search_came_from = {}
        self.search_path = []
        self.generating = False
        self.search_complete = False
        
        self.set_difficulty(difficulty_name)

    def set_difficulty(self, name):
        self.diff_name = name
        self.cols, self.rows, self.step_delay = DIFFICULTIES[name]
        
        # Fixed layout calculations using current window size
        self.margin = 20
        self.panel_w = 280
        self.gap = 20
        
        # Calculate available space for maze
        available_w = self.width - self.panel_w - (2 * self.margin) - self.gap
        available_h = self.height - (2 * self.margin)
        
        # Calculate cell size to fit the maze
        cell_w = available_w // self.cols
        cell_h = available_h // self.rows
        self.cell_size = max(3, min(cell_w, cell_h))  # Minimum cell size of 3
        
        # Calculate actual maze dimensions
        self.maze_w = self.cell_size * self.cols
        self.maze_h = self.cell_size * self.rows
        
        # Center the maze in available space
        self.maze_x = self.margin + (available_w - self.maze_w) // 2
        self.maze_y = self.margin + (available_h - self.maze_h) // 2
        
        # Panel positioning
        self.panel_x = self.width - self.panel_w - self.margin
        self.panel_y = self.margin
        self.panel_h = self.height - (2 * self.margin)
        
        self.maze = Maze(self.cols, self.rows)
        self.generate_maze(animated=False)
        self.reset_search_state()
        self.setup_buttons()
        
        self.start_idx = self.maze.index(0, 0)
        self.end_idx = self.maze.index(self.cols - 1, self.rows - 1)

    def setup_buttons(self):
        self.buttons = []
        px = self.panel_x + 15
        bw = self.panel_w - 30
        bh = 40
        
        py = self.panel_y + 110
        
        # Algorithm buttons
        for alg in ["DFS", "BFS", "Dijkstra", "A*"]:
            btn = Button(px, py, bw, bh, alg, 
                        lambda a=alg: self.select_algorithm(a), self.font)
            self.buttons.append(btn)
            py += bh + 8
        
        py += 15
        
        # Control buttons
        for text, action in [
            ("▶ Start Search", self.run_search),
            ("↻ Reset", self.reset_search_state),
            ("⚡ New Maze", lambda: self.generate_maze(animated=True))
        ]:
            btn = Button(px, py, bw, bh, text, action, self.font)
            self.buttons.append(btn)
            py += bh + 8
        
        py += 15
        
        # Difficulty buttons
        dw = (bw - 16) // 3
        for i, diff in enumerate(["Easy", "Medium", "Hard"]):
            btn = Button(px + i * (dw + 8), py, dw, 36, diff,
                        lambda d=diff: self.set_difficulty(d), self.font_label)
            self.buttons.append(btn)

    def select_algorithm(self, alg):
        self.algorithm_name = alg
        self.reset_search_state()

    def generate_maze(self, animated=True):
        self.generating = True
        self.search_complete = False
        
        def cb():
            self.draw()
            pygame.display.flip()
            pygame.time.delay(max(1, int(self.step_delay)))
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
        
        if animated:
            self.maze.generate_recursive_backtracker(animate_callback=cb)
        else:
            self.maze.generate_recursive_backtracker(animate_callback=None)
        
        self.generating = False
        self.start_idx = self.maze.index(0, 0)
        self.end_idx = self.maze.index(self.maze.cols - 1, self.maze.rows - 1)
        self.reset_search_state()

    def reset_search_state(self):
        self.running_search = False
        self.search_generator = None
        self.search_visited = set()
        self.search_came_from = {}
        self.search_path = []
        self.search_complete = False

    def run_search(self):
        if self.generating:
            return
        gen_func = ALGORITHM_MAP.get(self.algorithm_name)
        if not gen_func:
            return
        self.reset_search_state()
        self.running_search = True
        self.search_generator = gen_func(self.maze, self.start_idx, self.end_idx)

    def draw_cell(self, cell: Cell):
        x = self.maze_x + cell.c * self.cell_size
        y = self.maze_y + cell.r * self.cell_size
        s = self.cell_size
        
        pygame.draw.rect(self.screen, CELL, (x, y, s, s))
        
        wall_thickness = max(1, self.cell_size // 8)
        if cell.walls[0]:
            pygame.draw.line(self.screen, WALL, (x, y), (x + s - 1, y), wall_thickness)
        if cell.walls[1]:
            pygame.draw.line(self.screen, WALL, (x + s - 1, y), (x + s - 1, y + s - 1), wall_thickness)
        if cell.walls[2]:
            pygame.draw.line(self.screen, WALL, (x + s - 1, y + s - 1), (x, y + s - 1), wall_thickness)
        if cell.walls[3]:
            pygame.draw.line(self.screen, WALL, (x, y + s - 1), (x, y), wall_thickness)

    def draw(self):
        self.screen.fill(BG)
        
        # Draw cells
        for cell in self.maze.grid:
            self.draw_cell(cell)
        
        # Visited cells
        for idx in self.search_visited:
            c = self.maze.grid[idx]
            x = self.maze_x + c.c * self.cell_size
            y = self.maze_y + c.r * self.cell_size
            surf = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
            surf.fill((*VISITED, 100))
            self.screen.blit(surf, (x, y))
        
        # Path
        if self.search_path and len(self.search_path) >= 2:
            pts = []
            for idx in self.search_path:
                c = self.maze.grid[idx]
                x = self.maze_x + c.c * self.cell_size + self.cell_size // 2
                y = self.maze_y + c.r * self.cell_size + self.cell_size // 2
                pts.append((x, y))
            line_width = max(2, self.cell_size // 6)
            pygame.draw.lines(self.screen, PATH, False, pts, line_width)
            
            # Draw circles on path
            circle_radius = max(2, self.cell_size // 5)
            for x, y in pts:
                pygame.draw.circle(self.screen, PATH, (x, y), circle_radius)
        
        # Start & End
        for idx, color in [(self.start_idx, START), (self.end_idx, END)]:
            c = self.maze.grid[idx]
            x = self.maze_x + c.c * self.cell_size
            y = self.maze_y + c.r * self.cell_size
            size = max(self.cell_size - 4, 2)
            offset = (self.cell_size - size) // 2
            pygame.draw.rect(self.screen, color, 
                           (x + offset, y + offset, size, size), border_radius=2)
        
        self.draw_panel()

    def draw_panel(self):
        # Panel box
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_w, self.panel_h)
        pygame.draw.rect(self.screen, PANEL, panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, BORDER, panel_rect, 2, border_radius=12)
        
        py = self.panel_y + 25
        px = self.panel_x + 15
        
        # Title
        title = self.font_title.render("Auto Maze", True, TEXT)
        self.screen.blit(title, (px, py))
        py += 35
        
        subtitle = self.font.render("Solver", True, TEXT_LIGHT)
        self.screen.blit(subtitle, (px, py))
        py += 35
        
        # Divider
        pygame.draw.line(self.screen, BORDER, 
                        (px, py), (self.panel_x + self.panel_w - 15, py), 1)
        py += 18
        
        # Algorithm section
        label = self.font_label.render("ALGORITHM", True, TEXT_LIGHT)
        self.screen.blit(label, (px, py))
        
        # Update button states
        for btn in self.buttons[:4]:
            btn.active = (btn.text == self.algorithm_name)
        
        # Difficulty states
        for btn in self.buttons[-3:]:
            btn.active = (btn.text == self.diff_name)
        
        # Stats box at bottom
        stats_y = self.panel_y + self.panel_h - 180
        stats_box = pygame.Rect(px, stats_y, self.panel_w - 30, 110)
        pygame.draw.rect(self.screen, BG, stats_box, border_radius=8)
        
        stats_y += 12
        
        # Stats
        label = self.font_label.render("STATISTICS", True, TEXT_LIGHT)
        self.screen.blit(label, (px + 10, stats_y))
        stats_y += 22
        
        stats = [
            f"Grid: {self.cols} × {self.rows}",
            f"Explored: {len(self.search_visited)}",
            f"Path: {len(self.search_path)}"
        ]
        
        for stat in stats:
            text = self.font.render(stat, True, TEXT)
            self.screen.blit(text, (px + 10, stats_y))
            stats_y += 22
        
        # Status
        stats_y += 15
        if self.generating:
            status, color = "⚙ Generating...", TEXT_LIGHT
        elif self.running_search:
            status, color = "🔍 Searching...", BTN_ACTIVE
        elif self.search_complete and self.search_path:
            status, color = "✓ Path Found!", START
        else:
            status, color = "● Ready", TEXT
        
        text = self.font.render(status, True, color)
        text_rect = text.get_rect(centerx=self.panel_x + self.panel_w // 2, y=stats_y)
        self.screen.blit(text, text_rect)
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.hovered = btn.rect.collidepoint(mouse_pos)
            btn.draw(self.screen)

    def step_search(self):
        if not self.running_search or self.search_generator is None:
            return
        try:
            msg = next(self.search_generator)
        except StopIteration:
            self.running_search = False
            return
        
        if not msg:
            return
        
        code = msg[0]
        if code == "visit":
            self.search_visited = set(msg[2]) if len(msg) > 2 else set()
            self.search_came_from = dict(msg[3]) if len(msg) > 3 else {}
        elif code == "found":
            self.search_path = msg[1]
            self.running_search = False
            self.search_complete = True
        elif code == "notfound":
            self.running_search = False

    def mainloop(self):
        running = True
        last_step = 0
        
        while running:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.set_difficulty(self.diff_name)  # Recalculate layout
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        if not self.generating:
                            self.run_search()
                    elif event.key == pygame.K_g:
                        self.generate_maze(animated=True)
                    elif event.key == pygame.K_r:
                        self.reset_search_state()
                    elif event.key == pygame.K_1:
                        self.select_algorithm("DFS")
                    elif event.key == pygame.K_2:
                        self.select_algorithm("BFS")
                    elif event.key == pygame.K_3:
                        self.select_algorithm("Dijkstra")
                    elif event.key == pygame.K_4:
                        self.select_algorithm("A*")
                    elif event.key == pygame.K_e:
                        self.set_difficulty("Easy")
                    elif event.key == pygame.K_m:
                        self.set_difficulty("Medium")
                    elif event.key == pygame.K_h:
                        self.set_difficulty("Hard")
                
                for btn in self.buttons:
                    btn.handle_event(event, mouse_pos)
            
            if self.running_search:
                if pygame.time.get_ticks() - last_step >= max(1, int(self.step_delay)):
                    self.step_search()
                    last_step = pygame.time.get_ticks()
            
            self.draw()
            pygame.display.flip()
        
        pygame.quit()

if __name__ == "__main__":
    vis = Visualizer(DEFAULT_DIFFICULTY)
    vis.mainloop()