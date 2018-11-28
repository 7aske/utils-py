from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Button, Listener as MouseListener
from time import sleep
from threading import Thread
from win32gui import GetWindowText, GetForegroundWindow, SetPixel, GetDC
from win32api import RGB, GetSystemMetrics

run = False
pause = False
breaks = [Key.ctrl_l, Key.alt_l, Key.shift_l]
macros = {
    "prot": ['q', 'e', (0, 1), (0, -1), Key.tab],
    "bear": ['q', Key.tab, (0, 1)],
    "ret": ['f', 'e', 'q', Key.tab, (0, -1), (0, 1)]
}


class ScriptController(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        kl = KeyboardListener()
        ml = MouseListener()
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
                    print("\nRun")

                else:
                    print("\nPause")


            elif key.char == "\\":
                print("Exiting")
                raise SystemExit("Exiting")

        except Exception as e:
            pass

    def on_release(self, key):
        global breaks, pause
        try:
            if key in breaks:
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


class KeyPresser(Thread):
    gcd = 1
    kc = KeyboardController()
    mc = MouseController()
    c = RGB(255, 0, 0)
    dc = GetDC(0)
    macro = ""

    def __init__(self, m):
        print(macros[macro])
        self.macro = m
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def indicator(self):
        width = int(GetSystemMetrics(0) / 2)
        for i in range(width - 12, width + 12):
            for j in range(24):
                SetPixel(self.dc, i, j, self.c)

    def run(self):
        while True:
            global run, pause

            if run:
                self.indicator()

                if not pause:
                    for macro in macros:
                        if isinstance(macro, tuple):
                            print(macro[0], macro[1])
                            self.mc.scroll(macro[0], macro[1])

                        else:
                            self.kc.press(macro)
                            self.kc.release(macro)

                        sleep(0.1)
                sleep(self.gcd)


if __name__ == "__main__":
    macro = input(f"Spec {[key for key in macros.keys()]}: ")
    try:
        index = int(macro) - 1
        macro = list(macros.keys())[index]
        KeyPresser(macro)
    except ValueError:
        KeyPresser(macro)
    ScriptController()
