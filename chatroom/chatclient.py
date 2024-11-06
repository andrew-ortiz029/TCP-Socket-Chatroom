import socket
from threading import Thread
from datetime import datetime

# Sets the preselected IP and port for the chat server
host_name = "localhost"
port = 18000

# Creates the TCP socket
new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Connecting to", host_name, port, "...")
new_socket.connect((host_name, port))
print("Connected.")

# Global variable to hold the username
name = None

# Function to listen for messages from the server
def listen_for_messages():
    global running_flag
    while running_flag:
        try:
            message = new_socket.recv(1024).decode()
            if message:
                print("\n" + message)  # Print incoming messages
        except Exception as e:
            print("Error receiving message:", e)
            break

# Shared flag to control the thread
running_flag = True
thread_flag = False

# Loop to prompt the client for a selection
while True:
    print("\n1. Get a report of the chatroom from the server.")
    print("2. Request to join the chatroom.")
    print("3. Quit the program.")
    userSelection = input("Your choice: ")

    capacity_flag = False
    
    if userSelection == "1":
        new_socket.send(userSelection.encode())
        while True:
            response = new_socket.recv(1024).decode()
            messages = response.splitlines()

            for message in messages:
                if message.strip() == "end of report.":
                    break
                else:
                    print(message)

            if any(msg.strip() == "end of report." for msg in messages):
                break
        continue

    elif userSelection == "2":
        new_socket.send(userSelection.encode()) # send 2
        
        response = new_socket.recv(1024).decode() # wait for response on chat room capacity

        if response == "Chatroom is full. Try again later.": # chat room is at capacity 
            capacity_flag = True
            print(response)

        else: # chat room has capacity prompt for name
            print(response)
            while True: # start name loop
                name = input("Enter your username: ")
                new_socket.send(name.encode())

                # Wait for response on if the name is already taken or chat room is full 
                response = new_socket.recv(1024).decode()
                if response == "Username is already taken. Please choose another.":
                    print(response)
                    continue
                else:
                    print(response)  # Username accepted
                    print("Type lowercase 'q' at any time to quit!")
                    
                    if thread_flag == False: # ensure that only one thread is made for this client
                        thread_flag = True
                        running_flag = True
                        t = Thread(target=listen_for_messages)
                        t.daemon = True
                        print("thread starting...")
                        t.start()

                    break

    elif userSelection == "3":
        new_socket.send(userSelection.encode())
        print("Exiting the program.")
        new_socket.close()
        break

    else:
        print("Invalid input. Please try again.")
        continue
    
    if capacity_flag == True:
        continue # go back to the top of the loop

    # Loop for sending messages
    while True:
        to_send = input()

        if to_send.lower() == "q":
            new_socket.send(to_send.encode())  # Notify the server that the user is leaving the chat
            #print("You have left the chat room.")
             # Stop the listener thread by setting the flag to False
            running_flag = False
        
            # Wait for the thread to finish before exiting
            t.join()

            # Reset thread flag
            thread_flag = False
            
            break  # Break out of the message-sending loop to return to the main menu
        
        # Append the username and time to the message
        if name:  # Ensure the username is set
            to_send = name + ": " + to_send
            date_now = datetime.now().strftime("[%H:%M] ")
            to_send = date_now + to_send

            # Send the message to the server
            new_socket.send(to_send.encode())

