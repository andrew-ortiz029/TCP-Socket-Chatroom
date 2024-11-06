import socket
import traceback
from threading import Thread, Lock

# Create and Bind a TCP Server Socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#host_name = socket.gethostname()
host_name = "localhost"
s_ip = socket.gethostbyname(host_name)
port = 18000
serverSocket.bind((host_name, port))

# Outputs Bound Contents
print("Socket Bound")
print("Server IP: ", s_ip, " Server Port:", port)

# Listens for 5 Users
serverSocket.listen(10)

# Creates a set of clients
client_List = set()
active_usernames = set() # keeps track of unique usernames
msgList = []

# Create a dictionary for clients with their usernames to map them together in order to ensure messages aren't sent to unready clients
clients = {}


def clientWatch(cs):
    # Now decode if its 1, 2, 3
    while True:
        try:
            username = None # store client username
            # Constantly listens for incoming messages from a client
            msg = cs.recv(1024).decode()
            if not msg:  # Check if msg is empty (client has disconnected)
                print("Client disconnected unexpectedly.")
                break  # Exit the loop

            if msg == "1": # request a report
                if len(clients) == 0:
                    cs.send("There are 0 active users in the chatroom.\n".encode())
                    cs.send("end of report.\n".encode())
                else:
                    cs.send(f"There are {len(clients)} active users in the chatroom.\n".encode())
                    # give a report if theres active users in the chatroom
                    i = 1 
                    for client_socket, client_username in clients.items():
                        ip = client_socket.getpeername()[0] # get IP
                        port = client_socket.getpeername()[1] # get port
                        cs.send(f"{i}. {client_username} at IP: {ip} and port: {port}\n".encode())
                        i+=1 # iterate for each client
                    cs.send("end of report.\n".encode())

            elif msg == "2": # enter the chatroom if possible
                global active_usernames
                adminFlag = 0

                # 3 people max at a time in the chat room
                if len(client_List) >= 3:
                    cs.send("Chatroom is full. Try again later.".encode())
                    continue
                else:
                    cs.send("Chat room has space!".encode()) # send response to handle

                while True:
                    print("Waiting for input...")
                    msg = cs.recv(1024).decode()  # Wait for the input and if username is None then handle them entering
                    print("No longer waiting for input...")

                    if username is None: # if client doesn't have a username
                        if msg in active_usernames:
                            # Constantly listens for incoming message from a client
                            # msg = cs.recv(1024).decode()
                            cs.send("Username is already taken. Please choose another.".encode()) # this will prompt loop to run again and ask for another username input
                            continue  # Skip further processing until a name is received
                        else:
                            cs.send("Username is available.".encode())
                            username = msg # set username to msg
                            active_usernames.add(username) # add it to the set of usernames
                            client_List.add(cs) # add it to client list
        
                            # iterate through and send all clients message saying that new user joined chat
                            print(f"{username} has joined the chat.") # print server side
                            # Add the client to the clients dictionary
                            clients[cs] = username

                            # send welcome message
                            welcome_msg = f"Server: {username} joined the chatroom." 
                            msgList.append(welcome_msg)
                            # Send the message to all connected clients who are ready
                            for client_socket, client_username in clients.items():
                                client_socket.send(welcome_msg.encode())
                                
                            continue  # Skip further processing until a message is received

                    # if user enters admin as user name set admin Flag to 1, let server and client know admin connected
                    #if msg == "admin":
                        #adminFlag = 1
                        #print("Admin Connected")
                        #adminMsg = "Type 'viewall' to view all recorded messages"
                        #cs.send(adminMsg.encode())
                        #continue
                    
                    # if q is entered remove the client from the client list and close connection
                    if msg == "q":
                        print(f"{username} Disconnected")
                        del clients[cs]  # Remove the client from the dictionary
                        client_List.remove(cs)

                        # send exit message
                        exit_msg = f"Server: {username} left the chatroom." 
                        active_usernames.remove(username)
                        msgList.append(exit_msg)
                        cs.send("You have left the chatroom.".encode())

                        # Send the message to all connected clients who are ready
                        for client_socket, client_username in clients.items():
                            client_socket.send(exit_msg.encode())

                        username = None
                        #cs.close()
                        break

                    # splits of last word of message (due to username and time being sent)
                    newMsg = msg.split()
                    # print(newMsg[-1])
                    # checks if user is an admin and has entered 'viewall', sends messageList to the admin client
                    if adminFlag and newMsg[-1] == "viewall":
                        print("Admin Accessed Chat Log")
                        cs.send(("----------Chatlog----------").encode())
                        for x in msgList:
                            # print(x)
                            cs.send((x + "\n").encode())

                        cs.send(("\n----------EndLog----------").encode())
                        continue

                    # Iterates through clients and sends the message to all connected clients
                    # also only sends messages if client is ready
                    msgList.append(msg)
                    # Send the message to all connected clients who are ready
                    for client_socket, client_username in clients.items():
                        client_socket.send(msg.encode())

            elif msg.strip() == "3":  # Client is quitting the program
                if username in active_usernames:
                    active_usernames.remove(username)
                if cs in client_List:
                    client_List.remove(cs)
                if cs in clients:
                    del clients[cs]  # Remove the client from the dictionary
                cs.close()  # Close the socket
                # print("I am returning !!!!!!")
                return  # Exit the function

        except Exception as e:
            print(f"Error: {e}")
            print(f"Username: {username}")
            print(f"Client Socket: {cs}")
            print("Current active usernames:", active_usernames)
            print("Current client list:", client_List)
            print("Current clients dictionary:", clients)
                        
            # Log the traceback
            print("Traceback:")
            traceback.print_exc()
                        
            if username:
                active_usernames.remove(username)
            if cs in client_List:
                client_List.remove(cs)
            if cs in clients:
                del clients[cs]  # Remove the client from the dictionary

while True:
    lock = Lock() # create a lock instance

    # lets implement only up to 3 active users at a time
    try:
        # Continues to listen / accept new clients
        client_socket, client_address = serverSocket.accept()

        # add a lock because of threads
        #with lock:
            #if len(client_List) >= 3:
                #print(f"Connection denied for {client_address}: chatroom is at capactity.")
                #client_socket.send("Chatroom is full. Try again later.".encode())
                #client_socket.close() # close the socket as they are denied from entry
                #continue # next iteration

            # Client connects successfully
            #client_socket.send("Chatroom has space.".encode()) # send any other request showing that the chat room isn't full as the client is waiting on a request
        print(client_address, "Connected!")
            # Adds the client's socket to the client set
            # client_List.add(client_socket)

        # Create a thread that listens for each client's messages
        t = Thread(target=clientWatch, args=(client_socket,))

        # Make a daemon so thread ends when main thread ends
        t.daemon = True

        t.start()

    except Exception as e:
        print("Error accepting")

# Close out clients
for cs in client_List:
    cs.close()
# Close socket
s.close()
