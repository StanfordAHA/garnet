def generate_main(app_name, input_list, output_list):
    f = open("main.c", "w")
    
    
    input_list = [input.strip("tensor_").strip(".raw") for input in input_list]
    output_list = [output.strip("tensor_").strip(".raw") for output in output_list]
    
    string = f'''#include <stdio.h>
#include <stdlib.h>
#include \"diag/trace.h\"

#include \"amberm3vx_hal.h\"
#include \"{app_name}_script.h\"
#include \"{app_name}_input_script.h\"
#include \"{app_name}_unrolling.h\"
#include \"{app_name}_reg_write.h\"
#include \"{app_name}_gold.h\"
#include \"glb.h\"
#include \"glc.h\"
#include \"memory.h\"
#include \"define.h\"

HAL_PtfmCtrl_t PtfmCtl;

int main(int argc, char* argv[])
{{
  HAL_UNUSED(argc);
  HAL_UNUSED(argv);

  // Send a greeting to the trace device
  int status = HAL_PtfmCtrl_Initialize( & PtfmCtl);
  trace_printf(\"Status \");

  u32 cgra_mask = (1 << AHASOC_PCTRL_CGRA_Pos);
  u32 sys_mask = (1 << AHASOC_PCTRL_SYS_Pos);


  // Slower clocks for configuration
  status = HAL_PtfmCtrl_SelectClock( & PtfmCtl, cgra_mask, 0); // 2^1 = 2 60/2 = 30
  status = HAL_PtfmCtrl_SelectClock( & PtfmCtl, sys_mask, 3); // 2^2 = 4 60/4 = 15
  status = HAL_PtfmCtrl_DisableCG( & PtfmCtl, cgra_mask);
  status = HAL_PtfmCtrl_ClearReset( & PtfmCtl, cgra_mask);

  HAL_Cgra_Glc_WriteReg(GLC_CGRA_STALL_R, 0xFFFF);

  trace_printf(\"Config App\\n\");

  for (int config = 0; config < app_size; config++){{
	  HAL_Cgra_Tile_WriteReg(app_addrs_script[config], app_datas_script[config]);
  }}


  trace_printf(\"\\nCheck Config\\n\");
  for (int config = 0; config < app_size; config++){{
	  uint32_t read_data = HAL_Cgra_Tile_ReadReg(app_addrs_script[config]);
	  uint32_t addr = app_addrs_script[config];
	  uint32_t gold = app_datas_script[config];

	  if ( read_data != gold){{
		  trace_printf(\"config error: %d \", config);
		  trace_printf(\"address: %lx \", addr);
		  trace_printf(\"read_data %lx \", read_data);
		  trace_printf(\"gold data %lx\\n\", gold);
	  }}
  }}


  // Faster clocks for App
  status = HAL_PtfmCtrl_SelectClock( & PtfmCtl, sys_mask, 1); // 2^2 = 4 60/4 = 15

  // Check if inputs look alright
  uint16_t* input_read_base = AHASOC_CGRA_DATA_BASE;
'''

    f.write(string)

    for i in range(len(input_list)):
        f.write(f'  input_read_base = AHASOC_CGRA_DATA_BASE + 0x40000*{i};\n')
        f.write(f'  trace_printf("first location: %lx\\n", input_read_base[0]);\n')

    string = f'''  
  trace_printf(\"\\nCONFIG GLB\\n\");
  app_glb_config();

  trace_printf(\"\\nAPP Prep\\n\");

  HAL_Cgra_Glc_WriteReg(GLC_GLB_FLUSH_CROSSBAR_R, 0);
  HAL_Cgra_Glc_WriteReg(GLC_CGRA_STALL_R, 0x0);
  HAL_Cgra_Glc_WriteReg(GLC_GLOBAL_IER_R, 1);
  HAL_Cgra_Glc_WriteReg(GLC_STRM_F2G_IER_R, 0xffff);
  HAL_Cgra_Glc_WriteReg(GLC_STRM_G2F_IER_R, 0xffff);


  trace_printf(\"\\n** Run  **\\n\");
  const uint32_t start_addr = 0x0;
  const uint32_t read_start_addr = 0x20000;

'''

    f.write(string)

    for i in range(len(output_list)):
        f.write(f'  uint16_t* output_read_base{i} = (uint16_t*) (AHASOC_CGRA_DATA_BASE + read_start_addr + 0x40000*{i});\n')

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
	HAL_Cgra_Glc_WriteReg(GLC_STREAM_START_PULSE_R, stream_pulse_f2g << 16 | stream_pulse_g2f); // pulsed reg.

	// Wait for inputs to finish sending
    while(HAL_Cgra_Glc_ReadReg(GLC_STRM_G2F_ISR_R) != stream_pulse_g2f){{
        //cnt++;
    }}
    // Clear input statuses
    HAL_Cgra_Glc_WriteReg(GLC_STRM_G2F_ISR_R, stream_pulse_g2f);

    // Update Input Pointers
    update_glb_input(run);


    // Wait for outputs to all fill in
    while(HAL_Cgra_Glc_ReadReg(GLC_STRM_F2G_ISR_R) != stream_pulse_f2g){{
        //cnt++;
    }}

    // Clear output statuses
    HAL_Cgra_Glc_WriteReg(GLC_STRM_F2G_ISR_R, stream_pulse_f2g);

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
        f.write(f'    HAL_Cgra_Glb_WriteReg(0x100 * {i} + GLB_ST_DMA_HEADER_0_START_ADDR_R, 0x20000 + 0x40000*{i} + {output}_idx*2);\n')


    string = f'''
  }}

  // 5. Read cycle counter
  cycles = DWT->CYCCNT;

  // 6. Disable cycle counter
  DWT->CTRL &= ~CoreDebug_DEMCR_TRCENA_Msk;

  trace_printf(\"total cycles %d\\n\", cycles*2);

  trace_printf(\"wait for app\\n\");

  int errors = 0;

  uint16_t* output_read_base = AHASOC_CGRA_DATA_BASE + 0x40000*0 + 0x20000;

'''
    f.write(string)

    for i in range(len(output_list)):
        f.write(f'  output_read_base = AHASOC_CGRA_DATA_BASE + 0x40000*{i} + 0x20000;\n')
        f.write(f'  trace_printf("first location: %lx\\n", output_read_base[0]);\n')

    string = f'''

  trace_printf(\"check gold data\\n\");
  errors = check_gold_data();
  trace_printf(\"total errors: %d\\n\", errors);
  return 0;
}}
'''
    f.write(string)