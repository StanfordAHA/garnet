# Configuration
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
|flush_reg_sel|7|1||
|flush_reg_value|8|1||
|iter_cnt|9|32||
|mode|10|2||
|range_0|11|32||
|range_1|12|32||
|range_2|13|32||
|range_3|14|32||
|range_4|15|32||
|range_5|16|32||
|range_6|17|32||
|range_7|18|32||
|read_mode|19|1||
|ren_in_reg_sel|20|1||
|ren_in_reg_value|21|1||
|starting_addr|22|32||
|stencil_width|23|32||
|stride_0|24|32||
|stride_1|25|32||
|stride_2|26|32||
|stride_3|27|32||
|stride_4|28|32||
|stride_5|29|32||
|stride_6|30|32||
|stride_7|31|32||
|switch_db_reg_sel|32|1||
|switch_db_reg_value|33|1||
|tile_en|34|1||
|wen_in_reg_sel|35|1||
|wen_in_reg_value|36|1||

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
