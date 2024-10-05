# Lillypad Restoration Slideshow

This Python script creates a slideshow of images, using Pygame, that automatically detects USB drives, mounts them, and displays images stored on the USB drive. The project includes a fade-in and fade-out effect for images and a logging system for troubleshooting.

## Features

- Automatically detects and mounts USB devices
- Displays images in a slideshow format
- Supports fade-in and fade-out effects for smoother transitions
- Logs events and errors to a rotating log file

## Usage

- The script automatically mounts the first detected USB drive and searches for images (PNG, JPG, JPEG, GIF, BMP formats).
- Once the images are found, it displays them in a loop with a fade-in and fade-out effect.
- Press `ESC` to exit the slideshow.

### Configuration

The script uses the following default settings:

- **Image Size:** 1280x1080 pixels
- **Image Location:** Displayed at (100, 50) on the screen
- **Fade Speed:** 50 (can be adjusted in the script)
- **Wait Time Between Images:** 30 seconds
- **Log File:** `/home/pi/slideShow.log`

## Requirements

- Python 3.x
- Pygame
- Pyudev (for monitoring USB events)

## Installation

1. Install dependencies using pip:
   
   ```bash
   pip install pygame pyudev
   ```
