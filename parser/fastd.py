import socket
import json

class FastdParser:
    """ parser for fastd status sockets """

    def __init__(self, basepath = "/var/run/fastd/"):
        self.basepath = basepath

    def _file_status(self, filename):
        with open(filename, 'r') as file:
            return self._parse_status(file)

    def _parse_status(self, data):
        return json.load(data)

    def status(self, socketname):
        filename = self.basepath + "/" + socketname
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(filename)
            file = sock.makefile()
            return self._parse_status(file)

    def peer_for_mac(self, status, mac):
        match = [ (id,peer) for (id,peer) in status["peers"].items() if peer and peer["connection"] and peer["connection"]["mac_addresses"] and mac in peer["connection"]["mac_addresses"]]
        return match

