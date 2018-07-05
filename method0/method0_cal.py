import re

global lenpath


def get_info():
    f = open(infofile, 'r')
    texts = f.readlines()
    atime_list = []
    pnum_list = []
    waiting_time_list=[]

    for i in texts[1:]:
        atime=i.split(',')[5]
        hour = int(re.findall('\d+(?=:)', atime)[0])
        min = int(re.findall('(?<=:)\d+', atime)[0])
        if hour >= 8:
            amin = hour * 60 + min
        else:
            amin = (hour + 24) * 60 + min

        dtime=i.split(',')[6]
        try:
            hour = int(re.findall('\d+(?=:)', dtime)[0])
            min = int(re.findall('(?<=:)\d+', dtime)[0])
            if hour >= 8:
                dmin = hour * 60 + min
            else:
                dmin = (hour + 24) * 60 + min
        except:
            dmin=amin+10

        atime_list.append(amin)
        waiting_time_list.append(dmin-amin)
        if dmin-amin>30:
            print '!!!!!!!!'
            print dmin-amin,dtime,atime,dmin,amin
        pnum_list.append(int(i.split(',')[2].strip()))
    f.close()
    return atime_list, pnum_list,waiting_time_list


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
    infile = 'method0_out'+date+'.txt'
    atime_list, pnum_list,waiting_time_list = get_info()
    point_list = get_path()
    print date,'people number list=',pnum_list
    print date,'arrive time list=',atime_list
    person_per_car = [0] * (lenpath)
    for i in range(lenpath):
        for j in range(len(point_list[i])):
            pno = point_list[i][j] - 1
            person_per_car[i] += pnum_list[pno]
    print date,'person per car =' ,person_per_car
    outstring='\n'+date+'\n'+'people number list='+str(pnum_list)+'\narrive time list='+str(atime_list)+'\nperson per car =' +str(person_per_car)+'\nwaiting time='+ str(waiting_time_list)
    f=open(out_file,'a')
    f.write(outstring+'\n tot_waiting_time========'+str(sum(waiting_time_list)))
    f.close()
    outfile2 = '../ppc.csv'  # person per car
    f=open (outfile2,'a')
    print waiting_time_list
    f.write(str(person_per_car)[1:-1]+',')
    f.close()
f=open (outfile2,'a')
f.write('\n')
f.close()

