##################### VIKRAM - Defeating BETAAL's trickery #####################


import ipaddress
import platform
import re
import requests
import socket
import sys
import time
from plyer import notification

BETAAL_ADDR = "10.1.52.150"
BETAAL_PORT = 5000

BETAAL_URL = f"http://{BETAAL_ADDR}:{BETAAL_PORT}"
BETAAL_VERSION = "1.0"

HEADERS = {
    "user-agent": "Java/11.0.26",
    "accept": "text/html, image/gif, image/jpeg, */*, q=0.2"
}

OS = "WINDOWS"

# system = platform.system()
# if system == 'Linux':
#   OS = "LINUX"
# elif system == 'Darwin':
#   OS = "MAC"

heartbeat_payload = {
    "hallTicketNo": None,
    "localIp": None,
    "serverIp": None,
    "agentStatus": None,
    "appVersion": BETAAL_VERSION,
    "token": None
}

################################################################################


def validate_hall_ticket_no(hall_ticket_no):
  """Validate hall ticket number format."""
  pattern = r'^\d{2}BD[158]A(05|12|66|67)[A-HJ-NP-RT-Z0-9][A-HJ-NP-RT-Z1-9]$'
  return bool(re.match(pattern, hall_ticket_no))


def validate_ip(ip):
  """Validate IP address format."""
  pattern = r'10.11.([0-9]|[1-9][0-9]|1[0-9]{2]|2})'


def get_hall_ticket_no():
  """Get and validate hall ticket number interactively."""
  for _ in range(3):
    hall_ticket_no = input("\nEnter hall ticket number: ").strip().upper()
    if validate_hall_ticket_no(hall_ticket_no):
      return hall_ticket_no
    print("Invalid hall ticket number. Try again.", file=sys.stderr)
  else:
    raise Exception(
        "Invalid hall ticket number. Max attempts exceeded. Exiting.")


def get_server_ip(servers, server_names):
  """Get and validate server IP interactively."""
  print("\nAvailable servers:")
  for i in range(len(servers)):
    print(f"  {i+1}. {servers[i]} - {server_names[i]}")
  for _ in range(3):
    choice = input("Select server by number: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(servers):
      return servers[int(choice) - 1]
    print("Invalid input. Try again.", file=sys.stderr)
  else:
    raise Exception("Invalid input. Max attempts exceeded. Exiting.")


def get_local_ip():
  """Determine the local IP address of the device."""
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.settimeout(0)
  try:
    s.connect((BETAAL_ADDR, BETAAL_PORT))
    local_ip = s.getsockname()[0]
  except Exception:
    raise Exception("Not connected to the test network, Exiting")
  finally:
    s.close()
  return local_ip


def send_heartbeat(status="ON"):
  heartbeat_payload["agentStatus"] = status
  hb_response = requests.post(
  BETAAL_URL + "/student/create", json=heartbeat_payload, headers=HEADERS, timeout=2)

  if (status == "ON"):
    print("  Heartbeat sent. Status code:", hb_response.status_code)

  # Can be ignored??
  # if not hb_response.ok:
  #   print("Error response:", hb_response.text, file=sys.stderr)


def main():
  print("Starting VIKRAM - Defeating BETAAL's trickery")

  hall_ticket_no = sys.argv[1].upper() if len(sys.argv) > 1 else ""
  server_ip = sys.argv[2] if len(sys.argv) > 2 else ""

  heartbeat_payload["localIp"] = get_local_ip()

  send_heartbeat("OFF")

  response = requests.get(
      BETAAL_URL + f"/commands/get/{OS}", headers=HEADERS)
  if not response.ok:
    raise Exception("Failed to get details from the server. Exiting.")

  commands_data = response.json()
  servers = commands_data.get("server_ips", [])
  server_names = commands_data.get("server_names", [])
  heartbeat_payload["token"] = commands_data.get("token")
  heartbeat_interval = commands_data.get("heartbeatTime", 10)

  if not servers:
    raise Exception("No available servers available in response. Exiting.")

  if not validate_hall_ticket_no(hall_ticket_no):
    if hall_ticket_no:
      print("Invalid hall ticket number.", file=sys.stderr)
    hall_ticket_no = get_hall_ticket_no()

  if server_ip not in servers:
    if server_ip:
      print("Invalid server ip.", file=sys.stderr)
    server_ip = get_server_ip(servers, server_names)

  heartbeat_payload["hallTicketNo"] = hall_ticket_no
  heartbeat_payload["serverIp"] = server_ip

  print(f"\nSimulating BETAAL for {hall_ticket_no} to server {server_ip}")
  while True:
    try:
      send_heartbeat()
      time.sleep(heartbeat_interval)
    except KeyboardInterrupt:
      print("\033[2K\nStopping BETAAL simulation...")
      send_heartbeat("OFF")
      exit(0)
    except Exception as e:
        notification.notify(
            title = 'Disconnected from betaal server',
            message = 'Try reconnecting to test  network',
            app_icon = None,
            timeout = 10,
            hints = {
                "urgency": 2
            }
        )
        print(f"Error: {e}", file=sys.stderr)
        time.sleep(heartbeat_interval)


if __name__ == "__main__":
  main()
