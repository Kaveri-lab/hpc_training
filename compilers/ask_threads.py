from config import STREAM_CFG

def ask_threads():
    threads = STREAM_CFG["threads"]
    print("\nAvailable thread counts:")
    for i, t in enumerate(threads, 1):
        print(f"  [{i}] {t} thread(s)")
    while True:
        raw = input("  Pick a thread count: ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(threads):
                return threads[idx]
        except ValueError:
            pass
        print("  Invalid choice, try again.")
