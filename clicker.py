from win32gui import FindWindow, GetWindowRect
import pyautogui
import ctypes
import keyboard
import time

def getScreenshot():
    id = FindWindow(None, "Toaa  ")
    x0,y0,x1,y1 = GetWindowRect(id)
    width = x1-x0
    height = y1-y0


    keyboard.press_and_release("f2")
    time.sleep(0.5)
    clickposx = x0 + width * 7 / 8 
    clickposy = y0 + height / 2 
    pyautogui.click(clickposx, clickposy, button='left')
    time.sleep(0.5)
    clickposx = x0 + width * 7 / 8 
    clickposy = y0 + height * 15 / 16
    pyautogui.click(clickposx, clickposy, button='left')
    time.sleep(9)
    clickposx = x0 + width * 31 / 32 
    clickposy = y0 + height / 16
    pyautogui.click(clickposx, clickposy, button='left')


ctypes.windll.user32.SetProcessDPIAware()

getScreenshot()


