import pygame
import sys
import asyncio
import random
import math
from array import array

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

# ================= SCREEN CONFIG =================
VIRTUAL_W, VIRTUAL_H = 360, 480
# Set initial window size (not fullscreen)
window_w, window_h = 450, 600 

# Create a resizable window
WIN = pygame.display.set_mode((window_w, window_h), pygame.RESIZABLE)
CANVAS = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
pygame.display.set_caption("Tic Tac Toe Pro")

# ================= COLORS & FONTS =================
BG, LINE = (18, 18, 30), (70, 130, 180)
X_COLOR, O_COLOR = (0, 200, 255), (255, 90, 120)
BTN_COLOR, BTN_HOVER = (30, 30, 60), (60, 60, 120)
WHITE, TEXT_COLOR = (240, 240, 240), (200, 220, 255)

SMALL = pygame.font.SysFont("sans-serif", 20, bold=True)
BIG = pygame.font.SysFont("sans-serif", 40, bold=True)

# ================= AUDIO =================
def tone(freq=440, duration=0.15, volume=0.5):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array("h")
    for i in range(n_samples):
        t = math.sin(2 * math.pi * freq * i / sample_rate)
        buf.append(int(t * 32767 * volume))
    return pygame.mixer.Sound(buffer=buf)

S_CLICK = tone(600, 0.08, 0.4)
S_WIN = tone(900, 0.3, 0.6)
S_DRAW = tone(300, 0.3, 0.5)

# ================= GAME STATE =================
board = [0] * 10
player, game_over, winner = 1, False, 0
scene, mode, difficulty = "HOME", "AI", "MEDIUM"

WINS = [(1,2,3),(4,5,6),(7,8,9),(1,4,7),(2,5,8),(3,6,9),(1,5,9),(3,5,7)]
DIFFICULTY_SETTINGS = {"EASY": 0.50, "MEDIUM": 0.15, "HARD": 0.05, "IMPOSSIBLE": 0.01}

# ================= LOGIC =================
def check_win(b, p): return any(all(b[i] == p for i in w) for w in WINS)
def check_draw(b): return all(b[i] != 0 for i in range(1, 10))
def get_empty(b): return [i for i in range(1, 10) if b[i] == 0]

def computer_move():
    empty = get_empty(board)
    if not empty: return
    if random.random() < DIFFICULTY_SETTINGS[difficulty]:
        board[random.choice(empty)] = 2; return
    for p_val in [2, 1]:
        for c in empty:
            board[c] = p_val
            if check_win(board, p_val):
                board[c] = 2; return
            board[c] = 0
    board[random.choice(empty)] = 2

def reset_game():
    global board, player, game_over, winner
    board = [0] * 10; player = 1; game_over = False; winner = 0

# ================= COORDINATE MAPPING =================
def get_scaling_data():
    """Calculates how to fit the virtual canvas into the current window."""
    w, h = WIN.get_size()
    scale = min(w / VIRTUAL_W, h / VIRTUAL_H)
    nw, nh = int(VIRTUAL_W * scale), int(VIRTUAL_H * scale)
    ox, oy = (w - nw) // 2, (h - nh) // 2
    return scale, ox, oy, nw, nh

def get_virtual_mouse():
    mx, my = pygame.mouse.get_pos()
    scale, ox, oy, _, _ = get_scaling_data()
    return (mx - ox) / scale, (my - oy) / scale

def get_cell(v_pos):
    x, y = v_pos
    if y < 80 or y > 440: return None
    c, r = int(x // 120), int((y - 80) // 120)
    return r * 3 + c + 1 if 0 <= r <= 2 and 0 <= c <= 2 else None

# ================= DRAWING =================
def button(text, x, y, w, h, v_mouse):
    hover = x <= v_mouse[0] <= x+w and y <= v_mouse[1] <= y+h
    pygame.draw.rect(CANVAS, BTN_HOVER if hover else BTN_COLOR, (x, y, w, h), border_radius=10)
    t = SMALL.render(text, True, WHITE)
    CANVAS.blit(t, (x + w//2 - t.get_width()//2, y + h//2 - t.get_height()//2))
    return hover

def draw_marks():
    for i in range(1, 10):
        r, c = (i-1)//3, (i-1)%3
        cx, cy = c*120+60, r*120+140
        if board[i] == 1:
            pygame.draw.line(CANVAS, X_COLOR, (cx-30, cy-30), (cx+30, cy+30), 8)
            pygame.draw.line(CANVAS, X_COLOR, (cx+30, cy-30), (cx-30, cy+30), 8)
        elif board[i] == 2:
            pygame.draw.circle(CANVAS, O_COLOR, (cx, cy), 35, 6)

# ================= MAIN LOOP =================
async def main():
    global scene, player, game_over, winner, difficulty, mode
    clock = pygame.time.Clock()

    while True:
        v_mouse = get_virtual_mouse()
        mx, my = v_mouse
        CANVAS.fill(BG)

        if scene == "HOME":
            CANVAS.blit(BIG.render("TIC TAC TOE", True, TEXT_COLOR), (70, 120))
            b1 = button("VS COMPUTER", 60, 220, 240, 50, v_mouse)
            b2 = button("VS HUMAN", 60, 290, 240, 50, v_mouse)
        
        elif scene == "DIFFICULTY":
            CANVAS.blit(BIG.render("SELECT LEVEL", True, TEXT_COLOR), (80, 100))
            levels = [("EASY", 180), ("MEDIUM", 240), ("HARD", 300), ("IMPOSSIBLE", 360)]
            hovered_lvl = None
            for l, y in levels:
                if button(l, 80, y, 200, 45, v_mouse): hovered_lvl = l

        elif scene == "GAME":
            for i in range(1, 3):
                pygame.draw.line(CANVAS, LINE, (120*i, 80), (120*i, 440), 3)
                pygame.draw.line(CANVAS, LINE, (0, 80+120*i), (360, 80+120*i), 3)
            draw_marks()
            if not game_over:
                CANVAS.blit(SMALL.render(f"PLAYER {'X' if player==1 else 'O'}'S TURN", True, WHITE), (110, 40))
            else:
                msg = "DRAW!" if winner == 0 else ("X WINS!" if winner == 1 else "O WINS!")
                CANVAS.blit(BIG.render(msg, True, TEXT_COLOR), (100, 200))
                button("RESTART", 110, 280, 140, 45, v_mouse)
                button("HOME", 110, 340, 140, 45, v_mouse)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                if scene == "HOME":
                    if 60 <= mx <= 300:
                        if 220 <= my <= 270: 
                            mode="AI"; scene="DIFFICULTY"; S_CLICK.play()
                        elif 290 <= my <= 340:
                            mode="PVP"; reset_game(); scene="GAME"; S_CLICK.play()
                
                elif scene == "DIFFICULTY":
                    if 80 <= mx <= 280 and hovered_lvl:
                        difficulty = hovered_lvl
                        reset_game(); scene="GAME"; S_CLICK.play()

                elif scene == "GAME":
                    if game_over:
                        if 110 <= mx <= 250:
                            if 280 <= my <= 325: reset_game(); S_CLICK.play()
                            elif 340 <= my <= 385: scene="HOME"; S_CLICK.play()
                    else:
                        c = get_cell(v_mouse)
                        if c and board[c] == 0:
                            board[c] = player
                            S_CLICK.play()
                            if check_win(board, player):
                                winner=player; game_over=True; S_WIN.play()
                            elif check_draw(board):
                                game_over=True; S_DRAW.play()
                            else: player = 2 if player == 1 else 1

        if scene=="GAME" and mode=="AI" and player==2 and not game_over:
            await asyncio.sleep(0.3)
            computer_move()
            if check_win(board, 2): winner=2; game_over=True; S_WIN.play()
            elif check_draw(board): game_over=True; S_DRAW.play()
            else: player=1

        # Scale Canvas to Window
        scale, ox, oy, nw, nh = get_scaling_data()
        scaled_canvas = pygame.transform.smoothscale(CANVAS, (nw, nh))
        WIN.fill((0, 0, 0))
        WIN.blit(scaled_canvas, (ox, oy))
        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
