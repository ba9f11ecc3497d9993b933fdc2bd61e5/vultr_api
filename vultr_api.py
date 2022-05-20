#!/usr/bin/python3

#####################
#####  imports  #####
#####################

import requests
import json
import time
import sys
from tabulate import tabulate

##############################
#####  global variables  #####
##############################

base_url = "https://api.vultr.com"
api_token = XXXXXXXXXXXXXXXXXXXXXXXXXXX"
headers = {'Authorization': 'Bearer ' + api_token}
sshkey_id = ["XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX"]

#######################
#####  functions  #####
#######################

def help():
    print("")
    print("Usage: vultr_api.py [OPTION]")
    print("")
    print("\t-lcs\t--list-current-servers")
    print("\t-lo\t--list-os")
    print("\t-lr\t--list-regions")
    print("\t-lp\t--list-plans")
    print("\t-di\t--deploy-interactive")
    print("\t-Di\t--Destroy-interactive")
    print("")
    
def list_os():
    endpoint = "/v2/os"
    request = requests.get(base_url + endpoint, headers=headers)
    os_master_list = []
    oses = request.json()
    for os in oses['os']:
        os_list = []
        os_list.append(os['id'])
        os_list.append(os['name'])
        os_master_list.append(os_list)
    print(tabulate(os_master_list, headers=["id","name"], tablefmt="grid"))

def list_regions():
    endpoint = "/v2/regions"
    request = requests.get(base_url + endpoint, headers=headers)
    region_master_list = []
    regions = request.json()
    for region in regions['regions']:
        region_list = []
        region_list.append(region['id'])
        region_list.append(region['city'])
        region_master_list.append(region_list)
    print(tabulate(region_master_list, headers=["id","city"], tablefmt="grid"))

def list_plans():
    endpoint = "/v2/plans"
    request = requests.get(base_url + endpoint, headers=headers)
    plans_master_list = []
    plans = request.json()
    for plan in plans['plans']:
        if plan['type'] == "vc2":
            plans_list = []
            plans_list.append(plan['id'])
            plans_list.append(plan['vcpu_count'])
            plans_list.append(plan['ram'])
            plans_list.append(plan['disk'])
            plans_list.append(plan['bandwidth'])
            plans_list.append(plan['monthly_cost'])
            plans_list.append(','.join(plan['locations']))
            plans_master_list.append(plans_list)
    print(tabulate(plans_master_list, headers=["id","vcpu_count","ram","disk size","bandwidth","monthly_cost","locations"], tablefmt="grid"))

def list_current_servers():
    endpoint = "/v2/instances"
    request = requests.get(base_url + endpoint, headers=headers)
    current_servers_master_list = []
    current_servers = request.json()
    for current_server in current_servers['instances']:
        current_server_list = []
        current_server_list.append(current_server['id'])
        current_server_list.append(current_server['hostname'])
        current_server_list.append(current_server['os'])
        current_server_list.append(current_server['ram'])
        current_server_list.append(current_server['disk'])
        current_server_list.append(current_server['main_ip'])
        current_server_list.append(current_server['vcpu_count'])
        current_server_list.append(current_server['region'])
        current_server_list.append(current_server['power_status'])
        current_server_list.append(current_server['server_status'])
        current_server_list.append(current_server['v6_main_ip'])
        current_servers_master_list.append(current_server_list)
    print(tabulate(current_servers_master_list, headers=["id","hostname","os","ram","disk size","ipv4","vcpu_count","region","power_status","server_status","ipv6"], tablefmt="grid"))

def configure_instance():
    enable_ipv6 = True
    instance_details = {}
    should_enable_ipv6_question = "enable_ipv6? [Y/n] : "
    should_enable_ipv6_answer = input(should_enable_ipv6_question)
    if should_enable_ipv6_answer:
        if should_enable_ipv6_answer == "n":
            enable_ipv6 = False
    add_hostname = "add a hostname to this server : "
    hostname = input(add_hostname)
    add_label = "add a label to this server : "
    label = input(add_label)
    add_reverse_dns = "add a reverse dns to this server : "    
    global reverse_dns
    reverse_dns = input(add_reverse_dns)
    list_os()
    select_os = "select os by id : "
    os_choice = input(select_os)
    list_regions()
    select_region = "select region by id : "
    region_choice = input(select_region)
    list_plans()
    select_plan = "select plan by id : "
    plan_choice = input(select_plan)
    instance_details["sshkey_id"] = sshkey_id
    instance_details["enable_ipv6"] = enable_ipv6
    instance_details["hostname"] = hostname
    instance_details["label"] = label
    instance_details["os_id"] = os_choice
    instance_details["region"] = region_choice
    instance_details["plan"] = plan_choice
    return instance_details

def create_reverse_dns(instance_id, endpoint, ipv6_found):
    print("instance : " + instance_id + " is ready, creating reverse dns")
    instance_v4_request = requests.get(base_url + endpoint + '/' + instance_id + '/ipv4', headers=headers)
    instance_v4_details = instance_v4_request.json()
    instance_ipv4 = instance_v4_details['ipv4s'][0]['ip']
    if ipv6_found:
        instance_v6_request = requests.get(base_url + endpoint + '/' + instance_id + '/ipv6', headers=headers) 
        instance_v6_details = instance_v6_request.json()
        instance_ipv6 = instance_v6_details['ipv6s'][0]['ip']
        
        
    instance_rev_ipv4 = {
        "ip" : instance_ipv4,
        "reverse" : reverse_dns
    }
    
    if ipv6_found:
        instance_rev_ipv6 = {
            "ip" : instance_ipv6,
            "reverse" : reverse_dns
        }
        
    instance_ipv4_reverse_request = requests.post(base_url + endpoint + '/' + instance_id + '/ipv4/reverse', data=json.dumps(instance_rev_ipv4), headers=headers)
    
    if ipv6_found:
        instance_ipv6_reverse_request = requests.post(base_url + endpoint + '/' + instance_id + '/ipv6/reverse', data=json.dumps(instance_rev_ipv6), headers=headers)
        return instance_ipv4, instance_ipv6, reverse_dns, reverse_dns
    else:
        return instance_ipv4, reverse_dns
    
def create_instance():
    endpoint = "/v2/instances"
    instance_details = configure_instance()
    create_instance_request = requests.post(base_url + endpoint, data=json.dumps(instance_details), headers=headers)
    instance_creation_details = create_instance_request.json()
    instance_id = instance_creation_details['instance']['id']
    while True :
        # query instance status
        instance_request = requests.get(base_url + endpoint + '/' + instance_id, headers=headers)
        created_instance_details = instance_request.json()
        # wait for the instance to be fully populated
        if created_instance_details['instance']['status'] == "pending":
            print("instance : " + instance_id + " still creating, waiting...")
            time.sleep(2)
            continue
        else:
            ipv6_found = created_instance_details['instance']['v6_main_ip']
            reverse_dns_result = create_reverse_dns(instance_id, endpoint, ipv6_found)
            master_reverse_dns_list = []
            master_reverse_dns_list.append(reverse_dns_result)
            if ipv6_found:
                print(tabulate(master_reverse_dns_list, headers=["ipv4 address","ipv6 address","ipv4 reverse dns","ipv6 reverse dns"], tablefmt="grid"))
                print("all done.")
                break
            else:
                print(tabulate(master_reverse_dns_list, headers=["ipv4 address", "ipv4 reverse dns"], tablefmt="grid"))
                break

def delete_instance():
    endpoint = "/v2/instances"
    del_instance = "enter the id of the instance to delete : "
    instance_id = input(del_instance)    
    instance_deletion = requests.delete(base_url + endpoint + '/' + instance_id, headers=headers)
    if instance_deletion.status_code == 204:
        print("instance " + instance_id + " deleted.")

####################
#####  script  #####
####################

if len(sys.argv) == 1:
    help()
    sys.exit(0)
elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
    help()
    sys.exit(0)
elif sys.argv[1] == "-lo" or sys.argv[1] == "--list-os":
    list_os()
    sys.exit(0)
elif sys.argv[1] == "-lr" or sys.argv[1] == "--list-regions":
    list_regions()
    sys.exit(0)
elif sys.argv[1] == "-lp" or sys.argv[1] == "--list-plans":
    list_plans()
    sys.exit(0)
elif sys.argv[1] == "-lcs" or sys.argv[1] == "--list-current-servers":
    list_current_servers()
    sys.exit(0)
elif sys.argv[1] == "-di" or sys.argv[1] == "--deploy-interactive":
    create_instance()
    sys.exit(0)
elif sys.argv[1] == "-Di" or sys.argv[1] == "--Destroy-interactive":
    delete_instance()
    sys.exit(0)
else:
    print("Invalid command")
    sys.exit(1)
