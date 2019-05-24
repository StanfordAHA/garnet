This corresponds to the tests for the
[memory_core](https://github.com/StanfordAHA/CGRAGenerator/tree/master/hardware/generator_z/memory_core)
directory of the first generation CGRA.

See [./memory_core](./memory_core) for the functional model and implementation.

# Implemented Tests
* **test_passthru_fifo**
  * tests reading and writing the same value on the same clock - passing through a value
* **test_fifo_arb**
  * Does ten iterations (need to parameterize this) of pushes/pops of random integers
* **test_general_fifo**
  * Makes pushes and pops to the fifo sequentially/at a set cadence
* **test_db_basic_read**
  * Read out the basic 3x3x3 data cube with manual switch
* **test_db_long_read**
  * Similar to test_db_basic_read, but with different output address that gives
  * longer read access than write 
* **test_db_read_mode**
  * Fully manual state-machine operation - manual wen/ren/switch
* **test_db_arbitrary_rw_addr**
  * Test R+W at same time in arbitrary mode
* **test_db_arbitrary_addr**
  * Test W, then R, then switch, then R in arbitrary mode
* **test_db_auto**
  * Automatic generation mode for basic 3x3x3 data cube
* **test_db_auto2**
  * Same as db_long_read in automatic mode
* **test_sram_magma**
  * Make random writes and reads to/from sram
  
## Desired Tests
* More specific linebuffer test (rowbuffer - one in test_interconnect)
* Test full/empty fifo
* Test more stencil dimensions
* Test DB valid
* Test const mode config - especially for ROM/LUT mode for Nikhil





