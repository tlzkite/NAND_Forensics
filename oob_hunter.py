#!/usr/bin/env python3

# Bill Powell - 2025

import sys
from collections import defaultdict
from math import log2

# ======= CONFIGURABLE DEFAULTS =======
SAMPLE_PAGES = 1000      # Number of pages to analyze for each test
SCAN_STEP = 4            # Step size (in bytes) for offset scan
MAX_PAGES_TO_SCAN = 8    # How far past the page to scan, in pages
# =====================================

# Common NAND configurations
COMMON_LAYOUTS = [
    (512, 16),     # small block NAND
    (2048, 64),    # common large block
    (4096, 128),   # big NAND
    (8192, 256),   # modern chips
]

def byte_entropy(block):
    if not block:
        return 0
    freq = defaultdict(int)
    for b in block:
        freq[b] += 1
    total = len(block)
    entropy = -sum((count / total) * log2(count / total) for count in freq.values())
    return entropy

def analyze_oob_offsets(data, page_size, oob_size, sample_pages, max_pages_to_scan):
    max_offset = max_pages_to_scan * page_size
    offset_scores = []

    for offset in range(0, max_offset, SCAN_STEP):
        total_entropy = 0
        total_ff_ratio = 0
        samples = 0

        for i in range(sample_pages):
            base = i * (page_size + oob_size)
            oob_candidate = data[base + offset : base + offset + oob_size]
            if len(oob_candidate) != oob_size:
                continue

            entropy = byte_entropy(oob_candidate)
            ff_ratio = oob_candidate.count(0xFF) / oob_size

            total_entropy += entropy
            total_ff_ratio += ff_ratio
            samples += 1

        if samples == 0:
            continue

        avg_entropy = total_entropy / samples
        avg_ff_ratio = total_ff_ratio / samples
        score = (1 - avg_entropy / 8) + avg_ff_ratio

        offset_scores.append((offset, avg_entropy, avg_ff_ratio, score))

    offset_scores.sort(key=lambda x: x[3], reverse=True)
    return offset_scores[:5]  # Top 5 candidates

def run_autoscan(file_path, sample_pages, max_pages_to_scan):
    with open(file_path, "rb") as f:
        raw_data = f.read()

    print(f"\n[+] Scanning NAND dump: {file_path}")
    print(f"[+] Using {sample_pages} sample pages per layout\n")

    for page_size, oob_size in COMMON_LAYOUTS:
        total_chunk_size = (page_size + oob_size) * sample_pages
        if len(raw_data) < total_chunk_size:
            print(f"[-] Skipping page size {page_size} (not enough data for {sample_pages} pages)")
            continue

        data = raw_data[:total_chunk_size]

        print(f"=== Testing Page: {page_size} | OOB: {oob_size} ===")
        best_offsets = analyze_oob_offsets(data, page_size, oob_size, sample_pages, max_pages_to_scan)

        for offset, entropy, ff_ratio, score in best_offsets:
            print(f"Offset {offset:5d} (0x{offset:04X}) | Entropy: {entropy:.2f} | FF Ratio: {ff_ratio:.2f} | Score: {score:.2f}")
        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 autoscan_oob.py <nand_dump.bin> [sample_pages] [max_pages_to_scan]")
        sys.exit(1)

    file_path = sys.argv[1]
    sample_pages = int(sys.argv[2]) if len(sys.argv) > 2 else SAMPLE_PAGES
    max_pages_to_scan = int(sys.argv[3]) if len(sys.argv) > 3 else MAX_PAGES_TO_SCAN

    run_autoscan(file_path, sample_pages, max_pages_to_scan)
