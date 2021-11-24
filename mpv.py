import os
import subprocess
from json import loads, dumps
from typing import Union


class MpvJsonIpcReplyError(Exception):
    pass


def _build_json_ipc(command_name: str, *values: Union[str, int, bool]) -> str:
    # resulting JSON IPC should look like this: { "command": ["command_name", "param1", "param2", ...] }
    cmd_list = [command_name]
    for v in values:
        cmd_list.append(v)
    return dumps({"command": cmd_list})


def _parse_json_ipc_reply(output: str) -> Union[str, int, bool]:
    reply = loads(output)
    if reply['error'] != "success":
        raise MpvJsonIpcReplyError(reply['error'])
    return reply['data']


class Mpv:
    def __init__(self, mpv_socket_file: str):
        self._socket_file = mpv_socket_file

    def pause(self) -> None:
        self._set_property("pause", True)

    def resume(self) -> None:
        self._set_property("pause", False)

    def is_paused(self) -> bool:
        return _parse_json_ipc_reply(self._get_property("pause"))

    def is_in_fullscreen(self) -> bool:
        return _parse_json_ipc_reply(self._get_property("fullscreen"))

    def show_message(self, text: str, timeout: int = 3000) -> None:
        json_ipc = _build_json_ipc("show-text", text, timeout)
        os.system(self._construct_shell_command_with_silenced_stdout(json_ipc))

    def _set_property(self, property_name: str, value: bool) -> None:
        json_ipc = _build_json_ipc("set_property", property_name, value)
        os.system(self._construct_shell_command_with_silenced_stdout(json_ipc))

    def _get_property(self, property_name: str) -> str:
        json_ipc = _build_json_ipc("get_property", property_name)
        return subprocess.getoutput(self._construct_shell_command(json_ipc))

    def _construct_shell_command_with_silenced_stdout(self, json_ipc: str) -> str:
        return f"{self._construct_shell_command(json_ipc)} > /dev/null"

    def _construct_shell_command(self, json_ipc: str) -> str:
        return f'echo \'{json_ipc}\' | socat - "{self._socket_file}"'
