from config import HPL_CFG

def ask_compiler():
    # for stream default intel, for hpl intel and aocc
    keys    = [k for k in HPL_CFG["compilers"] if k != "default"]
    default = HPL_CFG["compilers"]["default"]

    print("\nAvailable compilers for HPL:")
    for i, key in enumerate(keys, 1):
        tag = " (default)" if key == default else ""
        print(f"  {i}. {key}{tag}")

    while True:
        choice = input("Pick compiler (press Enter for default): ").strip()
        if choice == "":
            print(f"Using: {default}")
            return default
        if choice.isdigit() and 1 <= int(choice) <= len(keys):
            selected = keys[int(choice) - 1]
            print(f"Using: {selected}")
            return selected
        print(f"Enter a number between 1 and {len(keys)}")
