import pygame
import time

def display_after_session_menu(screen, config):
    #Get Configurations
    BLACK = config['BLACK']
    WHITE = config['WHITE']
    GREEN = config['GREEN']
    RED = config['RED']
    large_font = config['large_font']
    medium_font = config['medium_font']
    infoObject = config['infoObject']

    screen.fill(BLACK)
    question_text = large_font.render("Do you want to continue?", True, WHITE)
    continue_text = medium_font.render("Press Y to continue", True, GREEN)
    quit_text = medium_font.render("Press N to exit", True, RED)

    # Positioning Text
    question_rect = question_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 4))
    continue_rect = continue_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2 - 50))
    quit_rect = quit_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2 + 50))

    # Blit Text to Screen
    screen.blit(question_text, question_rect)
    screen.blit(continue_text, continue_rect)
    screen.blit(quit_text, quit_rect)
    pygame.display.flip()


def display_in_trial_menu(screen, config):
    #Get Configurations
    BLACK = config['BLACK']
    WHITE = config['WHITE']
    GREEN = config['GREEN']
    RED = config['RED']
    medium_font = config['medium_font']
    infoObject = config['infoObject']

    screen.fill(BLACK)
    menu_title = medium_font.render("Trial Menu", True, WHITE)
    quit_text = medium_font.render("Press Q to Quit", True, RED)
    resume_text = medium_font.render("Press R to Resume", True, GREEN)

    # Positioning Text
    menu_title_rect = menu_title.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 3))
    quit_rect = quit_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2))
    resume_rect = resume_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2 + 100))

    # Blit Text to Screen
    screen.blit(menu_title, menu_title_rect)
    screen.blit(quit_text, quit_rect)
    screen.blit(resume_text, resume_rect)
    pygame.display.flip()

def display_input_menu(screen, config, input_text, input_error):
    #Get Configurations
    BLACK = config['BLACK']
    WHITE = config['WHITE']
    GREEN = config['GREEN']
    RED = config['RED']
    medium_font = config['medium_font']
    small_font = config['small_font']
    infoObject = config['infoObject']

    screen.fill(BLACK)
    prompt_text = medium_font.render("Enter Number of Recordings (Multiple of 3):", True, WHITE)
    input_display = medium_font.render(input_text, True, GREEN if not input_error else RED)
    instructions_text = small_font.render("Press Enter to Confirm", True, WHITE)

    # Positioning Text
    prompt_rect = prompt_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 3))
    input_rect = input_display.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2))
    instructions_rect = instructions_text.get_rect(center=(infoObject.current_w // 2, infoObject.current_h // 2 + 100))

    # Blit Text to Screen
    screen.blit(prompt_text, prompt_rect)
    screen.blit(input_display, input_rect)
    screen.blit(instructions_text, instructions_rect)
    pygame.display.flip()

def display_menu(screen, config):
# Display Main Menu

    #Get Configurations
    BLACK = config['BLACK']
    WHITE = config['WHITE']
    GREEN = config['GREEN']
    RED = config['RED']
    large_font = config['large_font']
    medium_font = config['medium_font']
    small_font = config['small_font']
    total_trials = config['total_trials']
    infoObject = config['infoObject']
    start_enable_time = config['start_enable_time']


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