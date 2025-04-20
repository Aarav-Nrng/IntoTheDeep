import os

files = os.listdir()

#this renumbers the file if there is a missing file in the sequence
for x, file in enumerate(files):
  if file != "renamer.py":
    num = int(file[0:-4])
    #if num > 18:
    while not os.path.exists(f'{x}.png'):
      os.rename(file, f'{x}.png')