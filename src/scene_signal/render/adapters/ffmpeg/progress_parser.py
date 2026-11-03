from typing import Callable, Any

class FFmpegProgressParser:
    @staticmethod
    def parse_stream(stdout_stream: Any, callback: Callable[[dict[str, str]], None]) -> None:
        current_block: dict[str, str] = {}
        for line in stdout_stream:
            line = line.strip()
            if not line:
                if current_block:
                    callback(current_block)
                    current_block = {}
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                current_block[key.strip()] = val.strip()
        if current_block:
            callback(current_block)
