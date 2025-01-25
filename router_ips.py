import json
import os

# Load intent file
script_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(script_dir, "intent.json")

with open(file_path, "r") as file:
    intent = json.load(file)


def get_as_of_router(router_name, intent):
    """
    Determines which AS a router belongs to based on the intent file.
    """
    for as_entry in intent["network"]:
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

    # Locate the current router and its links
    for as_entry in intent["network"]:
        if as_name in as_entry:
            all_routers = as_entry[as_name]["routers"]
            current_router = all_routers.get(router_name)
            if not current_router or "links" not in current_router:
                continue

            # Check if the interface is part of a peer link
            for link in current_router["links"]:
                if link["interface"] == interface_name:
                    target_router = link["target_router"]
                    target_router_as = get_as_of_router(target_router, intent)

                    # Create a unique key for this link including both routers and their AS names
                    link_key = tuple(sorted([(router_name, as_name), (target_router, target_router_as)]))

                    # Assign a unique subnet for the link if it doesn't exist
                    if link_key not in link_tracker:
                        link_tracker[link_key] = {
                            "link_id": len(link_tracker) + 1,
                            "shared_prefix": initiating_as_prefix,
                        }

                    link_info = link_tracker[link_key]
                    link_id = link_info["link_id"]
                    shared_prefix = link_info["shared_prefix"]

                    # Assign IPs based on router order
                    if router_name < target_router:
                        assigned_ip = f"{shared_prefix}:{link_id}::1/64"
                        print(f"[DEBUG] Assigned IP for {router_name} ({interface_name}): {assigned_ip}")
                        return assigned_ip
                    else:
                        assigned_ip = f"{shared_prefix}:{link_id}::2/64"
                        print(f"[DEBUG] Assigned IP for {router_name} ({interface_name}): {assigned_ip}")
                        return assigned_ip

    # Fallback for standalone interfaces
    if interface_name.startswith("Loopback"):
        ipv6 = f"{initiating_as_prefix}::{router_nbr}/128"
        print(f"[DEBUG] Loopback IP for {router_name}: {ipv6}")
        return ipv6
    elif interface_name.startswith("GigabitEthernet"):
        try:
            interface_parts = interface_name.split("/")
            main_interface = int(interface_parts[0][-1])
            sub_interface = int(interface_parts[1])
            ipv6 = f"{initiating_as_prefix}:{router_nbr}:{main_interface}:{sub_interface}::1/64"
            print(f"[DEBUG] Standalone IP for {router_name} ({interface_name}): {ipv6}")
            return ipv6
        except (IndexError, ValueError):
            raise ValueError(f"Invalid interface name format: {interface_name}")
    else:
        raise ValueError(f"Unknown interface type: {interface_name}")


def get_interface_subnet(router_name, interface_name, base_prefixes, intent, as_name, link_tracker):
    """
    Generate the IPv6 subnet for a given interface dynamically using `generate_ip_with_peer`.
    """
    full_address = generate_ip_with_peer(router_name, interface_name, as_name, intent, base_prefixes, link_tracker)
    subnet = full_address.split("::")[0] + "::/64"
    print(f"[DEBUG] Subnet for {router_name} ({interface_name}): {subnet}")
    return subnet


def generate_router_address_mapping(intent, base_prefixes, output_file="router_address_mapping.txt"):
    """
    Generate a detailed mapping of router interfaces and their dynamically generated IP addresses.
    """
    link_tracker = {}

    with open(output_file, "w") as file:
        file.write("Router Address Mapping:\n")
        file.write("=" * 50 + "\n")

        for as_entry in intent["network"]:
            for as_name, as_data in as_entry.items():
                file.write(f"\nAS: {as_name}\n")
                file.write("-" * 50 + "\n")

                for router_name, router_data in as_data["routers"].items():
                    file.write(f"Router: {router_name}\n")
                    file.write("Interfaces:\n")

                    for interface_name in router_data["interfaces"]:
                        ipv6_address = generate_ip_with_peer(
                            router_name,
                            interface_name,
                            as_name,
                            intent,
                            base_prefixes,
                            link_tracker
                        )
                        file.write(f"  {interface_name}: {ipv6_address}\n")

                    file.write("\n")
    print(f"Router address mapping written to {output_file}")


# Base prefixes for AS_X and AS_Y
base_prefixes = {
    "AS_X": "2001:100:4",
    "AS_Y": "2001:200:4"
}

# Generate the router address mapping
generate_router_address_mapping(intent, base_prefixes)
