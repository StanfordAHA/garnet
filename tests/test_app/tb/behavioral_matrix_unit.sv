/*=============================================================================
** Module: behavioral_matrix_unit.sv
** Description:
**              A behavioral matrix unit with ready-valid interface that drives
                the CGRA 
** Author: Michael Oduoza
** Change history:  12/31/2025 - Implement the first version
**===========================================================================*/
module behavioral_matrix_unit #(
    parameter int NUM_TX = 16384,
    parameter MU_DATAWIDTH = 16,
    parameter OC_0 = 32
) (
    input logic clk,
    input logic reset,
    input logic cgra2mu_ready,
    output logic mu2cgra_valid,
    output logic [MU_DATAWIDTH-1:0] mu2cgra [OC_0-1:0]
);

    integer tx_num = 0;
  
    logic [MU_DATAWIDTH-1:0] mu2cgra_data [0:NUM_TX][OC_0-1:0];
    logic mu2cgra_valid_data[0:NUM_TX]; 

    initial begin
        // Read data from file
        string MU2CGRA_FILENAME = "/aha/garnet/tests/test_app/mu2cgra_synthetic_data/mu2cgra.txt";
        string MU2CGRA_VALID_FILENAME = "/aha/garnet/tests/test_app/mu2cgra_synthetic_data/mu2cgra_valid.txt";

        $display("Reading mu2cgra data from %s", MU2CGRA_FILENAME);
        $display("Reading mu2cgra_valid data from %s", MU2CGRA_VALID_FILENAME);

        $readmemh(MU2CGRA_FILENAME, mu2cgra_data);
        $readmemh(MU2CGRA_VALID_FILENAME, mu2cgra_valid_data);

        mu2cgra_valid = 0;

        // This delay is temporary till I fix the testbench to remove data streaming for MU apps. (delay till after flush)
        #(3050*`CLK_PERIOD)
        while(tx_num < NUM_TX) begin
            #(`CLK_PERIOD)
            mu2cgra = mu2cgra_data[tx_num];
            mu2cgra_valid = mu2cgra_valid_data[tx_num];

            if (cgra2mu_ready|| !mu2cgra_valid) begin
                tx_num++;
            end

        //    @(posedge clk); 
        end
    
        #(`CLK_PERIOD)
        mu2cgra_valid = 0;
    end

endmodule