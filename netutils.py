import platform
import ifaddr
import socket
from requests.adapters import HTTPAdapter

TIMEOUT = 2
ADAPTERS = ifaddr.get_adapters()


class InterfaceBindingAdapter(HTTPAdapter):
  def __init__(self, interface, timeout, *args, **kwargs):
    self.interface = interface
    self.source_ip = get_ip_for_interface(interface)
    self.timeout = timeout
    super().__init__(*args, **kwargs)

  def init_poolmanager(self, *args, **kwargs):
    kwargs["source_address"] = (self.source_ip, 0)
    if platform.system() == "Linux":
      kwargs["socket_options"] = [
        (socket.SOL_SOCKET, socket.SO_BINDTODEVICE, self.interface.encode())
      ]
    super().init_poolmanager(*args, **kwargs)


# Function to get IP address for a given interface
def get_ip_for_interface(interface_name) -> ifaddr._shared._IPv4Address | None:
  for adapter in ifaddr.get_adapters():
    if adapter.name == interface_name or adapter.nice_name == interface_name:
      for ip in adapter.ips:
        if ip.is_IPv4:
          return ip.ip
  return None


# Function to switch network interface
def switch_interface(session, new_interface):
  source_ip = get_ip_for_interface(new_interface)
  if not source_ip:
    raise ValueError(f"Could not find an IP for interface: {new_interface}")

  try:
    # Check if adapters exist before removing
    if "http://" in session.adapters:
      session.adapters.pop("http://")
    if "https://" in session.adapters:
      session.adapters.pop("https://")
  except KeyError:
    pass  # Ignore errors if the adapter is already missing

  # Create a new adapter with the new interface
  new_adapter = InterfaceBindingAdapter(new_interface, TIMEOUT)

  # Mount the new adapter
  session.mount("http://", new_adapter)
  session.mount("https://", new_adapter)
