import random
import pygame as pg

pg.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 50, 50)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)

# Шрифты
font = pg.font.Font(None, 36)
big_font = pg.font.Font(None, 72)
small_font = pg.font.Font(None, 24)


def text_render(text, size=36, color=WHITE):
    if size == 72:
        f = big_font
    elif size == 24:
        f = small_font
    else:
        f = font
    return f.render(str(text), True, color)


class Paddle:
    def __init__(self, x, y, width=15, height=100, speed=7, color=WHITE):
        self.rect = pg.Rect(x, y, width, height)
        self.speed = speed
        self.score = 0
        self.color = color

    def move(self, up_key, down_key):
        keys = pg.key.get_pressed()
        if keys[up_key] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[down_key] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed

    def move_bot(self, ball, difficulty):
        if difficulty == 0:  # Легкий
            speed_factor = 0.5
            offset = 50
        elif difficulty == 1:  # Средний
            speed_factor = 0.7
            offset = 30
        else:  # Сложный
            speed_factor = 0.95
            offset = 10

        if self.rect.centery < ball.rect.centery - offset:
            self.rect.y += self.speed * speed_factor
        elif self.rect.centery > ball.rect.centery + offset:
            self.rect.y -= self.speed * speed_factor

        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def draw(self, screen):
        pg.draw.rect(screen, self.color, self.rect)


class Ball:
    def __init__(self, size=15, speed_x=5, speed_y=5):
        self.rect = pg.Rect(SCREEN_WIDTH // 2 - size // 2, SCREEN_HEIGHT // 2 - size // 2, size, size)
        self.size = size
        self.speed_x = random.choice([-speed_x, speed_x])
        self.speed_y = random.choice([-speed_y, speed_y])
        self.base_speed = speed_x

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.speed_y = -self.speed_y

    def reset(self, speed_multiplier=1):
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed_x = random.choice([-self.base_speed * speed_multiplier, self.base_speed * speed_multiplier])
        self.speed_y = random.choice([-self.base_speed * speed_multiplier, self.base_speed * speed_multiplier])

    def draw(self, screen, color=WHITE):
        pg.draw.ellipse(screen, color, self.rect)


class Game():
    def __init__(self):
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Ping Pong")
        self.clock = pg.time.Clock()
        self.running = True

        self.mode = "menu"
        self.game_state = "playing"
        self.difficulty = 1  # 0 - легкий, 1 - средний, 2 - сложный
        self.speed_multiplier = 1

        self.left_paddle = Paddle(30, SCREEN_HEIGHT // 2 - 50, color=BLUE)
        self.right_paddle = Paddle(SCREEN_WIDTH - 45, SCREEN_HEIGHT // 2 - 50, color=RED)
        self.ball = Ball()

        self.win_score = 5
        self.goal_timer = 0
        self.goal_delay = 60

        # Таймер игры (5 минут = 300 секунд)
        self.game_time = 300
        self.time_limit = 300
        self.start_ticks = 0

        self.menu_items = []
        self.menu_rects = []
        self.setup_menu()

        self.run()

    def setup_menu(self):
        """Настройка меню с выбором сложности"""
        self.menu_items = [
            {"text": "1. Игра против робота", "y": SCREEN_HEIGHT // 2 - 100},
            {"text": "2. Игра для двух игроков", "y": SCREEN_HEIGHT // 2},
            {"text": "Выбор сложности:", "y": SCREEN_HEIGHT // 2 + 100, "size": 24},
            {"text": "  Легкий", "y": SCREEN_HEIGHT // 2 + 140, "difficulty": 0},
            {"text": "  Средний", "y": SCREEN_HEIGHT // 2 + 180, "difficulty": 1},
            {"text": "  Сложный", "y": SCREEN_HEIGHT // 2 + 220, "difficulty": 2}
        ]

        self.menu_rects = []
        for item in self.menu_items:
            size = item.get("size", 36)
            text = text_render(item["text"], size)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, item["y"]))
            self.menu_rects.append(rect)

        self.title_text = text_render("ПИНГ-ПОНГ", 72)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))

    def event(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.mode = "menu"
                    self.reset_game()

            if event.type == pg.MOUSEBUTTONDOWN and self.mode == "menu":
                mouse_pos = pg.mouse.get_pos()
                for i, rect in enumerate(self.menu_rects):
                    if rect.collidepoint(mouse_pos):
                        if i == 0:  # Игра против робота
                            self.mode = "game_with_bot"
                            self.start_game()
                        elif i == 1:  # Игра для двух игроков
                            self.mode = "game_2players"
                            self.start_game()
                        elif i == 3:  # Легкий
                            self.difficulty = 0
                            self.speed_multiplier = 0.7
                        elif i == 4:  # Средний
                            self.difficulty = 1
                            self.speed_multiplier = 1.0
                        elif i == 5:  # Сложный
                            self.difficulty = 2
                            self.speed_multiplier = 1.5

    def start_game(self):
        """Запуск игры с таймером"""
        self.start_ticks = pg.time.get_ticks()
        self.game_time = self.time_limit
        self.reset_game()

    def reset_game(self):
        self.left_paddle.score = 0
        self.right_paddle.score = 0
        self.left_paddle.rect.centery = SCREEN_HEIGHT // 2
        self.right_paddle.rect.centery = SCREEN_HEIGHT // 2
        self.ball.reset(self.speed_multiplier)
        self.game_state = "playing"
        self.goal_timer = 0

    def check_collisions(self):
        if self.ball.rect.colliderect(self.left_paddle.rect) and self.ball.speed_x < 0:
            self.ball.speed_x = -self.ball.speed_x
            self.ball.speed_y += random.uniform(-1, 1)
            if abs(self.ball.speed_x) < 10:
                self.ball.speed_x *= 1.05

        if self.ball.rect.colliderect(self.right_paddle.rect) and self.ball.speed_x > 0:
            self.ball.speed_x = -self.ball.speed_x
            self.ball.speed_y += random.uniform(-1, 1)
            if abs(self.ball.speed_x) < 10:
                self.ball.speed_x *= 1.05

        if self.ball.rect.left < 0:
            self.right_paddle.score += 1
            self.game_state = "goal"
            self.goal_timer = self.goal_delay

        if self.ball.rect.right > SCREEN_WIDTH:
            self.left_paddle.score += 1
            self.game_state = "goal"
            self.goal_timer = self.goal_delay

        if self.left_paddle.score >= self.win_score or self.right_paddle.score >= self.win_score:
            self.game_state = "game_over"

    def update(self):
        if self.mode == "game_with_bot":
            self.left_paddle.move(pg.K_UP, pg.K_DOWN)
            self.right_paddle.move_bot(self.ball, self.difficulty)

        elif self.mode == "game_2players":
            self.left_paddle.move(pg.K_w, pg.K_s)
            self.right_paddle.move(pg.K_UP, pg.K_DOWN)

        if self.game_state == "playing":
            # Обновление таймера
            elapsed_seconds = (pg.time.get_ticks() - self.start_ticks) // 1000
            self.game_time = max(0, self.time_limit - elapsed_seconds)

            # Проверка окончания времени
            if self.game_time <= 0:
                self.game_state = "game_over"
                self.game_time = 0

            self.ball.move()
            self.check_collisions()
        elif self.game_state == "goal":
            self.goal_timer -= 1
            if self.goal_timer <= 0:
                self.ball.reset(self.speed_multiplier)
                self.game_state = "playing"

    def draw(self):
        if self.mode == "menu":
            self.draw_menu()
        else:
            self.draw_game()

        pg.display.update()

    def draw_menu(self):
        self.screen.fill(BLACK)
        self.screen.blit(self.title_text, self.title_rect)

        for i, item in enumerate(self.menu_items):
            rect = self.menu_rects[i]
            size = item.get("size", 36)
            text = text_render(item["text"], size)

            # Подсветка при наведении
            if rect.collidepoint(pg.mouse.get_pos()):
                text = text_render(item["text"], size, BLUE)

            # Отображение выбранной сложности
            if "difficulty" in item:
                if item["difficulty"] == self.difficulty:
                    text = text_render("✓ " + item["text"].strip(), size, GREEN)

            self.screen.blit(text, rect)

        # Отображение текущей сложности
        diff_texts = ["Легкий", "Средний", "Сложный"]
        current_diff = text_render(f"Текущая сложность: {diff_texts[self.difficulty]}", 24, YELLOW)
        diff_rect = current_diff.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(current_diff, diff_rect)

    def draw_game(self):
        self.screen.fill(BLACK)

        # Центральная линия
        for y in range(0, SCREEN_HEIGHT, 40):
            pg.draw.rect(self.screen, GRAY, (SCREEN_WIDTH // 2 - 2, y, 4, 20))

        self.left_paddle.draw(self.screen)
        self.right_paddle.draw(self.screen)
        self.ball.draw(self.screen, WHITE)

        # Отображение счета
        left_score = text_render(str(self.left_paddle.score), 72, BLUE)
        right_score = text_render(str(self.right_paddle.score), 72, RED)
        self.screen.blit(left_score, (SCREEN_WIDTH // 4 - 30, 20))
        self.screen.blit(right_score, (SCREEN_WIDTH * 3 // 4 - 30, 20))

        # Отображение таймера
        minutes = self.game_time // 60
        seconds = self.game_time % 60
        time_text = text_render(f"{minutes:02d}:{seconds:02d}", 36, YELLOW)
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2, 20))
        self.screen.blit(time_text, time_rect)

        # Отображение сложности
        diff_texts = ["Легкий", "Средний", "Сложный"]
        diff_display = text_render(f"Сложность: {diff_texts[self.difficulty]}", 24, GRAY)
        diff_rect = diff_display.get_rect(center=(SCREEN_WIDTH // 2, 55))
        self.screen.blit(diff_display, diff_rect)

        if self.game_state == "goal":
            goal_text = text_render("ГОЛ!", 72, GREEN)
            goal_rect = goal_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
            self.screen.blit(goal_text, goal_rect)

        if self.game_state == "game_over":
            if self.left_paddle.score > self.right_paddle.score:
                winner = "Игрок 1"
                win_color = BLUE
            elif self.right_paddle.score > self.left_paddle.score:
                winner = "Игрок 2" if self.mode == "game_2players" else "Робот"
                win_color = RED
            else:
                winner = "Ничья!"
                win_color = YELLOW

            if self.game_time <= 0:
                reason = "Время вышло!"
            else:
                reason = "Победа!"

            win_text = text_render(f"{winner} победил!", 72, win_color)
            win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
            self.screen.blit(win_text, win_rect)

            reason_text = text_render(reason, 36, WHITE)
            reason_rect = reason_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            self.screen.blit(reason_text, reason_rect)

            if self.left_paddle.score > self.right_paddle.score:
                self.left_paddle.draw(self.screen)
            elif self.right_paddle.score > self.left_paddle.score:
                self.right_paddle.draw(self.screen)

    def run(self):
        while self.running:
            self.event()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pg.quit()


if __name__ == "__main__":
    Game()