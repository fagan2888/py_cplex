infile='method1_out.txt'
f=open(infile,'r')
all=f.read()
import re
for i in range(1,92):
    if re.findall(str(i),all)!=[]:
        print i