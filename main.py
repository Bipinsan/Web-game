import pygame
import sys
import asyncio  # Required for web compatibility

pygame.init()

# --- WINDOW CONFIGURATION ---
WIDTH, HEIGHT = 360, 420
# For web platforms like Trinket, SCALED is usually handled by the browser container
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tic Tac Toe - Pro")

# Colors
BG = (245, 245, 245)
LINE = (50, 50, 50)
X_COLOR = (66, 133, 244)
O_COLOR = (219, 68, 55)
BTN_COLOR = (66, 133, 244)
BTN_HOVER = (50, 100, 200)
BACK_BTN_COLOR = (150, 150, 150)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)

# Fonts
# Note: Trinket sometimes struggles with None fonts; 'monospace' is safer for web
FONT = pygame.font.SysFont('monospace', 80, bold=True)
SMALL = pygame.font.SysFont('monospace', 25, bold=True)
TINY = pygame.font.SysFont('monospace', 18, bold=True)
BIG = pygame.font.SysFont('monospace', 35, bold=True)

# Game State
board = [0] * 10
player = 1
game_over = False
winner = 0
scene = "HOME"
mode = "AI"

wins = [(1,2,3),(4,5,6),(7,8,9),(1,4,7),(2,5,8),(3,6,9),(1,5,9),(3,5,7)]

# --- LOGIC FUNCTIONS ---
def check_win(b, p):
    for a, b_idx, c in wins:
        if b[a] == b[b_idx] == b[c] == p: return True
    return False

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
    best_score = -float('inf')
    move = None
    for cell in get_empty_cells(board):
        board[cell] = 2
        score = minimax(board, 0, False)
        board[cell] = 0
        if score > best_score:
            best_score = score
            move = cell
    if move: board[move] = 2

def get_cell(pos):
    x, y = pos
    if y < 40 or y > 360: return None
    col, row = x // 120, (y - 40) // 120
    cell = row * 3 + col + 1
    return cell if 1 <= cell <= 9 else None

def reset_game():
    global board, player, game_over, winner
    board = [0] * 10
    player = 1
    game_over = False
    winner = 0

# --- DRAWING FUNCTIONS ---
def draw_marks():
    for i in range(1, 10):
        r, c = (i - 1) // 3, (i - 1) % 3
        x, y = c * 120 + 40, r * 120 + 60
        if board[i] == 1: WIN.blit(FONT.render("X", True, X_COLOR), (x, y))
        elif board[i] == 2: WIN.blit(FONT.render("O", True, O_COLOR), (x, y))

def draw_button(text, x, y, w, h, active, color_override=None):
    color = BTN_HOVER if active else (color_override if color_override else BTN_COLOR)
    pygame.draw.rect(WIN, color, (x, y, w, h), border_radius=12)
    txt = SMALL.render(text, True, WHITE)
    WIN.blit(txt, (x + (w - txt.get_width()) // 2, y + (h - txt.get_height()) // 2))

def draw_home():
    WIN.fill(BG)
    title = BIG.render("TIC TAC TOE", True, LINE)
    WIN.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
    m_pos = pygame.mouse.get_pos()
    ai_active = 60 <= m_pos[0] <= 300 and 180 <= m_pos[1] <= 230
    draw_button("VS COMPUTER", 60, 180, 240, 50, ai_active)
    pvp_active = 60 <= m_pos[0] <= 300 and 250 <= m_pos[1] <= 300
    draw_button("VS HUMAN", 60, 250, 240, 50, pvp_active)

def draw_game_ui():
    WIN.fill(BG)
    pygame.draw.line(WIN, LINE, (120, 40), (120, 360), 5)
    pygame.draw.line(WIN, LINE, (240, 40), (240, 360), 5)
    pygame.draw.line(WIN, LINE, (0, 160), (360, 160), 5)
    pygame.draw.line(WIN, LINE, (0, 280), (360, 280), 5)
    m_pos = pygame.mouse.get_pos()
    back_active = 10 <= m_pos[0] <= 80 and 10 <= m_pos[1] <= 35
    pygame.draw.rect(WIN, BACK_BTN_COLOR if not back_active else BTN_HOVER, (10, 10, 70, 25), border_radius=5)
    back_txt = TINY.render("BACK", True, WHITE)
    WIN.blit(back_txt, (10 + (70 - back_txt.get_width()) // 2, 10 + (25 - back_txt.get_height()) // 2))
    status_text = "PVP Mode" if mode == "PVP" else "Vs Computer"
    status = SMALL.render(status_text, True, LINE)
    WIN.blit(status, (WIDTH - status.get_width() - 10, 10))

def draw_end_screen(text):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200); overlay.fill((0, 0, 0))
    WIN.blit(overlay, (0, 0))
    msg = BIG.render(text, True, WHITE)
    WIN.blit(msg, (WIDTH//2 - msg.get_width()//2, 140))
    m_pos = pygame.mouse.get_pos()
    btn_active = 110 <= m_pos[0] <= 250 and 220 <= m_pos[1] <= 270
    draw_button("RESTART", 110, 220, 140, 50, btn_active)

# --- ASYNC MAIN LOOP ---
async def main():
    global scene, mode, player, winner, game_over
    while True:
        if scene == "HOME":
            draw_home()
        else:
            draw_game_ui()
            draw_marks()
            if game_over:
                if winner == 1: draw_end_screen("X WINS!")
                elif winner == 2: draw_end_screen("O WINS!")
                else: draw_end_screen("DRAW!")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if scene == "HOME":
                    if 60 <= event.pos[0] <= 300 and 180 <= event.pos[1] <= 230:
                        mode = "AI"; reset_game(); scene = "GAME"
                    if 60 <= event.pos[0] <= 300 and 250 <= event.pos[1] <= 300:
                        mode = "PVP"; reset_game(); scene = "GAME"
                elif scene == "GAME":
                    if 10 <= event.pos[0] <= 80 and 10 <= event.pos[1] <= 35:
                        scene = "HOME"
                    if game_over:
                        if 110 <= event.pos[0] <= 250 and 220 <= event.pos[1] <= 270:
                            reset_game()
                    elif player == 1 or (player == 2 and mode == "PVP"):
                        cell = get_cell(event.pos)
                        if cell and board[cell] == 0:
                            board[cell] = player
                            if check_win(board, player): winner = player; game_over = True
                            elif check_draw(board): game_over = True
                            else: player = 3 - player

        if scene == "GAME" and mode == "AI" and player == 2 and not game_over:
            computer_move()
            if check_win(board, 2): winner = 2; game_over = True
            elif check_draw(board): game_over = True
            else: player = 1

        pygame.display.update()
        # This line is critical for Trinket/Web! It lets the browser breathe.
        await asyncio.sleep(0)

# Start the game
asyncio.run(main())
