import pygame
import sys
import time
import pickle
import numpy as np
from scipy.signal import butter, lfilter, iirnotch
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from checkbox import Checkbox
import platform
import serial
import serial.tools.list_ports
import datetime
from datetime import timedelta
import pandas as pd
from boxsdk import Client, OAuth2
import zipfile
import os

def find_serial_port():
    """
    Automatically find the correct serial port for the device across different operating systems.
    
    Returns:
        str: The path of the detected serial port, or None if not found.
    """
    system = platform.system()
    ports = list(serial.tools.list_ports.comports())
    
    for port in ports:
        if system == "Darwin":  # macOS
            if any(identifier in port.device.lower() for identifier in ["usbserial", "cu.usbmodem", "tty.usbserial"]):
                return port.device
        elif system == "Windows":
            if "com" in port.device.lower():
                return port.device
        elif system == "Linux":
            if "ttyUSB" in port.device or "ttyACM" in port.device:
                return port.device
    
    return None

def draw_plus_sign(screen, center_pos, plus_length, thickness, color):
    """
    Draws a plus sign at the specified center position.
    """
    # Draw horizontal line
    pygame.draw.line(
        screen,
        color,
        (center_pos[0] - plus_length // 2, center_pos[1]),
        (center_pos[0] + plus_length // 2, center_pos[1]),
        thickness
    )
    # Draw vertical line
    pygame.draw.line(
        screen,
        color,
        (center_pos[0], center_pos[1] - plus_length // 2),
        (center_pos[0], center_pos[1] + plus_length // 2),
        thickness
    )

def create_user_directory(first_name, last_name, session_num):
    """
    Creates a new directory for the current user's session.
    """
    dir_name = first_name + '_' + last_name + '_' + 'Session' + str(session_num)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    new_dir_path = os.path.join(script_dir, dir_name)
    os.mkdir(new_dir_path)
    return dir_name

class EEGProcessor:
    """
    Handles EEG data acquisition and basic filtering via BrainFlow.
    """
    def __init__(self):
        # Initialize BrainFlow
        BoardShim.enable_dev_board_logger()
        params = BrainFlowInputParams()
        # serial_port = find_serial_port()
        # params.serial_port = serial_port
        self.board_id = BoardIds.CYTON_DAISY_BOARD.value
        self.board = BoardShim(self.board_id, params)
        self.board.prepare_session()
        self.board.start_stream()
        print("BrainFlow streaming started...")

        # Sampling rate and window size
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.window_size_sec = 7  # seconds
        self.window_size_samples = int(self.window_size_sec * self.sampling_rate)

        # We set raw window size to 10 seconds
        self.window_size_raw = int(10 * self.sampling_rate)
        self.lowcut = 1.0
        self.highcut = 50.0
        self.notch = 60.0

        # EEG channels
        self.eeg_channels = BoardShim.get_eeg_channels(self.board_id)

        # Initialize buffers
        self.raw_data_buffer = np.empty((len(self.eeg_channels), 0))
        self.processed_data_buffer = np.empty((len(self.eeg_channels), 0))

    def stop(self):
        # Stop data stream and release session
        self.board.stop_stream()
        self.board.release_session()
        print("BrainFlow streaming stopped.")

    def get_recent_data(self):
        """
        Returns the most recent 7 seconds of processed EEG data.
        """
        data = self.board.get_board_data()
        if data.shape[1] == 0:
            return self.processed_data_buffer  # No new data

        # Append new raw data
        eeg_data = data[self.eeg_channels, :]
        self.raw_data_buffer = np.hstack((self.raw_data_buffer, eeg_data))

        # Process new data
        new_processed_data = np.empty(self.raw_data_buffer.shape)
        for i in range(len(self.eeg_channels)):
            # Filter each channel
            channel_data = self.raw_data_buffer[i, :].copy()
            # Bandpass filter
            b, a = butter(2, [self.lowcut, self.highcut], btype='band', fs=self.sampling_rate)
            channel_data = lfilter(b, a, channel_data)
            # Notch filter
            b, a = iirnotch(self.notch, 30, fs=self.sampling_rate)
            channel_data = lfilter(b, a, channel_data)
            new_processed_data[i, :] = channel_data

        self.processed_data_buffer = np.hstack((self.processed_data_buffer, new_processed_data))

        # Trim buffer sizes
        max_buffer_size = self.window_size_samples * 2
        if self.raw_data_buffer.shape[1] > self.window_size_raw:
            self.raw_data_buffer = self.raw_data_buffer[:, -self.window_size_raw:]
        if self.processed_data_buffer.shape[1] > max_buffer_size:
            self.processed_data_buffer = self.processed_data_buffer[:, -max_buffer_size:]

        if self.processed_data_buffer.shape[1] >= self.window_size_samples:
            return self.processed_data_buffer[:, -self.window_size_samples:]
        else:
            return self.processed_data_buffer

def save_data(eeg_processor, metadata, direction, trial_num, directory):
    """
    Save the last 7 seconds of EEG data plus metadata into a pickle file.
    """
    sig = eeg_processor.get_recent_data()
    filename = f"{direction}_{trial_num}.pkl"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    intermediate = os.path.join(script_dir, directory)
    filepath = os.path.join(intermediate, filename)

    with open(filepath, 'wb') as f:
        pickle.dump((sig, metadata), f)

def main():
    session_num = input("Enter the session number: ")
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

    # Control variables
    running = True
    in_menu = True
    in_input = False
    in_trial_menu = False
    in_questionaire_subject = False
    in_questionaire_physiological = False
    in_buffer_screen = False
    in_after_session_menu = False
    trial_number = 1
    total_trials = 20
    time_between_sessions = 180  
    start_enable_time = time.time()
    saved_questionnaire_data = False

    # Directions list (4 directions)
    directions = ["up", "down", "left", "right"]
    direction_index = 0
    current_direction = directions[direction_index]

    # Font sizes
    font_size_large = infoObject.current_h // 10
    font_size_medium = infoObject.current_h // 15
    font_size_small = infoObject.current_h // 20

    large_font = pygame.font.SysFont(None, font_size_large)
    medium_font = pygame.font.SysFont(None, font_size_medium)
    small_font = pygame.font.SysFont(None, font_size_small)

    # Calculate center
    center_x = infoObject.current_w // 2
    center_y = infoObject.current_h // 2
    center_pos = (center_x, center_y)

    # Move bars closer to center (not at the screen edges)
    # so the bar moves over a shorter distance.
    bar_offset_x = infoObject.current_w // 4.5   # horizontal offset from center
    bar_offset_y = infoObject.current_h // 4.5   # vertical offset from center

    # Set each bar's width and height (they will appear as small rectangles)
    bar_width_vert   = infoObject.current_w // 30  # width of left/right bars
    bar_height_vert  = infoObject.current_h // 5   # height of left/right bars
    bar_width_horiz  = infoObject.current_w // 5   # width of top/bottom bars
    bar_height_horiz = infoObject.current_h // 30  # height of top/bottom bars

    # Define rectangles for all four bars
    # LEFT
    left_bar_rect = pygame.Rect(
        center_x - bar_offset_x,         # x
        center_y - bar_height_vert // 2, # y
        bar_width_vert,                  # width
        bar_height_vert                  # height
    )
    # RIGHT
    right_bar_rect = pygame.Rect(
        center_x + bar_offset_x - bar_width_vert,
        center_y - bar_height_vert // 2,
        bar_width_vert,
        bar_height_vert
    )
    # TOP
    top_bar_rect = pygame.Rect(
        center_x - bar_width_horiz // 2,
        center_y - bar_offset_y,
        bar_width_horiz,
        bar_height_horiz
    )
    # BOTTOM
    bottom_bar_rect = pygame.Rect(
        center_x - bar_width_horiz // 2,
        center_y + bar_offset_y - bar_height_horiz,
        bar_width_horiz,
        bar_height_horiz
    )

    loading_bar_thickness = infoObject.current_h // 30
    clock = pygame.time.Clock()

    # Input variables
    input_text = ""
    input_error = False
    questionnaire_error = False

    # Questionnaire
    identity_index = 0
    free_response_index = 0
    identity_answers = ["", "", ""]
    free_response_answers = ["", ""]
    button_answers = [-1, -1, -1]

    # Checkbox positioning
    height_delta = infoObject.current_h // 11
    width_delta = infoObject.current_w // 11

    stim_button = Checkbox(screen, width_delta, height_delta * 2, 0, caption='0 mg', font_color=(255, 255, 255))
    stim_button2 = Checkbox(screen, width_delta * 3, height_delta * 2, 1, caption='1 - 49 mg', font_color=(255, 255, 255))
    stim_button3 = Checkbox(screen, width_delta * 5, height_delta * 2, 2, caption='50 - 99 mg', font_color=(255, 255, 255))
    stim_button4 = Checkbox(screen, width_delta * 7, height_delta * 2, 3, caption='100 - 150 mg', font_color=(255, 255, 255))
    stim_button5 = Checkbox(screen, width_delta * 9, height_delta * 2, 4, caption='> 150 mg', font_color=(255, 255, 255))
    stimulant_boxes = [stim_button, stim_button2, stim_button3, stim_button4, stim_button5]

    meal_button = Checkbox(screen, width_delta, height_delta * 4, 5, caption='No meal', font_color=(255, 255, 255))
    meal_button2 = Checkbox(screen, width_delta * 3, height_delta * 4, 6, caption='Light meal', font_color=(255, 255, 255))
    meal_button3 = Checkbox(screen, width_delta * 5, height_delta * 4, 7, caption='Medium meal', font_color=(255, 255, 255))
    meal_button4 = Checkbox(screen, width_delta * 7, height_delta * 4, 8, caption='Heavy meal', font_color=(255, 255, 255))
    meal_button5 = Checkbox(screen, width_delta * 9, height_delta * 4, 9, caption='Not sure', font_color=(255, 255, 255))
    meal_boxes = [meal_button, meal_button2, meal_button3, meal_button4, meal_button5]

    yes_exercise = Checkbox(screen, width_delta * 5, height_delta * 7, 10, caption='yes', font_color=(255, 255, 255))
    no_exercise = Checkbox(screen, width_delta * 6, height_delta * 7, 11, caption='no', font_color=(255, 255, 255))
    exercise_bool_boxes = [yes_exercise, no_exercise]

    plus_length = infoObject.current_h // 15

    # -----------------------------
    # Main Loop
    # -----------------------------
    while running:

        # -----------------------------
        # 1. MAIN MENU
        # -----------------------------
        if in_menu:
            screen.fill(BLACK)
            title_text = large_font.render("EEG Motor Imagery", True, WHITE)
            start_text = medium_font.render("Press S to Start", True, GREEN)
            set_text = medium_font.render("Press N to Set Number", True, WHITE)
            quit_text = medium_font.render("Press Q to Quit", True, RED)
            trials_text = small_font.render(f"Total Trials: {total_trials}", True, WHITE)

            title_rect = title_text.get_rect(center=(center_x, infoObject.current_h // 5))
            start_rect = start_text.get_rect(center=(center_x, center_y - font_size_medium))
            set_rect = set_text.get_rect(center=(center_x, center_y))
            quit_rect = quit_text.get_rect(center=(center_x, center_y + font_size_medium))
            trials_rect = trials_text.get_rect(center=(center_x, center_y - 1.1 * font_size_large))

            screen.blit(title_text, title_rect)
            screen.blit(start_text, start_rect)
            screen.blit(set_text, set_rect)
            screen.blit(quit_text, quit_rect)
            screen.blit(trials_text, trials_rect)
            pygame.display.flip()

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

        # -----------------------------
        # 2. SET NUMBER OF TRIALS
        # -----------------------------
        elif in_input:
            screen.fill(BLACK)
            prompt_text = medium_font.render("Enter Number of Recordings (Even):", True, WHITE)
            input_display = medium_font.render(input_text, True, GREEN if not input_error else RED)
            instructions_text = small_font.render("Press Enter to Confirm", True, WHITE)

            prompt_rect = prompt_text.get_rect(center=(center_x, infoObject.current_h // 3))
            input_rect = input_display.get_rect(center=(center_x, center_y))
            instructions_rect = instructions_text.get_rect(center=(center_x, center_y + 100))

            screen.blit(prompt_text, prompt_rect)
            screen.blit(input_display, input_rect)
            screen.blit(instructions_text, instructions_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RETURN:
                        if input_text.isdigit():
                            entered_number = int(input_text)
                            if entered_number > 0:
                                # Force an even number
                                if entered_number % 2 != 0:
                                    entered_number += 1
                                    input_error = True
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

        # -----------------------------
        # 3. QUESTIONNAIRE - SUBJECT INFO
        # -----------------------------
        elif in_questionaire_subject:
            screen.fill(BLACK)
            h_delta = infoObject.current_h // 8

            first_name_text = medium_font.render("Enter first name", True, WHITE)
            first_name_rect = first_name_text.get_rect(center=(center_x, h_delta))

            last_name_text = medium_font.render("Enter last name", True, WHITE)
            last_name_rect = last_name_text.get_rect(center=(center_x, h_delta * 2.5))

            eid_text = medium_font.render("Enter EID", True, WHITE)
            eid_rect = eid_text.get_rect(center=(center_x, h_delta * 4))

            first_name_response = medium_font.render(identity_answers[0], True, WHITE)
            first_name_response_rect = first_name_response.get_rect(center=(center_x, h_delta * 1.5))

            last_name_response = medium_font.render(identity_answers[1], True, WHITE)
            last_name_response_rect = last_name_response.get_rect(center=(center_x, h_delta * 3))

            eid_response = medium_font.render(identity_answers[2], True, WHITE)
            eid_response_rect = eid_response.get_rect(center=(center_x, h_delta * 5))

            screen.blit(first_name_text, first_name_rect)
            screen.blit(first_name_response, first_name_response_rect)
            screen.blit(last_name_text, last_name_rect)
            screen.blit(last_name_response, last_name_response_rect)
            screen.blit(eid_text, eid_rect)
            screen.blit(eid_response, eid_response_rect)

            if input_error:
                error_text = small_font.render("Please fill out all fields before proceeding.", True, RED)
                error_rect = error_text.get_rect(center=(center_x, infoObject.current_h - font_size_small))
                screen.blit(error_text, error_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    # Move among the three fields
                    elif event.key == pygame.K_DOWN and identity_index < 2:
                        identity_index += 1
                    elif event.key == pygame.K_UP and identity_index > 0:
                        identity_index -= 1
                    elif event.key == pygame.K_BACKSPACE:
                        identity_answers[identity_index] = identity_answers[identity_index][:-1]
                        input_error = False
                    elif event.key == pygame.K_RETURN:
                        # Check if all fields filled
                        if all(answer.strip() for answer in identity_answers):
                            in_questionaire_subject = False
                            in_questionaire_physiological = True
                            input_error = False
                        else:
                            input_error = True
                    else:
                        identity_answers[identity_index] += event.unicode
                        input_error = False

        # -----------------------------
        # 4. QUESTIONNAIRE - PHYSIOLOGICAL
        # -----------------------------
        elif in_questionaire_physiological:
            screen.fill(BLACK)
            hd = infoObject.current_h // 12

            stimulant_text = small_font.render(
                "How much stimulant (e.g. caffeine) have you consumed in the past 12 hours?", True, WHITE
            )
            meal_text = small_font.render(
                "Have you consumed a light, medium, or heavy meal in the past 12 hours?", True, WHITE
            )
            exercise_text = small_font.render("Have you exercised in the past 12 hours?", True, WHITE)
            food_description_text = small_font.render(
                "Describe what you ate in detail, include portion size if possible", True, WHITE
            )
            exercise_type_text = small_font.render(
                "If you have exercised, describe what you did and how long. N/A if no exercise", True, WHITE
            )

            stim_rect = stimulant_text.get_rect(center=(center_x, hd))
            meal_rect = meal_text.get_rect(center=(center_x, hd * 3))
            food_rect = food_description_text.get_rect(center=(center_x, hd * 5))
            ex_rect = exercise_text.get_rect(center=(center_x, hd * 7))
            ex_type_rect = exercise_type_text.get_rect(center=(center_x, hd * 9))

            screen.blit(stimulant_text, stim_rect)
            screen.blit(meal_text, meal_rect)
            screen.blit(food_description_text, food_rect)
            screen.blit(exercise_text, ex_rect)
            screen.blit(exercise_type_text, ex_type_rect)

            food_response = small_font.render(free_response_answers[0], True, WHITE)
            exercise_response = small_font.render(free_response_answers[1], True, WHITE)
            food_response_rect = food_response.get_rect(center=(center_x, hd * 6))
            exercise_response_rect = exercise_response.get_rect(center=(center_x, hd * 10))
            screen.blit(food_response, food_response_rect)
            screen.blit(exercise_response, exercise_response_rect)

            all_boxes = [stimulant_boxes, meal_boxes, exercise_bool_boxes]
            for box_holder in all_boxes:
                for box in box_holder:
                    box.render_checkbox()

            if questionnaire_error:
                error_text = small_font.render("Please answer all questions before proceeding.", True, RED)
                error_rect = error_text.get_rect(center=(center_x, infoObject.current_h - 50))
                screen.blit(error_text, error_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for box_holder in all_boxes:
                        for box in box_holder:
                            box.update_checkbox(event)
                            if box.checked:
                                # Uncheck others in same group
                                for b in box_holder:
                                    if b != box:
                                        b.checked = False
                    questionnaire_error = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_DOWN and free_response_index < 1:
                        free_response_index += 1
                    elif event.key == pygame.K_UP and free_response_index > 0:
                        free_response_index -= 1
                    elif event.key == pygame.K_BACKSPACE:
                        free_response_answers[free_response_index] = free_response_answers[free_response_index][:-1]
                        questionnaire_error = False
                    elif event.key == pygame.K_RETURN:
                        # Check if all answered
                        all_questions_answered = True
                        for box_holder in all_boxes:
                            if not any(box.checked for box in box_holder):
                                all_questions_answered = False
                                break
                        if any(not ans.strip() for ans in free_response_answers):
                            all_questions_answered = False

                        if all_questions_answered:
                            for ind, box_holder in enumerate(all_boxes):
                                for count, box in enumerate(box_holder):
                                    if box.checked:
                                        button_answers[ind] = count
                            in_questionaire_physiological = False
                            in_buffer_screen = True
                            questionnaire_error = False
                        else:
                            questionnaire_error = True
                    else:
                        free_response_answers[free_response_index] += event.unicode
                        questionnaire_error = False

        # -----------------------------
        # 5. BUFFER SCREEN
        # -----------------------------
        elif in_buffer_screen:
            if not saved_questionnaire_data:
                # Save results locally
                first_name = identity_answers[0]
                last_name = identity_answers[1]
                eid = identity_answers[2]
                stim = ""
                meal = ""
                describe_meal = free_response_answers[0]
                exercise_yn = free_response_answers[1]

                # Determine selected boxes
                for box in stimulant_boxes:
                    if box.get_checked():
                        stim = box.get_caption()
                        break
                for box in meal_boxes:
                    if box.get_checked():
                        meal = box.get_caption()
                        break
                for box in exercise_bool_boxes:
                    if box.get_checked():
                        exercise_yn = box.get_caption()
                        break

                directory = create_user_directory(first_name, last_name, session_num)
                metadata = {
                    "First Name": first_name,
                    "Last Name": last_name,
                    "EID": eid,
                    "Stimulant Use": stim,
                    "Meal Size": meal,
                    "Meal Description": describe_meal,
                    "Exercised": exercise_yn,
                    "Exercise Description": free_response_answers[1]
                }
                saved_questionnaire_data = True

            screen.fill(BLACK)
            buffer_screen_title = large_font.render("Ready?", True, WHITE)
            start_trial_text = medium_font.render("Press S to Start Trial", True, GREEN)

            buffer_screen_title_rect = buffer_screen_title.get_rect(center=(center_x, center_y // 2))
            start_trial_text_rect = start_trial_text.get_rect(center=(center_x, center_y))

            screen.blit(buffer_screen_title, buffer_screen_title_rect)
            screen.blit(start_trial_text, start_trial_text_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_s:
                        in_buffer_screen = False

        # -----------------------------
        # 6. TRIAL MENU (accessible via M)
        # -----------------------------
        elif in_trial_menu:
            screen.fill(BLACK)
            menu_title = medium_font.render("Trial Menu", True, WHITE)
            quit_text = medium_font.render("Press Q to Quit", True, RED)
            resume_text = medium_font.render("Press R to Resume", True, GREEN)

            menu_title_rect = menu_title.get_rect(center=(center_x, center_y // 2))
            quit_rect = quit_text.get_rect(center=(center_x, center_y))
            resume_rect = resume_text.get_rect(center=(center_x, center_y + 100))

            screen.blit(menu_title, menu_title_rect)
            screen.blit(quit_text, quit_rect)
            screen.blit(resume_text, resume_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_r:
                        in_trial_menu = False

        # -----------------------------
        # 7. AFTER SESSION MENU
        # -----------------------------
        elif in_after_session_menu:
            screen.fill(BLACK)
            question_text = large_font.render("Do you want to continue?", True, WHITE)
            continue_text = medium_font.render("Press Y to continue", True, GREEN)
            quit_text = medium_font.render("Press N to exit", True, RED)

            question_rect = question_text.get_rect(center=(center_x, center_y // 2))
            continue_rect = continue_text.get_rect(center=(center_x, center_y))
            quit_rect = quit_text.get_rect(center=(center_x, center_y + 100))

            screen.blit(question_text, question_rect)
            screen.blit(continue_text, continue_rect)
            screen.blit(quit_text, quit_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        in_after_session_menu = False
                        in_menu = True
                        start_enable_time = time.time() + time_between_sessions
                    elif event.key == pygame.K_n:
                        in_after_session_menu = False
                        running = False
                        eeg_processor.stop()
                        pygame.quit()
                        sys.exit()

        # -----------------------------
        # 8. MAIN TRIAL LOOP
        # -----------------------------
        else:
            # 8a. Focus Period
            screen.fill(BLACK)
            # Draw all four bars (always visible)
            pygame.draw.rect(screen, GREEN, left_bar_rect)
            pygame.draw.rect(screen, GREEN, right_bar_rect)
            pygame.draw.rect(screen, GREEN, top_bar_rect)
            pygame.draw.rect(screen, GREEN, bottom_bar_rect)

            # Draw trial info
            trial_info = small_font.render(f"Trial {trial_number}/{total_trials}", True, WHITE)
            trial_info_rect = trial_info.get_rect(topright=(infoObject.current_w - 50, 50))
            screen.blit(trial_info, trial_info_rect)

            # Draw plus sign in center
            draw_plus_sign(screen, center_pos, plus_length, loading_bar_thickness, WHITE)
            pygame.display.flip()

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

            # 8b. Direction Arrow
            screen.fill(BLACK)
            # Always draw the bars
            pygame.draw.rect(screen, GREEN, left_bar_rect)
            pygame.draw.rect(screen, GREEN, right_bar_rect)
            pygame.draw.rect(screen, GREEN, top_bar_rect)
            pygame.draw.rect(screen, GREEN, bottom_bar_rect)
            screen.blit(trial_info, trial_info_rect)

            arrow_color = WHITE
            arrow_length = infoObject.current_w // 15
            arrow_width = infoObject.current_h // 40

            # Draw the arrow for current_direction
            if current_direction == 'left':
                pygame.draw.polygon(
                    screen, arrow_color,
                    [
                        (center_x - arrow_length, center_y),
                        (center_x, center_y - arrow_width),
                        (center_x, center_y + arrow_width)
                    ]
                )
            elif current_direction == 'right':
                pygame.draw.polygon(
                    screen, arrow_color,
                    [
                        (center_x + arrow_length, center_y),
                        (center_x, center_y - arrow_width),
                        (center_x, center_y + arrow_width)
                    ]
                )
            elif current_direction == 'up':
                pygame.draw.polygon(
                    screen, arrow_color,
                    [
                        (center_x, center_y - arrow_length),
                        (center_x - arrow_width, center_y),
                        (center_x + arrow_width, center_y)
                    ]
                )
            else:  # down
                pygame.draw.polygon(
                    screen, arrow_color,
                    [
                        (center_x, center_y + arrow_length),
                        (center_x - arrow_width, center_y),
                        (center_x + arrow_width, center_y)
                    ]
                )

            draw_plus_sign(screen, center_pos, plus_length, loading_bar_thickness, WHITE)
            pygame.display.flip()

            pre_loading_duration = 1.7        
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

            # 8c. Loading Bar (7 seconds)
            loading_duration = 7
            loading_start_time = time.time()
            while time.time() - loading_start_time < loading_duration:
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

                elapsed_time = time.time() - loading_start_time
                loading_progress = elapsed_time / loading_duration

                screen.fill(BLACK)
                # Always draw the bars
                pygame.draw.rect(screen, GREEN, left_bar_rect)
                pygame.draw.rect(screen, GREEN, right_bar_rect)
                pygame.draw.rect(screen, GREEN, top_bar_rect)
                pygame.draw.rect(screen, GREEN, bottom_bar_rect)
                screen.blit(trial_info, trial_info_rect)

                # Draw direction arrow again
                if current_direction == 'left':
                    pygame.draw.polygon(
                        screen, arrow_color,
                        [
                            (center_x - arrow_length, center_y),
                            (center_x, center_y - arrow_width),
                            (center_x, center_y + arrow_width)
                        ]
                    )
                    # Horizontal distance from center to left bar
                    max_length = center_x - (left_bar_rect.x + left_bar_rect.width)
                    current_length = loading_progress * max_length
                    # Draw bar from center to the left
                    pygame.draw.rect(
                        screen, WHITE,
                        (
                            center_x - current_length,
                            center_y - loading_bar_thickness // 2,
                            current_length,
                            loading_bar_thickness
                        )
                    )

                elif current_direction == 'right':
                    pygame.draw.polygon(
                        screen, arrow_color,
                        [
                            (center_x + arrow_length, center_y),
                            (center_x, center_y - arrow_width),
                            (center_x, center_y + arrow_width)
                        ]
                    )
                    # Horizontal distance from center to right bar
                    max_length = (right_bar_rect.x) - center_x
                    current_length = loading_progress * max_length
                    pygame.draw.rect(
                        screen, WHITE,
                        (
                            center_x,
                            center_y - loading_bar_thickness // 2,
                            current_length,
                            loading_bar_thickness
                        )
                    )

                elif current_direction == 'up':
                    pygame.draw.polygon(
                        screen, arrow_color,
                        [
                            (center_x, center_y - arrow_length),
                            (center_x - arrow_width, center_y),
                            (center_x + arrow_width, center_y)
                        ]
                    )
                    # Vertical distance from center to top bar
                    max_length = center_y - (top_bar_rect.y + top_bar_rect.height)
                    current_length = loading_progress * max_length
                    pygame.draw.rect(
                        screen, WHITE,
                        (
                            center_x - loading_bar_thickness // 2,
                            center_y - current_length,
                            loading_bar_thickness,
                            current_length
                        )
                    )

                else:  # down
                    pygame.draw.polygon(
                        screen, arrow_color,
                        [
                            (center_x, center_y + arrow_length),
                            (center_x - arrow_width, center_y),
                            (center_x + arrow_width, center_y)
                        ]
                    )
                    # Vertical distance from center to bottom bar
                    max_length = (bottom_bar_rect.y) - center_y
                    current_length = loading_progress * max_length
                    pygame.draw.rect(
                        screen, WHITE,
                        (
                            center_x - loading_bar_thickness // 2,
                            center_y,
                            loading_bar_thickness,
                            current_length
                        )
                    )

                draw_plus_sign(screen, center_pos, plus_length, loading_bar_thickness, WHITE)
                pygame.display.flip()

                # Continuously save data throughout the 7s (if desired).
                # If you only want one file per trial, move this after the loop.
                save_data(eeg_processor, metadata, current_direction, trial_number, directory)

                clock.tick(60)
                if not running or in_trial_menu:
                    break

            if not running:
                break

            # 8d. Rest Period (3-5 seconds)
            rest_duration = np.random.uniform(3, 5)
            rest_start_time = time.time()
            while time.time() - rest_start_time < rest_duration and not in_trial_menu and running:
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
                pygame.draw.rect(screen, GREEN, left_bar_rect)
                pygame.draw.rect(screen, GREEN, right_bar_rect)
                pygame.draw.rect(screen, GREEN, top_bar_rect)
                pygame.draw.rect(screen, GREEN, bottom_bar_rect)
                screen.blit(trial_info, trial_info_rect)

                rest_text = small_font.render("Rest (Press M for Menu)", True, WHITE)
                rest_rect = rest_text.get_rect(center=center_pos)
                screen.blit(rest_text, rest_rect)
                pygame.display.flip()
                clock.tick(60)

            # Move to next direction
            direction_index = (direction_index + 1) % len(directions)
            current_direction = directions[direction_index]
            trial_number += 1

            # Check if all trials done
            if trial_number > total_trials:
                screen.fill(BLACK)
                completion_text = medium_font.render("All Trials Completed!", True, GREEN)
                completion_rect = completion_text.get_rect(center=center_pos)
                screen.blit(completion_text, completion_rect)
                pygame.display.flip()
                time.sleep(3)
                trial_number = 1
                in_after_session_menu = True

        # If we triggered the trial menu:
        while in_trial_menu and running:
            screen.fill(BLACK)
            menu_title = medium_font.render("Trial Menu", True, WHITE)
            quit_text = medium_font.render("Press Q to Quit", True, RED)
            resume_text = medium_font.render("Press R to Resume", True, GREEN)

            menu_title_rect = menu_title.get_rect(center=(center_x, center_y // 2))
            quit_rect = quit_text.get_rect(center=(center_x, center_y))
            resume_rect = resume_text.get_rect(center=(center_x, center_y + 100))

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

    # Final cleanup
    eeg_processor.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()