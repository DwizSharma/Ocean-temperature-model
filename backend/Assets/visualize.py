import numpy as np
import matplotlib.pyplot as plt

data = np.load('Final_X_JanFebMar.npy')

plt.plot(data)
plt.title("1D Data Visualization")
plt.xlabel("Index")
plt.ylabel("Value")
plt.show()
