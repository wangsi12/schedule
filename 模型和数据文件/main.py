import json
import schedule
import time
from draw import draw_gantt

#load data from json file 
InputDataPath='./InputDataFiles/'
with open(InputDataPath+'staic_plan_cc.json', encoding="utf8") as f:
    plan_cc = json.load(f)
    
with open(InputDataPath+'public_rule_process_time.json', encoding="utf8") as f:
    rule_process_time = json.load(f)    
    
with open(InputDataPath+'public_code_device.json', encoding="utf8") as f:
    rule_code_device = json.load(f)
    
with open(InputDataPath+'public_rule_transport_time.json', encoding="utf8") as f:
    rule_transport_time = json.load(f)

with open(InputDataPath+'Dynamicnamed.json', encoding="utf8") as f:
    Dynamic_named = json.load(f)



#print(plan_pre_cc)

#selected_tasks = plan_pre_cc[0:20] #杩欎釜灏辨槸浼犲叆鐨則ask4 8 13 15
selected_tasks = plan_cc
process_time = rule_process_time
code_device = rule_code_device
transport_time = rule_transport_time
#print(transport_time)
#print(process_time)

#print(code_device)
#print(process_time)
start = time.clock()
schedule_result = schedule.schedule_steel(selected_tasks,process_time,code_device,transport_time,Dynamic_named)
#print(schedule_result)
end = time.clock()
#for i in range(len(schedule_result)):
#    print(schedule_result[i])
#schedule_result = schedule.schedule(tasks)
#list_temp=['263421','279961','263582','263758','263759','263827']
#for i in range(len(schedule_result)):
#    if schedule_result[i]['Task']=='502':
#        print(schedule_result[i])
#draw_gantt(schedule.schedule_steel1(selected_tasks))
draw_gantt(schedule_result)


