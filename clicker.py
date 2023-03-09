from win32gui import FindWindow, GetWindowRect
import pyautogui
import ctypes

def getScreenshot():
    id = FindWindow(None, "Toaa  ")
    x0,y0,x1,y1 = GetWindowRect(id)

    print(pyautogui.size())

    width = x1-x0
    height = y1-y0

    clickposx = x0 + width * 2 /3 
    clickposy = y0 + height * 15 / 16

    print(clickposx, clickposy)
    print(x0,y0,x1,y1,width,height)
    pyautogui.click(clickposx, clickposy, button='left')


ctypes.windll.user32.SetProcessDPIAware()

getScreenshot()


