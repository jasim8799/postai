import copyright_flags

def run_startup_checks():
    copyright_flags.ensure_flags_file()

    flags = copyright_flags.load_flags()
    if flags:
        print(f"✅ Found flagged videos in copyright_flags.json:")
        for code, info in flags.items():
            if info.get("flagged"):
                print(f"   - {code}: {info}")
    else:
        print("✅ No flagged videos at the moment.")
