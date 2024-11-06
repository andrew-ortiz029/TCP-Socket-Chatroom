import socket
import os
import time
from threading import Thread
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, Scrollbar

# Sets the preselected IP and port for the chat server
host_name = "localhost"
port = 18000

# Creates the TCP socket
new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
new_socket.connect((host_name, port))

# Global variable to hold the username
name = None

# Shared flag to control the thread
running_flag = False
thread_flag = False

# Function to listen for messages from the server
def listen_for_messages():
    global running_flag
    while running_flag:
        try:
            message = new_socket.recv(1024).decode()
            if message:
                root.after(0, update_chat_history, message)  # Safe update of the chat history
        except Exception as e:
            print("Error receiving message:", e)
            break

# Function to safely update the chat history from the listener thread
def update_chat_history(message):
    chat_history.config(state=tk.NORMAL)  # Enable editing to insert the message
    chat_history.insert(tk.END, message + '\n')  # Print incoming messages
    chat_history.yview(tk.END)  # Auto-scroll to the bottom
    chat_history.config(state=tk.DISABLED)  # Disable editing after updating

# global thread variable
t = Thread(target=listen_for_messages)
t.daemon = True

# Function to request a report from the server
def request_report():
    new_socket.send("1".encode())
    response = new_socket.recv(1024).decode()
    messages = response.splitlines()

    chat_history.config(state=tk.NORMAL)  # Enable editing to insert the report
    for message in messages:
        if message.strip() == "end of report.":
            break
        chat_history.insert(tk.END, message + '\n')
    chat_history.yview(tk.END)  # Auto-scroll to the bottom
    chat_history.config(state=tk.DISABLED)  # Disable editing after updating

# Function to join the chatroom
def join_chatroom():
    new_socket.send("2".encode())
    
    response = new_socket.recv(1024).decode()  # Wait for response on chat room capacity
    if response == "Chatroom is full. Try again later.":
        messagebox.showinfo("Chatroom Full", response)
        return

    # Switch to username entry
    hide_main_menu()
    show_username_prompt()

# Function to set the username
def set_username():
    global name, thread_flag, running_flag, t
    username = username_entry.get()
    new_socket.send(username.encode())

    # Wait for response if username is valid
    response = new_socket.recv(1024).decode()
    if response == "Username is already taken. Please choose another.":
        messagebox.showinfo("Username Taken", response)
        return

    name = username
    chat_history.config(state=tk.NORMAL)  # Enable editing to insert welcome message
    chat_history.insert(tk.END, f"Welcome {name}! You have joined the chatroom.\n")
    chat_history.yview(tk.END)
    chat_history.config(state=tk.DISABLED)  # Disable editing after updating

    # Request the chat history
    chat_history.config(state=tk.NORMAL)  # Enable editing to receive the history
    while True:
        # Receive history in chunks
        response = new_socket.recv(1024).decode()
        messages = response.splitlines()

        for message in messages:
            if message.strip() == "end of report.":
                break
            chat_history.insert(tk.END, message + '\n')

        chat_history.yview(tk.END)  # Auto-scroll to the bottom

        if "end of report." in messages:
            break
    chat_history.config(state=tk.DISABLED)  # Disable editing after updating

    # hide username prompt
    hide_username_prompt()

    # Start the listener thread to receive messages
    if not thread_flag:
        thread_flag = True
        running_flag = True
        t.start()

    # Show the message input field
    show_message_input()

# Function to leave the chatroom
def leave_chatroom():
    global running_flag, t, thread_flag  # Declare `t` as global so we can access it
    
    # Step 1: Notify the server that the user is leaving the chatroom
    new_socket.send("q".encode())  
    running_flag = False  # Stop the listener thread immediately
    
    # Step 2: Safely stop the listener thread without blocking the GUI
    if t.is_alive():
        # Instead of t.join(), we will set a flag that signals the thread to stop
        print("Stopping listener thread.")
        t.join()  # Gracefully wait for the listener thread to finish

    # Step 3: Update the chat history with the message about leaving
    def update_gui():
        global thread_flag, running_flag
        chat_history.config(state=tk.NORMAL)  # Enable editing to insert message about leaving
        chat_history.insert(tk.END, "You have left the chatroom.\n")
        chat_history.yview(tk.END)
        chat_history.config(state=tk.DISABLED)  # Disable editing after updating
        
        # Step 4: Reset flags and show the main menu again
        thread_flag = False
        running_flag = False  # Reset running_flag just in case
        show_main_menu()  # Show the main menu after leaving the chatroom

    # Safely update the GUI after the thread has stopped
    print("im not reachinig here")
    root.after(0, update_gui)

# Function to send a message
def send_message():
    message = message_entry.get()
    if message.lower() == "q":
        leave_chatroom()
    elif message.lower() == "a":
        upload_file()
    elif name:
        date_now = datetime.now().strftime("[%H:%M] ")
        message = date_now + name + ": " + message
        new_socket.send(message.encode())
        message_entry.delete(0, tk.END)  # Clear the message input field

# Function to upload a file
def upload_file():
    file_path = filedialog.askopenfilename(title="Select a File")
    if file_path:
        try:
            new_socket.send("a".encode())
            filename = os.path.basename(file_path)
            new_socket.send(filename.encode())

            time.sleep(.5) # Sleep for .5 seconds

            with open(file_path, "r") as f:
                data = f.read()
                while data:
                    new_socket.send((str(data) + '\n').encode())
                    data = f.read()
            #new_socket.send("end of file.\n".encode())
            f.close()
            chat_history.config(state=tk.NORMAL)  # Enable editing to insert message about file
            chat_history.insert(tk.END, f"File '{filename}' sent successfully.\n")
            chat_history.yview(tk.END)
            chat_history.config(state=tk.DISABLED)  # Disable editing after updating
        except IOError:
            messagebox.showerror("File Error", "Invalid file path or file not found.")

# Helper functions to toggle between screens (menu -> chat, etc.)
def hide_main_menu():
    main_menu_frame.pack_forget()

def show_main_menu():
    main_menu_frame.pack(pady=20)

def show_username_prompt():
    username_prompt_frame.pack(pady=10)

def hide_username_prompt():
    username_prompt_frame.pack_forget()

def show_message_input():
    message_input_frame.pack(pady=10)

def hide_message_input():
    message_input_frame.pack_forget()

# Setup Tkinter GUI window
root = tk.Tk()
root.title("Chat Client")
root.geometry("600x500")

# Chat history display (Text widget)
chat_history_frame = tk.Frame(root)
chat_history_frame.pack(pady=10)
scrollbar = Scrollbar(chat_history_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
chat_history = tk.Text(chat_history_frame, height=20, width=70, wrap=tk.WORD, state=tk.DISABLED)
chat_history.pack(side=tk.LEFT)
scrollbar.config(command=chat_history.yview)
chat_history.config(yscrollcommand=scrollbar.set)

# Main menu (Request report / Join chatroom / Quit)
main_menu_frame = tk.Frame(root)

request_report_button = tk.Button(main_menu_frame, text="Request Report", command=request_report)
request_report_button.pack(pady=5)

join_button = tk.Button(main_menu_frame, text="Join Chatroom", command=join_chatroom)
join_button.pack(pady=5)

quit_button = tk.Button(main_menu_frame, text="Quit", command=root.quit)
quit_button.pack(pady=5)

main_menu_frame.pack(pady=20)

# Username entry frame (only shown after joining)
username_prompt_frame = tk.Frame(root)
username_label = tk.Label(username_prompt_frame, text="Enter your username:")
username_label.pack(pady=5)
username_entry = tk.Entry(username_prompt_frame)
username_entry.pack(pady=5)
username_submit_button = tk.Button(username_prompt_frame, text="Submit", command=set_username)
username_submit_button.pack(pady=5)

# Message input frame (only shown after joining)
message_input_frame = tk.Frame(root)

message_label = tk.Label(message_input_frame, text="Message:")
message_label.pack(side=tk.LEFT, padx=5)

message_entry = tk.Entry(message_input_frame, width=40)
message_entry.pack(side=tk.LEFT, padx=5)

send_button = tk.Button(message_input_frame, text="Send", command=send_message)
send_button.pack(side=tk.LEFT, padx=5)

leave_button = tk.Button(message_input_frame, text="Leave Chatroom", command=leave_chatroom)
leave_button.pack(side=tk.LEFT, padx=5)

# Start the main Tkinter loop
root.mainloop()
