
############################################
# IT WORKS BUT STILL NEEDS SOME ADJUSTMENTS#
############################################

import json
import os 


script_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(script_dir, "intent.json")

with open(file_path, "r") as file:
    intent = json.load(file)

def get_as_number(as_name):
    return 1 if as_name == "AS_X" else 2

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
            config.append(f" neighbor {ibgp['neighbor']} remote-as {get_as_number(ibgp['remote-as'])}")
        if "ebgp" in bgp_config:
            for ebgp in bgp_config["ebgp"]:
                config.append(f" neighbor {ebgp['neighbor']} remote-as {get_as_number(ebgp['remote-as'])}")
        config.append("!")


        config.append("address-family ipv6")
        if "ebgp" in bgp_config:
            config.append(f" network ") #to change not sure about placement
            for ebgp in bgp_config["ebgp"]:
                config.append(f" neighbor {ebgp['neighbor']} activate")
        for ibgp in bgp_config['ibgp']:
            config.append(f" neighbor {ibgp['neighbor']} activate")
        config.append("exit-address-family")
        config.append("!")
    
    if "ebgp" in bgp_config:
        config.append(f"ipv6 router ospf {router_data['protocols']['process-id']}")
        config.append(f" router-id {router_data['router-id']}")
    
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