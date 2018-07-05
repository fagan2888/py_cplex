#  coding:utf-8
#  匹配方法：当坐满或者等待时间到达上限时发出
import cplex
from cplex.exceptions import CplexError
import re
import time, datetime



global max_passenger
global tot_value


def populatebyrow(prob, tot, passenger_num, arrive_time, distance):
    I = range(0, tot + 1)
    K = range(0, tot)
    SI = range(1, tot + 1)
    LL = 100000
    prob.objective.set_sense(prob.objective.sense.minimize)
    arch = [[0] * (tot + 1) for i in range(tot + 1)]
    for i in range(tot + 1):
        for j in range(tot + 1):
            if (abs(arrive_time[i] - arrive_time[j]) <= 30 and i != j) or i == 0 or j == 0:
                arch[i][j] = 1
    x = [[[0] * tot for i in range(tot + 1)] for j in range(tot + 1)]
    my_colnames = []
    for i in range(tot + 1):
        for j in range(tot + 1):
            for k in range(tot):
                x[i][j][k] = 'x' + str(i) + ',' + str(j) + ',' + str(k)
                my_colnames.append(x[i][j][k])

    #  目标函数
    my_obj = []
    for i in range(tot + 1):
        for j in range(tot + 1):
            for k in range(tot):
                my_obj.append(distance[i][j])
    my_ub = [1] * (tot + 1) * (tot + 1) * tot
    prob.variables.add(obj=my_obj, types=[prob.variables.type.integer] * (tot + 1) * (tot + 1) * tot, ub=my_ub,
                       names=my_colnames)

    w_colnames = []
    w = [[0] * tot for i in I]
    for i in I:
        for k in range(tot):
            w[i][k] = 'w' + str(i) + str(k)
            w_colnames.append(w[i][k])
    prob.variables.add(names=w_colnames)

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
                    prob.linear_constraints.add(lin_expr=rows, senses=['L'], rhs=[LL - distance[i][j]])
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


def sending_passenger(now_path):
    path = [0]
    real_path = [0]
    first_point = now_path[0][1]
    real_path.append(id_list[first_point - 1])  # path中存储客户id
    path.append(first_point)
    for i in range(len(now_path) - 2):
        point = int(re.findall('(?<=\[' + str(path[-1]) + ',) \d+(?=\])', str(now_path))[0])
        path.append(point)
        real_path.append(id_list[point - 1])
    print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', real_path


def get_path(pi):
    x = [[[0] * tot for i in range(tot + 1)] for j in range(tot + 1)]
    pathlist = [[] for i in range(tot)]
    for i in range(1 + tot):
        for j in range(1 + tot):
            for k in range(tot):
                x[i][j][k] = pi[i * (tot + 1) * (tot) + j * tot + k]
                if abs(x[i][j][k] - 1) <= 0.1:  # 由于求解存在少量
                    pathlist[k].append([i, j])
    print pathlist
    for k in range(tot):
        if pathlist[k] != [[0, 0]]:
            # sending_passenger(pathlist[k])
            pass


def lpex1(tot, pnum, tlist, dist):
    global tot_value

    my_prob = cplex.Cplex()
    handle = populatebyrow(my_prob, tot, pnum, tlist, dist)
    my_prob.solve()
    numrows = my_prob.linear_constraints.get_num()
    numcols = my_prob.variables.get_num()

    slack = my_prob.solution.get_linear_slacks()
    pi = my_prob.solution.get_values()
    get_path(pi)

    # solution.get_status() returns an integer code
    print "Solution status = ", my_prob.solution.get_status(), ":",
    # the following line prints the corresponding string
    print my_prob.solution.status[my_prob.solution.get_status()]
    print "Solution value  = ", my_prob.solution.get_objective_value()
    my_prob.write("lpex1.lp")
    tot_value += my_prob.solution.get_objective_value()
    print tot_value


def get_cust_list():
    f1 = open(infile, 'r')
    all_cust = f1.readlines()
    cust_list = []
    for cust in all_cust[1:]:
        infos = cust.split(',')
        num = int(infos[2])
        atime = infos[5]
        hour = int(re.findall('\d+(?=:)', atime)[0])
        min = int(re.findall('(?<=:)\d+', atime)[0])
        if hour >= 9:
            amin = hour * 60 + min
        else:
            amin = (hour + 24) * 60 + min
        cust_list.append([num, amin - 540])
    return cust_list


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


def get_part_info(cust_list, dist_array, id_list):
    num = len(id_list)
    pnum = [0]
    time_list = [0]
    for id in id_list:
        pnum.append(cust_list[id - 1][0])
        time_list.append(cust_list[id - 1][1])

    if max(time_list[1:]) - min(time_list[1:]) > 30:
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

global tot_value

outfile='./method1/tot_dist.txt'
open(outfile,'w').close()
if __name__ == "__main__":
    for day in range(20,28):
        date=str(day)
        infile = './data/oneday'+date+'.csv'
        distfile = './data/'+date+'dist.csv'
        pathfile = './method1/method1_out'+date+'.txt'
        tot_value = 0
        cust_list = get_cust_list()
        atime = [0]
        for i in range(len(cust_list)):
            atime.append(cust_list[i][1])
        dist_array = get_dist_array()
        t0 = datetime.datetime.now()
        print 'START TIME = ', t0
        #max_passenger = 91
        count = 0
        f = open(pathfile, 'r')
        texts = f.readlines()
        lenpath = len(texts)
        point_list = [[] for i in range(lenpath)]
        for i in range(len(texts)):
            points = texts[i][4:-2].split(',')  # 如果是第三种方法后面界限改为-4，否则为-2
            for point in points:
                point_list[i].append(int(point))
        for oneline in point_list:
            id_list = []
            for poi in oneline:
                id_list.append(poi)
            tot = len(id_list)
            pnum_list, arrive_time, dist = get_part_info(cust_list, dist_array, id_list)
            pnum_list, arrive_time, dist = get_part_info(cust_list, dist_array, id_list)  # 重新获取需要的数据
            tot = len(id_list)

            print '>>> INPUT:', id_list
            count += 1
            print '当前为第%d次求解' % count
            lpex1(tot, pnum_list, arrive_time, dist)
            t1 = datetime.datetime.now()
            print t1
            print 'TIME USAGE = ', t1 - t0
        f=open(outfile,'a')
        f.write(date+','+str(tot_value)+'\n')
