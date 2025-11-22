import sys, os, tty, termios, traceback
from typing import Callable


class History:
    def __init__(self, circular: bool = True):
        self.circular: bool = circular
        self._index: int = 0
        self._buffer: list[str] = []

    def _get(self) -> str:
        if self._index < len(self._buffer) and self._index >= 0:
            return self._buffer[self._index]
        else:
            return ""

    def next(self) -> str:
        if self.circular and self._index == len(self._buffer):
            self._index = 0
        elif self._index < len(self._buffer):
            self._index += 1;
        return self._get()

    def prev(self) -> str:
        if self.circular and self._index == 0:
            self._index = len(self._buffer)
        elif self._index > 0:
            self._index -= 1
        return self._get()

    def push(self, string: str) -> None:
        if string and (not self._buffer or self._buffer[-1] != string):
            self._buffer.append(string)
            self._index = len(self._buffer)


def _write(msg: str, nl: bool = False, flush: bool = False) -> None:
    """ Wrap sys.stdout.write to avoid reportUnusedCallResult """
    _ = sys.stdout.write(msg)
    if nl:
        _ = sys.stdout.write('\n')
    if flush:
        _flush()


def _flush() -> None:
    """ Wrap sys.stdout.flush to avoid reportUnusedCallResult """
    _ = sys.stdout.flush()


def _clear_buf(l: int) -> None:
    _write('\r')
    _write(' ' * l)
    _write('\r')


def _get_unix_key() -> int:
    k = os.read(sys.stdin.fileno(), 3).decode()
    match len(k):
        case 3:
            k = ord(k[-1])
            return -k if k == 65 or k == 66 else k
        case 1:
            return ord(k)
        case _:
            return ord(k[-1])


class Shell:

    def __init__(self, prompt: str = "> ", history: History | None = None):
        self.prompt: str = prompt
        self.history: History = History(circular=False) if history is None else history
        self.cmds: dict[str, Callable[[list[str]], int]] = {}

    def _exec(self, cmdstr: str) -> None:
        """ cmd fields: cmd_name args """
        acmd = cmdstr.split()
        cmd_name = acmd[0]
        try:
            cmd = self.cmds[cmd_name]
        except KeyError:
            _write(f'{cmd_name}: command not found', nl=True)
        else:
            try:
                _ = cmd(acmd[1:])
            except Exception as e:
                _write(traceback.format_exc(), nl=True)

    def start(self) -> None:
        fd = sys.stdin.fileno()
        old_tty_attrs = tty.setcbreak(fd, termios.TCSANOW)
        try:
            _write(self.prompt)
            _flush()
            buf = ''
            while True:
                key = _get_unix_key()
                match key:
                    case -65: # up
                        pbuf = self.history.prev()
                        if not pbuf and not buf:
                            continue
                        _clear_buf(len(buf) + len(self.prompt))
                        buf = pbuf
                        _write(self.prompt)
                        _write(buf)
                    case -66: # down
                        nbuf = self.history.next()
                        if not pbuf and not buf:
                            continue
                        _clear_buf(len(buf) + len(self.prompt))
                        buf = nbuf
                        _write(self.prompt)
                        _write(buf)
                    case 9: # tab
                        _write("tab")
                    case 10: # ret
                        _write('\n')
                        if buf:
                            self.history.push(buf)
                            self._exec(buf)
                            buf = ''
                        _write(self.prompt)
                    case 67 | 68: # ignore left/right arrow keys
                        pass
                    case 127: # del
                        if buf:
                            _clear_buf(len(buf) + len(self.prompt))
                            _write(self.prompt)
                            buf = buf[:-1]
                            _write(buf)
                    case _:
                        c = chr(key)
                        buf = buf + chr(key)
                        _write(c)
                _flush()
        finally:
            termios.tcsetattr(fd, termios.TCSANOW, old_tty_attrs)
