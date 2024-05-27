import cv2
import matplotlib.pyplot as plt

img = cv2.imread('testcopy.jpg')
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, img = cv2.threshold(img, 170, 255, cv2.THRESH_BINARY)
plt.imshow(img, cmap='gray')
plt.show()