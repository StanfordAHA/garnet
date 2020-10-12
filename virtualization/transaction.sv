/*=============================================================================
** Module: proc_transaction.sv
** Description:
**              program for transaction
** Author: Taeyoung Kong
** Change history:
**  10/12/2020 - Implement the first version
**===========================================================================*/
typedef enum {MEM, REG} trans_t;

virtual class Transaction;
    // number of transaction
    static int no_trans = 0;

    trans_t trans_type;
    extern function void display();

endclass

function void Transaction::display();
    $display("Transaction type: %s, \t Transaction number: %0d", trans_type.name(), no_trans);
endfunction
