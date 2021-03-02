#!/usr/bin/env python3

from bayes_opt import BayesianOptimization

import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import axes3d, Axes3D
import numpy as np

def my_func(x, y):
    
    # print('x: {}'. format(x))
    return -(np.sin((np.power(x, 2) + np.power(y, 2)) ) + 0.1 * np.power(x-4, 3))
    #np.sin( 10*(np.power(x, 2)+np.power(y,2)) ) / 10 + 0.1 * np.power(x-4, 1.1)

pbounds = {'x': (2.0, 6.0), 'y': (2.0, 6.0)}

optimizer = BayesianOptimization(
    f=my_func,
    pbounds=pbounds,
    verbose=2, # verbose = 1 prints only when a maximum is observed, verbose = 0 is silent
    random_state=1,
)

optimizer.maximize(
    init_points=20,
    n_iter=100,
)

print(optimizer.max)



# plot
fig = plt.figure()
ax = Axes3D(fig)

x = np.arange(1.5, 6.0, 0.01)
y = np.arange(2.0, 6.0, 0.01)

X, Y = np.meshgrid(x,x)

z = my_func(X, Y)

res_x = optimizer.max['params']['x']
res_y = optimizer.max['params']['y']
ax.scatter(
    res_x, 
    res_y, 
    my_func(res_x, res_y), 
    s=128, 
    c='red', 
    alpha=1
    )
ax.plot_surface(X, Y, my_func(X, Y))

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
plt.show()



