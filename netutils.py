import socket
from requests.adapters import HTTPAdapter

TIMEOUT = 2


class InterfaceBindingAdapter(HTTPAdapter):
  def __init__(self, interface, timeout, *args, **kwargs):
    self.interface = interface
    self.timeout = timeout
    super().__init__(*args, **kwargs)

  def init_poolmanager(self, *args, **kwargs):
    kwargs['socket_options'] = [
        (socket.SOL_SOCKET, socket.SO_BINDTODEVICE, self.interface.encode())
    ]
    super().init_poolmanager(*args, **kwargs)

# Function to switch network interface


def switch_interface(session, new_interface):
  try:
    # Check if adapters exist before removing
    if 'http://' in session.adapters:
      session.adapters.pop('http://')
    if 'https://' in session.adapters:
      session.adapters.pop('https://')
  except KeyError:
    pass  # Ignore errors if the adapter is already missing

  # Create a new adapter with the new interface
  new_adapter = InterfaceBindingAdapter(new_interface, TIMEOUT)

  # Mount the new adapter
  session.mount('http://', new_adapter)
  session.mount('https://', new_adapter)
