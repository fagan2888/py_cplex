#  coding:utf-8
#  匹配方法：当坐满或者等待时间到达上限时发出
#  现在还有一些瑕疵，为了简化运算，并不是每一个乘客到达都出发匹配，只有到满足一定条件时才会现在主要只考虑了等待时间到达上限，还没有考虑坐满。
import cplex
from cplex.exceptions import CplexError
import re
import time, datetime


# cplex的模型构造
def populatebyrow(prob, tot, passenger_num, arrive_time, distance):
    I = range(0, tot + 1)  # 包括机场的订单目的地的集合
    K = range(0, tot)  # 车辆集合
    SI = range(1, tot + 1)  # 不包含机场的订单目的地集合
    LL = 10000  # 一个很大的数
    prob.objective.set_sense(prob.objective.sense.minimize)  # 设置模型求解目标为最小化
    arch = [[0] * (tot + 1) for i in range(tot + 1)]  # 用来记录可行路径的数组
    for i in range(tot + 1):
        for j in range(tot + 1):
            if (abs(arrive_time[i] - arrive_time[j]) <= 30 and i != j) or i == 0 or j == 0:
                arch[i][j] = 1  # 如果到达时间差距在30min内，路径可行（本程序中没有考虑绕路距离约束的预处理）
    x = [[[0] * tot for i in range(tot + 1)] for j in range(tot + 1)]
    my_colnames = []  # 用此列表装变量名称
    for i in range(tot + 1):
        for j in range(tot + 1):
            for k in range(tot):
                x[i][j][k] = 'x' + str(i) + ',' + str(j) + ',' + str(k)
                my_colnames.append(x[i][j][k])  #加入变量名称

    #  目标函数
    my_obj = []  # 目标函数前的系数
    for i in range(tot + 1):
        for j in range(tot + 1):
            for k in range(tot):
                my_obj.append(distance[i][j])  # 对系数list赋值
    my_ub = [1] * (tot + 1) * (tot + 1) * tot  # 确定变量的上界为1（其实在下面把变量设置为01变量应该就可以省去这句了）
    prob.variables.add(obj=my_obj, types=[prob.variables.type.integer] * (tot + 1) * (tot + 1) * tot, ub=my_ub,
                       names=my_colnames)

    w_colnames = []  # 这是程序的中间参数w，用来记录实际行驶距离
    w = [[0] * tot for i in I]
    for i in I:
        for k in range(tot):
            w[i][k] = 'w' + str(i) + str(k)
            w_colnames.append(w[i][k])
    prob.variables.add(names=w_colnames)  # 在模型中加入变量w

    #  公式1：每位乘客只能搭乘一次
    for j in SI:
        rows = [[[], []]]
        for k in K:
            for i in I:
                if arch[i][j] == 1:
                    rows[0][0].append(x[i][j][k])
                    rows[0][1].append(1)
        prob.linear_constraints.add(lin_expr=rows, senses=['E'], rhs=[1])

    #  公式2:乘客从机场出发
    for k in K:
        rows = [[[], []]]
        for j in I:
            rows[0][0].append(x[0][j][k])
            rows[0][1].append(1)
        prob.linear_constraints.add(lin_expr=rows, senses=['E'], rhs=[1])

    #  公式3：回到虚拟终点
    for k in K:
        rows = [[[], []]]
        for i in I:
            rows[0][0].append(x[i][0][k])
            rows[0][1].append(1)
        prob.linear_constraints.add(lin_expr=rows, senses=['E'], rhs=[1])

    #  公式4：有进必有出
    for k in K:
        for j in SI:
            rows = [[[], []]]
            for i in I:
                if arch[i][j] == 1:
                    rows[0][0].append(x[i][j][k])
                    rows[0][1].append(1)
            for m in I:
                if m != j:
                    rows[0][0].append(x[j][m][k])
                    rows[0][1].append(-1)
            prob.linear_constraints.add(lin_expr=rows, senses=['E'], rhs=[0])

    #  公式5：每辆车最多载客4人
    for k in K:
        rows = [[[], []]]
        for i in I:
            for j in SI:
                if arch[i][j] == 1:
                    rows[0][0].append(x[i][j][k])
                    rows[0][1].append(passenger_num[j])
        prob.linear_constraints.add(lin_expr=rows, senses=['L'], rhs=[4])

    #  公式6：实际访问时间约束
    for k in K:
        for i in I:
            for j in SI:
                if arch[i][j] == 1:
                    #  1
                    rows = [[[], []]]
                    rows[0][0].append(w[i][k])
                    rows[0][1].append(1)

                    rows[0][0].append(w[j][k])
                    rows[0][1].append(-1)

                    rows[0][0].append(x[i][j][k])
                    rows[0][1].append(LL)
                    prob.linear_constraints.add(lin_expr=rows, senses=['L'], rhs=[LL - distance[i][j]-0.2])
                    #  2
                    rows = [[[], []]]
                    rows[0][0].append(x[i][j][k])
                    rows[0][1].append(arrive_time[j])  # -1

                    rows[0][0].append(w[0][k])
                    rows[0][1].append(-1)
                    prob.linear_constraints.add(lin_expr=rows, senses=['L'], rhs=[0])

    #  公式7：绕路距离约束
    for k in K:
        for i in SI:
            rows = [[[], []]]
            for j in I:
                if arch[i][j] == 1:
                    rows[0][0].append(x[i][j][k])
                    rows[0][1].append(distance[0][i] * 1.3)  # without -1

            rows[0][0].append(w[i][k])
            rows[0][1].append(-1)

            rows[0][0].append(w[0][k])
            rows[0][1].append(1)
            prob.linear_constraints.add(lin_expr=rows, senses=['G'], rhs=[0])


#发送旅客
def sending_passenger(now_path,last=0):
    path = [0]#path是求解结果对应的访问路径，编号仅为从1到等待池中乘客数量
    real_path = [0]#realpath是对应于订单id的路径，编号根据实际订单id
    first_point = now_path[0][1]#离开机场后到达的第一个点
    print id_list
    print first_point
    # 因为需要将求解结果中的目的地id与乘客id对应，所以需要做如下转化
    real_path.append(id_list[first_point - 1])  # path中存储客户id
    path.append(first_point)
    for i in range(len(now_path) - 2):
        point = int(re.findall('(?<=\[' + str(path[-1]) + ',) \d+(?=\])', str(now_path))[0])#找到下一个点访问的点
        print point
        path.append(point)
        real_path.append(id_list[point - 1])
    print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', real_path
    if out_flag:#out_flag非0则输出到文件（只是为了调试的时候方便）
        f = open(outfile, 'a')
        f.write(str(real_path) + '\n')
        f.close()
    if last==1:#如果这次匹配结果已经包含最后一个旅客
        pass
    else:
        for gone_point in real_path[1:]:
            id_list.remove(gone_point)#从等待区中的id去除当前已经发送的乘客


# 从结果中得到车辆行驶路径
def get_path(pi):
    x = [[[0] * tot for i in range(tot + 1)] for j in range(tot + 1)]
    pathlist = [[] for i in range(tot)]
    for i in range(1 + tot):
        for j in range(1 + tot):
            for k in range(tot):
                x[i][j][k] = pi[i * (tot + 1) * (tot) + j * tot + k]
                if abs(x[i][j][k] - 1) <= 0.1:  # 由于求解结果存在少量偏差，当xijk与1的差距不大时均代表xijk==1
                    pathlist[k].append([i, j])
    print pathlist
    for k in range(tot):
        if id_list[-1] == max_passenger and pathlist[k] != [[0, 0]]:
            sending_passenger(pathlist[k],last=1) # 将旅客发送，last只是一个标志，当其为1时表明最后一个乘客已经到达
        else:
            flag = re.findall('\[1,', str(pathlist[k]))
            if flag != []:
                sending_passenger(pathlist[k])
                break


# 建立求解模型
def lpex1(tot, pnum, tlist, dist):
    my_prob = cplex.Cplex()  # 建立求解模型
    handle = populatebyrow(my_prob, tot, pnum, tlist, dist)  # 构造求解模型
    my_prob.solve()  # 解模型

    pi = my_prob.solution.get_values()  # 得到结果中的变量值
    get_path(pi)  # 根据变量值获得路径

    print "Solution status = ", my_prob.solution.get_status(), ":",
    # the following line prints the corresponding string
    print my_prob.solution.status[my_prob.solution.get_status()]
    print "Solution value  = ", my_prob.solution.get_objective_value()
    my_prob.write("lpex1.lp")


# 读取订单信息文件，返回订单信息列表
def get_cust_list():
    f1 = open(infile, 'r')
    all_cust = f1.readlines()  #读取文件
    cust_list = []
    for cust in all_cust[1:]:
        infos = cust.split(',')  # 按逗号分割
        num = int(infos[2])  # 订单中乘客数量
        atime = infos[5]  #到达时间
        hour = int(re.findall('\d+(?=:)', atime)[0])  #从到达时间中获取小时数据
        min = int(re.findall('(?<=:)\d+', atime)[0])  #从到达时间中获取分钟数据
        if hour >= 8:  #大于等于8表示为早上，否则为凌晨
            amin = hour * 60 + min  #将时间转换为分钟，方便计算
        else:
            amin = (hour + 24) * 60 + min
        cust_list.append([num, amin - 500])
    return cust_list


# 读取距离矩阵的csv文件，返回dist_array
def get_dist_array():
    f2 = open(distfile, 'r')
    all_dist = f2.readlines()
    tot = len(all_dist)  # this tot means the length of the distance file, It's actually the Number of Passenger + 1
    dist_array = [[0] * (tot + 1) for i in range(tot + 1)]
    for j in range(tot):
        dist_array[0][j] = round(float(all_dist[0].split(',')[j]) / 1000, 1)
    for i in range(1, tot):
        for j in range(i):
            dist_array[i][j] = round(float(all_dist[i].split(',')[j]) / 1000, 1)
            if j != 0:
                dist_array[j][i] = dist_array[i][j]
    # for i in range(tot):
    #     print dist_array[i]
    return dist_array


# 该函数为了获得等待池中的乘客的数据
def get_part_info(cust_list, dist_array, id_list):
    num = len(id_list)
    pnum = [0]
    time_list = [0]
    for id in id_list:
        pnum.append(cust_list[id - 1][0])
        time_list.append(cust_list[id - 1][1])

    if max(time_list[1:]) - min(time_list[1:]) > 30:  # 一个乘客到达时间的差距的最大值的判定，此处冗余了，可删除
        print '>>>TIME GAP TOO LARGE!!\n'

    dist = [[0] * (num + 1) for i in range(num + 1)]
    for i in range(num):
        dist[0][i + 1] = dist_array[0][id_list[i]]
    for i in range(num):
        for j in range(num):
            dist[i + 1][j + 1] = dist_array[id_list[i]][id_list[j]]

    # print 'tot=' + str(len(id_list)) + ';'
    # print 'knum='+str(int(len(id_list)))+';'
    # print tot,pnum,time_list,dist
    return pnum, time_list, dist


# 主函数
if __name__ == "__main__":
    for day in range(26,28):  # 这是为了不同的天数的数据
        date=str(day)  #将日期转换为字符串格式
        infile = '../data/oneday'+date+'.csv'  #订单列表文件
        distfile = '../data/'+date+'dist.csv'  #距离数据文件
        outfile = 'method2_out'+date+'.txt'  #路径输出文件
        out_flag = 1  #这个只是为了方便调试，如果为0，程序不输出
        if out_flag:
            open(outfile, 'w').close()
        global max_passenger  # 对于某一天来说的订单数量

        cust_list = get_cust_list()  # 乘客列表
        dist_array = get_dist_array()  #距离矩阵
        t0 = datetime.datetime.now()  #这是为了记录求解时间，t0为当前时间
        print 'START TIME = ', t0
        max_passenger = len(cust_list)  #订单数量为订单列表长度
        count = 0  # 一个用来计数的变量，记录cplex求解次数
        id_list = []  # 当前等待池中的乘客id列表
        pno = 1  # 此变量用来表示当前到达的乘客id
        while pno <= max_passenger + 1:
            print 'date = ',date
            print 'passenger No. =', pno
            id_list.append(pno)
            tot = len(id_list)  #等待池中订单数量
            pnum_list, arrive_time, dist = get_part_info(cust_list, dist_array, id_list)  #获得目前等待池中的乘客的数据
            # 下面这一句为判定，为了减少计算次数，实际程序中的判定为当乘客到达时间之差大于30时或等待区中的人数大于7人时，出发一次匹配
            if max(arrive_time[1:]) - min(arrive_time[1:]) > 30 or len(id_list) > 7:  # or sum(pnum_list)>=4:
                del id_list[-1]  # 减去一个超出要求的乘客（因为最近加入的一个是时间之差大于30的）
                pnum_list, arrive_time, dist = get_part_info(cust_list, dist_array, id_list)  # 重新获取需要的数据
                print pnum_list,arrive_time,dist
                tot = len(id_list)

                print '>>> INPUT:', id_list
                count += 1
                print '当前为第%d次求解' % count
                lpex1(tot, pnum_list, arrive_time, dist)  # 求解当前等待池中的乘客路径
                t1 = datetime.datetime.now()  # 求解完成后的时间
                print t1
                print 'TIME USAGE = ', t1 - t0
            # 如果已经是最后一位乘客
            elif pno == max_passenger:
                print '开始匹配最后一个乘客'
                print '>>> INPUT:', id_list
                count += 1
                print '当前为第%d次求解' % count
                lpex1(tot, pnum_list, arrive_time, dist)  # 求解当前等待池中的乘客路径
                t1 = datetime.datetime.now()
                print t1
                print 'TIME USAGE = ', t1 - t0
                break  #直接结束当前日期，进入下一个天的求解
            else:
                pno += 1
    # raw_input('\n\npress any key to quit')
