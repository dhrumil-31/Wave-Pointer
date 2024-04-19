import WavePointer
from threading import Thread
import tkinter
from tkinter.constants import *

root = tkinter.Tk()

if WavePointer.WavePointer.gc_mode:
        print('Gesture recognition is already active')
else:
        def stay_on_top():
            root.attributes('-topmost', True)
            root.after(2000, stay_on_top)
        
        root.title('WavePointer')
        wp = WavePointer.WavePointer()
        t = Thread(target = wp.start, args=(root,))
        t.start()
        root.tk.call('tk','windowingsystem')
        root.overrideredirect(True)
        stay_on_top()
        hs = root.winfo_screenheight()
        ws = root.winfo_screenwidth()
        x = (ws) - (500)
        y = (hs) - (200)

        root.geometry('%dx%d+%d+%d' % (500, 120, x, y))
        root.mainloop()
        print('Stopped Successfully')