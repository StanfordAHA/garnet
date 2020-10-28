
typedef enum int {
    IDLE = 0,
    QUEUED = 1,
    CONFIG = 2,
    RUNNING = 3,
    FINISH = 4
} app_state_t;

class KernelDriver;
    vAxilIfcDriver vifc_axil;
    vProcIfcDriver vifc_proc;

    extern function new(Kernel kernels, vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc);
    extern task run();
    extern task test();
    extern task post_test();
endclass

function GarnetDriver::new(Kernel kernels, vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc);
    this.kernels = kernels;
    this.num_app = kernels.size();
    this.vifc_axil = vifc_axil;
    this.vifc_proc = vifc_proc;
endfunction

    case (app_states[j])
        QUEUED: begin
            queue_time[j] -= 1;
            if (queue_time[j] <= 0) begin
                $display("start to config for app %0d @%0d", j, $time);
                app_states[j] = CONFIG;
            end
            ##1;
        end
        CONFIG: begin
            #(CLOCK_PERIOD-1);
            foreach (bitstreams[j][k]) begin
                // obtain the lock
                config_write = 1;
                config_read  = 0;
                config_addr  = bitstreams[j][k].addr;
                config_data  = bitstreams[j][k].data;
                #(CLOCK_PERIOD);
                // read back
                config_write = 0;
                config_read  = 1;
                #(CLOCK_PERIOD);
                IOHelper::assert_(read_config_data == bitstreams[j][k].data, $sformatf("[%0d] expected to read out %08X. got %08X", k, bitstreams[j][k].data, read_config_data));
            end
            // finished configuration
            config_write = 0;
            config_read = 0;
            #1;
            // need to assert reset and then start
            resets[j] = 1;
            #(CLOCK_PERIOD);
            resets[j] = 0;
            // start the application
            app_states[j] = RUNNING;
            $display("start to run app %0d @%0d", j, $time);
        end
        RUNNING: begin
            if (input_data[j].size()) begin
                inputs[j] = input_data[j].pop_front() & 'hFF;
            end
            if (valids[j]) begin
                output_data[j].push_back(outputs[j][7:0]);
            end
            if (output_data[j].size() == output_sizes[j]) begin
                ##20;
                $display("App %0d finished @%0d", j, $time);
                app_states[j] = FINISH;
            end
            #(CLOCK_PERIOD);
        end
        default: begin
            // nothing
            ##1;
        end
    endcase
