import json
import random
import socket
from collections.abc import Sequence
from typing import Union, Final

JsonTypes = Union[str, int, float, bool, None]

UTF_8: Final[str] = "utf-8"
BIN_EOL: Final[bytes] = b'\n'


class MpvJsonIpcReplyError(Exception):
    pass


def build_json_ipc_command(command_name: str, *command_args: JsonTypes, request_id: int = None) -> str:
    # JSON message form - "{"command":["command_name","param1","param2",...],"request_id":"number"}\n"
    json_message = {"command": [command_name, *command_args]}
    if request_id:
        json_message["request_id"] = request_id
    return f"{json.dumps(json_message, separators=(',', ':'))}\n"


def parse_json_ipc_reply(bin_messages: Sequence[bytes], request_id: int) -> JsonTypes:
    bin_strings = list(filter(None, bin_messages))
    strings = list(map(lambda b: b.decode(UTF_8), bin_strings))
    cmd_replies = list(filter(lambda s: "request_id" in s, strings))

    for reply in cmd_replies:
        message: dict = json.loads(reply)
        if message["request_id"] == request_id:
            if message["error"] != "success":
                raise MpvJsonIpcReplyError(message["error"])
            return message["data"]


class Mpv:
    def __init__(self, ipc_file_path: str) -> None:
        self._ipc_file_path = ipc_file_path
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(self._ipc_file_path)
        self._socket.settimeout(0.01)

    def pause(self) -> None:
        self._set_property("pause", True)

    def resume(self) -> None:
        self._set_property("pause", False)

    def is_paused(self) -> bool:
        return self._get_property("pause")

    def is_in_fullscreen(self) -> bool:
        return self._get_property("fullscreen")

    def show_message(self, text: str, timeout: int = 3000) -> None:
        cmd = build_json_ipc_command("show-text", text, timeout)
        self._send_command(cmd)

    def _set_property(self, property_name: str, value: bool) -> None:
        cmd = build_json_ipc_command("set_property", property_name, value)
        self._send_command(cmd)

    def _get_property(self, property_name: str) -> JsonTypes:
        id_ = random.randint(-2 ** 63, 2 ** 63 - 1)
        cmd = build_json_ipc_command("get_property", property_name, request_id=id_)
        self._send_command(cmd)
        return self._get_command_response(id_)

    def _send_command(self, json_ipc: str) -> None:
        self._socket.sendall(bytes(json_ipc, encoding=UTF_8))

    def _get_command_response(self, request_id: int) -> JsonTypes:
        return parse_json_ipc_reply(self._get_raw_data_from_socket(), request_id)

    def _get_raw_data_from_socket(self) -> list[bytes]:
        buffer = b''
        raw_messages = []
        try:
            while True:
                chunk = self._socket.recv(1024)
                if not chunk:
                    break

                buffer += chunk
                if BIN_EOL in buffer:
                    for line in buffer.split(BIN_EOL):
                        raw_messages.append(line)
                    buffer = b''
        except TimeoutError:
            # Use TimeOut exception as an end of a socket reply.
            pass

        return raw_messages
