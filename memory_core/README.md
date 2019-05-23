This corresponds to the
[memory_core](https://github.com/StanfordAHA/CGRAGenerator/tree/master/hardware/generator_z/memory_core)
directory of the first generation CGRA.

# Configuration
The memory core is configured as follows: when `config_en == 1` and
`config_addr[31:24] == 0`, the 32-bit configuration register (`config_mem`)
stores the value on the input wire `config_data`.

There are a range of features and register spaces associated with each.

| Feature | Index | Explanation                |
|---------|-------|----------------------------|
| Tile    | 0     | Used to configure the tile |
| SRAM1    | 1     | Access the first 256 words of SRAM |
| SRAM2    | 2     | Access the next 256 words of SRAM |
| SRAM3    | 3     | Access the next 256 words of SRAM |
| SRAM4    | 4     | Access the last 256 words of SRAM |

Within Feature 0 (Tile), there are a set of configuration registers with 
addresses and bit widths defined in the table

| Register Name  | Address | Width | Meaning | 
|----------------|---------|-------|---------|

|almost_count|0|4||
|arbitrary_addr|1|1||
|chain_idx|2|4||
|circular_en|3|1||
|depth|4|13||
|dimensionality|5|32||
|enable_chain|6|1||
|iter_cnt|7|32||
|mode|8|2||
|range_0|9|32||
|range_1|10|32||
|range_2|11|32||
|range_3|12|32||
|range_4|13|32||
|range_5|14|32||
|range_6|15|32||
|range_7|16|32||
|read_mode|17|1||
|starting_addr|18|32||
|stencil_width|19|32||
|stride_0|20|32||
|stride_1|21|32||
|stride_2|22|32||
|stride_3|23|32||
|stride_4|24|32||
|stride_5|25|32||
|stride_6|26|32||
|stride_7|27|32||
|tile_en|28|1||

and their interpretation is as follows:
* **Mode**
    * 0 → Line Buffer Mode
    * 1 → FIFO Mode
    * 2 → SRAM Mode
    * 3 → Double Buffer
* **Tile enable** is a global flag to enable or disable the entire memory core.
  It is active-high.
* **Depth** specifies the size of the line buffer or fifo in Line Buffer or
  FIFO mode, respectively.
* **Almost Count** specifies when the almost_full and almost_empty output
  signals are triggered in FIFO mode (it is unused in Line Buffer and SRAM
  modes). See the FIFO mode specification below for more details.
* **Enable Chain** allows this tile to be hooked up to another memory core tile
  to create effectively larger memories.
