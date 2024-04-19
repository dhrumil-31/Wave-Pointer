# Imports

import time
from types import NoneType
import mediapipe as mp
import pyautogui
# from gesture_encodings import Gest
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
import screen_brightness_control as sbcontrol
import json
import os


class Controller:
    tx_old = 0
    ty_old = 0
    trial = True
    flag = False
    grabflag = False
    vol_bright_flag = False
    scroll_flag = False
    pinchstartxcoord = None
    pinchstartycoord = None
    pinchdirectionflag = None
    prevpinchlv = 0
    pinchlv = 0
    framecount = 0
    prev_hand = None
    pinch_threshold = 0.3
    config_data = None
    directory = "WavePointer"
    fileName = "config.wptr"
    performed_func = None

    def getConfigData():
        documentsPath = os.path.expanduser('~/Documents')
        dirPath = os.path.join(documentsPath, Controller.directory)
        if(os.path.isdir(dirPath) == False):
            os.mkdir(dirPath)
        docPath = os.path.join(dirPath, Controller.fileName)
        if(os.path.isfile(docPath) == False):
            f = open(docPath, "w")
            f2 = open('config.json', 'r')
            Controller.config_data = json.load(f2)
            json_object = json.dumps(Controller.config_data, indent=4)
            f.write(json_object)
            f.close()
            f2.close()
        else:
            f = open(docPath, 'r')
            Controller.config_data = json.load(f)
            f.close()

    def getpinchylv(hand_result):
        dist = round((Controller.pinchstartycoord -
                     hand_result.landmark[8].y)*10, 1)
        return dist

    def getpinchxlv(hand_result):
        dist = round(
            (hand_result.landmark[8].x - Controller.pinchstartxcoord)*10, 1)
        return dist

    def changesystembrightness():
        currentBrightnessLv = sbcontrol.get_brightness()/100.0
        currentBrightnessLv += Controller.pinchlv/50.0
        if currentBrightnessLv > 1.0:
            currentBrightnessLv = 1.0
        elif currentBrightnessLv < 0.0:
            currentBrightnessLv = 0.0
        sbcontrol.fade_brightness(
            int(100*currentBrightnessLv), start=sbcontrol.get_brightness())

    def changesystemvolume():
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        currentVolumeLv = volume.GetMasterVolumeLevelScalar()
        currentVolumeLv += Controller.pinchlv/50.0
        if currentVolumeLv > 1.0:
            currentVolumeLv = 1.0
        elif currentVolumeLv < 0.0:
            currentVolumeLv = 0.0
        volume.SetMasterVolumeLevelScalar(currentVolumeLv, None)

    def scrollVertical():
        pyautogui.scroll(120 if Controller.pinchlv > 0.0 else -120)

    def scrollHorizontal():
        pyautogui.keyDown('shift')
        pyautogui.keyDown('ctrl')
        pyautogui.scroll(-120 if Controller.pinchlv > 0.0 else 120)
        pyautogui.keyUp('ctrl')
        pyautogui.keyUp('shift')

    def convertToString(string):
        return list(string.split(","))

    def keyUp(keyDownList):
        if len(keyDownList) > 1:
            keyDownList.reverse()
            for x in keyDownList:
                print(x)
                pyautogui.keyUp(x)
                time.sleep(0.1)
        else:
            print("in else")
            for x in keyDownList:
                print(x)
                pyautogui.keyUp(x)
                time.sleep(0.1)

    def performMacro(macro, keyMaps):
        keyDownList = []
        inList = Controller.convertToString(macro)
        for i in range(len(inList)):
            if  inList[i] == "pressedNext":
                continue
            elif inList[i] == "newNext":
                Controller.keyUp(keyDownList)
                keyDownList.clear()
                continue
            else:
                print(keyMaps[inList[i]])
                pyautogui.keyDown(keyMaps[inList[i]])
                keyDownList.append(keyMaps[inList[i]])
                time.sleep(0.1)
                
        if len(keyDownList) != 0:
            Controller.keyUp(keyDownList)
            keyDownList.clear()
            
    def get_position(hand_result):
        point = 10
        position = [hand_result.landmark[point].x,
                    hand_result.landmark[point].y]
        sx, sy = pyautogui.size()
        x_old, y_old = pyautogui.position()
        x = int(position[0]*sx)
        y = int(position[1]*sy)
        if Controller.prev_hand is None:
            Controller.prev_hand = x, y
        delta_x = x - Controller.prev_hand[0]
        delta_y = y - Controller.prev_hand[1]

        distsq = delta_x**2 + delta_y**2
        ratio = 1
        Controller.prev_hand = [x, y]

        if distsq <= 25:
            ratio = 0
        elif distsq <= 900:
            ratio = 0.07 * (distsq ** (1/2))
        else:
            ratio = 2.1
        x, y = x_old + delta_x*ratio, y_old + delta_y*ratio
        return (x, y)

    def pinch_control_init(hand_result):
        Controller.pinchstartxcoord = hand_result.landmark[8].x
        Controller.pinchstartycoord = hand_result.landmark[8].y
        Controller.pinchlv = 0
        Controller.prevpinchlv = 0
        Controller.framecount = 0

    # Hold final position for 5 frames to change status
    def pinch_control(hand_result, controlHorizontal, controlVertical, label, scrolling, changeBg, f, changeLabel):
        if Controller.framecount == 1:
            Controller.framecount = 0
            Controller.pinchlv = Controller.prevpinchlv
            if Controller.pinchdirectionflag == True:
                if scrolling:
                    changeLabel(label, "Horizontal Scroll", '#dde6d5')
                    changeBg(f, '#dde6d5')
                else:
                    changeLabel(label, "Brightness", '#dde6d5')
                    changeBg(f, '#dde6d5')
                controlHorizontal()  # x

            elif Controller.pinchdirectionflag == False:
                if scrolling:
                    changeLabel(label, "Vertical Scroll", '#dde6d5')
                    changeBg(f, '#dde6d5')
                else:
                    changeLabel(label, "Volume", '#dde6d5')
                    changeBg(f, '#dde6d5')
                controlVertical()  # y

        lvx = Controller.getpinchxlv(hand_result)
        lvy = Controller.getpinchylv(hand_result)

        if abs(lvy) > abs(lvx) and abs(lvy) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = False
            if abs(Controller.prevpinchlv - lvy) < Controller.pinch_threshold:
                Controller.framecount += 1
            else:
                Controller.prevpinchlv = lvy
                Controller.framecount = 0

        elif abs(lvx) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = True
            if abs(Controller.prevpinchlv - lvx) < Controller.pinch_threshold:
                Controller.framecount += 1
            else:
                Controller.prevpinchlv = lvx
                Controller.framecount = 0

    def handle_controls(gesture, hand_result, label, f, changeBg, closeFunc, changeLabel):
        gest_function_map = Controller.config_data["gest_functions"]
        keyMaps = Controller.config_data["key_mapping"]
        x, y = None, None

        print(gesture)

        if gesture in gest_function_map:
            gest_to_perform = gest_function_map[gesture]

            if gest_to_perform['func'] != 'func_neutral':
                if hand_result is not NoneType and hand_result is not None:
                    x, y = Controller.get_position(hand_result)

            if gest_to_perform['func'] != 'func_selection' and Controller.grabflag:
                Controller.grabflag = False
                changeLabel(label, gest_to_perform['func_name'], '#dde6d5')
                changeBg(f, '#dde6d5')
                pyautogui.mouseUp(button="left")
                Controller.performed_func = gest_to_perform['func']

            if gest_to_perform['func'] != 'func_vol_brightness_mode' and Controller.vol_bright_flag == True:
                Controller.vol_bright_flag = False
                Controller.performed_func = gest_to_perform['func']

            if gest_to_perform['func'] != 'func_scroll_mode' and Controller.scroll_flag == True:
                Controller.scroll_flag = False
                Controller.performed_func = gest_to_perform['func']

            if gest_to_perform['func'] == 'func_neutral':
                changeLabel(label, gest_to_perform['func_name'], '#C4B9E0')
                changeBg(f, '#C4B9E0')
                Controller.performed_func = gest_to_perform['func']

            elif gest_to_perform['func'] == 'func_close':
                closeFunc()

            elif gest_to_perform['func'] == 'func_move_mouse':
                changeLabel(label, gest_to_perform['func_name'], '#dde6d5')
                changeBg(f, '#dde6d5')
                Controller.flag = True
                Controller.performed_func = gest_to_perform['func']
                pyautogui.moveTo(x, y, duration=0.0)

            elif gest_to_perform['func'] == 'func_selection':
                if not Controller.grabflag:
                    changeLabel(label, gest_to_perform['func_name'], '#dde6d5')
                    changeBg(f, '#dde6d5')
                    Controller.grabflag = True
                    pyautogui.mouseDown(button="left")
                pyautogui.moveTo(x, y, duration=0.0)
                Controller.performed_func = gest_to_perform['func']

            elif gest_to_perform['func'] == 'func_left_click' and Controller.performed_func != gest_to_perform['func']:
                changeLabel(label, gest_to_perform['func_name'], '#dde6d5')
                changeBg(f, '#dde6d5')
                pyautogui.click()
                Controller.flag = False
                Controller.performed_func = gest_to_perform['func']

            elif gest_to_perform['func'] == 'func_right_click' and Controller.performed_func != gest_to_perform['func']:
                changeLabel(label, gest_to_perform['func_name'], '#dde6d5')
                changeBg(f, '#dde6d5')
                pyautogui.click(button='right')
                Controller.flag = False
                Controller.performed_func = gest_to_perform['func']

            elif gest_to_perform['func'] == 'func_double_click' and Controller.performed_func != gest_to_perform['func']:
                changeLabel(label, gest_to_perform['func_name'], '#dde6d5')
                changeBg(f, '#dde6d5')
                pyautogui.doubleClick()
                Controller.flag = False
                Controller.performed_func = gest_to_perform['func']

            elif gest_to_perform['func'] == 'func_scroll_mode':
                changeLabel(label, gest_to_perform['func_name'], '#dde6d5')
                changeBg(f, '#dde6d5')
                Controller.performed_func = gest_to_perform['func']
                if Controller.scroll_flag == False:
                    Controller.scroll_flag = True
                    Controller.pinch_control_init(hand_result)
                Controller.pinch_control(
                    hand_result, Controller.scrollHorizontal, Controller.scrollVertical, label, True, changeBg, f, changeLabel)

            elif gest_to_perform['func'] == 'func_vol_brightness_mode':
                changeLabel(label, gest_to_perform['func_name'], '#dde6d5')
                Controller.performed_func = gest_to_perform['func']
                changeBg(f, '#dde6d5')
                if Controller.vol_bright_flag == False:
                    Controller.vol_bright_flag = True
                    Controller.pinch_control_init(hand_result)
                Controller.pinch_control(hand_result, Controller.changesystembrightness,
                                         Controller.changesystemvolume, label, False, changeBg, f, changeLabel)

            else:
                if gest_to_perform['func'] == 'null' and gest_to_perform['custom'] == False:
                    print("in not assigned")
                    Controller.performed_func = gest_to_perform['func']
                    changeLabel(label, gest_to_perform['func_name'], '#C4B9E0')
                    changeBg(f, '#C4B9E0')
                else:
                    if gest_to_perform['custom'] == True and Controller.performed_func != gest_to_perform['func']:
                        changeLabel(
                            label, gest_to_perform['func_name'], '#C4B9E0')
                        changeBg(f, '#C4B9E0')
                        Controller.performed_func = gest_to_perform['func']
                        Controller.performMacro(
                            gest_to_perform['func'], keyMaps)

        else:
            print("in not assigned else")
            Controller.performed_func = 'null'
            changeLabel(label, '--Not assigned--', '#C4B9E0')
            changeBg(f, '#C4B9E0')
            # elif gest_to_perform['func'] == 'null':

        # if gesture == gest_map['last_two_fingers']:
        #     closeFunc()

        # if gesture ==gest_map['palm'] or gesture == gest_map['last4']:
        #     label.configure(text="Neutral mode", bg='#C4B9E0')
        #     changeBg(f,'#C4B9E0')
        # else:
        #     x,y = Controller.get_position(hand_result)

        # # Selection End
        # if gesture != Gest.FIST and Controller.grabflag:
        #     Controller.grabflag = False
        #     label.configure(text="Selection end", bg='#dde6d5')
        #     changeBg(f,'#dde6d5')
        #     pyautogui.mouseUp(button = "left")

        # if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag:
        #     Controller.pinchmajorflag = False

        # if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag:
        #     Controller.pinchminorflag = False

        # # Mouse Cursor Move
        # if gesture == Gest.V_GEST:
        #     label.configure(text="Mouse Cursor move", bg='#dde6d5')
        #     changeBg(f,'#dde6d5')
        #     Controller.flag = True
        #     pyautogui.moveTo(x, y, duration = 0.0)

        # elif gesture == Gest.FIST:
        #     if not Controller.grabflag :
        #         label.configure(text="Selection mode", bg='#dde6d5')
        #         changeBg(f,'#dde6d5')
        #         Controller.grabflag = True
        #         pyautogui.mouseDown(button = "left") # mousedown is mouseclick
        #     pyautogui.moveTo(x, y, duration = 0.0)

        # elif gesture == Gest.MID and Controller.flag:
        #     label.configure(text="Left Click", bg='#dde6d5')
        #     pyautogui.click()
        #     Controller.flag = False

        # elif gesture == Gest.INDEX and Controller.flag:
        #     label.configure(text="Right Click", bg='#dde6d5')
        #     changeBg(f,'#dde6d5')
        #     pyautogui.click(button='right')
        #     Controller.flag = False

        # elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:

        #     label.configure(text="Double Click", bg='#dde6d5')
        #     changeBg(f,'#dde6d5')
        #     pyautogui.doubleClick()
        #     Controller.flag = False

        # elif gesture == Gest.PINCH_MINOR:
        #     if Controller.pinchminorflag == False:
        #         label.configure(text="Scrolling mode", bg='#dde6d5')
        #         changeBg(f,'#dde6d5')
        #         Controller.pinch_control_init(hand_result)
        #         Controller.pinchminorflag = True
        #     Controller.pinch_control(hand_result,Controller.scrollHorizontal, Controller.scrollVertical,label,True, changeBg,f)

        # elif gesture == Gest.PINCH_MAJOR:
        #     label.configure(text="Volume/Brightness control mode", bg='#dde6d5')
        #     changeBg(f,'#dde6d5')
        #     if Controller.pinchmajorflag == False:
        #         Controller.pinch_control_init(hand_result)
        #         Controller.pinchmajorflag = True
        #     Controller.pinch_control(hand_result,Controller.changesystembrightness, Controller.changesystemvolume, label,False, changeBg,f)
