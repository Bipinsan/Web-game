import pygame
import sys
import asyncio
import random

pygame.init()

# --- DYNAMIC CONFIGURATION ---
# Get user screen info
info = pygame.display.Info()
SCREEN_W, SCREEN_H = info.current_w, info.current_h

# The "Internal" resolution we design for
VIRTUAL_W, VIRTUAL_H = 360, 480

# Calculate scaling to fit screen while maintaining aspect ratio
scale_factor = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
# Apply a slight reduction (0.9) if you don't want it to touch edges, 
# but for true full screen we use full scale.
WIDTH, HEIGHT = int(VIRTUAL_W * scale_factor), int(VIRTUAL_H * scale_factor)

# Calculate Offsets to center the virtual screen on the physical screen
OFFSET_X = (SCREEN_W - WIDTH) // 2
OFFSET_Y = (SCREEN_H - HEIGHT) // 2

# Set to Fullscreen
WIN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
# Internal surface for clean drawing before scaling
CANVAS = pygame.Surface((VIRTUAL_W, VIRTUAL_H))

pygame.display.set_caption("Tic Tac Toe - Pro Fullscreen")

# --- PALETTE & FONTS ---
BG = (240, 242, 245)
LINE = (180, 185, 195)
X_COLOR = (41, 121, 255)
O_COLOR = (255, 82, 82)
BTN_COLOR = (33, 33, 33)
BTN_HOVER = (60, 60, 60)
WHITE = (255, 255, 255)
TEXT_COLOR = (44, 62, 80)

try:
    FONT = pygame.font.SysFont('sans-serif', 80, bold=True)
    SMALL = pygame.font.SysFont('sans-serif', 20, bold=True)
    BIG = pygame.font.SysFont('sans-serif', 40, bold=True)
except:
    FONT = pygame.font.SysFont('monospace', 80, bold=True)
    SMALL = pygame.font.SysFont('monospace', 20, bold=True)
    BIG = pygame.font.SysFont('monospace', 40, bold=True)

# --- GAME STATE ---
board = [0] * 10
player = 1
game_over = False
winner = 0
scene = "HOME"
mode = "AI"
difficulty = "MEDIUM"

WINS = [(1,2,3),(4,5,6),(7,8,9),(1,4,7),(2,5,8),(3,6,9),(1,5,9),(3,5,7)]

# --- LOGIC ---
def check_win(b, p):
    return any(all(b[idx] == p for idx in combo) for combo in WINS)

def check_draw(b):
    return all(b[i] != 0 for i in range(1, 10))

def get_empty_cells(b):
    return [i for i in range(1, 10) if b[i] == 0]

def minimax(current_board, depth, is_maximizing):
    if check_win(current_board, 2): return 10 - depth
    if check_win(current_board, 1): return depth - 10
    if check_draw(current_board): return 0
    
    if is_maximizing:
        best_score = -float('inf')
        for cell in get_empty_cells(current_board):
            current_board[cell] = 2
            score = minimax(current_board, depth + 1, False)
            current_board[cell] = 0
            best_score = max(score, best_score)
        return best_score
    else:
        best_score = float('inf')
        for cell in get_empty_cells(current_board):
            current_board[cell] = 1
            score = minimax(current_board, depth + 1, True)
            current_board[cell] = 0
            best_score = min(score, best_score)
        return best_score

def computer_move():
    empty = get_empty_cells(board)
    if not empty: return
    mistake_chance = 0.50 if difficulty == "EASY" else 0.15 if difficulty == "MEDIUM" else 0.0
    if random.random() < mistake_chance:
        move = random.choice(empty)
    else:
        best_score = -float('inf')
        move = empty[0]
        for cell in empty:
            board[cell] = 2
            score = minimax(board, 0, False)
            board[cell] = 0
            if score > best_score:
                best_score = score
                move = cell
    board[move] = 2

def get_virtual_mouse():
    """Translates real screen mouse pos to virtual 360x480 pos"""
    mx, my = pygame.mouse.get_pos()
    vx = (mx - OFFSET_X) / scale_factor
    vy = (my - OFFSET_Y) / scale_factor
    return vx, vy

def get_cell(v_pos):
    vx, vy = v_pos
    if vy < 80 or vy > 440: return None
    col, row = int(vx // 120), int((vy - 80) // 120)
    if 0 <= col <= 2 and 0 <= row <= 2:
        return row * 3 + col + 1
    return None

def reset_game():
    global board, player, game_over, winner
    board = [0] * 10
    player = 1
    game_over = False
    winner = 0

# --- DRAWING ---
def draw_button(text, x, y, w, h, active, color=BTN_COLOR):
    c = BTN_HOVER if active else color
    pygame.draw.rect(CANVAS, c, (x, y, w, h), border_radius=12)
    txt = SMALL.render(text, True, WHITE)
    CANVAS.blit(txt, (x + (w - txt.get_width()) // 2, y + (h - txt.get_height()) // 2))

def draw_marks():
    for i in range(1, 10):
        r, c = (i - 1) // 3, (i - 1) % 3
        cx, cy = c * 120 + 60, r * 120 + 140
        if board[i] == 1:
            pygame.draw.line(CANVAS, X_COLOR, (cx-30, cy-30), (cx+30, cy+30), 12)
            pygame.draw.line(CANVAS, X_COLOR, (cx+30, cy-30), (cx-30, cy+30), 12)
        elif board[i] == 2:
            pygame.draw.circle(CANVAS, O_COLOR, (cx, cy), 35, 10)

def draw_home(v_mouse):
    CANVAS.fill(BG)
    title = BIG.render("TIC TAC TOE", True, TEXT_COLOR)
    CANVAS.blit(title, (VIRTUAL_W // 2 - title.get_width() // 2, 120))
    mx, my = v_mouse
    draw_button("VS COMPUTER", 60, 220, 240, 50, 60 <= mx <= 300 and 220 <= my <= 270)
    draw_button("VS HUMAN", 60, 290, 240, 50, 60 <= mx <= 300 and 290 <= my <= 340)

def draw_difficulty_screen(v_mouse):
    CANVAS.fill(BG)
    title = BIG.render("SELECT LEVEL", True, TEXT_COLOR)
    CANVAS.blit(title, (VIRTUAL_W // 2 - title.get_width() // 2, 100))
    mx, my = v_mouse
    levels = [("EASY", 180), ("MEDIUM", 250), ("IMPOSSIBLE", 320)]
    for name, y in levels:
        draw_button(name, 80, y, 200, 50, 80 <= mx <= 280 and y <= my <= y + 50)

def draw_game_ui(v_mouse):
    CANVAS.fill(BG)
    for i in range(1, 3):
        pygame.draw.line(CANVAS, LINE, (120 * i, 90), (120 * i, 430), 4)
        pygame.draw.line(CANVAS, LINE, (10, 80 + 120 * i), (350, 80 + 120 * i), 4)
    mx, my = v_mouse
    draw_button("BACK", 15, 20, 70, 30, 15 <= mx <= 85 and 20 <= my <= 50, (120, 120, 120))
    info = f"{mode} | {difficulty if mode == 'AI' else ''}"
    status = SMALL.render(info, True, (100, 100, 100))
    CANVAS.blit(status, (VIRTUAL_W - status.get_width() - 15, 25))

def draw_end_screen(text, v_mouse):
    overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 210)) 
    CANVAS.blit(overlay, (0, 0))
    msg = BIG.render(text, True, TEXT_COLOR)
    CANVAS.blit(msg, (VIRTUAL_W//2 - msg.get_width()//2, 200))
    mx, my = v_mouse
    draw_button("RESTART", 110, 280, 140, 50, 110 <= mx <= 250 and 280 <= my <= 330)

# --- MAIN LOOP ---
async def main():
    global scene, mode, player, winner, game_over, difficulty
    while True:
        v_mouse = get_virtual_mouse()
        
        if scene == "HOME": draw_home(v_mouse)
        elif scene == "DIFFICULTY": draw_difficulty_screen(v_mouse)
        else:
            draw_game_ui(v_mouse); draw_marks()
            if game_over:
                draw_end_screen("X WINS!" if winner == 1 else "O WINS!" if winner == 2 else "DRAW!", v_mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit(); sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = v_mouse
                if scene == "HOME":
                    if 60 <= mx <= 300:
                        if 220 <= my <= 270: scene = "DIFFICULTY"
                        if 290 <= my <= 340: mode = "PVP"; reset_game(); scene = "GAME"
                elif scene == "DIFFICULTY":
                    if 80 <= mx <= 280:
                        if 180 <= my <= 230: difficulty = "EASY"; mode = "AI"; reset_game(); scene = "GAME"
                        if 250 <= my <= 300: difficulty = "MEDIUM"; mode = "AI"; reset_game(); scene = "GAME"
                        if 320 <= my <= 370: difficulty = "IMPOSSIBLE"; mode = "AI"; reset_game(); scene = "GAME"
                elif scene == "GAME":
                    if 15 <= mx <= 85 and 20 <= my <= 50: scene = "HOME"
                    elif game_over and 110 <= mx <= 250 and 280 <= my <= 330: reset_game()
                    elif player == 1 or (player == 2 and mode == "PVP"):
                        cell = get_cell(v_mouse)
                        if cell and board[cell] == 0:
                            board[cell] = player
                            if check_win(board, player): winner = player; game_over = True
                            elif check_draw(board): game_over = True
                            else: player = 3 - player

        if scene == "GAME" and mode == "AI" and player == 2 and not game_over:
            await asyncio.sleep(0.5); computer_move()
            if check_win(board, 2): winner = 2; game_over = True
            elif check_draw(board): game_over = True
            else: player = 1

        # Center and Scale logic
        WIN.fill((0, 0, 0)) # Black bars for the background
        # Rescale the virtual canvas to the calculated fullscreen size
        scaled_win = pygame.transform.smoothscale(CANVAS, (WIDTH, HEIGHT))
        WIN.blit(scaled_win, (OFFSET_X, OFFSET_Y))
        
        pygame.display.update()
        await asyncio.sleep(0)

asyncio.run(main())

