from tkinter import Tk
from tkinter.constants import *

import numpy
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from matplotlib.figure import Figure
from matplotlib import pyplot as plt, animation

X = numpy.zeros((24, 32))
root = Tk()
plt.ion()
fig = Figure(figsize=(4, 4), dpi=100)
ax2 = fig.subplots()
im = ax2.imshow(X, cmap="nipy_spectral", clim=(20, 35), interpolation=None, animated=True)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=0, column=1, sticky=NSEW)
root.mainloop()
