#!/usr/bin/env python3

from scipy.optimize import minimize_scalar, Bounds
import matplotlib.pyplot as plt
import numpy as np


def f(x):
    return (x-2) * x * (x+2) ** 2

res = minimize_scalar(f, bounds=(5.0, 10.0), method='Bounded', options={'maxiter': 15, 'disp': True})
print(res)
print(res.x)

# plot
x = np.arange(-10.0, 10.0, 0.1)
fig, ax = plt.subplots() 
ax.plot(x, f(x))
ax.plot(res.x, f(res.x), 'ro')
plt.show()

