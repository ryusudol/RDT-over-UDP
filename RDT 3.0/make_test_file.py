import sys
import random

SIZE = 5 * 1024 * 1024

f = open("test_file.txt", "w")

for i in range(0, SIZE):
    f.write(str(random.randrange(0, 9)))

f.close()
