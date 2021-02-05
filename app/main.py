import json
import logging
import os
import sys
import time
import winreg
from pathlib import Path

from app.managers import taskmanager, mailmanager

STARTUP_REG_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "SkyWatchdog"


def loop(seconds):
    time.sleep(seconds)
    taskmanager.check()
    loop(seconds)


def setup_logger():
    appdata_dir = os.path.join(os.getenv('APPDATA'), 'SkyWatchdog')

    Path(appdata_dir).mkdir(parents=True, exist_ok=True)

    dst = os.path.join(appdata_dir, 'app.log')
    file_handler = logging.FileHandler(dst)
    formatter = logging.Formatter('================================================\n%(asctime)s : %(message)s',
                                  datefmt='%H:%M:%S %m.%d.%Y')

    file_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))
    logger.addHandler(file_handler)

    def handle_exception(exc_type, exc_value, exc_traceback):
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


def main():
    setup_logger()

    exe_path = sys.argv[0]

    with open(os.path.join(Path(exe_path).parent, "config.json"), encoding="utf-8") as config_file:
        config = json.load(config_file)

    # tylko gdy aplikcja jest uruchamiana jako apliakcja standalone
    if exe_path.endswith(".exe"):
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_PATH)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_PATH, 0, winreg.KEY_WRITE)

        if config.get("run-on-startup", False):
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_EXPAND_SZ, "\"%s\"" % exe_path)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except:
                pass

        winreg.CloseKey(key)

    mailmanager.setup(config.get("mail"))
    taskmanager.setup(config.get("tasks"))

    if config.get("notify").get("on-startup"):
        mailmanager.send_system_started_mail()

    loop(config.get("checkPeriod"))

    # thread = threading.Thread(target=loop, args=(config.get("checkPeriod", 1),))
    # thread.start()


if __name__ == '__main__':
    main()
