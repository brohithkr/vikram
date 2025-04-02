#!/usr/bin/env python3

##################### VIKRAM - Defeating BETAAL's trickery #####################

import platform
import re
import requests
import sys
import time
from typing import Tuple

if platform.system() != "Darwin":
  from plyer import notification

from netutils import ADAPTERS, switch_interface, get_ip_for_interface

BETAAL_ADDR = "10.11.52.150"
BETAAL_PORT = 5000

BETAAL_URL = f"http://{BETAAL_ADDR}:{BETAAL_PORT}"
BETAAL_VERSION = "1.1"

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

session = None

################################################################################


def validate_hall_ticket_no(hall_ticket_no):
  """Validate hall ticket number format."""
  pattern = r'^\d{2}BD[158]A(05|12|66|67)[A-HJ-NP-RT-Z0-9][A-HJ-NP-RT-Z1-9]$'
  return bool(re.match(pattern, hall_ticket_no))

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
  if len(servers) == 1:
    return servers[0]

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


def get_local_ip() -> Tuple[str, requests.Session]:
  """Determine the local IP address of the device."""
  session = requests.sessions.session()

  for adapter in ADAPTERS:
    if ip:= get_ip_for_interface(adapter.nice_name):
      switch_interface(session, adapter.nice_name)
      try:
        resp = session.get(BETAAL_URL, timeout=2)
        if resp.status_code < 400:  
          return ip, session
      except (requests.ConnectionError, requests.Timeout):
        pass

  raise Exception("Not connected to the test network, Exiting")


def send_heartbeat(status="ON"):
  heartbeat_payload["agentStatus"] = status
  hb_response = session.post(
      BETAAL_URL + "/student/start", json=heartbeat_payload, headers=HEADERS, timeout=2)

  if (status == "ON"):
    print(f"  {time.strftime('%I:%M:%S %p')} - Heartbeat sent. Status code:", hb_response.status_code, end="\r")

  # Can be ignored??
  # if not hb_response.ok:
  #   print("Error response:", hb_response.text, file=sys.stderr)


def main():
  print("Starting VIKRAM - Defeating BETAAL's trickery")

  hall_ticket_no = sys.argv[1].upper() if len(sys.argv) > 1 else ""
  server_ip = sys.argv[2] if len(sys.argv) > 2 else ""

  global session
  localip, session = get_local_ip()
  heartbeat_payload["localIp"] = localip
  send_heartbeat("OFF")

  response = session.get(
      BETAAL_URL + f"/commands/get/{OS}", headers=HEADERS,)
  if not response.ok:
    raise Exception("Failed to get details from the server. Exiting.")
  else:
    HEADERS["etag"] = response.headers.get("etag", "")

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

  prev = "Title"
  print(f"\nSimulating BETAAL for {hall_ticket_no} to server {server_ip}")
  while True:
    try:
      send_heartbeat()
      prev = "HB"
    except (requests.ConnectionError, requests.Timeout):
      if prev == "HB": 
        print()
      print(f"  {time.strftime('%I:%M:%S %p')} - Error: Disconnected from BETAAL server", file=sys.stderr)
      if platform.system() != "Darwin":
        notification.notify(
            title='Disconnected from BETAAL server',
            message='Try reconnecting to test network',
            app_name="Vikram",
            app_icon='notification',
            timeout=5,
            hints={"urgency": 1}
        )
        prev = "Err"
    except Exception as e:
      if prev == "HB": 
        print()
      print(f"Error: {e}", file=sys.stderr)
      prev = "Err"
    finally:
      try:
        time.sleep(heartbeat_interval)
      except KeyboardInterrupt:
        if prev == "HB": 
          print()
        print("\033[2D\033[K\nStopping BETAAL simulation...")
        try:
          send_heartbeat(status="OFF")
          prev = "HB"
        except Exception:
          if prev == "HB": 
            print()
          print(f"  {time.strftime('%I:%M:%S %p')} - Error: Disconnected from BETAAL server", file=sys.stderr)
        exit(0)


if __name__ == "__main__":
  try:
    main()
  except Exception as e:
    print("\nError:", e.args[0], file=sys.stderr)
