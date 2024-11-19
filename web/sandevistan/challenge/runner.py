import socket
import random
import hashlib
import os
import subprocess
import time
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# Configuration
LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = 4000
MIN_PORT = 28000
MAX_PORT = 30000
POW_DIFFICULTY = 6  # Number of leading zeros required in the PoW hash
INSTANCE_PREFIX = "sandevistan_"
SITE = "sandevistan.chal.perfect.blue"
INSTANCE_LIFETIME_MINUTES = 5

# Global variables
used_ports = set()
port_lock = Lock()
instances = {}
instance_lock = Lock()

def kill_existing_instances():
    print("Killing existing instances...")
    try:
        # Get a list of all Docker containers in JSON format
        result = subprocess.run(['docker', 'ps', '--format', '{{json .}}'], capture_output=True, text=True)
        containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
        
        for container in containers:
            # Check if the container name starts with our prefix
            if container['Names'].startswith(INSTANCE_PREFIX):
                print(f"Stopping container: {container['Names']}")
                subprocess.run(['docker', 'stop', container['ID']], check=True)
                subprocess.run(['docker', 'rm', container['ID']], check=True)
        
        print("Existing instances have been killed.")
    except subprocess.CalledProcessError as e:
        print(f"Error killing existing instances: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing Docker output: {e}")

def solve_pow(challenge, difficulty):
    nonce = 0
    while True:
        solution = f"{challenge}{nonce}".encode()
        hash_result = hashlib.sha256(solution).hexdigest()
        if hash_result.startswith('0' * difficulty):
            return nonce
        nonce += 1

def verify_pow(challenge, nonce, difficulty):
    solution = f"{challenge}{nonce}".encode()
    hash_result = hashlib.sha256(solution).hexdigest()
    return hash_result.startswith('0' * difficulty)

def get_available_port():
    with port_lock:
        available_ports = set(range(MIN_PORT, MAX_PORT + 1)) - used_ports
        if not available_ports:
            return None
        port = random.choice(list(available_ports))
        used_ports.add(port)
        return port

def release_port(port):
    with port_lock:
        used_ports.remove(port)

def generate_instance_name():
    return f"{INSTANCE_PREFIX}{int(time.time())}"

def start_instance(port, instance_name):
    env = os.environ.copy()
    env['PORT'] = str(port)
    subprocess.Popen(['docker', 'compose', '-p', instance_name, 'up', '-d'], env=env)

def stop_instance(instance_name):
    subprocess.run(['docker', 'compose', '-p', instance_name, 'down'])

def auto_kill_instance(instance_name, port):
    time.sleep(INSTANCE_LIFETIME_MINUTES * 60)
    with instance_lock:
        if instance_name in instances:
            stop_instance(instance_name)
            del instances[instance_name]
    release_port(port)
    print(f"Instance {instance_name} on port {port} has been terminated after {INSTANCE_LIFETIME_MINUTES} minutes.")

def handle_client(client_socket):
    challenge = os.urandom(16).hex()
    client_socket.send(f"Solve PoW: hashlib.sha256(b'{challenge}' + <your_input>).hexdigest().startswith('0' * {POW_DIFFICULTY}):".encode())
    
    nonce = client_socket.recv(1024).decode().strip()
    
    if verify_pow(challenge, nonce, POW_DIFFICULTY):
        port = get_available_port()
        if port is None:
            client_socket.send(b"No available ports. Please try again later.\n")
            client_socket.close()
            return

        instance_name = generate_instance_name()
        client_socket.send(f"PoW verified. Starting instance on port {SITE}:{port}\n".encode())
        
        # Start Docker Compose instance
        start_instance(port, instance_name)

        with instance_lock:
            instances[instance_name] = port

        # Schedule auto-kill
        ThreadPoolExecutor(max_workers=1).submit(auto_kill_instance, instance_name, port)
    else:
        client_socket.send(b"Invalid PoW solution. Disconnecting.\n")
    
    client_socket.close()

def main():
    # Kill existing instances before starting the server
    kill_existing_instances()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(5)

    print(f"Listening on {LISTEN_HOST}:{LISTEN_PORT}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            executor.submit(handle_client, client_socket)

if __name__ == "__main__":
    main()
