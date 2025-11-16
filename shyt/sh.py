import sys, os, tty, termios
from typing import List, Optional


class History:
    def __init__(self, circular: bool = True):
        self.circular = circular
        self._index = 0
        self._buffer: List[str] = []

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


class Shell:
    def __init__(self, prompt: str = "> ", history: Optional[History] = None):
        self.prompt = prompt
        self.history = History() if history is None else history

    def _exec(self, cmd: str) -> None:
        sys.stdout.write(f'     Execute {cmd}\n')
        sys.stdout.flush()

    @staticmethod
    def _clear_buf(l: int) -> None:
        sys.stdout.write('\r')
        sys.stdout.write(' ' * l)
        sys.stdout.write('\r')

    @staticmethod
    def _get_key() -> int:
        k = os.read(sys.stdin.fileno(), 3).decode()
        match len(k):
            case 3:
                k = ord(k[-1])
                return -k if k == 65 or k == 66 else k
            case 1:
                return ord(k)
            case _:
                return ord(k[-1])

    def start(self) -> None:
        fd = sys.stdin.fileno()
        old_tty_attrs = tty.setcbreak(fd, termios.TCSANOW)
        try:
            while True:
                sys.stdout.write(self.prompt)
                sys.stdout.flush()
                buf = ''
                while True:
                    key = self._get_key()
                    match key:
                        case -65: # up
                            pbuf = self.history.prev()
                            if pbuf is not None:
                                self._clear_buf(len(buf) + len(self.prompt))
                                buf = pbuf
                                sys.stdout.write(self.prompt)
                                sys.stdout.write(buf)
                        case -66: # down
                            nbuf = self.history.next()
                            if nbuf is not None:
                                self._clear_buf(len(buf) + len(self.prompt))
                                buf = nbuf
                                sys.stdout.write(self.prompt)
                                sys.stdout.write(buf)
                        case 9: # tab
                            sys.stdout.write("tab")
                        case 10: # ret
                            sys.stdout.write('\n')
                            if buf:
                                self.history.push(buf)
                                self._exec(buf)
                                buf = ''
                            sys.stdout.write(self.prompt)
                        case 67 | 68: # ignore left/right arrow keys
                            pass
                        case 127: # del
                            if buf:
                                self._clear_buf(len(buf) + len(self.prompt))
                                sys.stdout.write(self.prompt)
                                buf = buf[:-1]
                                sys.stdout.write(buf)
                        case _:
                            c = chr(key)
                            buf = buf + chr(key)
                            sys.stdout.write(c)
                    sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSANOW, old_tty_attrs)
