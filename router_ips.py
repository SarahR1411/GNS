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



def generate_ip_with_peer(router_name, interface_name, as_name, intent, base_prefixes):
    """
    Generate an IPv6 address for an interface, considering both peer links and standalone interfaces.
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

    # Fallback for non-linked interfaces (use updated generate_ip logic)
    if interface_name.startswith("Loopback"):
        # Loopback interfaces get a /128 unique address
        return f"{base_prefix}::{router_nbr}/128"
    elif interface_name.startswith("GigabitEthernet"):
        # Split the interface into main and sub-interface
        try:
            interface_parts = interface_name.split("/")
            main_interface = int(interface_parts[0][-1])  # Main interface (e.g., 1 from GigabitEthernet1/0)
            sub_interface = int(interface_parts[1])       # Sub-interface (e.g., 0 from GigabitEthernet1/0)
            return f"{base_prefix}:{router_nbr}:{main_interface}:{sub_interface}::1/64"
        except (IndexError, ValueError):
            # Handle malformed interface names
            raise ValueError(f"Invalid interface name format: {interface_name}")
    else:
        raise ValueError(f"Unknown interface type: {interface_name}")





def get_interface_subnet(router_name, interface_name, base_prefix, intent, as_name):
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
                    # Found the peer link; use the router and interface information to generate the subnet
                    peer_router = link["target_router"]
                    peer_nbr = int(peer_router.lstrip("R"))
                    interface_parts = interface_name.split("/")
                    main_interface = int(interface_parts[0][-1])  # First part of the interface
                    sub_interface = int(interface_parts[1])       # Second part of the interface

                    # Subnet shared between this router and its peer
                    return f"{base_prefix}:{min(router_nbr, peer_nbr)}:{main_interface}:{sub_interface}::/64"

    # Fallback logic for non-linked interfaces (ensures uniqueness)
    interface_parts = interface_name.split("/")
    main_interface = int(interface_parts[0][-1])
    sub_interface = int(interface_parts[1])
    return f"{base_prefix}:{router_nbr}:{main_interface}:{sub_interface}::/64"



def generate_router_address_mapping(intent, base_prefixes, output_file="router_address_mapping.txt"):
    """
    Generate a detailed mapping of router interfaces and their dynamically generated IP addresses.
    """
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
                        ipv6_address = generate_ip_with_peer(router_name, interface_name, as_name, intent, base_prefixes)
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
