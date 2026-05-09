import subprocess
import sys

from electric_meter.config import BOKEH_APP_PATH, PROJECT_ROOT


def main() -> int:
    return subprocess.call(
        [
            "bokeh",
            "serve",
            "--show",
            str(BOKEH_APP_PATH),
            "--allow-websocket-origin=192.168.1.170:5006",
            *sys.argv[1:],
        ],
        cwd=PROJECT_ROOT,
    )


if __name__ == "__main__":
    sys.exit(main())
