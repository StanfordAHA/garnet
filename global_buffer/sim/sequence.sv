/*=============================================================================
** Module: sequence.sv
** Description:
**              class for transaction sequence
** Author: Taeyoung Kong
** Change history:
**  04/20/2020 - Implement first version
**===========================================================================*/

class Sequence;
    Transaction trans_q[$];

    extern function void add(Transaction trans);
    extern function Transaction pop();
    extern function void empty();
endclass

function void Sequence::add(Transaction trans);
    trans_q.push_back(trans);
endfunction

function Transaction Sequence::pop();
    return trans_q.pop_front();
endfunction

function void Sequence::empty();
    trans_q = {};
endfunction
