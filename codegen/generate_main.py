def generate_main(app_name, input_list, output_list):
    f = open("main.c", "w")
    
    
    input_list = [input.strip("tensor_").strip(".raw") for input in input_list]
    output_list = [output.strip("tensor_").strip(".raw") for output in output_list]
    
    string = f'''#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "AHASOC.h"
#include "AHASOC_driver.h"
#include "garnet.h"
#include "uart_stdout.h"
#include "dma_utils.h"
#include "glb_memory.h"
#include \"./{app_name}/script.h\"
#include \"./{app_name}/input_script.h\"
#include \"./{app_name}/unrolling.h\"
#include \"./{app_name}/reg_write.h\"
// Skip gold checking
// #include \"./{app_name}/gold.h\"
#include "print_action.h"
#include "glb.h"
#include "glc.h"


int main(int argc, char* argv[])
{{

  AHASOC_PCTRL_TypeDef* pctrl = AHASOC_PCTRL;

  // Enable UART0 and CGRA.
  uint32_t mask = (1 << AHASOC_PCTRL_UART0_Pos) | (1 << AHASOC_PCTRL_DMA0_Pos) | (1 << AHASOC_PCTRL_CGRA_Pos);
  AHASOC_pctrl_SelectClock(pctrl, mask, 0x0);
  AHASOC_pctrl_DisableCG(pctrl, mask);
  AHASOC_pctrl_ClearReset(pctrl, mask);

  uint32_t sys_mask = (1 << AHASOC_PCTRL_SYS_Pos);
  AHASOC_pctrl_SelectClock(pctrl, sys_mask, 0x0);

  // UART init.
  UartStdOutInit();

  // Test banner message and revision number.
  puts("\\nAHASOC - App Test\\n");


  glc_reg_write(GLC_CGRA_STALL_R, 0xFFFF);

  printf(\"Config App\\n\");

  for (int config = 0; config < app_size; config++){{
	  write_cgra_reg(app_addrs_script[config], app_datas_script[config]);
  }}


  printf(\"\\nCheck Config\\n\");
  for (int config = 0; config < app_size; config++){{
	  uint32_t read_data = read_cgra_reg(app_addrs_script[config]);
	  uint32_t addr = app_addrs_script[config];
	  uint32_t gold = app_datas_script[config];

	  if ( read_data != gold){{
		  printf(\"config error: %d \", config);
		  printf(\"address: %lx \", addr);
		  printf(\"read_data %lx \", read_data);
		  printf(\"gold data %lx\\n\", gold);
	  }}
  }}

  move_input_data();

  // Check if inputs look alright
  uint16_t* input_read_base = AHASOC_CGRA_DATA_BASE;
'''

    f.write(string)

    for i in range(len(input_list)):
        f.write(f'  input_read_base = AHASOC_CGRA_DATA_BASE + 0x20000*{i};\n')
        f.write(f'  printf("first location: %lx\\n", input_read_base[0]);\n')

    string = f'''  
  printf(\"\\nCONFIG GLB\\n\");
  app_glb_config();

  printf(\"\\nAPP Prep\\n\");

  glc_reg_write(GLC_GLB_FLUSH_CROSSBAR_R, 0);
  glc_reg_write(GLC_CGRA_STALL_R, 0x0);
  glc_reg_write(GLC_GLOBAL_IER_R, 1);
  glc_reg_write(GLC_STRM_F2G_IER_R, 0xffff);
  glc_reg_write(GLC_STRM_G2F_IER_R, 0xffff);


  printf(\"\\n** Run  **\\n\");
  const uint32_t start_addr = 0x0;
  const uint32_t read_start_addr = 0x20000;

'''

    f.write(string)

    for i in range(len(output_list)):
        f.write(f'  uint16_t* output_read_base{i} = (uint16_t*) (AHASOC_CGRA_DATA_BASE + read_start_addr + 0x20000*{i});\n')

    f.write("\n")

    for output in output_list:
        f.write(f'  int {output}_idx = 0;\n')

    f.write("\n")

    string = f'''
  uint32_t cycles = 0;

  // 1. Enable trace and debug (if not enabled already)
  CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;

  // 2. Reset cycle counter
  DWT->CYCCNT = 0;

  // 3. Start cycle counter
  DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;

  for(int run=0; run < runs; run++){{

	// Start Input/Output GLB Tiles
	glc_reg_write(GLC_STREAM_START_PULSE_R, stream_pulse_f2g << 16 | stream_pulse_g2f); // pulsed reg.

	// Wait for inputs to finish sending
    while(glc_reg_read(GLC_STRM_G2F_ISR_R) != stream_pulse_g2f){{
        //cnt++;
    }}
    // Clear input statuses
    glc_reg_write(GLC_STRM_G2F_ISR_R, stream_pulse_g2f);

    // Update Input Pointers
    update_glb_input(run);


    // Wait for outputs to all fill in
    while(glc_reg_read(GLC_STRM_F2G_ISR_R) != stream_pulse_f2g){{
        //cnt++;
    }}

    // Clear output statuses
    glc_reg_write(GLC_STRM_F2G_ISR_R, stream_pulse_f2g);

    // Don't update for last tile
    if(run == runs-1){{
      break;
    }}

	// Updating output pointers
    int size;

'''
    f.write(string)

    idx = 0
    for i, output in enumerate(output_list):
        if "vals" not in output:
            f.write(f'    size = output_read_base{idx}[{output}_idx];\n')
            f.write(f'    int {output}_size = size + 1 + output_read_base{idx}[{output}_idx + size + 1] + 1;\n')
        else:
            f.write(f'    int {output}_size = output_read_base{idx}[X_mode_vals_idx] + 1;')
        idx += 1

    f.write("\n\n")

    for output in output_list:
        f.write(f'    {output}_idx += {output}_size;\n')

    string = f'''
    // GLB is byte addressable so 2x
'''
    f.write(string)


    for i, output in enumerate(output_list):
        f.write(f'    glb_reg_write(0x100 * {i} + GLB_ST_DMA_HEADER_0_START_ADDR_R, 0x20000 + 0x20000*{i} + {output}_idx*2);\n')


    string = f'''
  }}

  // 5. Read cycle counter
  cycles = DWT->CYCCNT;

  // 6. Disable cycle counter
  DWT->CTRL &= ~CoreDebug_DEMCR_TRCENA_Msk;

  printf(\"total cycles %d\\n\", cycles*2);

  printf(\"wait for app\\n\");

  int errors = 0;

  uint16_t* output_read_base = AHASOC_CGRA_DATA_BASE + 0x20000*0 + 0x10000;

'''
    f.write(string)

    for i in range(len(output_list)):
        f.write(f'  output_read_base = AHASOC_CGRA_DATA_BASE + 0x20000*{i} + 0x10000;\n')
        f.write(f'  printf("first location: %lx\\n", output_read_base[0]);\n')

    string = f'''

  printf(\"check gold data\\n\");

  // Skip error checking for power flow
  // errors = check_gold_data();
  
  printf(\"total errors: %d\\n\", errors);

  UartEndSimulation();

  return 0;
}}
'''
    f.write(string)
