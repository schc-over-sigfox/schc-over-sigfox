"""Deletes data in the flash storage."""

import os

os.fsformat('/flash')
print("Cleaned flash storage")
print(os.listdir(''))

os.fsformat('/sd')
print("Cleaned SD")
print(os.listdir('/sd'))
