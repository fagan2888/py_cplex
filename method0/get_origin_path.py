for date in range(20,28):
    print date
    date=str(date)
    infile='../data/oneday'+date+'.csv'
    outfile='method0_out'+date+'.txt'
    open(outfile,'w').close()
    f=open(infile,'r')
    texts=f.readlines()
    vnum_list=[]
    pnum_list=[]
    passenger_No=0
    for line in texts[1:]:
        passenger_No+=1
        vnum=int(line.split(',')[4].strip())
        pnum=passenger_No  # int(line.split(',')[0].strip())+1
        vnum_list.append(vnum)
        pnum_list.append(pnum)
    print vnum_list
    paths=[[0]for i in range(max(vnum_list))]
    for i in range(1,max(vnum_list)+1):
        for p in range(1,max(pnum_list)+1):
            if vnum_list[p-1]==i:
                paths[i-1].append(pnum_list[p-1])
    print paths
    for path in paths:
        f=open(outfile,'a')
        f.write(str(path)+'\n')