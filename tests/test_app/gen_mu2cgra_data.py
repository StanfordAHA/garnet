import os

# Function to generate a hexadecimal pattern that wraps at 0x1000
def generate_wrapping_hex_pattern():
    row = 0
    while True:
        yield " ".join(f"{((row + col) % 0x1000):02X}" for col in range(16))
        row += 16

# Write the pattern to a text file
def write_data_to_file(filename, line_generator, num_lines):
    with open(filename, "w") as file:
        for _ in range(num_lines):
            file.write(next(line_generator) + "\n")



# Open the output file
def write_valid_data_to_file(filename, num_lines):
    valid_count = 0
    with open(filename, "w") as file:
        for i in range(num_lines):
            # Alternate between 0 and 1
            
            # file.write(f"1\n")
            if (i%4 == 1):
                file.write(f"1\n")
                valid_count += 1
            else:
                file.write("0\n")

    print(f"Output written to mu2cgra.txt and mu2cgra_valid.txt with {num_lines} total tokens and {valid_count} valid tokens.")

if __name__ == "__main__":
    # Desired number of lines 
    num_lines = 16384
    hex_pattern_generator = generate_wrapping_hex_pattern()

    mu2cgra_synthetic_data_dirname = "/aha/garnet/tests/test_app/mu2cgra_synthetic_data"
    if not os.path.exists(mu2cgra_synthetic_data_dirname):
        os.makedirs(mu2cgra_synthetic_data_dirname)

    write_data_to_file(f"{mu2cgra_synthetic_data_dirname}/mu2cgra.txt", hex_pattern_generator, num_lines) 
    write_valid_data_to_file(f"{mu2cgra_synthetic_data_dirname}/mu2cgra_valid.txt", num_lines)
