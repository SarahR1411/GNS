import os
import shutil


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
    12 : ("fce06220-5b24-4eab-89c2-acdf0a798679", "i14")
}

config_folder = "config_files"
destination = "/home/srmili/GNS3/projects/GNS_Project1/project-files/dynamips"

def delete_existing_cfg_files(dest_folder):
    """Delete all .cfg files in the destination folder."""
    if os.path.exists(dest_folder):
        for file in os.listdir(dest_folder):
            if file.endswith(".cfg"):
                file_path = os.path.join(dest_folder, file)
                os.remove(file_path)
                print(f"Deleted existing .cfg file: {file_path}")

def delete_nvram_file(router_folder):
    """Delete the NVRAM file in the router folder (not in the configs subfolder)."""
    if os.path.exists(router_folder):
        for file in os.listdir(router_folder):
            if "nvram" in file:  # find any file containing 'nvram' in its name
                file_path = os.path.join(router_folder, file)
                os.remove(file_path)
                print(f"Deleted NVRAM file: {file_path}")

def move_configs():
    for router_number, (folder_id, router_name) in router_folder_corresp.items():
        router_folder = os.path.join(destination, folder_id)  # Router's main folder
        dest_folder = os.path.join(router_folder, "configs")  # 'configs' subfolder
        src_file = os.path.join(config_folder, f"R{router_number}_startup-config.cfg")
        dest_file = os.path.join(dest_folder, f"{router_name}_startup-config.cfg") #the config file must contain the node's local id or else GNS won't recognize it

        # Delete NVRAM file in the router's main folder
        delete_nvram_file(router_folder)

        # Delete existing .cfg files in the 'configs' subfolder
        if os.path.exists(dest_folder):
            delete_existing_cfg_files(dest_folder)

        # Move the new config file
        if os.path.exists(src_file):
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            shutil.move(src_file, dest_file)
            print(f"Moved {src_file} to {dest_file}")
        else:
            print(f"Source file not found: {src_file}")

if __name__ == "__main__":
    move_configs()
