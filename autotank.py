from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Listener as KeyboardListener
from time import sleep
from threading import Thread
from win32gui import GetWindowText, GetForegroundWindow

ls = KeyboardListener()
kb = KeyboardController()
ms = MouseController()

run = False
pause = False
breaks = [Key.ctrl_l, Key.alt_l, Key.shift_l]


class ScriptController(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()
        with KeyboardListener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def on_press(self, key):
        global breaks, pause
        try:
            if key in breaks:
                pause = True
            if key.char == "t":
                global run
                run = not run
                if run:
                    print("Staring\n")
                else:
                    print("Stoping\n")
            elif key.char == "\\":
                raise SystemExit("Exiting")

        except Exception as e:
            pass

    def on_release(self, key):
        global breaks, pause
        try:
            if key in breaks and not self.test_window():
                pause = False

        except Exception as e:
            pass

    def test_window(self):
        fg_window_name = ""
        try:
            fg_window_name = GetWindowText(GetForegroundWindow()).lower()

        except Exception as e:
            pass
        return fg_window_name != "world of warcraft"

    def run(self):
        global pause
        while True:
            pause = self.test_window()
            sleep(1)


class Keypresser(Thread):
    gcd = 1

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        while True:

            sleep(0.1)
            global run, pause
            if run and not pause:
                kb.press('q')
                kb.release('q')
                kb.press('e')
                kb.release('e')
                ms.scroll(0, 1)
                ms.scroll(0, -1)
                kb.press(Key.tab)
                kb.release(Key.tab)
                sleep(self.gcd)


Keypresser()
ScriptController()
