import pygame
import sys
import asyncio
import random
import math
import time
from array import array

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

# ================= SCREEN CONFIG =================
VIRTUAL_W, VIRTUAL_H = 360, 520
window_w, window_h = 450, 650

WIN = pygame.display.set_mode((window_w, window_h), pygame.RESIZABLE)
CANVAS = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
pygame.display.set_caption("Tic Tac Toe Pro")

# ================= COLORS & FONTS =================
BG, LINE = (18, 18, 30), (70, 130, 180)
X_COLOR, O_COLOR = (0, 200, 255), (255, 90, 120)
BTN_COLOR, BTN_HOVER = (30, 30, 60), (60, 60, 120)
WHITE, TEXT_COLOR = (240, 240, 240), (200, 220, 255)
GOLD, GREEN, RED = (255, 215, 0), (50, 205, 50), (255, 69, 58)

TINY = pygame.font.SysFont("sans-serif", 14, bold=True)
SMALL = pygame.font.SysFont("sans-serif", 18, bold=True)
MEDIUM = pygame.font.SysFont("sans-serif", 24, bold=True)
BIG = pygame.font.SysFont("sans-serif", 36, bold=True)

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
S_LOSE = tone(200, 0.3, 0.4)

# ================= GAME STATE =================
board = [0] * 10
player, game_over, winner = 1, False, 0
scene, mode, difficulty = "HOME", "AI", "MEDIUM"

# Competitive stats
player_score, ai_score, draws = 0, 0, 0
player_streak, ai_streak, current_streak = 0, 0, 0
best_time, game_start_time = float('inf'), 0
moves_made = 0

WINS = [(1,2,3),(4,5,6),(7,8,9),(1,4,7),(2,5,8),(3,6,9),(1,5,9),(3,5,7)]

# CORRECTED: Mistake probability (lower = smarter AI)
DIFFICULTY_SETTINGS = {
    "EASY": 0.50,        # 50% mistakes
    "MEDIUM": 0.15,      # 15% mistakes  
    "HARD": 0.05,        # 5% mistakes
    "IMPOSSIBLE": 0.01   # 1% mistakes
}

DIFF_COLORS = {
    "EASY": GREEN,
    "MEDIUM": (255, 165, 0),
    "HARD": RED,
    "IMPOSSIBLE": (138, 43, 226)
}

# ================= LOGIC =================
def check_win(b, p): 
    return any(all(b[i] == p for i in w) for w in WINS)

def check_draw(b): 
    return all(b[i] != 0 for i in range(1, 10))

def get_empty(b): 
    return [i for i in range(1, 10) if b[i] == 0]

def minimax(b, depth, is_maximizing, alpha=-math.inf, beta=math.inf):
    """Minimax with alpha-beta pruning for perfect AI"""
    if check_win(b, 2): return 10 - depth
    if check_win(b, 1): return depth - 10
    if check_draw(b): return 0
    
    if is_maximizing:
        max_eval = -math.inf
        for c in get_empty(b):
            b[c] = 2
            eval_score = minimax(b, depth + 1, False, alpha, beta)
            b[c] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha: break
        return max_eval
    else:
        min_eval = math.inf
        for c in get_empty(b):
            b[c] = 1
            eval_score = minimax(b, depth + 1, True, alpha, beta)
            b[c] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha: break
        return min_eval

def get_best_move():
    """Find optimal move using minimax"""
    best_score = -math.inf
    best_move = None
    for c in get_empty(board):
        board[c] = 2
        score = minimax(board, 0, False)
        board[c] = 0
        if score > best_score:
            best_score = score
            best_move = c
    return best_move

def computer_move():
    """AI move with difficulty-based mistakes"""
    empty = get_empty(board)
    if not empty: return
    
    # Make mistake based on difficulty
    if random.random() < DIFFICULTY_SETTINGS[difficulty]:
        # MISTAKE: Make random move
        board[random.choice(empty)] = 2
    else:
        # OPTIMAL: Use minimax algorithm
        best_move = get_best_move()
        if best_move:
            board[best_move] = 2

def reset_game():
    global board, player, game_over, winner, game_start_time, moves_made
    board = [0] * 10
    player = 1
    game_over = False
    winner = 0
    game_start_time = time.time()
    moves_made = 0

def reset_stats():
    global player_score, ai_score, draws, player_streak, ai_streak, current_streak, best_time
    player_score = ai_score = draws = 0
    player_streak = ai_streak = current_streak = 0
    best_time = float('inf')

# ================= COORDINATE MAPPING =================
def get_scaling_data():
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
    if y < 120 or y > 480: return None
    c, r = int(x // 120), int((y - 120) // 120)
    return r * 3 + c + 1 if 0 <= r <= 2 and 0 <= c <= 2 else None

# ================= DRAWING =================
def button(text, x, y, w, h, v_mouse, color=BTN_COLOR):
    hover = x <= v_mouse[0] <= x+w and y <= v_mouse[1] <= y+h
    pygame.draw.rect(CANVAS, BTN_HOVER if hover else color, (x, y, w, h), border_radius=10)
    t = SMALL.render(text, True, WHITE)
    CANVAS.blit(t, (x + w//2 - t.get_width()//2, y + h//2 - t.get_height()//2))
    return hover

def draw_marks():
    for i in range(1, 10):
        r, c = (i-1)//3, (i-1)%3
        cx, cy = c*120+60, r*120+180
        if board[i] == 1:
            pygame.draw.line(CANVAS, X_COLOR, (cx-30, cy-30), (cx+30, cy+30), 8)
            pygame.draw.line(CANVAS, X_COLOR, (cx+30, cy-30), (cx-30, cy+30), 8)
        elif board[i] == 2:
            pygame.draw.circle(CANVAS, O_COLOR, (cx, cy), 35, 6)

def draw_scoreboard():
    """Draw competitive scoreboard at top"""
    # Background bar
    pygame.draw.rect(CANVAS, (25, 25, 40), (0, 0, VIRTUAL_W, 50))
    
    # Player X score
    x_txt = SMALL.render(f"X: {player_score}", True, X_COLOR)
    CANVAS.blit(x_txt, (15, 8))
    
    # Draw count
    draw_txt = SMALL.render(f"DRAW: {draws}", True, WHITE)
    CANVAS.blit(draw_txt, (VIRTUAL_W//2 - draw_txt.get_width()//2, 8))
    
    # AI O score
    o_txt = SMALL.render(f"O: {ai_score}", True, O_COLOR)
    CANVAS.blit(o_txt, (VIRTUAL_W - o_txt.get_width() - 15, 8))
    
    # Streaks
    if current_streak > 1:
        streak_txt = TINY.render(f"🔥 {current_streak} STREAK!", True, GOLD)
        CANVAS.blit(streak_txt, (VIRTUAL_W//2 - streak_txt.get_width()//2, 30))
    
    # Difficulty indicator
    diff_color = DIFF_COLORS.get(difficulty, WHITE)
    diff_txt = TINY.render(f"{difficulty}", True, diff_color)
    CANVAS.blit(diff_txt, (15, 30))
    
    # Timer
    if not game_over and game_start_time > 0:
        elapsed = int(time.time() - game_start_time)
        timer_txt = TINY.render(f"⏱️ {elapsed}s", True, WHITE)
        CANVAS.blit(timer_txt, (VIRTUAL_W - timer_txt.get_width() - 15, 30))

# ================= MAIN LOOP =================
async def main():
    global scene, player, game_over, winner, difficulty, mode
    global player_score, ai_score, draws, player_streak, ai_streak, current_streak, best_time, moves_made
    
    clock = pygame.time.Clock()
    hovered_lvl = None

    while True:
        v_mouse = get_virtual_mouse()
        mx, my = v_mouse
        CANVAS.fill(BG)

        if scene == "HOME":
            CANVAS.blit(BIG.render("TIC TAC TOE PRO", True, TEXT_COLOR), (40, 100))
            
            # Stats display
            if player_score + ai_score + draws > 0:
                stats = TINY.render(f"Record: {player_score}W-{ai_score}L-{draws}D | Best Streak: {max(player_streak, ai_streak)}", True, WHITE)
                CANVAS.blit(stats, (VIRTUAL_W//2 - stats.get_width()//2, 160))
            
            button("VS COMPUTER", 60, 220, 240, 50, v_mouse)
            button("VS HUMAN", 60, 290, 240, 50, v_mouse)
            
            if player_score + ai_score + draws > 0:
                if button("RESET STATS", 90, 370, 180, 40, v_mouse, (60, 30, 30)):
                    pass  # Hover only
        
        elif scene == "DIFFICULTY":
            CANVAS.blit(BIG.render("SELECT LEVEL", True, TEXT_COLOR), (60, 80))
            
            levels = [
                ("EASY", 160, "50% mistakes"),
                ("MEDIUM", 230, "15% mistakes"),
                ("HARD", 300, "5% mistakes"),
                ("IMPOSSIBLE", 370, "1% mistakes")
            ]
            
            hovered_lvl = None
            for l, y, desc in levels:
                if button(l, 80, y, 200, 45, v_mouse, DIFF_COLORS.get(l, BTN_COLOR)):
                    hovered_lvl = l
                # Description
                desc_txt = TINY.render(desc, True, WHITE)
                CANVAS.blit(desc_txt, (VIRTUAL_W//2 - desc_txt.get_width()//2, y + 50))

        elif scene == "GAME":
            draw_scoreboard()
            
            # Grid lines
            for i in range(1, 3):
                pygame.draw.line(CANVAS, LINE, (120*i, 120), (120*i, 480), 3)
                pygame.draw.line(CANVAS, LINE, (0, 120+120*i), (360, 120+120*i), 3)
            
            draw_marks()
            
            if not game_over:
                turn_txt = SMALL.render(f"{'X' if player==1 else 'O'} TURN", True, X_COLOR if player==1 else O_COLOR)
                CANVAS.blit(turn_txt, (VIRTUAL_W//2 - turn_txt.get_width()//2, 70))
            else:
                # Game over message
                if winner == 0:
                    msg = "DRAW!"
                    color = WHITE
                elif winner == 1:
                    msg = "YOU WIN! 🎉"
                    color = GREEN
                else:
                    msg = "AI WINS!"
                    color = RED
                
                result_txt = MEDIUM.render(msg, True, color)
                CANVAS.blit(result_txt, (VIRTUAL_W//2 - result_txt.get_width()//2, 250))
                
                # Time info
                if winner == 1 and game_start_time > 0:
                    game_time = time.time() - game_start_time
                    time_txt = TINY.render(f"Time: {game_time:.1f}s | Moves: {moves_made}", True, WHITE)
                    CANVAS.blit(time_txt, (VIRTUAL_W//2 - time_txt.get_width()//2, 285))
                
                button("PLAY AGAIN", 90, 320, 180, 40, v_mouse, GREEN)
                button("HOME", 90, 370, 180, 40, v_mouse)
            
            # Show stats in corner
            total_games = player_score + ai_score + draws
            if total_games > 0:
                winrate = int((player_score / total_games) * 100)
                rate_txt = TINY.render(f"Win Rate: {winrate}%", True, WHITE)
                CANVAS.blit(rate_txt, (10, 495))

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                if scene == "HOME":
                    if 60 <= mx <= 300:
                        if 220 <= my <= 270:
                            mode = "AI"
                            scene = "DIFFICULTY"
                            S_CLICK.play()
                        elif 290 <= my <= 340:
                            mode = "PVP"
                            reset_game()
                            scene = "GAME"
                            S_CLICK.play()
                        elif 90 <= mx <= 270 and 370 <= my <= 410:
                            reset_stats()
                            S_CLICK.play()
                
                elif scene == "DIFFICULTY":
                    if 80 <= mx <= 280 and hovered_lvl:
                        difficulty = hovered_lvl
                        reset_game()
                        scene = "GAME"
                        S_CLICK.play()

                elif scene == "GAME":
                    if game_over:
                        if 90 <= mx <= 270:
                            if 320 <= my <= 360:
                                reset_game()
                                S_CLICK.play()
                            elif 370 <= my <= 410:
                                scene = "HOME"
                                S_CLICK.play()
                    else:
                        c = get_cell(v_mouse)
                        if c and board[c] == 0:
                            board[c] = player
                            moves_made += 1
                            S_CLICK.play()
                            
                            if check_win(board, player):
                                winner = player
                                game_over = True
                                
                                if mode == "AI":
                                    if winner == 1:
                                        player_score += 1
                                        current_streak += 1
                                        player_streak = max(player_streak, current_streak)
                                        game_time = time.time() - game_start_time
                                        best_time = min(best_time, game_time)
                                        S_WIN.play()
                                    else:
                                        ai_score += 1
                                        current_streak = 0
                                        S_LOSE.play()
                                else:
                                    S_WIN.play()
                                    
                            elif check_draw(board):
                                game_over = True
                                draws += 1
                                current_streak = 0
                                S_DRAW.play()
                            else:
                                player = 2 if player == 1 else 1

        # AI move
        if scene == "GAME" and mode == "AI" and player == 2 and not game_over:
            await asyncio.sleep(0.4)
            computer_move()
            moves_made += 1
            
            if check_win(board, 2):
                winner = 2
                game_over = True
                ai_score += 1
                current_streak = 0
                S_LOSE.play()
            elif check_draw(board):
                game_over = True
                draws += 1
                current_streak = 0
                S_DRAW.play()
            else:
                player = 1

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
