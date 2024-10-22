task Environment_write_bs();

// TODO NEXT this should be a task e.g. 'env_write_bs'
    //  // Want to do one of these where kernel=kernel[0]
    //  task Environment::write_bs(Kernel kernel);
    //      realtime start_time, end_time;
    //      $timeformat(-9, 2, " ns");
    //      repeat (10) @(vifc_proc.cbd);
    //      start_time = $realtime;
    //      $display("[%s] write bitstream to glb start at %0t", kernel.name, start_time);
    //      proc_drv.write_bs(kernel.bs_start_addr, kernel.bitstream_data);
    //      end_time = $realtime;
    //      $display("[%s] write bitstream to glb end at %0t", kernel.name, end_time);
    //      $display("[%s] It takes %0t time to write the bitstream to glb.", kernel.name,
    //               end_time - start_time);
    //  endtask

    $timeformat(-9, 2, " ns", 0);
    // repeat (10) @(vifc_proc.cbd);
    repeat (10) @(p_ifc.clk);
    start_time = $realtime;
    $display("[%s] write bitstream to glb start at %0t", kernels[0].name, start_time);

      // proc_drv  = new(p_ifc, proc_lock);
      // proc_drv.write_bs(kernels[0].bs_start_addr, kernels[0].bitstream_data);

      ProcDriver_write_bs_start_addr = kernels[0].bs_start_addr;
      ProcDriver_write_bs_bs_q = kernels[0].bitstream_data;
      ProcDriver_write_bs();

    end_time = $realtime;
    $display("[%s] write bitstream to glb end at %0t", kernels[0].name, end_time);
    $display("[%s] It takes %0t time to write the bitstream to glb.", kernels[0].name,
             end_time - start_time);


endtask // Environment_write_bs

