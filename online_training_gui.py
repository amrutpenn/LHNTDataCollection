import pygame
import sys
import time
import numpy as np
from eeg_processor import EEGProcessor
from Noise_Model import noise_model
import display_functions

def main():
    eeg_processor = EEGProcessor()

    # Initialize Pygame
    pygame.init()
    infoObject = pygame.display.Info()
    screen = pygame.display.set_mode((infoObject.current_w, infoObject.current_h), pygame.FULLSCREEN)
    pygame.display.set_caption("Motor Imagery Task")

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)

    # Fonts
    large_font = pygame.font.SysFont(None, 200)
    medium_font = pygame.font.SysFont(None, 100)
    small_font = pygame.font.SysFont(None, 50)


    # Control Variables
    running = True
    in_menu = True
    in_input = False
    in_trial_menu = False
    in_after_session_menu = False
    trial_number = 1
    total_trials = 3 # Default number of trials - changed to 2 on 1/25/2025
    batch_size = 3 #default number of trails in a single batch - added 1/25/2025
    time_between_sessions = 180 # number of seconds to wait between sessions of data collection
    start_enable_time = time.time() # the time at/after which the start button is enabled

    # Batch data buffer
    batch_data = []


    # Bar Settings
    green_bar_width = 20
    green_bar_height = 200
    loading_bar_thickness = 30
    arrow_offset_y = 100  # Move arrow up by 100 pixels

    # Positions for Green Bars
    left_green_bar_pos = (100, infoObject.current_h // 2 - green_bar_height // 2)
    right_green_bar_pos = (infoObject.current_w - 100 - green_bar_width, infoObject.current_h // 2 - green_bar_height // 2)

    # Center Position
    center_pos = (infoObject.current_w // 2, infoObject.current_h // 2)

    # Clock
    clock = pygame.time.Clock()

    # Input Variables
    input_text = ""
    input_error = False
    
    direction = 'left'  # Start with 'left' and alternate

    config = {
            'BLACK': BLACK,
            'WHITE': WHITE,
            'GREEN': GREEN,
            'RED': RED,
            'large_font': large_font,
            'medium_font': medium_font,
            'small_font': small_font,
            'total_trials': total_trials,
            'infoObject': infoObject,
            'start_enable_time': start_enable_time
            }
        

    while running:
        # Update within loop for input screen to properly update menu screen
        config['total_trials'] = total_trials
        config['start_enable_time'] = start_enable_time
        
        if in_menu:
            display_functions.display_menu(screen, config)
            # Processing Input at the Main Menu
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s: 
                        if time.time() >= start_enable_time:
                            in_menu = False
                            in_questionaire_subject = True
                    elif event.key == pygame.K_n:
                        in_input = True
                        in_menu = False
                        input_text = ""
                        input_error = False
                    elif event.key == pygame.K_q:
                        running = False

        elif in_input:
            # Display Input Menu for Setting Number of Trials
            display_functions.display_input_menu(screen, config, input_text, input_error)
            # Processing Inputs at the Input Menu
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        break
                    elif event.key == pygame.K_RETURN:
                        if input_text.isdigit():
                            entered_number = int(input_text)
                            if entered_number > 0:
                                total_trials = entered_number
                                in_input = False
                                in_menu = True
                            else:
                                input_error = True
                        else:
                            input_error = True
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode.isdigit():
                        input_text += event.unicode


        elif in_trial_menu: 
            # Display Trial Menu (Accessible via 'M' during trials)
            display_functions.display_in_trial_menu(screen, config)
            # Processing Inputs at the Trial Menu 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_r:
                        in_trial_menu = False


        elif in_after_session_menu:
            # Display After Session Menu
            display_functions.display_after_session_menu(screen, config)
            # Processing Inputs at the After Session Menu 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        in_after_session_menu = False
                        in_menu = True
                        start_enable_time = time.time() + time_between_sessions # Enable the start button 180 seconds after the current time
                    elif event.key == pygame.K_n: 
                        # Not fully sure if all of the following lines are necessary, but they are functional
                        in_after_session_menu = False
                        running = False
                        eeg_processor.board.stop_stream()
                        eeg_processor.board.release_session()
                        pygame.quit()
                        sys.exit()


        else:
            # Display Current Trial Number
            screen.fill(BLACK)
            # Redraw green bars
            pygame.draw.rect(screen, GREEN, (*left_green_bar_pos, green_bar_width, green_bar_height))
            pygame.draw.rect(screen, GREEN, (*right_green_bar_pos, green_bar_width, green_bar_height))

            # Draw Current Trial Info
            trial_info = small_font.render(f"Trial {trial_number}/{total_trials}", True, WHITE)
            trial_info_rect = trial_info.get_rect(topright=(infoObject.current_w - 50, 50))
            screen.blit(trial_info, trial_info_rect)

            # Draw Focus Period '+' sign
            plus_text = large_font.render("+", True, WHITE)
            plus_rect = plus_text.get_rect(center=center_pos)
            screen.blit(plus_text, plus_rect)
            pygame.display.flip()

            # Collect data during focus period
            focus_duration = 3  # seconds
            focus_start_time = time.time()
            while time.time() - focus_start_time < focus_duration:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                            break
                clock.tick(60)

            if not running:
                break

            # Show Arrow (Moved Up)
            arrow_length = 100
            arrow_color = WHITE
            arrow_width = 20
            arrow_y_offset = arrow_offset_y  # Move arrow up by arrow_offset_y pixels

            # Clear screen but keep green bars and trial info
            screen.fill(BLACK)
            # Redraw green bars
            pygame.draw.rect(screen, GREEN, (*left_green_bar_pos, green_bar_width, green_bar_height))
            pygame.draw.rect(screen, GREEN, (*right_green_bar_pos, green_bar_width, green_bar_height))
            # Redraw trial info
            screen.blit(trial_info, trial_info_rect)

            # Draw Arrow
            if direction == 'left':
                pygame.draw.polygon(screen, arrow_color, [
                    (center_pos[0] - arrow_length, center_pos[1] - arrow_y_offset),
                    (center_pos[0], center_pos[1] - arrow_y_offset - arrow_width),
                    (center_pos[0], center_pos[1] - arrow_y_offset + arrow_width)
                ])
            else:
                pygame.draw.polygon(screen, arrow_color, [
                    (center_pos[0] + arrow_length, center_pos[1] - arrow_y_offset),
                    (center_pos[0], center_pos[1] - arrow_y_offset - arrow_width),
                    (center_pos[0], center_pos[1] - arrow_y_offset + arrow_width)
                ])
            pygame.display.flip()

            # Wait before starting the loading bar
            pre_loading_duration = 1.5  # second
            pre_loading_start = time.time()
            while time.time() - pre_loading_start < pre_loading_duration:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                            break
                clock.tick(60)

            if not running:
                break

            # TODO: Implement real model call (Last 1.5 seconds of data)
            model_input = eeg_processor.get_recent_data(1.5)
            print(model_input.shape)

            # Loading Bar
            loading_duration = 14  # Max trial time in seconds

            # Perf counter is a more accurate timer
            loading_start_time = time.perf_counter()

            # Initialize loading bar variables
            current_direction = direction
            current_length = 0
            # From center to left green bar
            max_length = center_pos[0] - (left_green_bar_pos[0] + green_bar_width)

            while time.perf_counter() - loading_start_time < loading_duration and current_length < max_length:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                            break
                        elif event.key == pygame.K_m:
                            in_trial_menu = True
                            break


                screen.fill(BLACK)
                # Redraw green bars
                pygame.draw.rect(screen, GREEN, (*left_green_bar_pos, green_bar_width, green_bar_height))
                pygame.draw.rect(screen, GREEN, (*right_green_bar_pos, green_bar_width, green_bar_height))
                # Redraw trial info
                screen.blit(trial_info, trial_info_rect)

                # TODO: Implement real model call (Last 1.5 seconds of data)
                model_input = eeg_processor.get_recent_data(1.5)

                # Calling noise model
                current_direction = noise_model(direction, current_direction)

                # Redraw Arrow
                if direction == 'left':
                    
                    # Move bar to reflect input from model
                    if current_direction == 'left':
                        current_length += 3
                        
                    else:
                        current_length -= 3
                        

                    pygame.draw.polygon(screen, arrow_color, [
                        (center_pos[0] - arrow_length, center_pos[1] - arrow_y_offset),
                        (center_pos[0], center_pos[1] - arrow_y_offset - arrow_width),
                        (center_pos[0], center_pos[1] - arrow_y_offset + arrow_width)
                    ])                    
                    

                    # Draw loading bar moving left from center
                    pygame.draw.rect(screen, WHITE, (
                        center_pos[0] - current_length,  # Start at center and move left
                        center_pos[1] - loading_bar_thickness // 2,
                        current_length,
                        loading_bar_thickness
                    ))
                else:

                    # Move bar to reflect input from model
                    if current_direction == 'right':
                        current_length += 3
                        
                    else:
                        current_length -= 3
                        

                    pygame.draw.polygon(screen, arrow_color, [
                        (center_pos[0] + arrow_length, center_pos[1] - arrow_y_offset),
                        (center_pos[0], center_pos[1] - arrow_y_offset - arrow_width),
                        (center_pos[0], center_pos[1] - arrow_y_offset + arrow_width)
                    ])
                    

                    # Draw loading bar moving right from center
                    pygame.draw.rect(screen, WHITE, (
                        center_pos[0],  # Start at center and move right
                        center_pos[1] - loading_bar_thickness // 2,
                        current_length,
                        loading_bar_thickness
                    ))

                pygame.display.flip()
                # save_data(eeg_processor, metadata, direction, trial_number, directory)
                clock.tick(60)

            trial_length = time.perf_counter() - loading_start_time
            trial_data = eeg_processor.get_recent_data(trial_length)
            batch_data.append(trial_data)

            if not running:
                break

            # Optional rest period with accessible menu
            rest_duration = 2  # seconds
            rest_start_time = time.time()
            while time.time() - rest_start_time < rest_duration:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                            break
                        elif event.key == pygame.K_m:
                            in_trial_menu = True
                            break

                # Display Rest Text with Menu Instruction
                screen.fill(BLACK)
                # Redraw green bars
                pygame.draw.rect(screen, GREEN, (*left_green_bar_pos, green_bar_width, green_bar_height))
                pygame.draw.rect(screen, GREEN, (*right_green_bar_pos, green_bar_width, green_bar_height))
                # Redraw trial info
                screen.blit(trial_info, trial_info_rect)

                rest_text = small_font.render("Rest (Press M for Menu)", True, WHITE)
                rest_rect = rest_text.get_rect(center=center_pos)
                screen.blit(rest_text, rest_rect)
                pygame.display.flip()
                clock.tick(60)

            # Screen for uploading previous batch of trials to model
            # also activates after final trial is completed (when batch size =/= 2)
            if direction == 'right' and ((trial_number % batch_size == 0) or trial_number == total_trials):
                # TODO: Call function to train model (full batches) input parameter is np array training_data
                # train model with batch_data list
                print(batch_data)
                batch_data = []
                clock.tick(60)
                batch_load_example_time = 3 #seconds
                batch_load_start_time = time.time()
                while time.time() - batch_load_start_time < batch_load_example_time:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                            break
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                running = False
                                break

                    # Display Batch Text 
                    screen.fill(BLACK)
                    batch_load_text = medium_font.render("Sending previous batch to model!", True, WHITE)
                    batch_load_rect = batch_load_text.get_rect(center=center_pos)
                    screen.blit(batch_load_text, batch_load_rect)

                    batch_size_text = small_font.render(f"Batch size currently set to {batch_size} trials.", True, WHITE)
                    batch_size_rect = batch_size_text.get_rect(center=(infoObject.current_w / 2, infoObject.current_h / 2 + 50))
                    screen.blit(batch_size_text, batch_size_rect)
                    pygame.display.flip()

            if not running:
                break

            # Alternate Direction
            if direction == 'left':
                direction = 'right'
            else:
                direction = 'left'

            if direction == 'left':
                trial_number += 1

            # Check if all trials are completed
            if trial_number > total_trials:
                # Display a completion message
                screen.fill(BLACK)
                completion_text = medium_font.render("All Trials Completed!", True, GREEN)
                completion_rect = completion_text.get_rect(center=center_pos)
                screen.blit(completion_text, completion_rect)
                pygame.display.flip()
                # Wait for 3 seconds before returning to menu
                time.sleep(3)
                trial_number = 1  # Reset trial number
                in_after_session_menu = True

        # Handle Trial Menu outside the main loop to avoid missing quit events
        while in_trial_menu and running:
            # Display Trial Menu (Accessible via 'M' during trials)
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

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    in_trial_menu = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                        in_trial_menu = False
                    elif event.key == pygame.K_r:
                        in_trial_menu = False


if __name__ == "__main__":
    main()