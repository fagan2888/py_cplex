
import re

global lenpath


def get_info():
    f = open(infofile, 'r')
    texts = f.readlines()
    atime_list = []
    pnum_list = []
    for i in texts[1:]:
        atime=i.split(',')[5]
        hour = int(re.findall('\d+(?=:)', atime)[0])
        min = int(re.findall('(?<=:)\d+', atime)[0])
        if hour >= 9:
            amin = hour * 60 + min
        else:
            amin = (hour + 24) * 60 + min
        atime_list.append(amin)
        pnum_list.append(int(i.split(',')[2].strip()))
    f.close()
    return atime_list, pnum_list


def get_path():
    f = open(infile, 'r')
    texts = f.readlines()
    global lenpath
    lenpath = len(texts)
    point_list = [[] for i in range(lenpath)]
    for i in range(len(texts)):
        points = texts[i][4:-2].split(',')
        for point in points:
            point_list[i].append(int(point))
    # print point_list
    return point_list



out_file='info.txt'
open(out_file,'w').close()
for day in range(20,28):
    date=str(day)
    infofile = '../data/oneday'+date+'.csv'
    infile = 'method2_out'+date+'.txt'

    atime_list, pnum_list = get_info()
    point_list = get_path()
    print 'people number list=',pnum_list
    print 'arrive time list=',atime_list
    person_per_car = [0] * (lenpath)
    for i in range(lenpath):
        for j in range(len(point_list[i])):
            pno = point_list[i][j] - 1
            person_per_car[i] += pnum_list[pno]
    print 'person per car =' ,person_per_car

    dtime_list=[0]*lenpath
    wating_time_list=[0]*len(atime_list)
    for i in range(lenpath):
        part_arrive_time=[]
        for j in point_list[i]:
            part_arrive_time.append(atime_list[j-1])  # because the point No. start from 1

        if person_per_car[i]==4:
            dtime_list[i]=max(part_arrive_time)
        else:
            dtime_list[i]=int(min(part_arrive_time))+30
        for j in point_list[i]:
            wating_time_list[j-1]=(dtime_list[i]-atime_list[j-1])
    print 'depature time list=', dtime_list

    print 'wating time list=',wating_time_list

    outstring='\n'+date+'\n'+'people number list='+str(pnum_list)+'\narrive time list='+str(atime_list)+'\nperson per car =' +str(person_per_car)+'wating time list='+ str(wating_time_list)
    f=open(out_file,'a')
    f.write(outstring+'\n tot_waiting_time========'+str(sum(wating_time_list)))
    f.close()
    outfile2 = '../ppc.csv'
    f=open (outfile2,'a')
    f.write(str(person_per_car)[1:-1]+',')
    f.close()
f=open (outfile2,'a')
f.write('\n')
f.close()


