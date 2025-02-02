import pygame
import time
from Noise_Model import noise_model

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

total_trials = 10

# Fonts
large_font = pygame.font.SysFont(None, 200)
medium_font = pygame.font.SysFont(None, 100)
small_font = pygame.font.SysFont(None, 50)

start_enable_time = 10

infoObject = pygame.display.Info()

class GUI:
    def init_gui():
         # Initialize Pygame
        pygame.init()
        screen = pygame.display.set_mode((infoObject.current_w, infoObject.current_h), pygame.FULLSCREEN)
        pygame.display.set_caption("Motor Imagery Task")

    def show_menu(screen):
        # Display Main Menu
            screen.fill(BLACK)
            title_text = large_font.render("EEG Motor Imagery", True, WHITE)
            start_text = medium_font.render("Press S to Start", True, GREEN)
            set_text = medium_font.render("Press N to Set Number", True, WHITE)
            quit_text = medium_font.render("Press Q to Quit", True, RED)
            trials_text = small_font.render(f"Total Trials: {total_trials}", True, WHITE)
            wait_text = small_font.render(f"You have to wait {round(start_enable_time - time.time())} seconds before starting!", True, WHITE)

            # Positioning Text
            title_rect = title_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 4))
            start_rect = start_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2 - 50))
            set_rect = set_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2 + 50))
            quit_rect = quit_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2 + 150))
            trials_rect = trials_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2 - 150))
            wait_rect = wait_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2 + 250))

            # Blit Text to Screen
            screen.blit(title_text, title_rect)
            screen.blit(start_text, start_rect)
            screen.blit(set_text, set_rect)
            screen.blit(quit_text, quit_rect)
            screen.blit(trials_text, trials_rect)
            if (start_enable_time > time.time()): # If the start button is currently disabled
                screen.blit(wait_text, wait_rect)
            pygame.display.flip()