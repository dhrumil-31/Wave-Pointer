# Imports
import cv2
import mediapipe as mp
import pyautogui
from multi_hand_label import HLabel
from hand_recognition import HandRecog
from controller import Controller
from google.protobuf.json_format import MessageToDict
import tkinter as tk
pyautogui.FAILSAFE = False
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


class WavePointer():
    gc_mode = 0
    cap = None
    CAM_HEIGHT = None
    app = None
    w = None
    CAM_WIDTH = None
    hr_major = None  # Right Hand by default
    hr_minor = None  # Left hand by default
    dom_hand = True
    flag_hands_recognised = False

    def __init__(self):
        WavePointer.gc_mode = 1
        WavePointer.cap = cv2.VideoCapture(0)
        # WavePointer.CAM_HEIGHT = WavePointer.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        # WavePointer.CAM_WIDTH = WavePointer.cap.get(cv2.CAP_PROP_FRAME_WIDTH)

    def classify_hands(results):
        left, right = None, None
        try:
            handedness_dict = MessageToDict(results.multi_handedness[0])
            if handedness_dict['classification'][0]['label'] == 'Right':
                right = results.multi_hand_landmarks[0]
            else:
                left = results.multi_hand_landmarks[0]
        except:
            pass

        try:
            handedness_dict = MessageToDict(results.multi_handedness[1])
            if handedness_dict['classification'][0]['label'] == 'Right':
                right = results.multi_hand_landmarks[1]
            else:
                left = results.multi_hand_landmarks[1]
        except:
            pass

        if WavePointer.dom_hand == True:
            WavePointer.hr_major = right
            WavePointer.hr_minor = left
        else:
            WavePointer.hr_major = left
            WavePointer.hr_minor = right

    def changeBg(f, color):
        f.configure(background=color)
    
    def changeLabel(label,text, color='#dde6d5', fg="black"):
        label.configure(text=text, bg=color,fg="black")

    def start(self, root):

        def quit_wavepointer():
            WavePointer.cap.release()
            root.destroy()

        Controller.getConfigData()

        handmajor = HandRecog(HLabel.MAJOR)
        handminor = HandRecog(HLabel.MINOR)

        f = tk.Frame(root, bg="#ffffba", width=500, height=120)
        f.grid(row=0, column=0, sticky="NW")
        f.grid_propagate(0)
        f.update()
        root.protocol('WM_DELETE_WINDOW', quit_wavepointer)
        label = tk.Label(f, text="Loading Config...", font=(
            "Helvetica", 18), background='#ffffba', foreground="black")
        label.place(relx=.5, rely=.5, anchor="center")

        with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8, min_tracking_confidence=0.8) as hands:
            while WavePointer.cap.isOpened() and WavePointer.gc_mode:
                success, image = WavePointer.cap.read()

                if not success:
                    print("Ignoring empty camera frame.")
                    continue

                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)

                # image.flags.writeable = True
                # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if results.multi_hand_landmarks:
                    if(WavePointer.flag_hands_recognised is False):
                        WavePointer.flag_hands_recognised = True
                        WavePointer.changeLabel(label,"Hands Detected",'#C4B9E0')
                        WavePointer.changeBg(f, color='#C4B9E0')
                    WavePointer.classify_hands(results)
                    handmajor.update_hand_result(WavePointer.hr_major)
                    handminor.update_hand_result(WavePointer.hr_minor)

                    handmajor.set_finger_state()
                    handminor.set_finger_state()
                    gest = handminor.get_gesture()

                    if gest == 36:
                        Controller.handle_controls(
                            str(gest), handminor.hand_result, label, f, WavePointer.changeBg, quit_wavepointer, WavePointer.changeLabel)
                    else:
                        gest = handmajor.get_gesture()
                        Controller.handle_controls(
                            str(gest), handmajor.hand_result, label, f, WavePointer.changeBg, quit_wavepointer,WavePointer.changeLabel)

                    # for hand_landmarks in results.multi_hand_landmarks:
                    #     mp_drawing.draw_landmarks(
                    #         image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                else:
                    WavePointer.flag_hands_recognised = False
                    WavePointer.changeBg(f, color='#D96D78')
                    WavePointer.changeLabel(label,"No hands detected",'#D96D78')
                    # Window.changeBg(color='red')
                    Controller.prev_hand = None
                # cv2.imshow('WavePointer', image)
                # if cv2.waitKey(5) & 0xFF == 13:
                #     break
        WavePointer.cap.release()
        cv2.destroyAllWindows()

# Start directly
# gc1 = WavePointer()
# gc1.start()
