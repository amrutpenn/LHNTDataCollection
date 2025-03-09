# EEG Motor Imagery Data Collection GUI

A Python-based graphical user interface for collecting EEG data during motor imagery tasks. This application is designed to record brain activity while users imagine moving either left or right, following visual cues.

## Prerequisites

- Python 3.x
- Required Python packages:
  - pygame
  - numpy
  - scipy
  - brainflow
  - pandas
  - boxsdk
  - pyserial

## Installation

1. Clone this repository or download the source code
2. Install the required packages:
```bash
pip install pygame numpy scipy brainflow pandas boxsdk pyserial
```

## Usage

### Starting the Application

Run the application using Python:
```bash
python data_collection_gui.py
```

### Main Menu

The main menu displays several options:
- Press 'S' to Start: Begins a new recording session
- Press 'N' to Set Number: Set the number of trials (must be even)
- Press 'Q' to Quit: Exits the application

### Setting Up a Session

1. When starting a new session, you'll be prompted to enter:
   - First name
   - Last name
   - EID (identification number)
   - Physiological information:
     - Stimulant consumption
     - Meal information
     - Exercise history

2. Use arrow keys to navigate between input fields
3. Press Enter to confirm your entries

### During the Trial

Each trial consists of several phases:

1. **Focus Period (3 seconds)**
   - A '+' symbol appears in the center
   - Focus on the screen

2. **Direction Cue**
   - An arrow appears pointing either left or right
   - This indicates which direction to imagine movement

3. **Loading Bar (7 seconds)**
   - A progress bar moves towards the indicated direction
   - Imagine moving your hand in the indicated direction

4. **Rest Period (2 seconds)**
   - Brief rest between trials
   - Press 'M' to access the menu if needed

### Trial Menu

Access the trial menu by pressing 'M' during a trial:
- Press 'R' to Resume the current session
- Press 'Q' to Quit the session

### After Session

After completing all trials:
1. You'll be asked if you want to continue:
   - Press 'Y' to start another session (after a 3-minute cooldown)
   - Press 'N' to exit the application

2. Your data will be automatically:
   - Saved locally
   - Compressed into a zip file
   - Uploaded to Box storage

## Data Storage

- Each session creates a new directory with the format: `{first_name}_{last_name}_Session{number}`
- Data is saved in pickle (.pkl) format
- All session data is automatically uploaded to Box storage
- User information is tracked and updated in a central table

## Troubleshooting

If you encounter issues with the serial port connection:
1. Ensure your EEG device is properly connected
2. Check that you have appropriate permissions to access the serial port
3. The application will attempt to automatically detect the correct port for your system

## Notes

- The number of trials must be even as the application alternates between left and right directions
- A 3-minute cooldown period is enforced between sessions
- The application supports Windows, macOS, and Linux operating systems





