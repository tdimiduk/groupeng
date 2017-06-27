import sys
import os

from src import controller

path = os.path.abspath(__file__)
print(path)
root = os.path.split(path)[0]
gf = os.path.join(root, 'test_group_size.groupeng')
print(gf)

controller.run(gf)

