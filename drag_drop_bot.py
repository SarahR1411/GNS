import os
import shutil

# Dictionary mapping router number to its folder ID and router name
router_folder_corresp = {
    5 : ("0cdfc724-c2af-4ebf-8da6-a9f2adb35c51", "i3"),
    14 : ("2afa751b-268b-4974-ba16-2bec9036dfef", "i7"),
    1: ("8d3e55f5-f7f3-4d21-9831-9d4a675795bc", "i1"),
    10 : ("13fc9f8b-3920-41f9-b198-c15bb6627c8c", "i13"),
    3 : ("284c438a-bbb6-4baf-83c6-fbe73b575d93", "i2"),
    4 : ("881e5b96-0fab-4ddd-9cb7-bf11b4c91459", "i10"),
    13 : ("30974b98-87ea-4f4c-b3b5-1511f964add5", "i8"),
    9 : ("94978ba0-84b5-466b-8d6a-2a80256d4744", "i5"),
    7 : ("a5bb323b-06e8-41e2-bd54-82f7cb27e8ca", "i4"),
    8 : ("b6194714-d95f-49dc-8564-37520e8c2868", "i12"),
    11 : ("d0347ac7-f0a2-469f-a8b9-604555db3a0c", "i6"),
    6 : ("dfb89e34-7823-4447-ade3-aa26347b1ea1", "i11"),
    2 : ("e30e197d-464f-4764-b50c-9c46200cf67a", "i9"),
    12 : ("fce06220-5b24-4eab-89c2-acdf0a798679", "i14"),
    16 : ("c3ca05ee-217b-4776-9cd3-a8c19fb8acfd", "i16"),
    17 : ("68a7ff1f-8411-4f35-8a60-db15faaca488", "i17"),
    18 : ("99e969ab-ceb4-4038-981f-f8a128b89b84", "i18"),
    19 : ("431f69fa-6ba4-47e5-895e-ba19def72105", "i19"),
    15 : ("a93e3c2b-d846-4bc6-8203-3adac65926be", "i15")

}

# Folder where the router configuration files are stored
config_folder = "config_files"
# Destination folder where GNS3 expects the configuration files to be moved
destination = "/home/srmili/GNS3/projects/GNS_Project1/project-files/dynamips"


def delete_existing_cfg_files(dest_folder):
    """
    Deletes all .cfg files from the destination folder (if they exist).
    This is to avoid conflicts with existing configurations before moving the new ones.
    """
    if os.path.exists(dest_folder):
        for file in os.listdir(dest_folder):
            if file.endswith(".cfg"):   # Filter to only .cfg files
                file_path = os.path.join(dest_folder, file)
                os.remove(file_path)    # Remove the file
                print(f"Deleted existing .cfg file: {file_path}")


def delete_nvram_file(router_folder):
    """
    Deletes any NVRAM files in the router folder.
    NVRAM files can be problematic in certain scenarios, so they are removed before adding new configurations.
    """
    if os.path.exists(router_folder):
        for file in os.listdir(router_folder):
            if "nvram" in file:  # Search for files containing 'nvram' in their name
                file_path = os.path.join(router_folder, file)
                os.remove(file_path)    # Remove the file
                print(f"Deleted NVRAM file: {file_path}")


def move_configs():
    """
    This function moves configuration files from the source folder to the appropriate destination folder
    based on the router folder and router number mapping provided in 'router_folder_corresp'.
    It also handles the deletion of existing configuration and NVRAM files as needed.
    """
    # Iterate over each router in the mapping dictionary
    for router_number, (folder_id, router_name) in router_folder_corresp.items():
        router_folder = os.path.join(destination, folder_id)  # Router's main folder path
        dest_folder = os.path.join(router_folder, "configs")  # Path to the 'configs' subfolder
        src_file = os.path.join(config_folder, f"R{router_number}_startup-config.cfg")  # Source config file
        dest_file = os.path.join(dest_folder, f"{router_name}_startup-config.cfg") # Destination config file with router's local ID

        # Delete NVRAM file in the router's main folder before moving the new config file
        delete_nvram_file(router_folder)

        # Delete any existing .cfg files in the destination config folder to avoid conflicts
        if os.path.exists(dest_folder):
            delete_existing_cfg_files(dest_folder)

        # Move the new configuration file from the source to the destination folder
        if os.path.exists(src_file):
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)    # Create the destination folder if it doesn't exist
            shutil.move(src_file, dest_file)    # Move the config file to the destination
            print(f"Moved {src_file} to {dest_file}")
        else:
            print(f"Source file not found: {src_file}")

if __name__ == "__main__":
    move_configs()  # Call the function to start moving the config files
