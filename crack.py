import requests
import time
import socket
import json
import sys
import re
import ipaddress

serverAddr = "http://10.11.52.150:5000"

headers = {
    "user-agent": "Java/11.0.26",
    "accept": "text/html, image/gif, image/jpeg, */*, q=0.2"
}

def validate_hall_ticket(hall_ticket):
    """Validate hall ticket number format."""
    pattern = r'^\d{2}BD[158]A(05|12|66|67)[A-HJ-NP-RT-Z0-9][A-HJ-NP-RT-Z1-9]$'
    return bool(re.match(pattern, hall_ticket))

def validate_ip(ip):
    """Validate IP address format."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def get_input_with_validation(servers):
    """Get and validate hall ticket number and server IP interactively."""
    hall_ticket = sys.argv[1].upper() if len(sys.argv) >= 2 else ""
    server_ip = sys.argv[2] if len(sys.argv) >= 3 else ""

    while not validate_hall_ticket(hall_ticket):
        hall_ticket = input("Enter hall ticket number: ").strip().upper()
        if not validate_hall_ticket(hall_ticket):
            print("Invalid hall ticket format. Please try again.")

    while not validate_ip(server_ip):
        if(len(servers) < 1):
            server_ip = input("Enter server IP address: ").strip().upper()
        if(len(servers) == 1):
            server_ip = servers[0]["ip"]
        print("Please select a server IP address from below: ")
        for index, server in enumerate(servers):
            print(f"{index+1}. {server["ip"]} ({server["name"]})")
        choice = int(input("Enter the index of your selection: "))
        server_ip = servers[choice - 1]["ip"]

        if not validate_ip(server_ip):
            print("Invalid IP address format. Please try again.")

    return hall_ticket, server_ip

def get_local_ip():
    """Determine the local IP address of the device."""
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = '127.0.0.1'
    return local_ip

def main():
    # Get and validate command line arguments
    hall_ticket = ""
    server_ip = ""

    # Step 1: GET the commands and token
    commands_url = f"{serverAddr}/commands/get/WINDOWS"

    response = requests.get(commands_url, headers=headers)

    if response.ok:
        commands_data = response.json()
        # print(json.dumps(commands_data, indent=4))
        token = commands_data.get("token")
        serverIps = commands_data.get("server_ips", [])
        serverNames = commands_data.get("server_names", [])
        servers = [{"ip": ip,"name": name} for ip, name in zip(serverIps, serverNames)]
        heartbeat_interval = 29
    else:
        raise Exception("Failed to get commands from the server.")

    if len(sys.argv) >= 3:
        if validate_hall_ticket(sys.argv[1]) and validate_ip(sys.argv[2]):
            hall_ticket = sys.argv[1].upper()
            server_ip = sys.argv[2]
        else:
            hall_ticket, server_ip = get_input_with_validation(servers)
    else:
        hall_ticket, server_ip = get_input_with_validation(servers)


    # Step 2: Define the heartbeat function
    def send_heartbeat():
        local_ip = get_local_ip()
        heartbeat_payload = {
            "hallTicketNo": hall_ticket,
            "localIp": local_ip,
            "serverIp": server_ip,
            "agentStatus": "ON",
            "appVersion": "1.0",
            "token": token
        }
        heartbeat_url = f"{serverAddr}/student/create"
        hb_response = requests.post(heartbeat_url, json=heartbeat_payload, headers=headers)
        print("Heartbeat sent. Status code:", hb_response.status_code)
        if not hb_response.ok:
            print("Error response:", hb_response.text)

    def send_stop_heartbeat():
        local_ip = get_local_ip()
        heartbeat_payload = {
            "hallTicketNo": hall_ticket,
            "localIp": local_ip,
            "serverIp": server_ip,
            "agentStatus": "OFF",
            "appVersion": "1.0",
            "token": token
        }
        heartbeat_url = f"{serverAddr}/student/create"
        hb_response = requests.post(heartbeat_url, json=heartbeat_payload, headers=headers)
        print("Stop Heartbeat sent. Status code:", hb_response.status_code)
        if not hb_response.ok:
            print("Error response:", hb_response.text)

    # Step 3: Send heartbeat every 30 seconds (or as specified)
    print(f"Starting betaal simulation for {hall_ticket} to server {server_ip}")
    while True:
        try:
            send_heartbeat()
            time.sleep(heartbeat_interval)
        except KeyboardInterrupt:
            print("\nSending stop heartbeat...")
            send_stop_heartbeat()
            print("\nStopping agent.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(heartbeat_interval)

if __name__ == "__main__":
    main()
