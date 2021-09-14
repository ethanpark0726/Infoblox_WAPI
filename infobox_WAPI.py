from ast import copy_location
import requests
import urllib3
import json
import pprint
from cfonts import render
import credentials

auth = (prod_server_id, prod_server_pw)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def formatMAC(mac):
    """Infoblox only supports MAC format with colon-delimeted (xx:xx:xx:xx:xx:xx) when searching
       This method normalize the MAC address

    """
    new_mac = str()

    if mac[2] != ':':
        if mac[2] == '-':
            new_mac = mac.replace('-', ':')
        elif mac[2] == '.':
            new_mac = mac.replace('.', ':')
            
        # 1111.2222.3333
        # 111122223333
        else:
            if len(mac) != 12:
                temp = mac.split('.')
                
                for elem in temp:
                    new_mac += elem[0:2] + ':' + elem[2:4] + ':'
            
            else:
                for i in range(0, len(mac), 4):
                    new_mac += mac[i:i + 2] + ':' + mac[i + 2:i + 4] + ':'
            new_mac = new_mac[0:-1]
    else:
        new_mac = mac

    return new_mac

def removeMACFilterAddress(mac_list):
    """Remove MAC address from the IPAM
       Infoblox Menu: Data Management >> DHCP >> IPv4 Filters

       Handling multiple MAC address removal
    """
    for mac in mac_list:

        r = requests.get(f'{prod_server}macfilteraddress?mac={formatMAC(mac)}', auth=auth, \
            verify=False, headers=headers)

        returnData = json.loads(r.text)
        
        if len(returnData) < 1:
            print("The MAC address is not existed")
            return
        
        for elem in returnData:
            ref_object = elem.get('_ref')
            r = requests.delete(f'{prod_server}{ref_object}/mac={mac}', auth=auth, \
                verify=False, headers=headers)

            if r.status_code == 200:
                print("MAC has been removed!")
            else:
                print("The operation has not been completed!")

def removeIPv4Address(ipv4address_list):
    """Remove ipv4address from the IPAM
       Infoblox Menu: Data Management >> IPAM

       Can be removed either Fixed Address or Reservation
       Associated records are also purged (e.g. A record, host record)
    """
    print("---- Associated DNS record will be removed as well")
    for ipv4address in ipv4address_list:
        r = requests.get(f'{prod_server}ipv4address?ip_address={ipv4address}', auth=auth, \
            verify=False, headers=headers)
        
        returnData = json.loads(r.text)
        
        if len(returnData) < 1:
            print("The ipv4address is not existed")
            return

        for elem in returnData:
            ref_object = elem.get('_ref')
            r = requests.delete(f'{prod_server}{ref_object}/ip_address={ipv4address}', auth=auth, \
                verify=False, headers=headers)

        if r.status_code == 200:
            print("ipv4address has been removed!")
        else:
            print("The operation has not been completed!")

def assignFixedAddress(mac, network, name="", comment=""):
    """Assign a Fixed IP address to the IPAM
       network parameter can be either a.b.c.d/y or a.b.c.d

    """

    for elem in mac:
        data = {
            "ipv4addr": {
                "_object_function": "next_available_ip",
                "_object": "network",
                "_object_parameters": {"network": network},
                "_result_field": "ips",
            },
            "mac": elem,
            "name": name,
            "comment": comment
        }

        r = requests.post(f'{prod_server}fixedaddress?_return_fields%2B=ipv4addr', auth=auth, json=data, \
            verify=False, headers=headers)
        
        if r.status_code == 201:
            print(f"Assigned IP address: {json.loads(r.text).get('ipv4addr')}")
        elif r.status_code == 400:
            print(json.loads(r.text).get('text'))    

def updateSecurityZone(mac, securityZone):
    """Update a securityZone which is one of extensible attributes

    """
    data = {
        "extattrs": {
            "Security Zone": {"value": securityZone},
        },
    }

    for elem in mac:
        r = requests.get(f'{prod_server}macfilteraddress?mac={formatMAC(elem)}&_return_fields%2B=extattrs', \
            auth=auth, verify=False, headers=headers)
        
        returnData = json.loads(r.text)
        ref_object = returnData[0].get('_ref')
        r = requests.put(f'{prod_server}{ref_object}/mac={formatMAC(elem)}?_return_fields%2B=extattrs', \
            auth=auth, json=data, verify=False, headers=headers)

        print("Updated to => ", json.loads(r.text).get('extattrs').get('Security Zone').get('value'))

def createARecord(ARecord, ipv4addr, view):
    """Create a A Record along with a PTR Record
       view: Internal, External, UFCampus

    """
    data = {
        "name": ARecord,
        "view": view,
        "ipv4addr": ipv4addr
    }
    r = requests.post(f'{prod_server}record:a?_return_fields%2B=name,ipv4addr,view', auth=auth, json=data, \
        verify=False, headers=headers)

    pprint.pprint(r.text)
    ptr_data = {
        "name": '.'.join(ipv4addr.split('.')[::-1]),
        "ptrdname": ARecord,
        "ipv4addr": ipv4addr
    }
    r = requests.post(f'{prod_server}record:ptr?_return_fields%2B=name,ptrdname,ipv4addr', auth=auth, json=ptr_data, \
        verify=False, headers=headers)
    pprint.pprint(r.text)

def createReservationIPAddress(network, name="", comment=""):
    pass
def createCNAMERecord(canonical, name, view):
    pass
def removeCNAMERecord(canonical, name, view):
    pass
def updatesecurityZone(securityZone):
    pass
def createNetworkPermission():
    pass

if __name__ == '__main__':

    #mac = ['BC-C3-42-CD-93-15']
    #removeMACFilterAddress(mac)
    #network = "10.14.239.0"
    assignFixedAddress(["8cdcd46167b2"], "10.14.82.0", name="HP printer")
    #createARecord("pythonAPITest.shands.ufl.edu", "10.25.3.69", "Internal")
    #removeIPv4Address(['10.7.11.131'])
    
    # ipv4addr = '10.7.11.170'
    # r = requests.get(f'{prod_server}record:host?ipv4addr={ipv4addr}&_return_fields%2B=name', \
    #     auth=auth, verify=False, headers=headers)
    
    # pprint.pprint(len(json.loads(r.text)))
    
    # print("Enter the MAC: ")
    # mac = input()
    # print("Network with subnet bit")
    # network = input()
    

    #createARecord("pythonAPITest.shands.ufl.edu", "10.25.3.69", "Internal")
    # ipv4 = '10.15.96.21'
    # r = requests.get(f'{prod_server}ipv4address?ip_address={ipv4}', auth=auth, \
    #     verify=False, headers=headers)
    
    # return_data = json.loads(r.text)[0].get('_ref')
    # r = requests.delete(f'{prod_server}{return_data}/ip_address={ipv4}', auth=auth, \
    #         verify=False, headers=headers)

    # pprint.pprint(r.text) 
    
    #output = render("ezIPAM", font='3d', colors=('candy', 'candy'), align='center', line_height=5)
    #print(output)

    #updateSecurityZone(["e865.49fd.9fa8"],"WAP (RESERVED)")
    
    #simple-term-menu 