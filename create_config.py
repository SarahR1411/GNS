
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
    config.append(f"hostname {router_name}")
    config.append("ipv6 unicast-routing")
    config.append("ipv6 cef")


    for interface, ipv6_address in router_data["interfaces"].items():
        config.append(f"interface {interface}")
        config.append(f" ipv6 address {ipv6_address}")
        config.append(" ipv6 enable")
        config.append("!")
    
    # If RIP enabled
    
    if router_data["protocols"].get("ripng"):
        config.append(f"ipv6 router rip {router_name}")
        config.append(" redistribute connected")
    
    # If OSPF enabled

    if "ospf" in router_data["protocols"]:
        ospf_config = router_data["protocols"]["ospf"]
        config.append(f"ipv6 router ospf {ospf_config['process-id']}")
        config.append(f" router-id {ospf_config['router-id']}")
        for net, settings, in ospf_config.get("networks", {}).items():
            config.append(f" network {net} area {settings['area']}")
        config.append("!")

        for interface in router_data["interfaces"].keys():
            config.append(f"interface {interface}")
            config.append(f" ipv6 ospf {ospf_config['process-id']} area {0}") 
            config.append("!")
    
    # For BGP config
    
    if as_name == "AS_X": #There's a slight difference in structure between AS_X and AS_Y in the intent file
        bgp_config = router_data['protocols'].get("bgp", {})
        if "ibgp" in bgp_config:
            config.append(f"router bgp {as_number}")
            for ibgp in bgp_config["ibgp"]:
                config.append(f" neighbor {ibgp['neighbor']} remote-as {get_as_number(ibgp['remote-as'])}")
        
        if "ebgp" in bgp_config:
            config.append(f"router bgp {as_number}")
            for ebgp in bgp_config["ebgp"]:
                config.append(f" neighbor {ebgp['neighbor']} remote-as {get_as_number(ebgp['remote-as'])}")
    else:
        for protocol in ["ibgp", "ebgp"]:
            if protocol in router_data["protocols"]:
                config.append(f"router bgp {as_number}")
                for neighbor in router_data["protocols"][protocol]:
                    config.append(f" neighbor {neighbor['neighbor']} remote-as {get_as_number(neighbor['remote-as'])}")
    
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