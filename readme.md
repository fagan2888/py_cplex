# 三种匹配策略与机场现有方案的匹配结果

> 注意:method文件打注释的为method2.py，其他的文件内容都很类似，大部分是重复的，就没有打注释了

## 主要流程

1. 三种匹配方案获取匹配结果

2. 从匹配结果文件获取总行驶距离和总等待时间

3. 车辆数量直接手动统计的

4. 每车人数是直接写到匹配程序的输出结果里的，然后自己手动复制出来的

## 文件

1. data为每天的订单列表和距离数据

2. 三个method文件分别是三个策略的匹配程序

    * info.txt 为程序的输出文件，包括了每车乘客数量和乘客总等待时间
    
    * method.py是匹配程序，并将结果按天输出到txt文件中
    
    * method_cal是用来对匹配结果进行统计，生成info.txt
    
    * tot_dist是根目录下get_tot_dis.py文件生成的，用来记录实际行驶距离
 
3. 根目录下的其他文件

    主要都是其他文件的内容的汇总了