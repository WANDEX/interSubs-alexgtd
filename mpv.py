import os
import subprocess
from json import loads


class Mpv:
    def __init__(self, mpv_socket_path: str):
        self.socket_path = mpv_socket_path

    def pause(self):
        os.system(
            'echo \'{ "command": ["set_property", "pause", true] }\' | socat - "' + self.socket_path + '" > /dev/null')

    def resume(self):
        os.system(
            'echo \'{ "command": ["set_property", "pause", false] }\' | socat - "' + self.socket_path + '" > /dev/null')

    def is_paused(self):
        stdout = subprocess.getoutput(
            'echo \'{ "command": ["get_property", "pause"] }\' | socat - "' + self.socket_path + '"')
        try:
            return loads(stdout)['data']
        except:
            return self.is_paused()

    def is_in_fullscreen(self):
        stdout = subprocess.getoutput(
            'echo \'{ "command": ["get_property", "fullscreen"] }\' | socat - "' + self.socket_path + '"')
        try:
            return loads(stdout)['data']
        except:
            return self.is_in_fullscreen()

    def show_text(self, message, timeout=3000):
        os.system('echo \'{ "command": ["show-text", "' + message + '", "' + str(
            timeout) + '"] }\' | socat - "' + self.socket_path + '" > /dev/null')
