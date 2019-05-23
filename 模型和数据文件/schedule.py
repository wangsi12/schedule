# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 11:17:38 2018

@author: ZeroPC
"""
from __future__ import division
import pprint
import json
import pyomo.environ as pe
from pyomo.opt import SolverFactory
from pyomo.core import Var
import os 
import numpy as np
import time
import datetime
import random
import datetime
from pyomo.environ  import *
'''部分变量描述不清楚的，可以用print打印一下看看具体是什么，结合我的变量名字和用处应该可以理解'''
'''数据检查函数'''
def task_inspect(selected_tasks,process_time,code_device,transport_time,ALL_PATH_ID_list):
    #task预处理
    list_jb=ALL_PATH_ID_list
    l=len(selected_tasks)
    task_PNON=[]
    task_SG=[]
    task_FINERY_PATH_ID=[]
    task_CC_START_TIME=[]
    for i in range(l):
        task_PNON.append(selected_tasks[i]['PONO'])
        task_SG.append(selected_tasks[i]['SG'])
        task_FINERY_PATH_ID.append(selected_tasks[i]['FINERY_PATH_ID'])
        if selected_tasks[i]['CC_START_TIME']!='':
            task_CC_START_TIME.append(selected_tasks[i]['CC_START_TIME'])
    #process_time预处理
    process_time_l=len(process_time)
    process_time_SG=[]
    for i in range(process_time_l): 
        process_time_SG.append(process_time[i]['SG'])
    #SG判断
    len_SG=len(task_SG)
    for i in range(len_SG):
        if task_SG[i] not in process_time_SG:
            print("警告：加工时间数据中不存在您所输入的浇次，请核对staic_plan_cc数据：",task_SG[i])
    #工序判定
    len_FINERY_PATH_ID=len(task_FINERY_PATH_ID)
    for i in range(len_FINERY_PATH_ID):
        for j in range(len(task_FINERY_PATH_ID[i])):
           if task_FINERY_PATH_ID[i][j] not in list_jb:
               print("警告：此工序为非法工序号：",task_FINERY_PATH_ID[i][j])
    #预计连铸开始时间判定
    nowdate = datetime.datetime.now() 
    nowdate = nowdate.strftime("%Y-%m-%d %H:%M:%S") 
    for i in range(len(task_CC_START_TIME)) :
        if task_CC_START_TIME[i]<nowdate:
            print("警告，您输入的连铸机预计开始时间为过去时间",task_CC_START_TIME[i])

#staic_Plan_CC处理函数目地是让无序的task按照有序的'CC_ID'进行排列
def sort_task(selected_tasks,CC_ID_list):
    result=[]
    len_task=len(selected_tasks)
    result=sorted(selected_tasks,key = lambda e:e.__getitem__('PLAN_NUMBER'))
    result2=[]
    for i in range(len(CC_ID_list)):
        for j in range(len_task):
          if result[j]['CC_ID']==CC_ID_list[i]:
              result2.append(result[j])
    return result2

#用于打包各个浇次中炉次的集合，
'''输入是selected_tasks。
输出list_jiaoci_start（每个浇次开始炉次）, list_luci（所有炉次）, list_jiaoci_end（每个浇次结束的炉次）,list_remove_end（每个浇次去除末尾炉次的剩下炉次）,
list_pono_cast（每个炉次所对应的pono号）,list_CC_ID（#连铸变化的pono）,list_CC_START_TIME（连铸机开始的时间与pono的集合）'''
def task_pack(selected_tasks,CC_ID_list,CC_IDENTIFY):
    selected_tasks=sort_task(selected_tasks,CC_ID_list)#这里调用上一个函数进行排序
#    for i in range(len(selected_tasks)):
#        print(selected_tasks[i]["PLAN_NUMBER"])
    
    list_pono_cast=[[0 for i in range(2)]for i in range(len(selected_tasks))]
    list_CC_ID=[]#连铸变化的pono
    #4.1新改的begin    
    list_CC_START_TIME=[]#连铸机预计开始时间
    list_CC_START_TIME_temp=[]
    for i in range(len(selected_tasks)):
        if i==0:
             
             list_CC_START_TIME_temp.append(selected_tasks[i]['PONO'])
             list_CC_START_TIME_temp.append(selected_tasks[i]['CC_START_TIME'])
             list_CC_START_TIME.append(list_CC_START_TIME_temp)
             list_CC_START_TIME_temp=[]

        else :
            if selected_tasks[i]['CC_ID']!=selected_tasks[i-1]['CC_ID'] :
                
                list_CC_START_TIME_temp.append(selected_tasks[i]['PONO'])
                list_CC_START_TIME_temp.append(selected_tasks[i]['CC_START_TIME'])
                list_CC_START_TIME.append(list_CC_START_TIME_temp)
                list_CC_START_TIME_temp=[]
#4.1新改的 end
    for i in range(len(selected_tasks)):
        list_pono_cast[i][0]=selected_tasks[i]['PONO']
        list_pono_cast[i][1]=selected_tasks[i]['CC_ID']
        if i>1:
            if selected_tasks[i]['CC_ID']!=selected_tasks[i-1]['CC_ID'] :
                
                list_CC_ID.append(selected_tasks[i-1]['PONO'])
    
    list_jiaoci_start=[]#所有浇次开始炉次
    list_luci=[]#所有炉次号
    list_jiaoci_end=[]#所有浇次末尾炉次集合
    list_remove_end=[]#所有去除末尾炉次的剩下炉次的集合
    for i in range(len(selected_tasks)):
        list_luci.append(selected_tasks[i]['PONO'])
        if i==0:
            list_jiaoci_start.append(selected_tasks[i]['PONO'])
        elif  selected_tasks[i]['CC_IDENTIFY']==str(CC_IDENTIFY) or selected_tasks[i-1]['CC_ID']!=selected_tasks[i]['CC_ID']:
            list_jiaoci_start.append(selected_tasks[i]['PONO'])
            list_jiaoci_end.append(selected_tasks[i-1]['PONO'])
        if i==len(selected_tasks)-1:
            list_jiaoci_end.append(selected_tasks[i]['PONO'])
    
    for i in range(len(list_luci)):
           if list_luci[i] in list_jiaoci_end:
               a=0#啥也不做的意思
           else:
                list_remove_end.append(list_luci[i])
    return  list_jiaoci_start, list_luci, list_jiaoci_end,list_remove_end,list_pono_cast,list_CC_ID,list_CC_START_TIME,selected_tasks

def addtime(date1,date2,date3):
    date1=datetime.datetime.strptime(date1,"%Y-%m-%d %H:%M:%S")
    date2=datetime.datetime.strptime(date2,"%Y-%m-%d %H:%M:%S")
    date3=datetime.datetime.strptime(date3,"%Y-%m-%d %H:%M:%S")
    return date2-date1+date3
#时间转换函数，目的是为了把我们的计算出来的相对时间转化为实际的时间
def time_add(s):
    timeArray = time.localtime(s)#绉掓暟
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    nowdate = datetime.datetime.now() # 鑾峰彇褰撳墠鏃堕棿
    nowdate = nowdate.strftime("%Y-%m-%d %H:%M:%S") # 褰撳墠鏃堕棿杞崲涓烘寚瀹氬瓧绗︿覆鏍煎紡
    date1 =otherStyleTime
    date2 = r'1970-01-01 08:00:00'
    data3 =nowdate 
    return addtime(date2,date1,data3)
#调度模型函数 pyomo语言建立，需要传入三个辅助列表list_sb,list_CC_ID,list_pono_cast
def model_main(list_sb,list_CC_ID,list_pono_cast,gu_zd,ALL_PATH_ID_list,blank):
    k_zhidian=gu_zd
    list_jb=ALL_PATH_ID_list
    #list_jb_last=list_jb[len(list_jb)-1]
    list_jb_first=0

    model = AbstractModel("diaoduxin")
    
    model.I=Set()
    
    #meige 每个浇次开始的炉次
    model.I1=Set()
    #i+1的炉次
    model.I2=Set()
    #每个浇次结束的炉次
    model.I3=Set()
    #model.I4=Set()
    
    model.J=Set()
    model.J2=Set()
    model.J3=Set()

    
    model.K=Set()
    model.A=Set(within=model.I*model.J3)
    model.A2=Set(within=model.I*model.J3)
    model.A3=Set(within=model.I*model.J)
    
    model.M2=Param(model.I)#每个炉次的最后一道工序
    model.M=Param(model.A3)#ij索引工序号
    model.p=Param(model.A,within=NonNegativeReals)
    model.T=Param(model.J3,model.J3,within=NonNegativeReals)
    model.d=Param(model.I1,within=NonNegativeReals)
    #juecebianliang
    model.x= Var(model.I,model.J,model.K, within=Binary)
    model.y= Var(model.I,model.I,model.J, within=Binary)
    model.t= Var(model.A3, within=NonNegativeIntegers)
    model.tu= Var(model.A3, within=NonNegativeIntegers)
    model.td= Var(model.A3, within=NonNegativeIntegers)
    def obj_rule(model):
       
     
        return sum(model.t[i,model.M2[i]]-model.t[i,list_jb_first] for i in model.I )+10*sum(model.tu[i1,model.M2[i1]] for i1 in model.I1 )+10*sum(model.td[i1,model.M2[i1]] for i1 in model.I1) 
    model.obj = Objective(rule=obj_rule,sense=minimize)
    
    def list_next(list1,i):#计算列表小一个元素
        return list1[list1.index(i)+1]
    
    
    
    def getTwoDimensionListIndex(L,value): # 
     
        data = [data for data in L if data[0]==value]  
        index = L.index(data[0])  
        return index
    
    def con_rule(model,i,j):
        
        if model.M[i,j+1]!=blank and model.M[i,j]!=blank and  j!=model.M2[i] :
            #print("testj",i,model.M[i,j])
            if model.p[i,model.M[i,j]]==0:
                a=0
            else:
                a=1
            #print(model.M[i,j+1])
            return (model.t[i,j+1]-model.t[i,j]-model.p[i,model.M[i,j]]-a*model.T[model.M[i,j],model.M[i,j+1]] )>=0
        return Constraint.Skip
    model.con = Constraint(model.I,model.J2,rule=con_rule)
    
    def con_rule1(model,i):
#        print("list_sb",list_sb)
#        print(list_next(list_sb,i),i,model.p[i,model.M[i,model.M2[i]]])
        #print("con_rule1",i)
        return (model.t[list_next(list_sb,i),model.M2[list_next(list_sb,i)]]-model.t[i,model.M2[i]]-model.p[i,model.M[i,model.M2[i]]])==0
        #return (model.t[list_next(list_sb,i),model.M2[i]]-model.t[i,model.M2[i]]-model.p[i,model.M[i,model.M2[i]]])==0
    model.con1 = Constraint(model.I2, rule=con_rule1)
    def con_rule2(model,i):
        if str(i) not in list_CC_ID:
            #print("con_rule2",i)
            return (model.t[list_next(list_sb,i),model.M2[list_next(list_sb,i)]]-model.t[i,model.M2[i]]-model.p[i,model.M[i,model.M2[i]]])>=80
            #return (model.t[list_next(list_sb,i),model.M2[i]]-model.t[i,model.M2[i]]-model.p[i,model.M[i,model.M2[i]]])>=40
        return Constraint.Skip
    model.con2 = Constraint(model.I3, rule=con_rule2)
    #
    def con_rule3(model,i):
        return (model.t[i,model.M2[i]]-model.tu[i,model.M2[i]]+model.td[i,model.M2[i]]==model.d[i])
    model.con3 = Constraint(model.I1, rule=con_rule3)
    
    def con_rule4(model,i,j):
        
        if model.M[i,j+1]!=blank and  j!=model.M2[i] :
            return sum(model.x[i,j,k]  for k in model.K if k_zhidian[str(k)]==model.M[i,j] )==1
        return Constraint.Skip
    model.con4 = Constraint(model.I,model.J2,rule=con_rule4)
     
    def con_rule44(model,i,k):
        if list_pono_cast[getTwoDimensionListIndex(list_pono_cast, str(i))][1]==str(k):
            #print("list_pono_cast",list_pono_cast)
            return model.x[i,model.M2[i],k]==1
        return Constraint.Skip
    model.con44 = Constraint(model.I,model.K, rule=con_rule44)
    
#    def con_rule5(model,i,r,j):
#        if i!=r and model.M[i,j+1]!=blank and  j!=model.M2[i]:
#            return (model.y[i,r,j]+model.y[r,i,j])==1 
#        return Constraint.Skip
#       
#    model.con5 = Constraint(model.I,model.I,model.J2, rule=con_rule5)
    def con_rule5(model,i,r,j,jr):
        if i!=r and model.M[i,j+1]!=blank and  j!=model.M2[i] and model.M[i,j]==model.M[r,jr]:
            return (model.y[i,r,j]+model.y[r,i,jr])==1 
        return Constraint.Skip
       
    model.con5 = Constraint(model.I,model.I,model.J2,model.J2, rule=con_rule5)
    
#    def con_rule6(model,i,r,j,k):
#        if k_zhidian[str(k)]==model.M[i,j]and i!=r and  model.M[i,j+1]!=blank and  j!=model.M2[i]:                    
#            return (model.t[r,j]-model.t[i,j]-model.p[i,model.M[i,j]]+10000*(3-model.x[i,j,k]-model.x[r,j,k]-model.y[i,r,j]))>=0
#        return Constraint.Skip
#    
#    model.con6 = Constraint(model.I,model.I,model.J2,model.K, rule=con_rule6)
    def con_rule6(model,i,r,j,jr,k):
        if k_zhidian[str(k)]==model.M[i,j]and i!=r and  model.M[i,j+1]!=blank and  j!=model.M2[i] and model.M[i,j]==model.M[r,jr]:                    
            return (model.t[r,jr]-model.t[i,j]-model.p[i,model.M[i,j]]+10000*(3-model.x[i,j,k]-model.x[r,jr,k]-model.y[i,r,j]))>=0
        return Constraint.Skip
    
    model.con6 = Constraint(model.I,model.I,model.J2,model.J2,model.K, rule=con_rule6)
    
#    def con_rule7(model,i,j,j1,k):##为了保证同一时刻只有一个加工
#        if  i!=list_sb[-1] and model.M[i,j]==model.M[list_next(list_sb,i),j1] and model.M[i,j+1]!=blank :                  
#            return (model.t[list_next(list_sb,i),j1]-model.t[i,j])+10000*(3-model.x[i,j,k]-model.x[list_next(list_sb,i),j1,k]-model.y[i,list_next(list_sb,i),j])>=model.p[i,model.M[i,j]]
#        return Constraint.Skip
#    
#    model.con7 = Constraint(model.I,model.J2,model.J2,model.K, rule=con_rule7)
###   
#    def con_rule8(model,i,j,j1,k):
#        if k_zhidian[str(k)]==model.M[i,j] and  model.M[i,j+1]!=blank and  j!=model.M2[i] and i!=list_sb[-1] and model.M[i,j]==model.M[list_next(list_sb,i),j1] :                    
#            return (model.t[list_next(list_sb,i),j1]-model.t[i,j]-model.p[i,model.M[i,j]]+10000*(3-model.x[i,j,k]-model.x[list_next(list_sb,i),j1,k]-model.y[i,list_next(list_sb,i),j]))>=0
#        return Constraint.Skip
#    
#    model.con8 = Constraint(model.I,model.J2,model.J2,model.K, rule=con_rule8)
#    
    
    return model
#这是将计算出来的结果转化成字典输出，为了使得能应用于甘特图。
'''其中task_test就是输入的task，process_time是加工时间（为了计算每个工序结束时间用的），list_lie,list_lie2,list_hang是对solver求解的结果保存的列表
jiaoci_beigin_time1是我们计算出来的每个炉次的预计开胶时间（这块注意是每个炉次的，因为是后改的所以变量名字是jiaoci_beigin_time1）
输出list_result是结果列表'''

def getTwoDimensionListIndex(L,value): #获得二维列表某个元素所在的index 
         
        data = [data for data in L if data[0]==value]  
        index = L.index(data[0])  
        return index
#连铸工序时间
'''file是输入的task，list_jiaoci_start,list_luci分别是浇次开始的炉次和全部炉次的集合。
输出是各个炉次的连铸工序的加工所用时间'''
def Calculate_continuous_castingtime(file,list_jiaoci_start,list_luci):#连铸工序时间
    task=file
    p_list=[]
    for i in range(len(task)):
        w=230 #钢水质量
        a=task[i]["THICKNESS"]  #输出板坯厚度
        wide_odd=(task[i]["LOT_ODD_WIDTH1"]+task[i]["LOT_ODD_WIDTH2"])/2  #奇流板坯宽度
        wide_even=(task[i]["LOT_EVEN_WIDTH1"]+task[i]["LOT_EVEN_WIDTH2"])/2  #偶流板坯宽度
        v=1.2 #拉速
        if(task[i]["PONO"] in list_jiaoci_start):
            p=(w*1e6)/(7.8*a*(wide_odd+wide_even)*(v-0.2))
            p_list.append([task[i]["PONO"],int(p)])
        else:
            front=list_luci.index(task[i]["PONO"])-1
            last_wide_odd=(task[front]["LOT_ODD_WIDTH1"]+task[front]["LOT_ODD_WIDTH2"])/2    #上一炉次奇流板坯宽度
            last_wide_even=(task[front]["LOT_EVEN_WIDTH2"]+task[front]["LOT_EVEN_WIDTH2"])/2  #上一炉次偶流板坯宽度
            wide=wide_odd+wide_even+last_wide_odd+last_wide_even
            p=(w*1e6-31.2*a*wide)/(3.9*a*wide*(v-0.2))+8/(v-0.2)
            p_list.append([task[i]["PONO"],int(p)])
    p_list2=[]
    for i in range(len(list_luci)):
        p_list2.append(p_list[getTwoDimensionListIndex(p_list,list_luci[i])])
        
        
    return p_list2
def i_j_index(selected_tasks,CC_ID_list,all_reality_FINERY_PATH_ID_NUM,FINERY_PATH_ID_list,ALL_PATH_ID_list,blank):#建立通过ij索引工序号
    task=sort_task(selected_tasks,CC_ID_list)
    task_len=len(task)
    pono_FINERY=[[0 for col in range(2)] for row in range(task_len)] 
    for i in range(task_len):
        pono_FINERY[i][0]=task[i]['PONO']
        pono_FINERY[i][1]=task[i]['FINERY_PATH_ID']
    list_i_j_PATH_ID=[[blank  for col in range(all_reality_FINERY_PATH_ID_NUM)] for row in range(task_len)]    
    list_FINERY_qian=[] 
    list_FINERY_hou=[]
    for i in range(len(ALL_PATH_ID_list)):
        if FINERY_PATH_ID_list[0]==ALL_PATH_ID_list[i]:
            FINERY_begin=i
        if FINERY_PATH_ID_list[len(FINERY_PATH_ID_list)-1]==ALL_PATH_ID_list[i]:
            FINERY_end=i     
    for i in range(len(ALL_PATH_ID_list)):
        if i< FINERY_begin:
          list_FINERY_qian.append(ALL_PATH_ID_list[i])
        if i>FINERY_end:
          list_FINERY_hou.append(ALL_PATH_ID_list[i])
    list_pono_fuzhu=[]
    for i in range(task_len): 
        guxu_temp=pono_FINERY[i][1]
        for j in range(FINERY_begin):
            list_i_j_PATH_ID[i][j]=list_FINERY_qian[j]
        for j in range(FINERY_begin,FINERY_begin+len(guxu_temp)):
            list_i_j_PATH_ID[i][j]=guxu_temp[j-FINERY_begin]
        for j in range(FINERY_begin+len(guxu_temp),FINERY_begin+len(guxu_temp)+len(list_FINERY_hou)):
            list_i_j_PATH_ID[i][j]=list_FINERY_hou[j-FINERY_begin-len(guxu_temp)]
        list_pono_fuzhu.append(pono_FINERY[i][0])
    return list_pono_fuzhu, list_i_j_PATH_ID 
#data数据生成文件，输入变量同上有具体解释
def data(task_test,process_time,code_device,transport_time,list_jiaoci_start, list_luci, list_jiaoci_end,list_remove_end,list_pono_cast,list_CC_ID,list_CC_START_TIME,FINERY_PATH_ID_list,ALL_PATH_ID_list,gu_zd,CC_ID_list,all_reality_FINERY_PATH_ID_NUM,blank):
    cast_time=Calculate_continuous_castingtime(task_test,list_jiaoci_start,list_luci)#yang
    #print("cast_time",cast_time)
    fo = open("foo1.dat", "w")
    num=len(list_luci)
    lu=len(list_luci)#
    lu_num=list_luci#炉次的全部集合
   
    fo.write('set I :=')
    for i in range(num):
        fo.write(str(lu_num[i])+" ")
    fo.write(';') 
    list_sb=[]
    for p in lu_num:
        list_sb.append(int(p))
        
    
    fo.write("\n")
    fo.write('set I1 :=')
    jiaoci_begin=list_jiaoci_start
    #num1=0      
    for j in  range(len(jiaoci_begin)):
        fo.write(str(jiaoci_begin[j])+" ")
    fo.write(';')
    
#    fo.write("\n")
#    fo.write('set I7 :=')
#    fo.write(str(-9999))
#    fo.write(';')
    
    
    fo.write("\n")
    fo.write('set I2 :=')
    for j in  range(len(list_remove_end)):
        fo.write(str(list_remove_end[j])+" ")
    fo.write(';')
    
    # #各个浇次末尾炉次算法
    
    fo.write("\n")
    fo.write('set I3 :=')
    for j in  range(len(list_jiaoci_end)-1):#鍑忓幓1鐨勭洰鍦版槸涓轰簡婊¤冻鏈€鍚庝竴涓倝娆℃湯鐢ㄤ笉涓婄殑瑕佹眰
        fo.write(str(list_jiaoci_end[j])+" ")
    fo.write(';')
    fo.write("\n") 
    
    
    DEVICE_ID=[]#宸ュ簭璁惧鍙?
    PROCESS_TIME=[]#宸ュ簭璁惧鍔犲伐鏃堕棿
    for i in range(len(process_time)):
        if process_time[i]['DEVICE_ID'] in DEVICE_ID:
            aaaaaaaaaa=0
        else:
            DEVICE_ID.append(process_time[i]['DEVICE_ID'])
            PROCESS_TIME.append(process_time[i]['PROCESS_TIME'])
    
    jg_time={}#鍚勭宸ュ簭瀵瑰簲鍔犲伐鏃堕棿鈥斺€斿瓧鍏稿舰寮忚〃绀?
    for i in range(len(DEVICE_ID)):
        jg_time[DEVICE_ID[i]]=PROCESS_TIME[i]
    
    
    jiagong_paixu_int=[]#鎸夐『搴忕殑鍔犲伐鎺掑簭鍙?int鍨?
    jiagong_paixu_str=[]#鎸夐『搴忕殑鍔犲伐鎺掑簭鍙?string鍨?
    for i in DEVICE_ID:
        jiagong_paixu_int.append(int(i))
    jiagong_paixu_int.sort()
    for i in jiagong_paixu_int:
        jiagong_paixu_str.append(str(i))
    
    lujing=[[0 for col in range(2)] for row in range(len(gu_zd))]  
    #print("lujing",lujing)
    i=0
    for key in gu_zd:
        lujing[i][0]=str(gu_zd[key])
        lujing[i][1]=str(key)
        i=i+1
    #lujing[len(code_device)][0]='U'
    #lujing[len(code_device)][1]='321'#杩欐槸鍥犱负鏁版嵁搴撶殑闂
    guxu_num=[]
    #all_reality_FINERY_PATH_ID_NUM=,all_reality_FINERY_PATH_ID_NUM,blank
    for i in range(all_reality_FINERY_PATH_ID_NUM):
        guxu_num.append(i)
    
    #print("code_device",lujing)
    guxu_sy=ALL_PATH_ID_list
    guxu_sy1=FINERY_PATH_ID_list
    
    
    
    lujing_x=np.array(lujing)#np  zhuanghuan 
    fo.write('set J :=')
    for i in range(len(guxu_num)):
        fo.write(str(guxu_num[i])+' ')
    fo.write(';')
    fo.write("\n")
    fo.write('set J2 :=')
    for i in range(len(guxu_num)-1):
        fo.write(str(guxu_num[i])+' ')
    fo.write(';')
    fo.write("\n")
    
    fo.write('set J3 :=')
    for i in range(len(guxu_sy)):
        fo.write(str(guxu_sy[i])+' ')
    fo.write(';')
    fo.write("\n")
    
    
    
    list_pono_fuzhu,list_i_j_PATH_ID=i_j_index(task_test,CC_ID_list,all_reality_FINERY_PATH_ID_NUM,FINERY_PATH_ID_list,ALL_PATH_ID_list,blank)
    lu=len(list_pono_fuzhu)
    fo.write('param :M:=')
    fo.write("\n") 
    for i in range(lu):
        for j in range(all_reality_FINERY_PATH_ID_NUM): 
            fo.write(str(list_pono_fuzhu[i])+' '+str(j)+' '+str(list_i_j_PATH_ID[i][j]))
            if i!=lu-1 or j!=all_reality_FINERY_PATH_ID_NUM-1:
                fo.write("\n")
    if i==lu-1 and j==all_reality_FINERY_PATH_ID_NUM-1:
        fo.write(';') 
   
    fo.write("\n")
    
    fo.write('param :M2:=')#每个炉次所对应的最后一道
    fo.write("\n") 
    for i in range(lu):
        for j in range(all_reality_FINERY_PATH_ID_NUM):
            if list_i_j_PATH_ID[i][j]==blank:
                fo.write(str(list_pono_fuzhu[i])+' '+str(j-1))
                if i==lu-1 :
                    fo.write(';')
                fo.write("\n")
                break;
            elif j==all_reality_FINERY_PATH_ID_NUM-1:
                fo.write(str(list_pono_fuzhu[i])+' '+str(j))
                if i==lu-1 :
                    fo.write(';')
                fo.write("\n")
                break; 
   
    
   
    
    
    fo.write('set K :=')
    for i in range(lujing_x.shape[0]):
        fo.write(str(lujing[i][1])+' ')
    fo.write(';')
    fo.write("\n")
    
    
    fo.write('set A :=')
    
    gongxushu=len(guxu_sy)
    for i in range(lu):
        for j in range(gongxushu-1):#zhelide 4 shihuibiande 
            fo.write('('+str(task_test[i]['PONO'])+','+str(guxu_sy[j])+')'+' ') 
    fo.write(';')
    fo.write("\n")
  
    fo.write('set A :=')
    
    gongxushu=len(guxu_sy)
    for i in range(lu):
        for j in range(gongxushu):#zhelide 4 shihuibiande 
            fo.write('('+str(task_test[i]['PONO'])+','+str(guxu_sy[j])+')'+' ') 
    fo.write(';')
    fo.write("\n")
    
    fo.write('set A3 :=')
    
    gongxushu=len(guxu_num)
    for i in range(lu):
        for j in range(gongxushu):#zhelide 4 shihuibiande 
            fo.write('('+str(task_test[i]['PONO'])+','+str(guxu_num[j])+')'+' ') 
    fo.write(';')
    fo.write("\n")
   #这里的加工时间是需要改进的  
   
    list_temp_time=[]#用它的原因是:茅坤论文默认相同工序不同设备加工时间相同,实际不一样.这里我要保证输入输出的加工时间是相同的
    list_temp_time_hang=[]
    
    gongxushu=len(guxu_sy)
    fo.write('param :p:=')
    fo.write("\n") 
    for i in range(lu):      
        for j in range(gongxushu):#zhelide 4 shihuibiande 
            fo.write(task_test[i]['PONO']+' '+guxu_sy[j])
            
            list_temp_time_hang.append(task_test[i]['PONO'])
            list_temp_time_hang.append(guxu_sy[j])
            
            if j!=gongxushu-1:
                for o in range(lujing_x.shape[0]):
                    if lujing[o][0]==guxu_sy[j]:
                        lu_index=o#zheli zhi xuan ze yige 
        
                    for t in range(len(process_time)):
                        if task_test[i]['SG']==process_time[t]['SG'] and  lujing[lu_index][1]==process_time[t]['DEVICE_ID'] :
                            ttt=t
                fo.write(' '+str(process_time[ttt]['PROCESS_TIME']))
                list_temp_time_hang.append(process_time[ttt]['PROCESS_TIME'])
            else:
                i_index=getTwoDimensionListIndex(cast_time,task_test[i]['PONO'])
                fo.write(' '+str(cast_time[i_index][1]))
                list_temp_time_hang.append(cast_time[i_index][1])
            if i!=lu-1 or j!=gongxushu-1:
                fo.write("\n")
                 ###改的地方
            
            if i==lu-1 and j==gongxushu-1:
                fo.write(';')
            
            list_temp_time.append(list_temp_time_hang)
            list_temp_time_hang=[]
    fo.write("\n")
   # print("list_temp_time",list_temp_time)


    time=[]
    gongxu_list=[]
    gongxu_zd={}
    for mm in guxu_sy:
        gongxu_list.append(mm)
    for nnn in gongxu_list:
        for oo in range(lujing_x.shape[0]): 
            if lujing[oo][0]==nnn:
               gongxu_zd[nnn] =lujing[oo][1]
               break;
    
                
    
    
    for i in range(len(transport_time)):
        if (transport_time[i]['START_ID']==str(gongxu_zd[ALL_PATH_ID_list[0]]) and transport_time[i]['END_ID']==str(gongxu_zd[ALL_PATH_ID_list[1]])) or (transport_time[i]['START_ID']==str(gongxu_zd[ALL_PATH_ID_list[1]]) and transport_time[i]['END_ID']==str(gongxu_zd[ALL_PATH_ID_list[2]])) or (transport_time[i]['START_ID']==str(gongxu_zd[ALL_PATH_ID_list[2]]) and transport_time[i]['END_ID']==str(gongxu_zd[ALL_PATH_ID_list[3]])) or(transport_time[i]['START_ID']==str(gongxu_zd[ALL_PATH_ID_list[3]]) and transport_time[i]['END_ID']==str(gongxu_zd[ALL_PATH_ID_list[4]])) or (transport_time[i]['START_ID']==str(gongxu_zd[ALL_PATH_ID_list[4]]) and transport_time[i]['END_ID']==str(gongxu_zd[ALL_PATH_ID_list[5]])):
            time.append(transport_time[i]['TRANSTIME'])
          
    
    
    fo.write("\n")
    fo.write('param T:')
    fo.write("\n")
    fo.write('        ')
    for n in range(1,len(guxu_sy)):
        fo.write(guxu_sy[n]+'  ')
    fo.write(':=')
    
    fo.write("\n")
    
    for i in range(len(guxu_sy)-1):    
        fo.write('     ')
        fo.write(str(guxu_sy[i])+' ')
        for j in range(1,len(guxu_sy)):
            if i>=j:
                fo.write(str(0)+' ')
            else:
                for n in range(len(transport_time)):
                    if (gongxu_zd[guxu_sy[i]]==transport_time[n]['START_ID'] and gongxu_zd[guxu_sy[j]]==transport_time[n]['END_ID'])  :
                        fo.write(str(transport_time[n]['TRANSTIME'])+' ')
        if i==len(guxu_sy)-2:
            fo.write(';') 
        else:
            fo.write("\n")
    jiaoci_beigin_time=[]
    jiaoci_beigin_time1=predict_jiaoci_beigin_time(cast_time,list_CC_START_TIME,list_jiaoci_start,list_luci)
    for i in range(len(jiaoci_beigin_time1)):
        jiaoci_beigin_time.append(jiaoci_beigin_time1[i][1])
   
    #jiaoci_beigin_time=[200,506,200,316,400,500,200,392,546]

    fo.write("\n")
    fo.write('param :d:=')
    fo.write("\n")
    for i in range(len(jiaoci_beigin_time)):
        fo.write('   ')
        fo.write(str(jiaoci_begin[i]))
        fo.write(' ')
        fo.write(str(jiaoci_beigin_time[i]))
        if i==len(jiaoci_beigin_time)-1:
            fo.write(';') 
        else:
            fo.write("\n")
    fo.close() 
    return list_sb,cast_time,list_temp_time

#预计浇次计算函数。输入cast_time是整理后的各个浇次时间，剩下的输入同上意思。输出就是各个浇次预计开浇时间集合
def predict_jiaoci_beigin_time(cast_time,list_CC_START_TIME,list_jiaoci_start,list_luci):
    
    def time_char_to_minute(timeDateStr):#时间转化成‘分’的函数
        time1=datetime.datetime.strptime(timeDateStr,"%Y-%m-%d %H:%M:%S")
        secondsFrom1970=time.mktime(time1.timetuple())
        ticks = time.time()
        time_result=(secondsFrom1970-ticks)/60
        time_result=float('%.2f' % time_result)
        return int(time_result)
    def getTwoDimensionListIndex(L,value): # 
     
        data1 = [data1 for data1 in L if data1[0]==value]  
        index = L.index(data1[0])  
        return index
    #做一个炉次的集合
    jiaoci_beigin_time=[[0 for i in range(2)]for i in range(len(list_jiaoci_start))]
    for i in range(len(list_jiaoci_start)):
        jiaoci_beigin_time[i][0]=list_jiaoci_start[i]
        
    num_cast_predict=0
    num_cast_plan=0
    sum_num=0
    list_CC_START_TIME.append(['0', '0'])
    for i in range(len(list_luci)):
        if list_luci[i]==list_CC_START_TIME[num_cast_predict][0]:
            sum_num=time_char_to_minute(list_CC_START_TIME[num_cast_predict][1])
            jiaoci_beigin_time[num_cast_plan][1]=time_char_to_minute(list_CC_START_TIME[num_cast_predict][1])
            num_cast_predict=num_cast_predict+1
            num_cast_plan=num_cast_plan+1
            index=getTwoDimensionListIndex(cast_time,list_luci[i])
            sum_num=sum_num+(cast_time[index][1])#时间累和
        elif list_luci[i]==list_jiaoci_start[num_cast_plan] and list_luci[i]!=list_CC_START_TIME[num_cast_predict][0]:
            index=getTwoDimensionListIndex(cast_time,list_luci[i])
            jiaoci_beigin_time[num_cast_plan][1]=sum_num+80
            sum_num=sum_num+(cast_time[index][1])+80#时间累和加80是因为换炉子的时间
            
            num_cast_plan=num_cast_plan+1
        else:
            index=getTwoDimensionListIndex(cast_time,list_luci[i])
            sum_num=sum_num+(cast_time[index][1])#时间累和
            
    return jiaoci_beigin_time 
def Dynamic_list(Dynamic_named):
    cc_num=Dynamic_named[0]['CC_ID_NUM']#连铸机数
    FINERY_PATH_ID_NUM=Dynamic_named[0]['FINERY_PATH_ID_NUM']#精炼工序数
    ALL_PATH_ID_NUM=Dynamic_named[0]['ALL_PATH_ID_NUM']#全部工序数
    CC_IDENTIFY=Dynamic_named[0]['CC_IDENTIFY']#区分不同浇次的标志位
    CC_ID_list=[]#连铸机数目
    for i in range(cc_num):
        CC_ID_list.append(str(Dynamic_named[i]['CC_ID']))
    
    FINERY_PATH_ID_list=[]
    for i in range(FINERY_PATH_ID_NUM):
        FINERY_PATH_ID_list.append(str(Dynamic_named[i]['FINERY_PATH_ID']))
    
    ALL_PATH_ID_list=[]
    for i in range(ALL_PATH_ID_NUM):
        ALL_PATH_ID_list.append(str(Dynamic_named[i]['ALL_PATH_ID']))
    
    gu_zd={}#各个设备号所对应的工序
    l=len(Dynamic_named)
    for i in range(l):
        gu_zd[str(Dynamic_named[i]['DEVICE_ID'])]=str(Dynamic_named[i]['NAME'])
    

    all_reality_FINERY_PATH_ID_NUM=Dynamic_named[0]['all_reality_FINERY_PATH_ID_NUM']
    blank=Dynamic_named[0]['blank']
    return gu_zd,FINERY_PATH_ID_list,ALL_PATH_ID_list,CC_ID_list,CC_IDENTIFY,all_reality_FINERY_PATH_ID_NUM,blank

def result_list_to_result(task_test,process_time,list_lie,list_lie2,cast_time,gu_zd,FINERY_PATH_ID_list,ALL_PATH_ID_list,list_temp_time):
    list_result=[]
    result={}
    
#    process_time_len=len(process_time)
#    for i in range(len(list_lie2)):
#        for j in range(len(task_test)):
#            if str(list_lie2[i][0])==str(task_test[j]['PONO']):
#                sg=task_test[j]['SG']
#        for k in range(process_time_len):
#            if str(list_lie2[i][1])==str(process_time[k]['DEVICE_ID']) and str(sg)==str(process_time[k]['SG']):
#               list_lie2[i].append(list_lie2[i][2]+process_time[k]['PROCESS_TIME'])
#               break
#        if (i<len(list_lie2)-1 and list_lie2[i][0]!=list_lie2[i+1][0]) or i==len(list_lie2)-1:
#            for g in range(len(cast_time)):
#                if cast_time[g][0]==str(list_lie2[i][0]):
#                    list_lie2[i].append(list_lie2[i][2]+cast_time[g][1])
    for i in range(len(list_lie2)):
        for j in range(len(list_temp_time)):
            if str(list_lie2[i][0])==str(list_temp_time[j][0]) and str(gu_zd[str(list_lie2[i][1])])==str(list_temp_time[j][1]):
                list_lie2[i].append(list_lie2[i][2]+int(list_temp_time[j][2]))
            


                
        result['Task']=str(list_lie2[i][1])
        result['Start']=str(time_add(list_lie2[i][2]*60))
        result['Finish']=str(time_add(list_lie2[i][3]*60))
        result['Resource']=str(list_lie2[i][0])            
                    
                     
        
        list_result.append(result) 
        result={}
        #result.clear()
            
    #print("list_result",list_lie2)
    
    return list_result
#这部分是主函数，用于调用上诉所有函数，也是外部接口使用的时候所要调用的函数        
def schedule_steel(selected_tasks,process_time,code_device,transport_time,Dynamic_named):
    gu_zd,FINERY_PATH_ID_list,ALL_PATH_ID_list,CC_ID_list,CC_IDENTIFY,all_reality_FINERY_PATH_ID_NUM,blank=Dynamic_list(Dynamic_named)
    list_jiaoci_start, list_luci, list_jiaoci_end,list_remove_end,list_pono_cast,list_CC_ID,list_CC_START_TIME ,selected_tasks=task_pack(selected_tasks,CC_ID_list,CC_IDENTIFY)
    task_inspect(selected_tasks,process_time,code_device,transport_time,ALL_PATH_ID_list)
    task_test=selected_tasks
    #data/文件的写入
    list_sb,cast_time,list_temp_time=data(task_test,process_time,code_device,transport_time,list_jiaoci_start, list_luci, list_jiaoci_end,list_remove_end,list_pono_cast,list_CC_ID,list_CC_START_TIME,FINERY_PATH_ID_list,ALL_PATH_ID_list,gu_zd,CC_ID_list,all_reality_FINERY_PATH_ID_NUM,blank)
   
    jiaoci_beigin_time =predict_jiaoci_beigin_time(cast_time,list_CC_START_TIME,list_jiaoci_start,list_luci)
    #print("list_CC_START_TIME",list_CC_START_TIME)
    
    
    
    
    #模型的计算
    model=model_main(list_sb,list_CC_ID,list_pono_cast,gu_zd,ALL_PATH_ID_list,blank)#调度模型
    #模型的求解
    solver = SolverFactory("gurobi")
    instance = model.create_instance('foo1.dat')
    results = solver.solve(instance,tee=True,keepfiles=False)
    results.write()
  
    #结果输出
    list_hang=[]
    list_lie=[]
    for i in instance.I:
        list_hang.append(i)#濮ｅ繋绔寸悰灞炬付閸氬酣鍋呮稉顏勫帗缁辩姵妲搁悙澶嬵偧
        
        for j in instance.J:
            if instance.M[i,j]!=blank:
                for k in instance.K:                   
                    if instance.x[i,j,k].value==1:
                        
                        list_hang.append(k)
                        list_hang.sort()
        list_lie.append(list_hang.copy())
        list_hang.clear()
    


    list_hang2=[]
    list_lie2=[]#瀵版鍩岄崥鍕嚋瀹搞儱绨惃鍕磻婵濮炲銉︽闂?
    for i in instance.I:
        for j in instance.J:
            if instance.M[i,j]!=blank:
                for k in instance.K:
                   if instance.x[i,j,k].value==1:
                       list_hang2.append(i)
                       list_hang2.append(k)
                       list_hang2.append(instance.t[i,j].value)
                       list_lie2.append(list_hang2.copy())
                       list_hang2.clear()          
    luci_reality=[]
    for i in range(len(list_lie)):
         luci_reality.append(list_lie[i][-1])
    
    #print(list_lie2)
    list_result=result_list_to_result(task_test,process_time,list_lie,list_lie2,cast_time,gu_zd,FINERY_PATH_ID_list,ALL_PATH_ID_list,list_temp_time)#
    #print(task_test)
    
    #return list_result
    return list_result

