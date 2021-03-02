#!/usr/bin/env python3

from scipy.optimize import minimize

import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import axes3d, Axes3D
import numpy as np

def f(coords):
    x, y = coords
    # print('x: {}'. format(x))
    return np.sin((np.power(x, 2) + np.power(y, 2)) ) + 0.1 * np.power(x-4, 3)
    #np.sin( 10*(np.power(x, 2)+np.power(y,2)) ) / 10 + 0.1 * np.power(x-4, 1.1)


# plot
fig = plt.figure()
ax = Axes3D(fig)

x = np.arange(1.5, 6.0, 0.01)
y = np.arange(2.0, 6.0, 0.01)

X, Y = np.meshgrid(x,x)

coordinates = X, Y

z = f(coordinates)
res = minimize(f, x0=[4.0, 4.0], bounds=((2.0, 6.0), (2.0, 6.0)))
print(res)
res_x = res.x[0]
res_y = res.x[1]
ax.scatter([res_x], [res_y], f(res.x), s=128, c='red', alpha=1)
ax.plot_surface(X, Y, f([X, Y]))
print(res.x[0])
print(type(res.x[0]))

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
plt.show()



