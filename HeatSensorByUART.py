from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from serial import Serial, SerialException
from tkinter import *
from tkinter import Toplevel
from tkinter.ttk import *
import numpy as np
from matplotlib import pyplot as plt, animation
import threading


def root_setup():
    global root, com_name, line_num, t_limit, t_dot, t_max, t_min, offset
    root = Tk()
    root.columnconfigure((1, 2, 3), weight=1)
    root.rowconfigure((1, 2), weight=1)
    com_name = StringVar()
    line_num = StringVar()
    offset = StringVar()
    t_limit = StringVar()
    t_dot = StringVar()
    t_max = float(0)
    t_min = float(0)
    com_name.set("COM")
    line_num.set("24")
    offset.set("0")
    t_limit.set("max:" + str(t_max) + " ; min:" + str(t_min))
    Entry(textvariable=com_name).grid(row=0, column=1)
    Entry(textvariable=line_num).grid(row=0, column=2)
    #Entry(textvariable=offset).grid(row=0,column=3)
    Label(textvariable=t_limit).grid(row=1, column=0)
    Label(textvariable=t_dot).grid(row=2, column=0)


root_setup()
ser = Serial(baudrate=460800)
run_over = False
refresh_over = False
project_end = False
plt.ion()


class ReadComInBackground(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.X = X

    def run(self):
        global ser, run_over, refresh_over, im, t_max, t_min, project_end
        y = [[0]] * int(line_num.get())
        count = 0
        while True:
            try:
                if project_end:
                    break
                if not run_over:
                    x = ser.read_until()
                    if x[1] == int.from_bytes(b':', byteorder="big"):
                        y[x[0] - 48] = list(map(float, x[2:-3].decode().split(",")))
                    elif x[2] == int.from_bytes(b':', byteorder="big"):
                        y[(x[0] - 48) * 10 + x[1] - 48] = list(map(float, x[3:-3].decode().split(",")))
                    count = count + 1
                    if count >= len(y):
                        data_fail = False
                        if [] not in y:
                            for d in range(len(y)):
                                if len(y[d]) < 32:
                                    data_fail = True
                                    count = 0
                            if not data_fail:
                                y_offset = np.array(y)
                                y_offset += int(offset.get())
                                y = y_offset.tolist()
                                self.X = y
                                self.getMaxAndMin(y)
                                run_over = True
                                count = 0
#                            if ser.inWaiting() > 500:
#                                ser.read(ser.inWaiting())
                        else:
                            count = 0

                if refresh_over:
                    run_over = False
                    refresh_over = False
                # print(':', end="")

            except SerialException:
                print(sys.exc_info())
            except ValueError:
                pass
            except IndexError:
                pass

    def getMaxAndMin(self, y):
        global t_max, t_min
        temp_tmax = []
        temp_tmin = []
        for _ in range(len(y)):
            temp_tmax.append(max(y[_]))
            temp_tmin.append(min(y[_]))
        t_max = max(temp_tmax)
        t_min = min(temp_tmin)


def init():
    a = fig.subplots()
    im.set_clim(((t_min+20)/2, (t_max+35)/2))
    return a


def refresh(i):
    global run_over, refresh_over
    if run_over:
        im.set_data(myt.X)
        refresh_over = True
        t_limit.set("max:" + str(t_max) + ";min:" + str(t_min))
    return im,


def fresh_start():
    global im, X, myt, start_flag

    global ser
    if ser.isOpen():
        ser.close()
    ser.setPort(com_name.get())
    try:
        ser.open()
        myt.start()
    except SerialException:
        raise


def on_pick(event):
    class OffsetWindow(Toplevel):
        def __init__(self):
            super().__init__()
            self.title("Offset")
            self.geometry("200x100+"+str(int(root.winfo_width()/2))+"+"+str(int(root.winfo_height()/2)))
            self.area_offset = StringVar()
            self.area_offset.set("0")
            if X_offset[int(event.ydata)][int(event.xdata)] != 0:
                self.area_offset.set(str(X_offset[int(event.ydata)][int(event.xdata)]))
            Label(self, text="offset:").pack()
            self.t_offset = Entry(self, textvariable=self.area_offset)
            self.t_offset.pack()
            self.btnOK = Button(self, text="OK", command=lambda: self.modifyOffset()).pack()

        def modifyOffset(self):
            X_offset[int(event.ydata)][int(event.xdata)] = int(self.t_offset.get())
            self.destroy()
    try:
        _ = str(myt.X[int(event.ydata)][int(event.xdata)])

        t_dot.set("temp="+_+";offset:"+str(X_offset[int(event.ydata)][int(event.xdata)]))
        w = OffsetWindow()
        root.wait_window(w)

    except IndexError:
        print("out of range: ", event.xdata, event.ydata)


def switch_interpolation():
    if im._interpolation == 'nearest':
        im.set_interpolation("bicubic")
    else:
        im.set_interpolation('nearest')


X = [[0] * 32] * int(line_num.get())
X_offset = np.array(X)
myt = ReadComInBackground()

fig = Figure(figsize=(4, 5), dpi=100)
subtitle = fig.suptitle("ThermalView")
ax2 = fig.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=1, rowspan=2, column=1, columnspan=3, sticky=NSEW)
fig.canvas.mpl_connect('button_press_event', on_pick)
# canvas.draw()
im = ax2.imshow(X, cmap="nipy_spectral", clim=(20, 35), interpolation=None, animated=True)
cbar = fig.colorbar(im)
cbar.set_ticks(np.linspace(0, 100, 21))
an = animation.FuncAnimation(fig=fig, func=refresh, frames=150, interval=25, blit=True)
button_start = Button(text="start", command=lambda: fresh_start()).grid()
button_switch = Button(text="switch", command=lambda: switch_interpolation()).grid()

if __name__ == '__main__':
    com_name.set("COM6")
    line_num.set("24")
    root.mainloop()
    project_end = True
    plt.close('all')
    if ser.isOpen():
        ser.close()
