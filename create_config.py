import json
import os 


script_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(script_dir, "intent.json")

with open(file_path, "r") as file:
    intent = json.load(file)

def get_as_number(as_name): 
    return 1 if as_name == "AS_X" else 2

def get_as_name(as_number):
    return "AS_X" if as_number == 1 else "AS_Y"

def find_router_name(ip, remote_as, structure=intent):
    as_name = get_as_name(remote_as)
    index = 0 if as_name == "AS_X" else 1
    for router, details in structure['network'][index][get_as_name(remote_as)]['routers'].items():
        for interface, addr in details['interfaces'].items():
            if ip == addr.split("/")[0]:
                return router
    return None

def create_config(router_name, router_data, as_name):
    config = []
    as_number = get_as_number(as_name)
    config.append(f"!\nhostname {router_name}")
    config.append("!")
    config.append("no ip domain lookup")
    config.append("ipv6 unicast-routing")
    config.append("ipv6 cef")
    config.append("!")


    for interface, ipv6_address in router_data["interfaces"].items():
        config.append(f"interface {interface}")
        config.append(" no ip address")
        config.append(" negotiation auto")
        config.append(f" ipv6 address {ipv6_address}")
        config.append(" ipv6 enable")
        if router_data["protocols"].get("ripng"):
            config.append(f" ipv6 rip {router_data['protocols']['process-id']} enable")
        if "ospf" in router_data["protocols"]:
            config.append(f" ipv6 ospf {router_data['protocols']['process-id']} area {0} ")
        config.append("!")
    
    # If RIP enabled
    
    if router_data["protocols"].get("ripng"):
        config.append(f"ipv6 router rip {router_data['protocols']['process-id']}")
        config.append(" redistribute connected")
        config.append("!")
    
    # For BGP config
    
    
    bgp_config = router_data['protocols'].get("bgp", {})

    if "ibgp" in bgp_config:
        config.append(f"router bgp {as_number}")
        config.append(f" bgp router-id {router_data['router-id']}")
        config.append(" bgp log-neighbor-changes")
        config.append(" no bgp default ipv4-unicast")
        for ibgp in bgp_config["ibgp"]:
            config.append(f" neighbor {ibgp['neighbor']} remote-as {ibgp['remote-as']}")
            config.append(f" neighbor {ibgp['neighbor']} update-source {ibgp['interface']}")
        if "ebgp" in bgp_config:
            for ebgp in bgp_config["ebgp"]:
                config.append(f" neighbor {ebgp['neighbor']} remote-as {ebgp['remote-as']}")
                config.append(f" neighbor {ebgp['neighbor']} description Connection to {find_router_name(ebgp['neighbor'], ebgp['remote-as'])} in AS {ebgp['remote-as']}")
        config.append("!")


        config.append("address-family ipv6")
        if "ebgp" in bgp_config:
            if "advertise" in bgp_config['ebgp'][0]:
                for net in bgp_config['ebgp'][0]['advertise']:
                    config.append(f" network {net}") 
            for ebgp in bgp_config["ebgp"]:
                config.append(f" neighbor {ebgp['neighbor']} activate")
        for ibgp in bgp_config['ibgp']:
            config.append(f" neighbor {ibgp['neighbor']} activate")
        if "ebgp" in bgp_config:
            for rule in bgp_config["ebgp"][0]["prefix-lists"]:
                if rule == "inbound":
                    config.append(f"neighbor {bgp_config['ebgp'][0]['neighbor']} prefix-list {bgp_config['ebgp'][0]['prefix-lists']['inbound']['name']} in")
                if rule == "outbound":
                    config.append(f"neighbor {bgp_config['ebgp'][0]['neighbor']} prefix-list {bgp_config['ebgp'][0]['prefix-lists']['outbound']['name']} out")
        config.append("exit-address-family")
        config.append("!")
    
    if as_name == "AS_Y":
        config.append(f"ipv6 router ospf {router_data['protocols']['process-id']}")
        config.append(f" router-id {router_data['router-id']}\n!")
    

    if "ebgp" in bgp_config:
            for rule in bgp_config["ebgp"][0]["prefix-lists"]:
                if rule == "inbound":
                    config.append(f"ipv6 prefix-list {bgp_config['ebgp'][0]['prefix-lists']['inbound']['name']} seq {bgp_config['ebgp'][0]['prefix-lists']['inbound']['rules'][0]['seq']} {bgp_config['ebgp'][0]['prefix-lists']['inbound']['rules'][0]['action']} {bgp_config['ebgp'][0]['prefix-lists']['inbound']['rules'][0]['prefix']} ")
                if rule == "outbound":
                    config.append(f"ipv6 prefix-list {bgp_config['ebgp'][0]['prefix-lists']['outbound']['name']} seq {bgp_config['ebgp'][0]['prefix-lists']['outbound']['rules'][0]['seq']} {bgp_config['ebgp'][0]['prefix-lists']['outbound']['rules'][0]['action']} {bgp_config['ebgp'][0]['prefix-lists']['outbound']['rules'][0]['prefix']} ")

    
    config.append("!\nend")
    return "\n".join(config)

def main():
    os.makedirs("config_files", exist_ok=True) # will make the folder if it doesn't exist
    for as_data in intent['network']:
        for as_name, content in as_data.items():
            for router_name, router_data in content["routers"].items():
                config = create_config(router_name, router_data, as_name)
                output = os.path.join("config_files", f"{router_name}_startup.cfg")
                with open(output, "w") as config_file:
                    config_file.write(config) 
                print(f"Generated config file for {router_name} at {output}")

main()