import json
import os 


script_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(script_dir, "intent.json")

with open(file_path, "r") as file:
    intent = json.load(file)

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

def generate_ip_with_peer(router_name, interface_name, as_name, intent, base_prefixes):
    """
    Generate an IPv6 address for an interface dynamically, considering peer connections from the intent file.
    """
    base_prefix = base_prefixes[as_name]  # Get base prefix for current AS

    # Find the router and its links in the intent file
    for as_entry in intent["network"]:
        if as_name in as_entry:
            all_routers = as_entry[as_name]["routers"]
            current_router = all_routers.get(router_name)
            if not current_router or "links" not in current_router:
                continue

            # Loop through the links to find a match for the interface
            for link in current_router["links"]:
                if link["interface"] == interface_name:
                    target_router = link["target_router"]
                    target_interface = link["target_interface"]

                    # Assign ::1 for this router and ::2 for the peer
                    if router_name < target_router:  # Sort routers to ensure consistency
                        return f"{base_prefix}:{router_name.lstrip('R')}:{interface_name.split('/')[-1]}::1/64"
                    else:
                        return f"{base_prefix}:{target_router.lstrip('R')}:{target_interface.split('/')[-1]}::2/64"

    # Default fallback for non-linked interfaces
    return generate_ip(interface_name, int(router_name.lstrip("R")), base_prefix)

def get_interface_subnet(router_name, interface_name, base_prefix):
    """
    Generate the IPv6 subnet for a given interface name and router number.
    """
    router_nbr = int(router_name.lstrip("R"))
    if interface_name.startswith("GigabitEthernet"):
        interface_parts = interface_name.split("/")
        main_interface = int(interface_parts[0][-1])  
        sub_interface = int(interface_parts[1]) 
        return f"{base_prefix}:{router_nbr}:{main_interface}:{sub_interface}::/64"
    return None


def generate_router_address_mapping(intent, base_prefixes, output_file="router_address_mapping.txt"):
    """
    Generate a detailed mapping of router interfaces and their dynamically generated IP addresses.
    """
    with open(output_file, "w") as file:
        file.write("Router Address Mapping:\n")
        file.write("=" * 50 + "\n")

        for as_entry in intent['network']:
            for as_name, as_data in as_entry.items():
                base_prefix = base_prefixes[as_name]
                file.write(f"\nAS: {as_name}\n")
                file.write("-" * 50 + "\n")

                for router_name, router_data in as_data["routers"].items():
                    file.write(f"Router: {router_name}\n")
                    file.write("Interfaces:\n")

                    # Generate addresses for each interface using the peer-aware function
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



print(get_interface_subnet("R1", "GigabitEthernet1/0", "2001:100:4"))
print(get_interface_subnet("R1", "GigabitEthernet2/0", "2001:100:4"))
print(get_interface_subnet("R1", "GigabitEthernet1/1", "2001:100:4"))
