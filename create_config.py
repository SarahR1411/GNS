import json
import os 


script_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(script_dir, "intent.json")

with open(file_path, "r") as file:
    intent = json.load(file)

def get_as_number(as_name): 
    return 1 if as_name == "AS_X" else 2

def get_as_of_router(router_name, intent):
    """
    Determines which AS a router belongs to based on the intent file.
    """
    for as_entry in intent['network']:
        for as_name, data in as_entry.items():
            if router_name in data["routers"]:
                return as_name
    raise ValueError(f"Router {router_name} not found in any AS.")


def generate_ip(interface_name, router_nbr, base_prefix):
    """
    Generate an IPv6 address for a given interface name and router number.
    """
    if interface_name.startswith("Loopback"):
        return f"{base_prefix}::{router_nbr}/128"
    elif interface_name.startswith("GigabitEthernet"):
        interface_parts = interface_name.split("/")
        main_interface = int(interface_parts[0][-1])
        sub_interface = int(interface_parts[1])
        return f"{base_prefix}:{router_nbr}:{main_interface}:{sub_interface}::1/64"
    return None

def get_interface_subnet(router_name, interface_name, base_prefix, intent, as_name):
    """
    Generate the IPv6 subnet for a given interface considering peer relationships.
    """
    # Locate the current router and its links
    for as_entry in intent["network"]:
        if as_name in as_entry:
            all_routers = as_entry[as_name]["routers"]
            current_router = all_routers.get(router_name)
            if not current_router or "links" not in current_router:
                continue

            # Check for the link that matches the given interface
            for link in current_router["links"]:
                if link["interface"] == interface_name:
                    # Found the peer link -> use the router and interface information to generate the subnet
                    peer_router = link["target_router"]
                    peer_interface = link["target_interface"]

                    # Generate the subnet based on the current router and interface
                    router_nbr = int(router_name.lstrip("R"))
                    peer_nbr = int(peer_router.lstrip("R"))
                    interface_parts = interface_name.split("/")
                    main_interface = int(interface_parts[0][-1])  
                    sub_interface = int(interface_parts[1])       

                    # Subnet shared between this router and its peer
                    return f"{base_prefix}:{min(router_nbr, peer_nbr)}:{main_interface}:{sub_interface}::/64"

    # if no link is found
    router_nbr = int(router_name.lstrip("R"))
    if interface_name.startswith("GigabitEthernet"):
        interface_parts = interface_name.split("/")
        main_interface = int(interface_parts[0][-1])
        sub_interface = int(interface_parts[1])
        return f"{base_prefix}:{router_nbr}:{main_interface}:{sub_interface}::/64"
    return None


def generate_ip_with_peer(router_name, interface_name, as_name, intent, base_prefixes):
    """
    Generate an IPv6 address for an interface considering both peer links and standalone interfaces.
    """
    base_prefix = base_prefixes[as_name]
    router_nbr = int(router_name.lstrip("R"))

    # Find the router and its links in the intent file
    for as_entry in intent["network"]:
        if as_name in as_entry:
            all_routers = as_entry[as_name]["routers"]
            current_router = all_routers.get(router_name)
            if not current_router or "links" not in current_router:
                continue

            # Check if the interface is part of a link
            for link in current_router["links"]:
                if link["interface"] == interface_name:
                    target_router = link["target_router"]
                    target_interface = link["target_interface"]
                    target_router_nbr = int(target_router.lstrip("R"))

                    # Determine the shared subnet
                    shared_subnet = f"{base_prefix}:{min(router_nbr, target_router_nbr)}:{max(router_nbr, target_router_nbr)}"

                    # Assign unique host IDs based on router order
                    if router_name < target_router:
                        return f"{shared_subnet}::1/64"
                    else:
                        return f"{shared_subnet}::2/64"

    # for non-linked interfaces 
    if interface_name.startswith("Loopback"):
        return f"{base_prefix}::{router_nbr}/128"
    elif interface_name.startswith("GigabitEthernet"):
        # Split the interface into main and sub-interface
        try:
            interface_parts = interface_name.split("/")
            main_interface = int(interface_parts[0][-1]) 
            sub_interface = int(interface_parts[1])      
            return f"{base_prefix}:{router_nbr}:{main_interface}:{sub_interface}::1/64"
        except (IndexError, ValueError):
            # if malformed interface names
            raise ValueError(f"Invalid interface name format: {interface_name}")
    else:
        raise ValueError(f"Unknown interface type: {interface_name}")


def create_config(router_name, router_data, as_name, router_nbr):

    """
    Generates the startup configuration for a given router based on the provided intent file.
    """

    # router_data is the data for one specific router 

    config = []
    ibgp_list = []
    current_as = get_as_number(as_name)
    remote_as  = 2 if current_as == 1 else 1
    router_id = f"{router_nbr}.{router_nbr}.{router_nbr}.{router_nbr}"
    process_id = router_nbr
    base_prefixes = {
    "AS_X": "2001:100:4",
    "AS_Y": "2001:200:4"
    }
    base_prefix = base_prefixes[as_name]

    all_routers = None
    for as_entry in intent['network']:
        if as_name in as_entry:
            all_routers = as_entry[as_name]["routers"]
            break
    if not all_routers:
        raise KeyError(f"AS '{as_name}' not found in intent['network']")

    

    config.append(f"!\nhostname {router_name}")
    config.append("!")
    config.append("no ip domain lookup")
    config.append("ipv6 unicast-routing")
    config.append("ipv6 cef")
    config.append("!")


    
    #defines ip addresses of current router's interfaces
    for interface_name in router_data["interfaces"]:
        ipv6_address = generate_ip_with_peer(router_name, interface_name, as_name, intent, base_prefixes)
        config.append(f"interface {interface_name}")
        config.append(" no ip address")
        config.append(" negotiation auto")
        config.append(f" ipv6 address {ipv6_address}")
        config.append(" ipv6 enable")
        if router_data["protocols"].get("ripng"):
            config.append(f" ipv6 rip {process_id} enable")
        if "ospf" in router_data["protocols"]:
            config.append(f" ipv6 ospf {process_id} area 0")
        config.append("!")
    
    # If RIP enabled
    
    if router_data["protocols"].get("ripng"):
        config.append(f"ipv6 router rip {process_id}")
        config.append(" redistribute connected")
        config.append("!")
    
    # For BGP config
    
    bgp_config = router_data['protocols'].get("bgp", {})

    if bgp_config.get("ibgp"):
        config.append(f"router bgp {current_as}")
        config.append(f" bgp router-id {router_id}")
        config.append(" bgp log-neighbor-changes")
        config.append(" no bgp default ipv4-unicast")

        for peer_name, peer_data in all_routers.items():
            peer_number = int(peer_name.lstrip("R"))  # Extract the router number
            if peer_name != router_name:  # Exclude the current router
                ibgp_address = generate_ip("Loopback0", peer_number, base_prefixes[as_name]).split('/')[0]
                ibgp_list.append(ibgp_address)
                config.append(f" neighbor {ibgp_address} remote-as {current_as}")
                config.append(f" neighbor {ibgp_address} update-source Loopback0")


    if "ebgp" in bgp_config:
        for ebgp in bgp_config["ebgp"]:

            target_router = ebgp["target_router"]
            target_router_number = int(target_router.lstrip("R"))
            target_router_as = get_as_of_router(target_router, intent)
            target_base_prefix = base_prefixes[target_router_as]

            neighbor_ip = generate_ip_with_peer(router_name, ebgp["interface"], as_name, intent, base_prefixes).split('/')[0]

            config.append(f" neighbor {neighbor_ip} remote-as {remote_as}")
            config.append(f" neighbor {neighbor_ip} description Connection to {target_router} in AS {remote_as}")
    
        config.append("!")

        config.append("address-family ipv6")

        for ebgp in bgp_config['ebgp']:

            advertise_network = get_interface_subnet(router_name, ebgp["interface"], base_prefix, intent, as_name)
            config.append(f" network {advertise_network}")

            target_router = ebgp["target_router"]
            target_router_number = int(target_router.lstrip("R"))
            target_router_as = get_as_of_router(target_router, intent)
            target_base_prefix = base_prefixes[target_router_as]

            neighbor_ip = generate_ip_with_peer(router_name, ebgp["interface"], as_name, intent, base_prefixes).split('/')[0]
            config.append(f" neighbor {neighbor_ip} activate")

    if "address-family ipv6" not in config:
        config.append("address-family ipv6")
    for ip in ibgp_list:
        config.append(f" neighbor {ip} activate")
        
    config.append("exit-address-family")
    config.append("!")
    
    if as_name == "AS_Y":
        config.append(f"ipv6 router ospf {process_id}")
        config.append(f" router-id {router_id}\n!")
    
    config.append("!\nend")
    return "\n".join(config)

def main():

    i = 1

    os.makedirs("config_files", exist_ok=True) # will make the folder if it doesn't exist
    for as_data in intent['network']:
        for as_name, content in as_data.items():
            for router_name, router_data in content["routers"].items():
                config = create_config(router_name, router_data, as_name, i)
                output = os.path.join("config_files", f"{router_name}_startup-config.cfg")
                with open(output, "w") as config_file:
                    config_file.write(config) 
                print(f"Generated config file for {router_name} at {output}")
                i += 1

main()