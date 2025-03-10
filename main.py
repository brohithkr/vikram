#!/usr/bin/env python3

##################### VIKRAM - Defeating BETAAL's trickery #####################

import re
import requests
import sys
import time
from typing import Tuple
import netifaces
from plyer import notification

from netutils import switch_interface

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


def get_local_ip() -> Tuple[(str, requests.Session)]:
  """Determine the local IP address of the device."""  
  session = requests.sessions.session()
  ifaces = netifaces.interfaces()
  for iface in ifaces:
    addr = None
    try:
      addr = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
    except KeyError:
      continue
    switch_interface(session, iface)
    try:
      resp = session.get(BETAAL_URL, timeout=2)
      if (resp.status_code < 400):
        return (addr, session)
    except requests.ConnectionError:
      pass
    except requests.Timeout:
      pass
  raise Exception("Not connected to the test network, Exiting")


def send_heartbeat(status="ON"):
  heartbeat_payload["agentStatus"] = status
  hb_response = session.post(
      BETAAL_URL + "/student/start", json=heartbeat_payload, headers=HEADERS, timeout=2)

  if (status == "ON"):
    print("  Heartbeat sent. Status code:", hb_response.status_code)

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

  print(f"\nSimulating BETAAL for {hall_ticket_no} to server {server_ip}")
  while True:
    try:
      send_heartbeat()
      time.sleep(heartbeat_interval)
    except KeyboardInterrupt:
      print("\033[2K\nStopping BETAAL simulation...")
      send_heartbeat(status="OFF")
      exit(0)
    except Exception as e:
      notification.notify(
          title='Disconnected from BETAAL server',
          message='Try reconnecting to test network',
          app_icon=None,
          timeout=10,
          hints={
              "urgency": 2
          }
      )
      print(f"Error: {e}", file=sys.stderr)
      time.sleep(heartbeat_interval)


if __name__ == "__main__":
  try: 
    main()
  except Exception as e:
    print("\nErr:", e.args[0], file=sys.stderr)
