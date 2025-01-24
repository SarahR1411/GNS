import json
import os 


script_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(script_dir, "intent.json")

with open(file_path, "r") as file:
    intent = json.load(file)

def generate_ip(interface_name, router_nbr, base_prefix):
    """
    Generate a unique IPv6 address for a given interface name and router number.
    """
    if interface_name.startswith("Loopback"):
        return f"{base_prefix}::{router_nbr}/128"
    elif interface_name.startswith("GigabitEthernet"):
        # Split the interface to include both main and sub-interface
        interface_parts = interface_name.split("/")
        main_interface = int(interface_parts[0][-1])  # Extracts main interface (e.g., 1 from GigabitEthernet1/0)
        sub_interface = int(interface_parts[1])       # Extracts sub-interface (e.g., 0 from GigabitEthernet1/0)

        # Use both main_interface and sub_interface for uniqueness
        return f"{base_prefix}:{router_nbr}:{main_interface}:{sub_interface}::1/64"
    return None

def get_as_of_router(router_name, intent):
    """
    Determines which AS a router belongs to based on the intent file.
    """
    for as_entry in intent['network']:
        for as_name, data in as_entry.items():
            if router_name in data["routers"]:
                return as_name
    raise ValueError(f"Router {router_name} not found in any AS.")


def generate_ip_with_peer(router_name, interface_name, as_name, intent, base_prefixes, link_tracker):
    """
    Generate a unique IPv6 address for an interface considering both peer links and standalone interfaces.
    """
    initiating_as_prefix = base_prefixes[as_name]  
    router_nbr = int(router_name.lstrip("R"))  

    # locate the current router and its links
    for as_entry in intent["network"]:
        if as_name in as_entry:
            all_routers = as_entry[as_name]["routers"]
            current_router = all_routers.get(router_name)
            if not current_router or "links" not in current_router:
                continue

            # check if the interface is part of a peer link
            for link in current_router["links"]:
                if link["interface"] == interface_name:
                    target_router = link["target_router"]
                    target_router_as = get_as_of_router(target_router, intent)
                    target_router_nbr = int(target_router.lstrip("R"))

                    # create a unique key for this link including the initiating router's AS
                    link_key = tuple(sorted([(router_name, as_name), (target_router, target_router_as)]))

                    # make sure each link has a unique subnet and shared prefix
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

                    # Assign ::1 and ::2 based on router order
                    if router_name < target_router:
                        return f"{shared_prefix}:{link_id}::1/64"  # This router gets ::1
                    else:
                        return f"{shared_prefix}:{link_id}::2/64"  # Peer router gets ::2

    # for standalone interfaces
    if interface_name.startswith("Loopback"):
        ipv6 = f"{initiating_as_prefix}::{router_nbr}/128"
        print(f"[DEBUG] Loopback IP: {router_name} ({interface_name}) -> {ipv6}")
        return ipv6
    elif interface_name.startswith("GigabitEthernet"):
        try:
            interface_parts = interface_name.split("/")
            main_interface = int(interface_parts[0][-1])  # Extract the main interface
            sub_interface = int(interface_parts[1])       # Extract the sub-interface
            ipv6 = f"{initiating_as_prefix}:{router_nbr}:{main_interface}:{sub_interface}::1/64"
            print(f"[DEBUG] Standalone GigabitEthernet IP: {router_name} ({interface_name}) -> {ipv6}")
            return ipv6
        except (IndexError, ValueError):
            raise ValueError(f"Invalid interface name format: {interface_name}")
    else:
        raise ValueError(f"Unknown interface type: {interface_name}")




def get_interface_subnet(router_name, interface_name, base_prefix, intent, as_name, link_tracker):
    """
    Generate the IPv6 subnet for a given interface dynamically, ensuring uniqueness across all interfaces.
    """
    router_nbr = int(router_name.lstrip("R"))

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
                    # Found the peer link
                    peer_router = link["target_router"]
                    peer_nbr = int(peer_router.lstrip("R"))

                    # Create a unique key for the link (ensures no duplicates)
                    link_key = tuple(sorted([router_name, peer_router]))
                    if link_key not in link_tracker:
                        # Assign a new unique link ID
                        link_tracker[link_key] = len(link_tracker) + 1

                    # Use the unique link ID for the subnet
                    link_id = link_tracker[link_key]
                    return f"{base_prefix}:{link_id}::/64"

    # Fallback logic for non-linked interfaces (ensures uniqueness)
    interface_parts = interface_name.split("/")
    main_interface = int(interface_parts[0][-1])
    sub_interface = int(interface_parts[1])
    return f"{base_prefix}:{router_nbr}:{main_interface}:{sub_interface}::/64"




def generate_router_address_mapping(intent, base_prefixes, output_file="router_address_mapping.txt"):
    """
    Generate a detailed mapping of router interfaces and their dynamically generated IP addresses.
    """
    link_tracker = {}  # Initialize the link tracker to ensure unique subnets for peer links

    with open(output_file, "w") as file:
        file.write("Router Address Mapping:\n")
        file.write("=" * 50 + "\n")

        for as_entry in intent["network"]:
            for as_name, as_data in as_entry.items():
                base_prefix = base_prefixes[as_name]
                file.write(f"\nAS: {as_name}\n")
                file.write("-" * 50 + "\n")

                for router_name, router_data in as_data["routers"].items():
                    file.write(f"Router: {router_name}\n")
                    file.write("Interfaces:\n")

                    for interface_name in router_data["interfaces"]:
                        # Pass the link_tracker to generate_ip_with_peer
                        ipv6_address = generate_ip_with_peer(
                            router_name,
                            interface_name,
                            as_name,
                            intent,
                            base_prefixes,
                            link_tracker  # Ensures consistent unique subnets for links
                        )
                        file.write(f"  {interface_name}: {ipv6_address}\n")

                    file.write("\n")
    print(f"Router address mapping written to {output_file}")




base_prefixes = {
    "AS_X": "2001:100:4",
    "AS_Y": "2001:200:4"
}


generate_router_address_mapping(intent, base_prefixes)



# print(get_interface_subnet("R1", "GigabitEthernet1/0", "2001:100:4"))
# print(get_interface_subnet("R1", "GigabitEthernet2/0", "2001:100:4"))
# print(get_interface_subnet("R1", "GigabitEthernet1/1", "2001:100:4"))
