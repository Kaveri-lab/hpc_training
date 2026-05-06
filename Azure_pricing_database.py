import os, sys, time, h5py, numpy as np, requests
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.subscription import SubscriptionClient
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─────────────────────────────────────────────
# CREDENTIALS 
# ─────────────────────────────────────────────
TENANT_ID       = "_"
CLIENT_ID       = "_"
CLIENT_SECRET   = "_"
SUBSCRIPTION_ID = "_"
# ─────────────────────────────────────────────

BASE_URL     = "https://prices.azure.com/api/retail/prices"
OUTPUT_FILE  = os.path.expanduser("~/azure_project/azure_pricing.h5")
DISPLAY_FILE = os.path.expanduser("~/azure_project/azure_pricing_display.txt")

def get_session():
    session = requests.Session()
    retry   = Retry(total=5, backoff_factor=3, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session

def get_azure_clients():
    print("\n[1/6] Connecting to Azure with your credentials...")
    try:
        credential     = ClientSecretCredential(
            tenant_id     = TENANT_ID,
            client_id     = CLIENT_ID,
            client_secret = CLIENT_SECRET
        )
        compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)
        sub_client     = SubscriptionClient(credential)
        list(compute_client.virtual_machine_sizes.list("eastus"))[:1]
        print(f"      Done! Connected successfully")
        return compute_client, sub_client
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

def fetch_accessible_regions(sub_client):
    """
    Fetch only 53 standard accessible regions
    Excludes Jio India and restricted regions
    """
    print("\n[2/6] Fetching your 53 accessible regions...")

    # These 5 regions are excluded
    EXCLUDE = {
        "jioindiacentral",
        "jioindiawest",
        "francesouth",
        "germanynorth",
        "norwaywest"
    }

    try:
        regions = []
        for location in sub_client.subscriptions.list_locations(SUBSCRIPTION_ID):
            if location.name not in EXCLUDE:
                regions.append(location.name)
        regions = sorted(regions)
        print(f"      Done! Found {len(regions)} regions")
        return regions
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

def fetch_sdk_specs(compute_client, region):
    """
    Get vCPU and Memory from Azure SDK
    Returns 1123 VMs with correct specs
    """
    try:
        specs = {}
        for vm in compute_client.virtual_machine_sizes.list(region):
            specs[vm.name] = {
                "vcpu":   vm.number_of_cores,
                "memory": round(vm.memory_in_mb / 1024, 2)
            }
        return specs
    except Exception as e:
        return {}

def fetch_region_prices(session, region):
    """
    Get ALL instances and prices from public API
    Returns complete list of 1452 VMs
    """
    params = {"$filter": (
        f"serviceName eq 'Virtual Machines' "
        f"and priceType eq 'Consumption' "
        f"and currencyCode eq 'USD' "
        f"and armRegionName eq '{region}'"
    )}
    prices = {}
    url    = BASE_URL

    while url:
        try:
            response = session.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            break

        for item in data.get("Items", []):
            sku_name = item.get("skuName", "")
            arm_sku  = item.get("armSkuName", "")
            price    = item.get("retailPrice", 0)
            product  = item.get("productName", "")

            if "Windows"          in sku_name: continue
            if "Windows"          in product:  continue
            if "Spot"             in sku_name: continue
            if "Low Priority"     in sku_name: continue
            if "Dev/Test"         in sku_name: continue
            if "Virtual Machines" not in product: continue
            if not arm_sku or price <= 0: continue

            # Keep lowest price per VM
            if arm_sku not in prices or price < prices[arm_sku]:
                prices[arm_sku] = price

        url    = data.get("NextPageLink")
        params = {}
        time.sleep(0.2)

    return prices

def fetch_region_data(session, compute_client, region):


    # Step 1: Get vCPU & Memory from SDK (1123 VMs)
    sdk_specs = fetch_sdk_specs(compute_client, region)

    # Step 2: Get complete instance list from API (1452 VMs)
    prices = fetch_region_prices(session, region)

    if not prices:
        return []

    instances = []
    for arm_sku, price in prices.items():
        specs = sdk_specs.get(arm_sku, {})
        instances.append({
            "instance": arm_sku,
            "price":    price,
            "vcpu":     specs.get("vcpu", 0),
            "memory":   specs.get("memory", 0.0),
        })

    return instances

def build_hierarchy(session, compute_client, regions):
    print(f"\n[3/6] Fetching VM data for each region...")
    print(f"      Processing {len(regions)} regions\n")

    region_data = {}
    total_vms   = 0

    for i, region in enumerate(regions, 1):
        print(f"      [{i:3}/{len(regions)}] {region}...", end="\r")
        instances = fetch_region_data(session, compute_client, region)
        if instances:
            region_data[region] = instances
            total_vms += len(instances)

    print(f"\n\n      Done! {len(region_data)} regions, {total_vms:,} VMs")
    return region_data

def write_hdf5(region_data):
    """Write all data to HDF5 file"""
    print(f"\n[4/6] Writing HDF5 file...")
    with h5py.File(OUTPUT_FILE, "w") as f:
        ag = f.create_group("Azure")
        for region, instances in sorted(region_data.items()):
            rg = ag.create_group(region)
            rg.create_dataset("Instance",         data=np.array([i["instance"] for i in instances], dtype=h5py.string_dtype()))
            rg.create_dataset("Instance Pricing", data=np.array([i["price"]    for i in instances], dtype=np.float64))
            rg.create_dataset("Memory",           data=np.array([i["memory"]   for i in instances], dtype=np.float64))
            rg.create_dataset("vCPU",             data=np.array([i["vcpu"]     for i in instances], dtype=np.int32))
    print(f"      Done! HDF5 file saved: {OUTPUT_FILE}")

def write_display_file(region_data):
    """
    Write readable text file
    View with: cat azure_pricing_display.txt
    """
    print(f"\n[5/6] Writing display text file...")
    total = sum(len(v) for v in region_data.values())

    with open(DISPLAY_FILE, "w") as f:
        # Header
        f.write("=" * 75 + "\n")
        f.write("  AZURE VM PRICING DATABASE\n")
        f.write("  Team: Nidhi & Kaveri Pandappa Kallennavar\n")
        f.write("=" * 75 + "\n")
        f.write(f"  Total Regions : {len(region_data)}\n")
        f.write(f"  Total VMs     : {total:,}\n")
        f.write("=" * 75 + "\n\n")

        # Regions summary
        f.write("REGIONS SUMMARY:\n")
        f.write("-" * 45 + "\n")
        for region in sorted(region_data.keys()):
            count = len(region_data[region])
            f.write(f"  {region:<30} {count:>5} VMs\n")
        f.write("\n")

        # Detailed data per region
        f.write("=" * 75 + "\n")
        f.write("DETAILED DATA PER REGION:\n")
        f.write("=" * 75 + "\n")

        for region in sorted(region_data.keys()):
            instances = region_data[region]
            f.write(f"\nREGION: {region}  ({len(instances)} VMs)\n")
            f.write("-" * 75 + "\n")
            f.write(f"{'Instance':<35} {'Price/hr':>10} {'Memory(GB)':>12} {'vCPU':>6}\n")
            f.write("-" * 75 + "\n")
            for i in instances:
                f.write(
                    f"{i['instance']:<35} "
                    f"${i['price']:>9.4f} "
                    f"{i['memory']:>12.1f} "
                    f"{i['vcpu']:>6}\n"
                )
            f.write("\n")

    print(f"      Done! Display file saved: {DISPLAY_FILE}")

def show_summary(region_data):
    """Print summary on screen"""
    total = sum(len(v) for v in region_data.values())

    print(f"\n[6/6] Complete!")
    print(f"\n{'='*75}")
    print(f"  AZURE PRICING DATABASE - SUMMARY")
    print(f"{'='*75}")
    print(f"  Total Regions : {len(region_data)}")
    print(f"  Total VMs     : {total:,}")
    print(f"{'='*75}")

    # Show all regions
    print(f"\n  REGIONS:")
    print(f"  {'-'*45}")
    for region in sorted(region_data.keys()):
        count = len(region_data[region])
        print(f"  {region:<30} {count:>5} VMs")

    # Show sample from eastus
    if "eastus" in region_data:
        instances = region_data["eastus"]
        print(f"\n  SAMPLE — eastus (first 5 VMs):")
        print(f"  {'-'*75}")
        print(f"  {'Instance':<35} {'Price/hr':>10} {'Memory(GB)':>12} {'vCPU':>6}")
        print(f"  {'-'*75}")
        for i in instances[:5]:
            print(f"  {i['instance']:<35} ${i['price']:>9.4f} {i['memory']:>12.1f} {i['vcpu']:>6}")
        print(f"  ... and {len(instances)-5} more VMs in eastus")

    print(f"\n{'='*75}")
    print(f"  Files generated:")
    print(f"  1. HDF5    : {OUTPUT_FILE}")
    print(f"  2. Display : {DISPLAY_FILE}")
    print(f"\n  To view all data on screen:")
    print(f"  cat ~/azure_project/azure_pricing_display.txt")
    print(f"\n  Copy to Desktop:")
    print(f"  cp ~/azure_project/azure_pricing.h5 /mnt/c/Users/user/Desktop/")
    print(f"\n  View HDF5 online:")
    print(f"  https://myhdf5.hdfgroup.org")
    print(f"{'='*75}\n")

def main():
    if "your-" in TENANT_ID:
        print("[ERROR] Please update your credentials!")
        sys.exit(1)

    print("=" * 75)
    print("  Azure VM Pricing -> HDF5 Generator")
    print("  Team: Nidhi & Kaveri Pandappa Kallennavar")
    print("  Mode: Combined — Prices API + Azure SDK")
    print("=" * 75)

    session                    = get_session()
    compute_client, sub_client = get_azure_clients()
    regions                    = fetch_accessible_regions(sub_client)
    region_data                = build_hierarchy(session, compute_client, regions)
    write_hdf5(region_data)
    write_display_file(region_data)
    show_summary(region_data)

if __name__ == "__main__":
    main()