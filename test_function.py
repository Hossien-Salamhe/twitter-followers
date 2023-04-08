from datetime import datetime

print("Current Time =", datetime.now().strftime("%H:%M:%S"))


import random

x = [{i} for i in range(10)]
random.shuffle(x)
print(x)