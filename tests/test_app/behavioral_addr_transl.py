


def mu_addr_to_glb_addr(mu_addr: int, addr_width: int) -> int:
    binary_mu_addr = bin(mu_addr)[2:].zfill(addr_width)  # Convert to binary, remove the '0b' prefix, and pad to 21 bits
    print(f"MU: {binary_mu_addr}")
    binary_glb_addr = binary_mu_addr[0:3] + "00" + binary_mu_addr[3:16] + binary_mu_addr[18:]
    print(f"GB: {binary_glb_addr}")
    return int(binary_glb_addr, 2)



def glb_addr_to_mu_addr(glb_addr: int, addr_width: int) -> int:
    binary_glb_addr = bin(glb_addr)[2:].zfill(addr_width)  # Convert to binary, remove the '0b' prefix, and pad to 21 bits
    print(f"GB: {binary_glb_addr}")
    binary_mu_addr = binary_glb_addr[0:3] + binary_glb_addr[5:18] + binary_glb_addr[3:5] + binary_glb_addr[18:]
    print(f"MU: {binary_mu_addr}")
    return int(binary_mu_addr, 2)



if __name__ == "__main__":
   glb_base_addr = 1310720

   input_offset = glb_base_addr
   input_scale_offset = input_offset + (1 * 64 * 56 * 56)
   weight_offset = input_scale_offset + (1 * 1 * 56 * 56)
   weight_scale_offset = weight_offset + (64 * 64 * 3 * 3)
   bias_offset = weight_scale_offset + (64 * 1 * 3 * 3)


   print(mu_addr_to_glb_addr(input_offset, 21))
   print(mu_addr_to_glb_addr(input_scale_offset, 21))
   print(mu_addr_to_glb_addr(weight_offset, 21))
   print(mu_addr_to_glb_addr(weight_scale_offset, 21))
   print(mu_addr_to_glb_addr(bias_offset, 21))