import pygame
import random
import math
from bisect import bisect_left, bisect_right

# THis is solution including binary search and prefix sums
def max_total_fruits(fruits, start_pos, k):
    positions = [pos for pos, _ in fruits]
    amounts = [amt for _, amt in fruits]
    prefix_sum = [0]
    for amt in amounts:
        prefix_sum.append(prefix_sum[-1] + amt)
    
    def get_sum(l, r):
        return prefix_sum[r+1] - prefix_sum[l]
    
    left = bisect_left(positions, start_pos - k)
    res = 0
    curr = 0
    l = left
    for r in range(left, len(fruits)):
        if positions[r] > start_pos + k:
            break
        curr += fruits[r][1]
        while l <= r:
            dist1 = abs(start_pos - positions[l]) + (positions[r] - positions[l])
            dist2 = abs(start_pos - positions[r]) + (positions[r] - positions[l])
            if min(dist1, dist2) <= k:
                break
            curr -= fruits[l][1]
            l += 1
        res = max(res, curr)
    return res

class Particle:
    def __init__(self, x, y, color, velocity):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity
        self.life = 30
        self.max_life = 30
    
    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.velocity[1] += 0.2  # gravity
        self.life -= 1
    
    def draw(self, screen):
        alpha = self.life / self.max_life
        size = int(3 * alpha)
        if size > 0:
            color = (*self.color, int(255 * alpha))
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (size, size), size)
            screen.blit(s, (self.x - size, self.y - size))

class FloatingText:
    def __init__(self, text, x, y, color=(255, 255, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.start_y = y
        self.color = color
        self.life = 60
        self.max_life = 60
    
    def update(self):
        self.y = self.start_y - (1 - self.life / self.max_life) * 30
        self.life -= 1
    
    def draw(self, screen, font):
        alpha = self.life / self.max_life
        if alpha > 0:
            text_surface = font.render(self.text, True, self.color)
            text_surface.set_alpha(int(255 * alpha))
            screen.blit(text_surface, (self.x, self.y))

# Enhanced game class
class FruitHarvestGame:
    def __init__(self):
        # Config
        self.SCREEN_WIDTH = 1200
        self.SCREEN_HEIGHT = 800
        self.FRUIT_RADIUS = 15
        self.FONT_SIZE = 28
        self.NUM_POSITIONS = 50
        self.k = 20
        
        # Colors
        self.BG_COLOR = (20, 25, 40)
        self.GROUND_COLOR = (50, 80, 50)
        self.PLAYER_COLOR = (100, 150, 255)
        self.UI_COLOR = (255, 255, 255)
        self.FRUIT_COLORS = [
            (255, 100, 100),  # Red apple
            (255, 165, 0),    # Orange
            (255, 255, 100),  # Banana
            (128, 255, 128),  # Green apple
            (255, 100, 255),  # Purple grape
        ]
        
        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("🍎 Fruit Harvest Adventure 🍊")
        self.font = pygame.font.Font(None, self.FONT_SIZE)
        self.big_font = pygame.font.Font(None, 48)
        self.clock = pygame.time.Clock()
        
        # Game state
        self.reset_game()
        
        # Visual effects
        self.particles = []
        self.floating_texts = []
        self.camera_shake = 0
        self.time = 0
    
    def reset_game(self):
        self.start_pos = 25
        self.fruits = sorted([[i, random.randint(1, 5)] for i in random.sample(range(self.NUM_POSITIONS), 12)])
        
        self.scale = (self.SCREEN_WIDTH - 100) // self.NUM_POSITIONS
        self.player_x = self.start_pos
        self.steps_left = self.k
        self.collected = 0
        self.eaten = set()
        self.game_over = False
        self.won = False
        
        # Animation variables
        self.player_bounce = 0
        self.fruit_animations = {}
        for pos, _ in self.fruits:
            self.fruit_animations[pos] = {
                'bounce': random.random() * 6.28,
                'collected': False,
                'collection_time': 0
            }
    
    def add_particles(self, x, y, color, count=8):
        for _ in range(count):
            velocity = [random.uniform(-3, 3), random.uniform(-5, -1)]
            self.particles.append(Particle(x, y, color, velocity))
    
    def add_floating_text(self, text, x, y, color=(255, 255, 255)):
        self.floating_texts.append(FloatingText(text, x, y, color))
    
    def draw_background(self):
        # Gradient background
        for y in range(self.SCREEN_HEIGHT):
            color_ratio = y / self.SCREEN_HEIGHT
            r = int(self.BG_COLOR[0] * (1 - color_ratio) + 40 * color_ratio)
            g = int(self.BG_COLOR[1] * (1 - color_ratio) + 60 * color_ratio)
            b = int(self.BG_COLOR[2] * (1 - color_ratio) + 80 * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.SCREEN_WIDTH, y))
        
        # Ground
        ground_y = self.SCREEN_HEIGHT - 150
        pygame.draw.rect(self.screen, self.GROUND_COLOR, 
                        (0, ground_y, self.SCREEN_WIDTH, 150))
        
        # Grass effect
        for i in range(0, self.SCREEN_WIDTH, 10):
            height = random.randint(5, 15)
            pygame.draw.line(self.screen, (60, 120, 60), 
                           (i, ground_y), (i, ground_y - height), 2)
    
    def draw_fruits(self):
        ground_y = self.SCREEN_HEIGHT - 150
        
        for pos, amount in self.fruits:
            x = 50 + pos * self.scale
            
            # Fruit animation
            anim = self.fruit_animations[pos]
            anim['bounce'] += 0.1
            bounce_offset = math.sin(anim['bounce']) * 3
            
            if pos in self.eaten:
                # Collection animation
                if not anim['collected']:
                    anim['collected'] = True
                    anim['collection_time'] = self.time
                    self.add_particles(x, ground_y - 30, self.FRUIT_COLORS[amount % len(self.FRUIT_COLORS)])
                    self.add_floating_text(f"+{amount}", x, ground_y - 60, (255, 255, 100))
                continue
            
            fruit_y = ground_y - 30 + bounce_offset
            
            # Fruit shadow
            shadow_y = ground_y - 10
            shadow_surface = pygame.Surface((self.FRUIT_RADIUS * 2, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surface, (0, 0, 0, 50), 
                              (0, 0, self.FRUIT_RADIUS * 2, 8))
            self.screen.blit(shadow_surface, (x - self.FRUIT_RADIUS, shadow_y))
            
            # Fruit body
            color = self.FRUIT_COLORS[amount % len(self.FRUIT_COLORS)]
            pygame.draw.circle(self.screen, color, (int(x), int(fruit_y)), self.FRUIT_RADIUS)
            
            # Fruit highlight
            highlight_color = tuple(min(255, c + 60) for c in color)
            pygame.draw.circle(self.screen, highlight_color, 
                             (int(x - 4), int(fruit_y - 4)), self.FRUIT_RADIUS // 3)
            
            # Amount text with background
            text = self.font.render(str(amount), True, (255, 255, 255))
            text_rect = text.get_rect(center=(x, fruit_y - 40))
            
            # Text background circle
            pygame.draw.circle(self.screen, (0, 0, 0, 150), text_rect.center, 12)
            self.screen.blit(text, text_rect)
    
    def draw_player(self):
        ground_y = self.SCREEN_HEIGHT - 150
        px = 50 + self.player_x * self.scale
        
        # Player bounce animation
        self.player_bounce += 0.2
        bounce_offset = math.sin(self.player_bounce) * 2
        
        # Camera shake
        shake_x = random.randint(-self.camera_shake, self.camera_shake) if self.camera_shake > 0 else 0
        shake_y = random.randint(-self.camera_shake, self.camera_shake) if self.camera_shake > 0 else 0
        
        player_y = ground_y - 80 + bounce_offset + shake_y
        player_x = px + shake_x
        
        # Player shadow
        shadow_surface = pygame.Surface((20, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, (0, 0, 0, 80), (0, 0, 20, 8))
        self.screen.blit(shadow_surface, (player_x - 10, ground_y - 10))
        
        # Player body (simple character)
        # Head
        pygame.draw.circle(self.screen, self.PLAYER_COLOR, (int(player_x), int(player_y - 20)), 8)
        # Body
        pygame.draw.rect(self.screen, self.PLAYER_COLOR, 
                        (player_x - 6, player_y - 12, 12, 20))
        # Arms
        pygame.draw.circle(self.screen, self.PLAYER_COLOR, (int(player_x - 10), int(player_y - 5)), 3)
        pygame.draw.circle(self.screen, self.PLAYER_COLOR, (int(player_x + 10), int(player_y - 5)), 3)
        # Legs
        pygame.draw.circle(self.screen, self.PLAYER_COLOR, (int(player_x - 4), int(player_y + 10)), 3)
        pygame.draw.circle(self.screen, self.PLAYER_COLOR, (int(player_x + 4), int(player_y + 10)), 3)
        
        # Eyes
        pygame.draw.circle(self.screen, (255, 255, 255), (int(player_x - 3), int(player_y - 22)), 2)
        pygame.draw.circle(self.screen, (255, 255, 255), (int(player_x + 3), int(player_y - 22)), 2)
        pygame.draw.circle(self.screen, (0, 0, 0), (int(player_x - 3), int(player_y - 22)), 1)
        pygame.draw.circle(self.screen, (0, 0, 0), (int(player_x + 3), int(player_y - 22)), 1)
    
    def draw_ui(self):
        # UI Background
        ui_surface = pygame.Surface((self.SCREEN_WIDTH, 80), pygame.SRCALPHA)
        pygame.draw.rect(ui_surface, (0, 0, 0, 150), (0, 0, self.SCREEN_WIDTH, 80))
        self.screen.blit(ui_surface, (0, 0))
        
        # Steps left with progress bar
        steps_text = f"Steps: {self.steps_left}/{self.k}"
        text_surface = self.font.render(steps_text, True, self.UI_COLOR)
        self.screen.blit(text_surface, (20, 20))
        
        # Progress bar
        bar_width = 200
        bar_height = 10
        bar_x = 20
        bar_y = 50
        
        # Background bar
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        # Progress bar
        progress = (self.k - self.steps_left) / self.k
        progress_width = int(bar_width * progress)
        color = (255, 100, 100) if progress > 0.8 else (100, 255, 100)
        pygame.draw.rect(self.screen, color, (bar_x, bar_y, progress_width, bar_height))
        
        # Collected fruits
        collected_text = f"Collected: {self.collected}"
        text_surface = self.font.render(collected_text, True, (255, 255, 100))
        self.screen.blit(text_surface, (300, 20))
        
        # Instructions
        if self.steps_left > 0:
            instruction_text = "Use ← → arrow keys to move"
            text_surface = self.font.render(instruction_text, True, (200, 200, 200))
            text_rect = text_surface.get_rect(center=(self.SCREEN_WIDTH // 2, 50))
            self.screen.blit(text_surface, text_rect)
    
    def update_effects(self):
        # Update particles
        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update()
        
        # Update floating texts
        self.floating_texts = [t for t in self.floating_texts if t.life > 0]
        for text in self.floating_texts:
            text.update()
        
        # Camera shake decay
        if self.camera_shake > 0:
            self.camera_shake -= 1
    
    def draw_effects(self):
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw floating texts
        for text in self.floating_texts:
            text.draw(self.screen, self.font)
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        moved = False
        
        if self.steps_left > 0 and not self.game_over:
            if keys[pygame.K_LEFT] and self.player_x > 0:
                self.player_x -= 1
                moved = True
            elif keys[pygame.K_RIGHT] and self.player_x < self.NUM_POSITIONS - 1:
                self.player_x += 1
                moved = True
            
            if moved:
                self.steps_left -= 1
                self.camera_shake = 2
                
                # Check for fruit collection
                for pos, amt in self.fruits:
                    if pos == self.player_x and pos not in self.eaten:
                        self.collected += amt
                        self.eaten.add(pos)
                        self.camera_shake = 5
                        break
    
    def check_game_end(self):
        if self.steps_left == 0 and not self.game_over:
            self.game_over = True
            max_possible = max_total_fruits(self.fruits, self.start_pos, self.k)
            self.won = self.collected == max_possible
            
            # Add dramatic effect
            self.camera_shake = 10
            center_x = self.SCREEN_WIDTH // 2
            center_y = self.SCREEN_HEIGHT // 2
            
            if self.won:
                self.add_particles(center_x, center_y, (255, 255, 100), 20)
                self.add_floating_text("PERFECT!", center_x - 50, center_y - 100, (255, 255, 100))
            
            print(f"Game Over! {'WIN' if self.won else 'LOSE'} - Collected: {self.collected} / Max: {max_possible}")
    
    def draw_game_over(self):
        if not self.game_over:
            return
            
        # Semi-transparent overlay
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 150), (0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        max_possible = max_total_fruits(self.fruits, self.start_pos, self.k)
        result_text = "🎉 PERFECT HARVEST! 🎉" if self.won else "🍎 Game Over 🍎"
        color = (100, 255, 100) if self.won else (255, 100, 100)
        
        text_surface = self.big_font.render(result_text, True, color)
        text_rect = text_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(text_surface, text_rect)
        
        # Score text
        score_text = f"Collected: {self.collected} / Max Possible: {max_possible}"
        score_surface = self.font.render(score_text, True, (255, 255, 255))
        score_rect = score_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
        self.screen.blit(score_surface, score_rect)
        
        # Restart instruction
        restart_text = "Press R to play again or ESC to quit"
        restart_surface = self.font.render(restart_text, True, (200, 200, 200))
        restart_rect = restart_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(restart_surface, restart_rect)
    
    def run(self):
        running = True
        
        while running:
            self.time += 1
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset_game()
            
            if not self.game_over:
                self.handle_input()
                self.check_game_end()
            
            self.update_effects()
            
            # Draw everything
            self.draw_background()
            self.draw_fruits()
            self.draw_player()
            self.draw_effects()
            self.draw_ui()
            self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

# Run the game
if __name__ == "__main__":
    game = FruitHarvestGame()
    game.run()