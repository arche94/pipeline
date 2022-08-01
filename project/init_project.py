import os

##### NOT TO BE USED FOR NOW

for i in range(9):
  dir_shot = '001_000'+str(i+1)
  os.mkdir(dir_shot)
  os.mkdir(dir_shot+'/cam')
  os.mkdir(dir_shot+'/assets')
