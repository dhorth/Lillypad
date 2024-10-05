import pyudev
import psutil
import subprocess
import os
import signal
import time

context = pyudev.Context()

monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by(subsystem='block', device_type='partition')

# Start monitoring in the background
monitor.start()

print("Monitoring for USB drives...")

connected_device_node = None
process = None  # To store the process object of the started program

def get_mount_point(device_node):
    """
    Get the mount point for the given device node.
    """
    partitions = psutil.disk_partitions()
    for partition in partitions:
        if partition.device == device_node:
            return partition.mountpoint
    return None

def wait_for_mount(device_node, timeout=10):
    """
    Wait for the device to be mounted within a given timeout.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        mount_point = get_mount_point(device_node)
        if mount_point:
            return mount_point
        time.sleep(0.5)  # Wait before checking again
    return None


def check_usb_drive(mount_point):
    # List all files and directories in the mount point
    try:
        devices = os.listdir(mount_point)
        if devices:
            print("USB drive(s) detected:")
            for device in devices:
                print(f" - {device}")
            return True
        else:
            print("No USB drives detected.")
            return False
    except FileNotFoundError:
        print(f"Mount point '{mount_point}' does not exist.")
        return False


try:
    if __name__ == "__main__":
        usb_inserted = check_usb_drive('/media')
        if usb_inserted:
            # Perform actions with the detected USB drive
             process = subprocess.Popen(['python3', 'slideShow.py', '/media'])
        else:
            # Handle case where no USB drive is detected
            print("No USB drive to inserted waiting.")
            
except KeyboardInterrupt:
    print("Monitoring stopped.")
    if process:
        print(f"Stopping the process with PID: {process.pid}")
        os.kill(process.pid, signal.SIGTERM)       
        
# Event loop to handle device events
try:
    for device in iter(monitor.poll, None):
        if device.action == 'add' and process is None:
            connected_device_node = device.device_node
            print(f"USB drive connected: {connected_device_node}")
            
            # Wait for the device to be mounted
            mount_point = wait_for_mount(connected_device_node)
            
            if mount_point:
                print(f"Device mounted at {mount_point}")
                # Replace '/path/to/your/other_program.py' with the path to your Python script
                process = subprocess.Popen(['python3', 'slideShow.py', mount_point])
                print(f"Started process with PID: {process.pid}")
            else:
                print(f"Device {connected_device_node} is not mounted after timeout.")

        elif device.action == 'remove' and device.device_node == connected_device_node:
            print(f"USB drive removed: {device.device_node}")
            if process:
                print(f"Stopping the process with PID: {process.pid}")
                os.kill(process.pid, signal.SIGTERM)
                process = None
            print("Program stopped. Exiting monitor.")
            break

except KeyboardInterrupt:
    print("Monitoring stopped.")
    if process:
        print(f"Stopping the process with PID: {process.pid}")
        os.kill(process.pid, signal.SIGTERM)

print("Program exited.")
