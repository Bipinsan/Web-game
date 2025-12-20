import pygame
import sys
import asyncio
import random
import math
from array import array

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

# ================= SCREEN =================
info = pygame.display.Info()
SCREEN_W, SCREEN_H = info.current_w, info.current_h
VIRTUAL_W, VIRTUAL_H = 360, 480
scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
WIDTH, HEIGHT = int(VIRTUAL_W * scale), int(VIRTUAL_H * scale)
OFFSET_X = (SCREEN_W - WIDTH) // 2
OFFSET_Y = (SCREEN_H - HEIGHT) // 2

WIN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
CANVAS = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
pygame.display.set_caption("Tic Tac Toe Pro")

# ================= COLORS =================
BG = (18, 18, 30)
LINE = (70, 130, 180)
X_COLOR = (0, 200, 255)
O_COLOR = (255, 90, 120)
BTN_COLOR = (30, 30, 60)
BTN_HOVER = (60, 60, 120)
WHITE = (240, 240, 240)
TEXT_COLOR = (200, 220, 255)

# ================= FONTS =================
FONT = pygame.font.SysFont("sans-serif", 80, bold=True)
SMALL = pygame.font.SysFont("sans-serif", 20, bold=True)
BIG = pygame.font.SysFont("sans-serif", 40, bold=True)

# ================= SOUND =================
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
player = 1
game_over = False
winner = 0
scene = "HOME"
mode = "AI"
difficulty = "MEDIUM"

WINS = [(1,2,3),(4,5,6),(7,8,9),
        (1,4,7),(2,5,8),(3,6,9),
        (1,5,9),(3,5,7)]

DIFFICULTY_SETTINGS = {"EASY": 0.50, "MEDIUM": 0.15, "HARD": 0.05, "IMPOSSIBLE": 0.01}

# ================= LOGIC =================
def check_win(b, p):
    return any(all(b[i] == p for i in w) for w in WINS)

def check_draw(b):
    return all(b[i] != 0 for i in range(1, 10))

def get_empty(b):
    return [i for i in range(1, 10) if b[i] == 0]

def minimax_fast(b, depth, is_ai):
    if check_win(b, 2): return 10 - depth
    if check_win(b, 1): return depth - 10
    if check_draw(b) or depth >= 4: return 0

    best = -999 if is_ai else 999
    for c in get_empty(b):
        b[c] = 2 if is_ai else 1
        score = minimax_fast(b, depth + 1, not is_ai)
        b[c] = 0
        best = max(best, score) if is_ai else min(best, score)
    return best

def computer_move():
    empty = get_empty(board)
    if not empty: return

    if random.random() < DIFFICULTY_SETTINGS[difficulty]:
        board[random.choice(empty)] = 2
        return

    for p_val in [2, 1]: # Check for win then check for block
        for c in empty:
            board[c] = p_val
            if check_win(board, p_val):
                board[c] = 2
                return
            board[c] = 0

    best, move = -999, random.choice(empty)
    for c in empty:
        board[c] = 2
        score = minimax_fast(board, 0, False)
        board[c] = 0
        if score > best:
            best, move = score, c
    board[move] = 2

def reset_game():
    global board, player, game_over, winner
    board = [0] * 10
    player = 1
    game_over = False
    winner = 0

# ================= INPUT & DRAW =================
def get_virtual_mouse():
    mx, my = pygame.mouse.get_pos()
    return (mx - OFFSET_X) / scale, (my - OFFSET_Y) / scale

def get_cell(pos):
    x, y = pos
    if y < 80 or y > 440: return None
    c, r = int(x // 120), int((y - 80) // 120)
    return r * 3 + c + 1 if 0 <= r <= 2 and 0 <= c <= 2 else None

def button(text, x, y, w, h, hover):
    color = BTN_HOVER if hover else BTN_COLOR
    pygame.draw.rect(CANVAS, color, (x, y, w, h), border_radius=10)
    pygame.draw.rect(CANVAS, LINE, (x, y, w, h), 2, border_radius=10)
    t = SMALL.render(text, True, WHITE)
    CANVAS.blit(t, (x + w//2 - t.get_width()//2, y + h//2 - t.get_height()//2))

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
            CANVAS.blit(BIG.render("TIC TAC TOE", True, TEXT_COLOR), (70,120))
            button("VS COMPUTER", 60, 220, 240, 50, 60 <= mx <= 300 and 220 <= my <= 270)
            button("VS HUMAN", 60, 290, 240, 50, 60 <= mx <= 300 and 290 <= my <= 340)

        elif scene == "DIFFICULTY":
            CANVAS.blit(BIG.render("SELECT LEVEL", True, TEXT_COLOR), (80,100))
            levels = [("EASY",180),("MEDIUM",240),("HARD",300),("IMPOSSIBLE",360)]
            for l, y in levels:
                button(l, 80, y, 200, 45, 80 <= mx <= 280 and y <= my <= y+45)

        elif scene == "GAME":
            # Draw Grid
            for i in range(1,3):
                pygame.draw.line(CANVAS, LINE, (120*i, 80), (120*i, 440), 3)
                pygame.draw.line(CANVAS, LINE, (0, 80+120*i), (360, 80+120*i), 3)
            draw_marks()
            
            # Status Text
            if not game_over:
                txt = f"PLAYER {'X' if player==1 else 'O'}'S TURN"
                CANVAS.blit(SMALL.render(txt, True, WHITE), (110, 40))
            else:
                msg = "DRAW!" if winner == 0 else ("X WINS!" if winner == 1 else "O WINS!")
                CANVAS.blit(BIG.render(msg, True, TEXT_COLOR), (100, 200))
                button("RESTART", 110, 280, 140, 45, 110 <= mx <= 250 and 280 <= my <= 325)
                button("HOME", 110, 340, 140, 45, 110 <= mx <= 250 and 340 <= my <= 385)

        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit(); sys.exit()

            if e.type == pygame.MOUSEBUTTONDOWN:
                if scene == "HOME":
                    if 60 <= mx <= 300:
                        if 220 <= my <= 270: 
                            mode="AI"; scene = "DIFFICULTY"; S_CLICK.play()
                        elif 290 <= my <= 340:
                            mode="PVP"; reset_game(); scene="GAME"; S_CLICK.play()

                elif scene == "DIFFICULTY":
                    if 80 <= mx <= 280:
                        if 180 <= my <= 225: difficulty="EASY"
                        elif 240 <= my <= 285: difficulty="MEDIUM"
                        elif 300 <= my <= 345: difficulty="HARD"
                        elif 360 <= my <= 405: difficulty="IMPOSSIBLE"
                        else: continue
                        reset_game(); scene="GAME"; S_CLICK.play()

                elif scene == "GAME":
                    if game_over:
                        if 110 <= mx <= 250:
                            if 280 <= my <= 325: reset_game(); S_CLICK.play()
                            elif 340 <= my <= 385: scene="HOME"; S_CLICK.play()
                    else:
                        c = get_cell(v_mouse)
                        if c and board[c] == 0:
                            # Logical move for both PvP and Human starting AI turn
                            board[c] = player
                            S_CLICK.play()
                            if check_win(board, player):
                                winner=player; game_over=True; S_WIN.play()
                            elif check_draw(board):
                                game_over=True; S_DRAW.play()
                            else:
                                player = 2 if player == 1 else 1

        # AI Move Logic
        if scene=="GAME" and mode=="AI" and player==2 and not game_over:
            await asyncio.sleep(0.3) # Slight delay for realism
            computer_move()
            if check_win(board, 2):
                winner=2; game_over=True; S_WIN.play()
            elif check_draw(board):
                game_over=True; S_DRAW.play()
            else:
                player=1

        # Scaling and Rendering
        scaled_win = pygame.transform.smoothscale(CANVAS, (WIDTH, HEIGHT))
        WIN.fill((0, 0, 0))
        WIN.blit(scaled_win, (OFFSET_X, OFFSET_Y))
        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())

