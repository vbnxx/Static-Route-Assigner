import requests
import json
import statistics
import ripe.atlas.sagan as rip
import ipaddress
requests.packages.urllib3.disable_warnings()

#asking user for an IP address of the router they currently using
while True:
    try:
        router_ip = ipaddress.ip_address(input("Please enter router IP address: "))
        break
    except ValueError:
        continue

#api url for static routes
api_url_route = "https://{0}/restconf/data/Cisco-IOS-XE-native:native/ip/route/ip-route-interface-forwarding-list".format(router_ip)

headers = { "Accept": "application/yang-data+json",
            "Content-type":"application/yang-data+json"
                }

basicauth = ("cisco", "cisco123!")


#this function takes measurement ID as a parameter, creates dictionary with the contents of the measurement ID and returns the dictionary
def data(mes_id):
    try:
        url = 'https://atlas.ripe.net//api/v2/measurements/{0}/results/?format=json'.format(str(mes_id))
        req = requests.get(url) #calling api 
        dictionarty = {}
        for i in req.json(): 
            dictionarty.update(i)
        return dictionarty
    except:
        print("Error with measurement ID, error code {}".format(req.status_code))
        exit()

#this funtctions creates loopbacks interfaces, based on the ISPs IP addresses from the previous task
def Create_loopbacks():
    ip_end=[1,5,9] #end of IP addresses of the ISPs
    for num in range(3): 
        #interface configuration
        intConf = {
        "ietf-interfaces:interface": {
                "name": "Loopback{0}".format(num+1),
                "description" : "ISP{0}".format(num+1),
                "type": "iana-if-type:softwareLoopback",
                "enabled": True,
                "ietf-ip:ipv4": {
                    "address": [
                                {
                                    "ip": "10.10.10.{0}".format(ip_end[num]),#based on the loop different end is chosen
                                    "netmask": "255.255.255.252"
                                }]
                                    },
                        "ietf-ip:ipv6": {}
                    }
                    }
        
        api_url = "https://{0}/restconf/data/ietf-interfaces:interfaces/interface=Loopback{1}".format(router_ip,num+1)
        #sending updates to the router
        resp = requests.patch(api_url, data=json.dumps(intConf), auth=basicauth, headers=headers, verify=False)
        if(resp.status_code >= 200 and resp.status_code <= 299):
            print("STATUS OK: {}".format(resp.status_code))
        else:
            print("Error code {}, reply: {}".format(resp.status_code, resp.json()))

#this function  creates static routes, based on destination IP and loopback number parameters 
def Create_stat_route(dest_ip,loopback_num):
    #in the next 5 lines I'm taking destination ip from the measurement ID and convering it into network address, I assume that the subnet mask for each IP address is /24
    x = dest_ip.split(".")
    x.pop()
    x.append("0")
    dest_ip=" ".join(x)
    dest_ip = dest_ip.replace(" ",".")
    #static route configuration
    statConf = {
                "Cisco-IOS-XE-native:ip-route-interface-forwarding-list":[
                        {
                        "prefix": "{0}".format(dest_ip),
                        "mask" : "255.255.255.0",
                        #measurement with the least RTT is a desired static route, then I'm checking RTT between the other two creating two additional floating routes with administrative distance successively: 5 and 10   
                        "fwd-list":[
                            {
	                        "fwd":"Loopback{0}".format(loopback_num[0])
                            },
                            {
                                "fwd":"Loopback{0}".format(loopback_num[1]),
                                "metric" : 5
                            },
                            {
                                "fwd":"Loopback{0}".format(loopback_num[2]),
                                "metric" : 10
                            }
                            
                        ]
                    }
                    ]   
                }   
    api_url = "https://{0}/restconf/data/Cisco-IOS-XE-native:native/ip/route/ip-route-interface-forwarding-list".format(router_ip)
    #sending configuration to the router
    resp = requests.patch(api_url_route, data=json.dumps(statConf), auth=basicauth, headers=headers, verify=False)
    if(resp.status_code >= 200 and resp.status_code <= 299):
        print("STATUS OK: {}".format(resp.status_code))
    else:
        print("Error code {}, reply: {}".format(resp.status_code, resp.json()))

#additional function to print static routes configuration
def print_static_routes():
    resp = requests.get(api_url_route, auth=basicauth, headers=headers, verify=False)
    response_json = resp.json()
    print(json.dumps(response_json, indent=4))

#addiational function to print main menu and return option chosen by a user
def main_menu():
    start=int(input("What would you like to do today?\n1)Configure static routes\n2)Print static routes on the router\n3)Exit\n"))
    return start

#main function
def main():
    while True:
        option = main_menu()
        #1st option creates static routes
        if option==1:

            #user inputs 3 measurement IDs int() allows to input only integer values
            input1= int(input("Enter first mesurment id: "))
            input2= int(input("Enter second mesurment id: "))
            input3 = int(input("Enter third mesurment id: "))

            #3 dictionaries are created
            data_info1 = data(input1)
            data_info2 = data(input2)
            data_info3 = data(input3)
            
            #from each dictionary i take measurement name to find out what kind of query they contain
            measurments = [data_info1["msm_name"],data_info2["msm_name"],data_info3["msm_name"]]

            #if all of them are ping then:
            if all(name=="Ping" for name in measurments):
	            
                #creating loopback interfaces
                Create_loopbacks()

                #for each measurement labeled with the number (1,2,3), I'm retrieving data about ping: destination IP and average RTT
                result1 = rip.PingResult(data_info1)
                dest_ip1= result1.destination_address
                rtt1=result1.rtt_average
                print(rtt1)
                result2 = rip.PingResult(data_info2)
                dest_ip2 = result2.destination_address
                rtt2=result2.rtt_average
                print(rtt2)
                result3 = rip.PingResult(data_info3)
                dest_ip3 = result3.destination_address
                rtt3=result3.rtt_average
                print(rtt3)

                #rtt1 is the least:
                if (rtt1 < rtt2 and rtt1 < rtt3):
                    #rtt2 is less than rtt3
                    if rtt2<rtt3:
                        #create static route to customer via ISP1 (lookback1), floating route via ISP2 (lookback2) with administrative distance 5 and floating route via ISP3 (lookback3) with administrative distance 10
                        Create_stat_route(dest_ip1,[1,2,3])
                    #rtt3 is less than rtt2
                    else:
                        #create static route to customer via ISP1 (lookback1), floating route via ISP3 (lookback2) with administrative distance 5 and floating route via ISP2 (lookback2) with administrative distance 10
                        Create_stat_route(dest_ip1, [1,3,2])
                
                #rtt2 is the least
                elif (rtt2 < rtt3 and rtt2<rtt1):
                    #rtt1 is less than rtt3
                    if rtt1<rtt3:
                        #create static route to customer via ISP2 (lookback2), floating route via ISP1 (lookback1) with administrative distance 5 and floating route via ISP3 (lookback3) with administrative distance 10
                        Create_stat_route(dest_ip2,[2,1,3])
                    #rtt3 is less than rtt1
                    else:
                        #create static route to customer via ISP2 (lookback2), floating route via ISP3 (lookback3) with administrative distance 5 and floating route via ISP1 (lookback1) with administrative distance 10
                        Create_stat_route(dest_ip2,[2,3,1])
                
                #rtt3 is the least
                else:
                    #rtt1 is less than rtt2
                    if rtt1<rtt2:
                        #create static route to customer via ISP3 (lookback3), floating route via ISP1 (lookback1) with administrative distance 5 and floating route via ISP2 (lookback2) with administrative distance 10
                        Create_stat_route(dest_ip3,[3,1,2])
                    #rtt2 is less than rtt1
                    else:
                        #create static route to customer via ISP3 (lookback3), floating route via ISP2 (lookback2) with administrative distance 5 and floating route via ISP1 (lookback1) with administrative distance 10
                        Create_stat_route(dest_ip3,[3,2,1])
                
                #print static route
                print_static_routes()

            #all of the measurement names are Traceroute
            elif all(name=="Traceroute" for name in measurments):
                
                #creating loopback interfaces
                Create_loopbacks()

                #for each measurement labeled with the number (1,2,3), I'm retrieving data about traceroute: destination IP and average RTT, but since traceroute can have many rtt in each hop it makes it more complex to retrieve average RTT, which I'm explaining in a word document
                result1 = rip.TracerouteResult(data_info1)
                dest_ip1=result1.destination_address
                hops1=result1.hops
                medians_rtt1=sorted([i.median_rtt for i in hops1 if i.median_rtt!=None])
                result2 = rip.TracerouteResult(data_info2)
                dest_ip2=result2.destination_address
                hops2=result2.hops
                medians_rtt2=sorted([i.median_rtt for i in hops2 if i.median_rtt!=None])
                result3 = rip.TracerouteResult(data_info3)
                dest_ip3=result3.destination_address
                hops3=result3.hops
                medians_rtt3=sorted([i.median_rtt for i in hops3 if i.median_rtt!=None])
                median_rtt1 = statistics.median(medians_rtt1)
                median_rtt2 = statistics.median(medians_rtt2)
                median_rtt3 = statistics.median(medians_rtt3)
                
                #rtt1 is the least
                if (median_rtt1 < median_rtt2 and median_rtt1 < median_rtt3):
                    #rtt2 is less than rtt3
                    if median_rtt2<median_rtt3:
                        #create static route to customer via ISP1 (lookback1), floating route via ISP2 (lookback2) with administrative distance 5 and floating route via ISP3 (lookback3) with administrative distance 10
                        Create_stat_route(dest_ip1,[1,2,3])
                    #rtt3 is less than rtt2
                    else:
                        #create static route to customer via ISP1 (lookback1), floating route via ISP3 (lookback3) with administrative distance 5 and floating route via ISP2 (lookback2) with administrative distance 10
                        Create_stat_route(dest_ip1, [1,3,2])
                
                #rtt2 is the least
                elif (median_rtt2 < median_rtt3 and median_rtt2<median_rtt1):
                    #rtt1 is less than rtt3
                    if median_rtt1<median_rtt3:
                        #create static route to customer via ISP2 (lookback2), floating route via ISP1 (lookback1) with administrative distance 5 and floating route via ISP3 (lookback3) with administrative distance 10
                        Create_stat_route(dest_ip2,[2,1,3])
                    else:
                        #create static route to customer via ISP2 (lookback2), floating route via ISP3 (lookback3) with administrative distance 5 and floating route via ISP1 (lookback1) with administrative distance 10
                        Create_stat_route(dest_ip2,[2,3,1])
                
                #rtt3 is the least
                else:
                    #rtt1 is less than rtt2
                    if median_rtt1<median_rtt2:
                        #create static route to customer via ISP3 (lookback3), floating route via ISP1 (lookback1) with administrative distance 5 and floating route via ISP2 (lookback2) with administrative distance 10
                        Create_stat_route(dest_ip3,[3,1,2])
                    #rtt2 is less than rtt1
                    else:
                        #create static route to customer via ISP3 (lookback3), floating route via ISP2 (lookback2) with administrative distance 5 and floating route via ISP1 (lookback1) with administrative distance 10
                        Create_stat_route(dest_ip3,[3,2,1])
                
                #print static route
                print_static_routes()

            #if at least one of the measurement names is: DNS, HTTP or SSL error message is printed 
            elif ("DNS" in measurments) or ("SSL" in measurments) or ("HTTP" in measurments):
                print("Sorry we do not support this type of measurments. \n")
            
            #if all of the names aren't the same (e.g Ping,Ping, Traceroute or Ping, Traceroute, Traceroute) error message is printed 
            else:
                print("We require all of the measurments to be the same to create static routes, please enter ID measurments again.\n")
        
        #2nd option prints static routes
        elif option == 2:
            print_static_routes()
        
        #3rd option exits the program
        elif option == 3:
            break
        
        else:
            print("Please choose the correct option\n")
        

if __name__=="__main__":
    main()
