#!/usr/bin/env python3

import socket
import os
import shlex
import subprocess
import base64

def server():
    host = '127.0.0.1'
    port = 12345

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    print(f"Server listening on {host}:{port}")

    conn, addr = server_socket.accept()
    print(f"Client connected: {addr}")

    current_directory = os.getcwd()

    while True:
        command = input(f"user@{socket.gethostname()}:{current_directory}$ ")
        conn.sendall(command.encode())

        if command.lower() == 'exit':
            break

        if command.lower() == 'ggez':
            print("GG EZ. Closing connections and exiting.")
            conn.sendall("exit".encode())
            conn.close()
            server_socket.close()
            exit()

        try:
            if command.startswith("cd "):
                try:
                    new_dir = command[3:].strip()
                    if os.path.isdir(new_dir):
                        os.chdir(new_dir)
                        current_directory = os.getcwd()
                        conn.sendall(f"cwd:{current_directory}".encode())
                    else:
                        print("cd: no such directory:", new_dir)
                        conn.sendall(f"cd: no such directory: {new_dir}".encode())
                except Exception as e:
                    error_message = f"Error changing directory: {e}"
                    print(error_message)
                    conn.sendall(error_message.encode())
            elif command == "ll":
                try:
                    ls_command = "ls -al"
                    process = subprocess.Popen(shlex.split(ls_command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    output = stdout.decode() + stderr.decode()
                    print(output)
                except Exception as e:
                    error_message = f"An error occurred: {e}"
                    print(error_message)
                    conn.sendall(error_message.encode())
            elif command.startswith("deploy "):  # Deploy with spaces
                try:
                    parts = command.split(" ", 2)
                    if len(parts) != 3:
                        raise ValueError("Invalid deploy command.  Usage: deploy /server/path /client/path")

                    server_path = parts[1].strip()
                    client_path = parts[2].strip()

                    with open(server_path, "r") as f:
                        script_content = f.read()

                    script_content_encoded = base64.b64encode(script_content.encode()).decode()

                    conn.sendall(f"deploy:{client_path}:{script_content_encoded}".encode())  # Send deploy info

                    output = conn.recv(4096).decode()  # Receive script output
                    print(output)  # Print on the server

                except FileNotFoundError:
                    error_message = f"Script file not found: {server_path}"
                    print(error_message)
                    conn.sendall(error_message.encode())
                except ValueError as e:
                    error_message = str(e)
                    print(error_message)
                    conn.sendall(error_message.encode())
                except Exception as e:
                    error_message = f"Error deploying/executing script: {e}"
                    print(error_message)
                    conn.sendall(error_message.encode())
            else:
                try:
                    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    output = stdout.decode() + stderr.decode()
                    print(output)
                except FileNotFoundError:
                    error_message = f"Command not found: {command}"
                    print(error_message)
                    conn.sendall(error_message.encode())
                except Exception as e:
                    error_message = f"An error occurred: {e}"
                    print(error_message)
                    conn.sendall(error_message.encode())

        except ConnectionResetError:
            print("Client disconnected.")
            break
        except Exception as e:
            print(f"A general error occurred on the server: {e}")
            break

    conn.close()
    server_socket.close()

if __name__ == "__main__":
    server()
