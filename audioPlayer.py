import os
import stat
import sys
import time
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import pyudev
import threading
import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE

# Set up the RotatingFileHandler
log_file = "/home/pi/audioPlayer.log"
max_log_size = 5 * 1024 * 1024  # 5 MB (cap size)
backup_count = 3  # Keep 3 backup files

handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=backup_count)
mp3_files = []  # a list of all images being shown


def walktree(dir,callback):
    """Recursively descend the directory tree rooted at top, calling the
    callback function for each regular file.
    """
    logging.debug("walktree "+dir)
    for f in os.listdir(dir):
        pathname = os.path.join(dir, f)
        mode = os.stat(pathname).st_mode
        if stat.S_ISDIR(mode):
            # It's a directory, recurse into it
            walktree(pathname, callback)
        elif stat.S_ISREG(mode):
            # It's a file, call the callback function
            callback(pathname)
        else:
            # Unknown file type, logging.info a message
            logging.info(f'Skipping {pathname}')

def addtolist(file, extensions=['.mp3']):
    """Add a file to a global list of image files."""
    global mp3_files  # ugh
    filename, ext = os.path.splitext(file)
    e = ext.lower()
    # Only add common image types to the list.
    if e in extensions:
        logging.info(f'Adding to list: {file}')
        mp3_files.append(file)


# Initialize pygame mixer for audio playback
def init_pygame_audio():
    try:
        logging.info("Initializing pygame mixer for audio")
        pygame.mixer.init()
        logging.info("Pygame audio initialized")
    except Exception as e:
        logging.error(f"Error initializing pygame audio: {e}")
        raise

def monitor_usb_events():
    """Monitor USB insert and remove events."""
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block', device_type='partition')
    
    for device in iter(monitor.poll, None):
        action = device.action
        logging.info(f"Device event detected: {device.device_node}, Action: {action}")
        handle_device_changes(device, action)

def handle_device_changes(device, action):
    """Handle USB device insertion or removal."""
    if action == "add":
        logging.info("USB device inserted and mounted.")
        device_name = get_device_name()
        if device_name:
            mp3_files.clear()
            walktree(startdir, addtolist)
            if mp3_files:
                logging.info(f"Starting slideshow with {len(mp3_files)} mp3s.")
            else:
                logging.warning("No mp3s found on the USB device.")
    elif action == "remove":
        logging.info("USB device removed, stopping slideshow.")
        mp3_files.clear()
        

# Play an individual MP3 file
def play_mp3(mp3_file):
    try:
        logging.info(f"Loading MP3 file: {mp3_file}")
        pygame.mixer.music.load(mp3_file)

        # Set the volume (0.0 is mute, 1.0 is full volume)
        pygame.mixer.music.set_volume(1)

        logging.info(f"Playing MP3 file: {mp3_file}")
        pygame.mixer.music.play()
        
        # Wait for the music to finish playing
        while pygame.mixer.music.get_busy():
            time.sleep(1)
        
        logging.info(f"Finished playing: {mp3_file}")
    except Exception as e:
        logging.error(f"Error playing MP3 file {mp3_file}: {e}")

# Play a sequence of MP3 files
def play_mp3_slideshow(mp3_files):
    for mp3_file in mp3_files:
        logging.debug("Starting to play "+mp3_file)
        play_mp3(mp3_file)

# Main function to set up and play the audio slideshow
def main():
    logging.debug("starting audio player")
    
    #give the system a chance to wake up
    time.sleep(15)


    # Initialize pygame mixer
    init_pygame_audio()

    # Path to directory containing MP3 files (replace with your directory)
    mp3_directory = "/mnt/usb"
    
    # Collect all mp3 files in the directory
    #mp3_files = [os.path.join(mp3_directory, f) for f in os.listdir(mp3_directory) if f.endswith(".mp3")]
    walktree(mp3_directory, addtolist)
    
    if not mp3_files:
        logging.error("No MP3 files found in the directory")
        return
    
    logging.info(f"Found {len(mp3_files)} MP3 files. Starting slideshow...")
    
    # Play the MP3 files in a loop
    play_mp3_slideshow(mp3_files)
    
    # Quit pygame when done
    pygame.mixer.quit()

if __name__ == "__main__":
    main()
