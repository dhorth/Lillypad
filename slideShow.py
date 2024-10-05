#!/usr/bin/env python3
####################################################################
# Lillypad Restoration Slideshow
#-------------------------------------------------------------------
#
#This application is designed to display a slideshow of images on a
# portion of a Raspberry Pi display. It was originally created for a
# vintage TV that no longer worked. We replaced the old tube display
# with an LCD monitor and a Raspberry Pi. Since the LCD screen was 
# smaller than the original tube, the slideshow needed to use only a
# portion of the screen.
#
#The application uses Pygame to position and display images at a 
# preconfigured location on the screen. You can adjust both the size
# of the image and the position of its top-left corner by modifying 
# the settings below.
#
#Additionally, the program detects when a USB device is inserted, 
# scans the drive for images, and begins the slideshow automatically.
# While the slideshow works best if the images are the same size as 
# the configured image_size, the application can resize and crop 
# images that are different sizes to fit the display.
####################################################################

import argparse
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

file_list = []  # a list of all images being shown
title = "Lillypad Restoration Slideshow!"  # caption of the window...
waittime = 30   # default time to wait between images (in seconds)
white=(255,255,255)
image_location=(100,50) #the actual location of the image on the display, adjust this to center the image for your output device
image_size=(1280,1080) #default size of the image, this should match the width and height of your output device
fadeSpeed=50  #the speed of the slideshow

startdir="/mnt/usb"
logo="/home/pi/Icon.png"


# Set up the RotatingFileHandler
log_file = "/home/pi/slideShow.log"
max_log_size = 5 * 1024 * 1024  # 5 MB (cap size)
backup_count = 3  # Keep 3 backup files

handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=backup_count)

# Set up the logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


# Initalize PyGame and set the display to fullscreen
def init_pygame():
    try:
        logging.debug("init pygame")
        
        pygame.init()

        logging.debug("set display mode")
        #pygame.display.set_mode((0,0),pygame.FULLSCREEN|pygame.NOFRAME,32)
        # Hide the mouse pointer
        pygame.mouse.set_visible(False)
        
        # Test for image support
        if not pygame.image.get_extended():
            logging.info("Your Pygame isn't built with extended image support.")
            print("Shutting down - pygame error")
            sys.exit(1)
        else:
            logging.info("pygame starting")

      
        try:
            logging.debug("pygame set display mode")
            modes = pygame.display.list_modes()
            pygame.display.set_mode(max(modes))
        except  Exception as e:
            logging.error('mode: An exception occurred: {}'.format(e))

        try:
            logging.debug("pygame set caption to "+title)
            screen = pygame.display.get_surface()
            if screen is None:
                raise Exception("Failed to initialize display.")
            pygame.display.set_caption(title)
        except  Exception as e:
            logging.error('caption: An exception occurred: {}'.format(e))

        try:
            logging.debug("pygame fullscreen")
            pygame.display.toggle_fullscreen()
        except  Exception as e:
            logging.error('fullscreen: An exception occurred: {}'.format(e))

        logging.info("pygame init complete")
        
        return screen
    except  Exception as e:
        logging.error('PY GAME: An exception occurred: {}'.format(e))


#Recursively descend the directory tree rooted at top, calling the callback function for each regular file
def walktree(dir,callback):
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


#Add a file to a global list of image files.
def addtolist(file, extensions=['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
    global file_list  # ugh
    filename, ext = os.path.splitext(file)
    e = ext.lower()
    # Only add common image types to the list.
    if e in extensions:
        logging.info(f'Adding to list: {file}')
        file_list.append(file)


#A function to handle keyboard/mouse/device input events.
def handle_input(events):
    for event in events:  # Hit the ESC key to quit the slideshow.
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            pygame.quit()
            logger.info("Keyboard interrupt shutting down")
            print("Shutting down - keyboard interrupt")
            sys.exit()
      
# Function to fade in an image at the specified location on the display
def fade_in(screen, image, speed=fadeSpeed):
    for alpha in range(0, 256, speed):
        image.set_alpha(alpha)
        screen.fill((0, 0, 0))  # Fill screen with black before drawing the image
        screen.blit(image, image_location)
        pygame.display.update()
        pygame.time.delay(20)
        
# Function to fade out an image
def fade_out(screen, image, speed=fadeSpeed):
    for alpha in range(255, -1, -speed):
        image.set_alpha(alpha)
        screen.fill((0, 0, 0))
        screen.blit(image, image_location)
        pygame.display.update()
        pygame.time.delay(20)

        
# Get the image from the list and fade in and out
def show_image(screen, imageName):
    try:
        logging.debug("Show Image "+imageName)
        img = pygame.image.load(imageName)

        img = crop_and_resize(img)

        img = img.convert_alpha()

        # Rescale the image to fit the current display
        img=pygame.transform.scale(img,image_size)


        fade_in(screen,img)

        pygame.display.flip()

        handle_input(pygame.event.get())
        time.sleep(waittime)

        fade_out(screen,img)

    except pygame.error as e:
        logging.error(f"Error: {e}. Pygame display may not be initialized. Initializing now...")
        # Call your init method here
        screen = init_pygame()
        time.sleep(5)

    except  Exception as e:
        logging.error('show_image: An exception occurred: {}'.format(e))
        time.sleep(5)


#Crops and resizes the image to the target size (1024x1024) while maintaining the aspect ratio.
def crop_and_resize(image, target_size=(1024, 1024)):
    
    # Get the original image size
    img_width, img_height = image.get_size()
    
    # Calculate the aspect ratio of the original image
    aspect_ratio = img_width / img_height
    
    # Target size to maintain
    target_width, target_height = target_size
    
    # Determine the cropping area
    if aspect_ratio > 1:  # Wider than tall
        # Crop a horizontal section of the image to maintain the aspect ratio
        new_width = img_height
        new_height = img_height
        crop_rect = pygame.Rect((img_width - new_width) // 2, 0, new_width, new_height)
    else:  # Taller than wide or square
        # Crop a vertical section of the image to maintain the aspect ratio
        new_width = img_width
        new_height = img_width
        crop_rect = pygame.Rect(0, (img_height - new_height) // 2, new_width, new_height)
    
    # Crop the image using the rect
    cropped_image = image.subsurface(crop_rect)
    
    # Resize the cropped image to the target size (1024x1024)
    resized_image = pygame.transform.scale(cropped_image, target_size)
    
    return resized_image        


#  Depending on how the LCD display is mounted you may need to rotate screen
def rotate_display():
    logging.debug("rotate display")
    # Replace HDMI-1 with your actual display output name
    command = "xrandr --output HDMI-1 --rotate right"
    
    # Run the command using subprocess
    result = subprocess.run(command, shell=True, check=True)
    
    # Check if the command was successful
    if result.returncode == 0:
        logging.info("Display rotated successfully.")
    else:
        logging.info("Failed to rotate display.")


#Check if the device is mounted at the given mount point.
def device_mounted(mount_point):
    return os.path.ismount(mount_point)


#Monitor USB insert and remove events.
def monitor_usb_events():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block', device_type='partition')
    
    for device in iter(monitor.poll, None):
        action = device.action
        logging.info(f"Device event detected: {device.device_node}, Action: {action}")
        handle_device_changes(device, action)


#Detects the USB device by scanning the connected block devices.
def get_device_name():
    logging.info("Looking for USB device...")

    # Run lsblk and capture the output
    result = subprocess.run(['lsblk', '-rno', 'NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL'], stdout=subprocess.PIPE)
    output = result.stdout.decode()
    logging.debug(f"lsblk output:\n{output}")

    # Split the output into lines and find the device with the correct filesystem (e.g., vfat)
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and (parts[1] == 'exfat' or parts[1] == 'vfat'):  # Adjust 'vfat' to match the filesystem type
            device_name = f"/dev/{parts[0]}"
            logging.info(f"USB device found: {device_name}")
            return device_name

    logging.warning("No USB device found.")
    return None


#Mount the USB device.
def mount_device(device_name, mount_point):
    """"""
    logging.debug(f"Mounting device {device_name} at {mount_point}")
    try:
        if not os.path.ismount(mount_point):
            os.makedirs(mount_point, exist_ok=True)

        subprocess.run(['sudo', 'mount', device_name, mount_point], check=True)
        logging.info(f"Mounted {device_name} at {mount_point}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to mount {device_name}: {e}")


#Unmount the USB device if it's mounted.
def unmount_device(mount_point):
    """"""
    logging.debug(f"Unmounting device at {mount_point}")
    try:
        subprocess.run(['sudo', 'umount', mount_point], check=True)
        logging.info(f"Unmounted device from {mount_point}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to unmount device: {e}")


#Handle USB device insertion or removal.
def handle_device_changes(device, action):
    if action == "add":
        logging.info("USB device inserted and mounted.")
        device_name = get_device_name()
        if device_name:
            mount_device(device_name, startdir)
            file_list.clear()
            walktree(startdir, addtolist)
            if file_list:
                logging.info(f"Starting slideshow with {len(file_list)} images.")
            else:
                logging.warning("No images found on the USB device.")
    elif action == "remove":
        logging.info("USB device removed, stopping slideshow.")
        file_list.clear()
        unmount_device(startdir)

# Main
def main():
    global file_list, title, waittime
    print("Slideshow starting")
    logging.debug("Starting slideshow using dir - "+startdir)
    
    #give the system a chance to wake up
    time.sleep(10)
    
    #try to mount the usb device just in case
    mount_device("/dev/sda1", startdir)
    
    # Start monitoring USB events
    monitor_thread = threading.Thread(target=monitor_usb_events)
    monitor_thread.daemon = True
    monitor_thread.start()
   
    
    # Set the DISPLAY environment variable
    os.environ['DISPLAY'] = ':0'

    try:
        deviceName=get_device_name() 
        mount_device(deviceName, "/mnt/usb")
    except  Exception as e:
        logging.error('Mount Device: An exception occurred: {}'.format(e))
        
    
    logging.info("Looking for images at " + startdir)
    try:
        walktree(startdir, addtolist)  
    except  Exception as e:
        logging.error('Walktree: An exception occurred: {}'.format(e))


# this may take a while...
    if len(file_list) == 0:
        logging.info("no files adding our logo")
        file_list.append(logo)
    else:
        logging.info("Found in images "+str(len(file_list))+ " in "+startdir)

#    try:    
#        rotate_display()
#    except  Exception as e:
#        logging.error('Rotate Display: An exception occurred: {}'.format(e))
        
    try:    
        screen = init_pygame()
    except  Exception as e:
        logging.error('Init PyGame: An exception occurred: {}'.format(e))


    current = 0
    while True:
        if len(file_list) == 0:
            print("no files adding our logo")
            file_list.append(logo)
            current = 0

        try:
            show_image(screen, file_list[current])
        except pygame.error as err:
            logging.error(f"Failed to display {file_list[current]}: {err}")

        # When we get to the end, restart at the beginning
        if len(file_list) == 0:
            print("no files adding our logo")
            file_list.append(logo)
            current = 0
        else:
            current = (current + 1) % len(file_list)

if __name__ == "__main__":
    main()
