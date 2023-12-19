import ecdsa
import hashlib
import base58
from concurrent.futures import ThreadPoolExecutor
import time
import math
from tqdm import tqdm

def generate_bitcoin_address(private_key_bytes):
    sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    compressed_public_key = vk.to_string("compressed")

    sha256_hash = hashlib.sha256(compressed_public_key).digest()
    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
    extended_ripemd160_hash = b'\x00' + ripemd160_hash
    checksum = hashlib.sha256(hashlib.sha256(extended_ripemd160_hash).digest()).digest()[:4]
    extended_hash_with_checksum = extended_ripemd160_hash + checksum
    bitcoin_address = base58.b58encode(extended_hash_with_checksum).decode('utf-8')

    return bitcoin_address

def search_range(start, end, target_address):
    for number in range(start, end + 1):
        hex_private_key = hex(number)[2:].rjust(64, '0')
        private_key_bytes = bytes.fromhex(hex_private_key)
        generated_address = generate_bitcoin_address(private_key_bytes)

        if generated_address == target_address:
            return hex_private_key

def find_matching_address_in_range(start, end, target_address):
    mid = math.ceil((end - start) / 12)
    subrange_info = []

    for i in range(12):
        subrange_start = start + i * mid
        subrange_end = subrange_start + mid - 1 if i < 11 else end

        hex_start = hex(subrange_start)[2:].rjust(64, '0')
        hex_end = hex(subrange_end)[2:].rjust(64, '0')

        private_key_bytes_start = bytes.fromhex(hex_start)
        private_key_bytes_end = bytes.fromhex(hex_end)

        address_start = generate_bitcoin_address(private_key_bytes_start)
        address_end = generate_bitcoin_address(private_key_bytes_end)

        subrange_info.append({
            "subrange_number": i + 1,
            "decimal_range": (subrange_start, subrange_end),
            "hexadecimal_range": (hex_start, hex_end),
            "address_range": (address_start, address_end),
        })

    for info in subrange_info:
        print(f"Subrange {info['subrange_number']}:")
        print(f"  Decimal Range: {info['decimal_range'][0]} to {info['decimal_range'][1]}")
        print(f"  Hexadecimal Range: {info['hexadecimal_range'][0]} to {info['hexadecimal_range'][1]}")
        print(f"  Address Range: {info['address_range'][0]} to {info['address_range'][1]}")
        print()

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = []
        progress_bar = tqdm(total=12, desc="Overall Progress")

        for i in range(12):
            subrange_start = start + i * mid
            subrange_end = subrange_start + mid - 1 if i < 11 else end

            progress_bar.set_postfix_str(f"Subrange {i + 1}")
            futures.append(executor.submit(search_range, subrange_start, subrange_end, target_address))

        start_time = time.time()

        matched_hex_key = None

        for future in futures:
            result = future.result()
            progress_bar.update(1)
            if result:
                matched_hex_key = result
                break

        progress_bar.close()

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Time taken: {elapsed_time:.5f} seconds")

        if matched_hex_key:
            print(f"Match found! Hex key: {matched_hex_key}")
            return matched_hex_key
        else:
            print(f"No match found for the specified Bitcoin address: {target_address}")
            return None

# Get user input for the range
start = int(input("Enter the start number: "))
end = int(input("Enter the end number: "))
target_address = 'Input the address Here'
print("The Bitcoin Address this program is searching for is:", target_address)

# Validate the range
if start > end:
    print("Invalid range. The start number should be less than or equal to the end number.")
else:
    # Search for the specified Bitcoin address within the specified range
    matched_hex_key = find_matching_address_in_range(start, end, target_address)

    if matched_hex_key:
        # Save the matched hexadecimal private key to a file or use it as needed
        with open("matched_hex_key.txt", "w") as file:
            file.write(matched_hex_key)
        print(f"Matched hexadecimal private key saved to 'matched_hex_key.txt'.")
