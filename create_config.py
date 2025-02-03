import json
import os 

# Get the directory of the current script file
script_dir = os.path.dirname(os.path.realpath(__file__))

# Define the file path of the intent.json file in the same directory as the script
file_path = os.path.join(script_dir, "intent.json")

# Open and load the intent.json file into the 'intent' dictionary
with open(file_path, "r") as file:
    intent = json.load(file)

as_numbers = {}
for idx, as_entry in enumerate(intent["network"]):
    for as_name in as_entry:
        as_numbers[as_name] = idx + 1

def get_as_number(as_name):
    return as_numbers.get(as_name, 0)

def get_as_of_router(router_name, intent):
    """
    Determines which AS a router belongs to based on the intent file.
    """
    # Iterate over the AS entries in the network intent
    for as_entry in intent['network']:
        for as_name, data in as_entry.items():
            # Check if the router_name exists in the router list of the AS
            if router_name in data["routers"]:
                return as_name
    # If the router is not found, raise an error
    raise ValueError(f"Router {router_name} not found in any AS.")


def generate_ip_with_peer(router_name, interface_name, as_name, intent, base_prefixes, link_tracker):
    """
    Generate a unique IPv6 address for an interface considering both peer links and standalone interfaces.
    """
    initiating_as_prefix = base_prefixes[as_name]  # Get the base prefix for the AS
    router_nbr = int(router_name.lstrip("R"))  # Extract router number

    # Iterate through the network intent to find the specific router and its links
    for as_entry in intent["network"]:
        if as_name in as_entry:
            all_routers = as_entry[as_name]["routers"]
            current_router = all_routers.get(router_name)
            if not current_router or "links" not in current_router:
                continue

            # Loop through the links for the current router to find a matching interface
            for link in current_router["links"]:
                if link["interface"] == interface_name:
                    target_router = link["target_router"]
                    target_router_as = get_as_of_router(target_router, intent)

                    # Generate a unique key for the link using sorted router names and AS
                    link_key = tuple(sorted([(router_name, as_name), (target_router, target_router_as)]))

                    # Ensure a unique subnet for each link
                    if link_key not in link_tracker:
                        link_tracker[link_key] = {
                            "link_id": len(link_tracker) + 1,
                            "shared_prefix": initiating_as_prefix,
                        }

                    link_info = link_tracker[link_key]
                    link_id = link_info["link_id"]
                    shared_prefix = link_info["shared_prefix"]

                    print(f"[DEBUG] Link: {router_name} ({interface_name}) <-> {target_router} (AS: {target_router_as}), "
                          f"Link ID: {link_id}, Shared Prefix: {shared_prefix}")

                    # Assign ::1 or ::2 based on the router's role
                    # Assign addresses based on router role in the link
                    if link_key[0][0] == router_name:  # If this router is the first in the sorted key
                        assigned_ip = f"{shared_prefix}:{link_id}::1/64"
                        neighbor_ip = f"{shared_prefix}:{link_id}::2"
                    else:  # This router is second in the sorted key
                        assigned_ip = f"{shared_prefix}:{link_id}::2/64"
                        neighbor_ip = f"{shared_prefix}:{link_id}::1"

                    print(f"[DEBUG] Assigned IP for {router_name} on {interface_name}: {assigned_ip}")
                    print(f"[DEBUG] Neighbor IP for {router_name} to {target_router} (AS: {target_router_as}): {neighbor_ip}")

                    # Return assigned and neighbor IPs
                    return assigned_ip

    # Fallback for standalone interfaces
    if interface_name.startswith("Loopback"):
        return f"{initiating_as_prefix}::{router_nbr}/128"  # Loopbacks get unique /128 addresses
    elif interface_name.startswith("GigabitEthernet"):
        # Use router number and interface details for standalone GigabitEthernet interfaces
        try:
            # Handle sub-interfaces in GigabitEthernet type interfaces
            interface_parts = interface_name.split("/")
            main_interface = int(interface_parts[0][-1])  # Extract the main interface
            sub_interface = int(interface_parts[1])       # Extract the sub-interface
            return f"{initiating_as_prefix}:{router_nbr}:{main_interface}:{sub_interface}::1/64"
        except (IndexError, ValueError):
            raise ValueError(f"Invalid interface name format: {interface_name}")
    else:
        raise ValueError(f"Unknown interface type: {interface_name}")

def get_interface_subnet(router_name, interface_name, base_prefixes, intent, as_name, link_tracker):
    """
    Generate the IPv6 subnet for a given interface dynamically using `generate_ip_with_peer`.
    """

    full_address = generate_ip_with_peer(router_name, interface_name, as_name, intent, base_prefixes, link_tracker)

    # Extract the subnet part (everything up to "::") and append the /64 subnet mask
    subnet = full_address.split("::")[0] + "::/64"

    print(f"[DEBUG] Subnet for {router_name} on {interface_name}: {subnet}")
    return subnet



def create_config(router_name, router_data, as_name, router_nbr, link_tracker, base_prefixes):

    """
    Generates the startup configuration for a given router based on the provided intent file.
    """

    # router_data is the data for one specific router 

    config = []
    ibgp_list = []
    bgp_config = router_data['protocols'].get("bgp", {})
    current_as = get_as_number(as_name)
    router_id = f"{router_nbr}.{router_nbr}.{router_nbr}.{router_nbr}"
    process_id = router_nbr

    # Find all routers in the current AS
    all_routers = None
    for as_entry in intent['network']:
        if as_name in as_entry:
            all_routers = as_entry[as_name]["routers"]
            break
    if not all_routers:
        raise KeyError(f"AS '{as_name}' not found in intent['network']")

    config.append(f"!\nhostname {router_name}")
    config.append("!\nno ip domain lookup\nipv6 unicast-routing\nipv6 cef\n!")
    
    
    # Configure the interfaces of the current router
    for interface_name in router_data["interfaces"]:
        ipv6_address = generate_ip_with_peer(router_name, interface_name, as_name, intent, base_prefixes, link_tracker)
        config.append(f"interface {interface_name}")
        config.append(" no shutdown")
        config.append(" no ip address")
        config.append(" ipv6 enable")
        config.append(f" ipv6 address {ipv6_address}")
        if router_data["protocols"].get("ripng"):
            config.append(f" ipv6 rip {process_id} enable")
        if "ospf" in router_data["protocols"]:
            config.append(f" ipv6 ospf {process_id} area 0")
            cost_dict = router_data["protocols"].get("cost", {})
            cost_value = cost_dict.get(interface_name)  
            if cost_dict != {}:
                if cost_value is not None:  
                    config.append(f" ipv6 ospf cost {cost_value}")
        config.append(" negotiation auto")
        config.append("!")        
      

    # If RIP enabled
    
    if router_data["protocols"].get("ripng"):
        config.append(f"ipv6 router rip {process_id}")
        config.append(" redistribute connected")
        config.append("!")
    

    if "ospf" in router_data['protocols'] and "ebgp" in bgp_config:
        config.append(f"router ospfv3 {process_id}")
        config.append("!")
        config.append("address-family ipv6 unicast")
        for interface in router_data["protocols"]["ospf"]["passive_interfaces"]:
            config.append(f" passive-interface {interface}")
            config.append(f" router-id {router_id}")
        config.append("exit-address-family\n!")


    # For BGP config

    if bgp_config.get("ibgp"):
        config.append(f"router bgp {current_as}")
        config.append(f" bgp router-id {router_id}")
        config.append(" bgp log-neighbor-changes")
        config.append(" no bgp default ipv4-unicast")

        # Configure iBGP neighbors
        for peer_name in all_routers:
            if peer_name != router_name:
                ibgp_address = generate_ip_with_peer(peer_name, "Loopback0", as_name, intent, base_prefixes, link_tracker).split('/')[0]
                ibgp_list.append(ibgp_address)
                config.append(f" neighbor {ibgp_address} remote-as {current_as}")
                config.append(f" neighbor {ibgp_address} update-source Loopback0")

    # Configure eBGP neighbors if enabled
    if "ebgp" in bgp_config:
        for ebgp in bgp_config["ebgp"]:
            
            target_router = ebgp["target_router"]
            target_router_as = get_as_of_router(target_router, intent)
            remote_as = get_as_number(target_router_as)
            
            # Generate the eBGP neighbor IP
            neighbor_ip = generate_ip_with_peer(
                target_router, 
                ebgp["interface"],  
                target_router_as,
                intent,
                base_prefixes,
                link_tracker
            ).split('/')[0]

            # Log the generated neighbor IP
            print(f"[DEBUG] Neighbor IP for {router_name} to {target_router} (AS: {target_router_as}): {neighbor_ip}")

            # Add to the configuration
            config.append(f" neighbor {neighbor_ip} remote-as {remote_as}")
            config.append(f" neighbor {neighbor_ip} description Connection to {target_router} in AS {remote_as}")


        config.append("!")

        config.append("address-family ipv6")

        policies = bgp_config.get('policies', {})
        neighbor_policies = policies.get("neighbor_policies", [])

        for ebgp in bgp_config['ebgp']:
            advertise_router = ebgp['advertise']
            target_router = ebgp["target_router"]
            target_router_as = get_as_of_router(target_router, intent)
            remote_as = get_as_number(target_router_as)

            for interface in ebgp["advertise-interface"]:
            
                advertise_network = get_interface_subnet(
                                    advertise_router,  
                                    interface,  
                                    base_prefixes,      
                                    intent,             
                                    as_name,           
                                    link_tracker        
                                )
                
                print(f"[DEBUG] Advertised Network for {router_name}: {advertise_network}")
                config.append(f" network {advertise_network}")
            
            neighbor_ip = generate_ip_with_peer(target_router, ebgp["interface"], target_router_as, intent, base_prefixes, link_tracker).split('/')[0]
            config.append(f" neighbor {neighbor_ip} activate")
            
            for np in neighbor_policies:
                if np["neighbor_as"] == remote_as:
                    config.append(f" neighbor {neighbor_ip} send-community both")

                    for apply_item in np["apply"]:
                        direction = apply_item["direction"]
                        rmap_name = apply_item["route_map"]
                        config.append(f" neighbor {neighbor_ip} route-map {rmap_name} {direction}")
            


    if "address-family ipv6" not in config:
        config.append("!\naddress-family ipv6")

    for ip in ibgp_list:
        config.append(f" neighbor {ip} activate")
        
    config.append("exit-address-family")
    config.append("!")

    if "policies" in bgp_config:
        pol = bgp_config["policies"]
        
        # Community Lists
        for cl in pol.get("community_lists", []):
            name = cl["name"]
            action = cl["action"]
            value = cl["value"]
            config.append(f"ip community-list standard {name} {action} {value}")
        
        config.append('!')

        # Route Maps
        for rm in pol.get("route_maps", []):
            rm_name = rm["name"]
            seq = rm.get("sequence", 10)
            action = rm.get("action", "permit")
            config.append(f"route-map {rm_name} {action} {seq}")

            match_dict = rm.get("match", {})
            if "community" in match_dict:
                community_name = match_dict["community"]
                config.append(f" match community {community_name}")

            set_dict = rm.get("set", {})
            if "local_preference" in set_dict:
                lp = set_dict["local_preference"]
                config.append(f" set local-preference {lp}")

            config.append("!")


    
    if "ospf" in router_data["protocols"]:
        config.append(f"ipv6 router ospf {process_id}")
        config.append(f" router-id {router_id}\n!")
    
    config.append("!\nend")
    return "\n".join(config)

def main():
    link_tracker = {}
    base_prefixes = {}
    for as_entry in intent["network"]:
        for as_name, as_data in as_entry.items():
            base_prefixes[as_name] = as_data.get("base_prefix")

    os.makedirs("config_files", exist_ok=True)
    i = 1
    # Iterate through the intent file and generate configs for each router
    for as_data in intent['network']:
        for as_name, content in as_data.items():
            for router_name, router_data in content["routers"].items():
                config = create_config(router_name, router_data, as_name, i, link_tracker, base_prefixes)
                output = os.path.join("config_files", f"{router_name}_startup-config.cfg")
                with open(output, "w") as config_file:
                    config_file.write(config)   # Write the generated config to a file
                print(f"Generated config file for {router_name} at {output}")
                i += 1  # Increment router number for the next router

# Run the main function to generate the configs
main()