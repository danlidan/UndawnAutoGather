from PIL import ImageGrab
import cv2
import numpy as np
from win32gui import FindWindow, GetWindowRect
import ctypes
import time

MAKE_INPUT = True

ctypes.windll.user32.SetProcessDPIAware()
while True:
    window_name = "Toaa  "
    id = FindWindow(None, window_name)
    rect = GetWindowRect(id)

    screenshot = ImageGrab.grab(bbox=rect, all_screens=True)

    if MAKE_INPUT:
        screenshot.save("input/%s.jpg" % int(time.time()))
    else:
        screenshot_array = np.array(screenshot)
        screenshot_array = cv2.cvtColor(screenshot_array, cv2.COLOR_BGR2RGB)
        cv2.imshow('screenshot', screenshot_array)
    if cv2.waitKey(25) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break