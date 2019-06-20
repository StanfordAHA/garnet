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
|chain_wen_in_reg_sel|3|1||
|chain_wen_in_reg_value|4|1||
|circular_en|5|1||
|depth|6|16||
|dimensionality|7|4||
|enable_chain|8|1||
|flush_reg_sel|9|1||
|flush_reg_value|10|1||
|iter_cnt|11|32||
|mode|12|2||
|range_0|13|32||
|range_1|14|32||
|range_2|15|32||
|range_3|16|32||
|range_4|17|32||
|range_5|18|32||
|rate_matched|19|1||
|ren_in_reg_sel|20|1||
|ren_in_reg_value|21|1||
|starting_addr|22|16||
|stencil_width|23|16||
|stride_0|24|16||
|stride_1|25|16||
|stride_2|26|16||
|stride_3|27|16||
|stride_4|28|16||
|stride_5|29|16||
|switch_db_reg_sel|30|1||
|switch_db_reg_value|31|1||
|tile_en|32|1||
|wen_in_reg_sel|33|1||
|wen_in_reg_value|34|1||

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
  **NOTE**: If using double buffer in manual mode - necessary software fix is to set depth
  to the maximum size - if using 1 tile - set `depth = 512` 
* **Almost Count** specifies when the almost_full and almost_empty output
  signals are triggered in FIFO mode (it is unused in Line Buffer and SRAM
  modes). See the FIFO mode specification below for more details.
* **Enable Chain** allows this tile to be hooked up to another memory core tile
  to create effectively larger memories.
