"""Deletes data in the flash storage."""

import os

os.fsformat('/flash')
print("Cleaned flash storage")
print(os.listdir(''))
