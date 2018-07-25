This corresponds to the original `memory_core` module.

This documentation was based on the Memory Core Specification provided to Lenny
by Raj.

# Configuration
The memory core is configured as follows: when `config_en == 1` and
`config_addr[31:24] == 0`, the 32-bit configuration register (`config_mem`)
stores the value on the input wire `config_data`.

The 32-bit configuration register `config_mem` has the following sub-fields

|      19      |     19:16    |  15:3 |      2      |  1:0 |
|--------------|--------------|-------|-------------|------|
| Enable Chain | Almost Count | Depth | Tile Enable | Mode |

and their interpretation is as follows:
* **Mode**
    * 0 → Line Buffer Mode
    * 1 → FIFO Mode
    * 2 → SRAM Mode
    * 3 → INVALID
* **Tile enable** is a global flag to enable or disable the entire memory core.
  It is active-high.
* **Depth** specifies the size of the line buffer or fifo in Line Buffer or
  FIFO mode, respectively.
* **Almost Count** specifies when the almost_full and almost_empty output
  signals are triggered in FIFO mode (it is unused in Line Buffer and SRAM
  modes). See the FIFO mode specification below for more details.
* **Enable Chain** allows this tile to be hooked up to another memory core tile
  to create effectively larger memories.
