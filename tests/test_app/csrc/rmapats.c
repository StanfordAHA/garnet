// file = 0; split type = patterns; threshold = 100000; total count = 0.
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include "rmapats.h"

void  hsG_0__0 (struct dummyq_struct * I1361, EBLK  * I1356, U  I707);
void  hsG_0__0 (struct dummyq_struct * I1361, EBLK  * I1356, U  I707)
{
    U  I1622;
    U  I1623;
    U  I1624;
    struct futq * I1625;
    struct dummyq_struct * pQ = I1361;
    I1622 = ((U )vcs_clocks) + I707;
    I1624 = I1622 & ((1 << fHashTableSize) - 1);
    I1356->I752 = (EBLK  *)(-1);
    I1356->I753 = I1622;
    if (0 && rmaProfEvtProp) {
        vcs_simpSetEBlkEvtID(I1356);
    }
    if (I1622 < (U )vcs_clocks) {
        I1623 = ((U  *)&vcs_clocks)[1];
        sched_millenium(pQ, I1356, I1623 + 1, I1622);
    }
    else if ((peblkFutQ1Head != ((void *)0)) && (I707 == 1)) {
        I1356->I755 = (struct eblk *)peblkFutQ1Tail;
        peblkFutQ1Tail->I752 = I1356;
        peblkFutQ1Tail = I1356;
    }
    else if ((I1625 = pQ->I1264[I1624].I775)) {
        I1356->I755 = (struct eblk *)I1625->I773;
        I1625->I773->I752 = (RP )I1356;
        I1625->I773 = (RmaEblk  *)I1356;
    }
    else {
        sched_hsopt(pQ, I1356, I1622);
    }
}
void  hs_0_M_184_0__simv_daidir (UB  * pcode, scalar  val)
{
    UB  * I1689;
    *(pcode + 0) = val;
    *(pcode + 1) = X4val[val];
    RmaRtlXEdgesHdr  * I977 = (RmaRtlXEdgesHdr  *)(pcode + 8);
    RmaRtlEdgeBlock  * I811;
    U  I5 = I977->I5;
    scalar  I843 = (((I5) >> (16)) & ((1 << (8)) - 1));
    US  I1505 = (1 << (((I843) << 2) + (X4val[val])));
    if (I1505 & 31692) {
        rmaSchedRtlXEdges(I977, I1505, X4val[val]);
    }
    (I5) = (((I5) & ~(((U )((1 << (8)) - 1)) << (16))) | ((X4val[val]) << (16)));
    I977->I5 = I5;
    {
        unsigned long long * I1747 = derivedClk + (4U * X4val[val]);
        memcpy(pcode + 104 + 4, I1747, 25U);
    }
    {
        U  I1538;
        RP  I1539;
        RP  I1540;
        U  * I1541;
        U  I1494;
        RP  I1542;
        U  I1543 = 0;
        scalar  I1544;
        scalar  I1493 = X4val[val];
        U  I1545 = 0;
        scalar  I1546 = 0;
        scalar  I1547 = 0;
        struct dummyq_struct * pQ;
        U  I1359;
        I1359 = 0;
        pQ = (struct dummyq_struct *)ref_vcs_clocks;
        I1539 = (RP )(pcode + 136);
        I1540 = (RP )(I1539 + 0U);
        I1541 = (U  *)(I1540 + 24U);
        I1494 = *I1541;
        I1544 = (scalar )((((I1494) >> (0)) & ((1 << (3)) - 1)));
        I1538 = (I1544 << 2) + I1493;
        I1538 = 1 << I1538;
        if (I1538 & 8718) {
            I1546 = 0x1;
        }
        if (I1543 && !I1546) {
            I1546 = 0x3;
        }
        (*I1541) = (((*I1541) & ~(((U )((1 << (3)) - 1)) << (0))) | ((I1493) << (0)));
        if (I1538 & 8718) {
            I1547 |= (0x1 << I1545);
        }
        I1545++;
        I1547 = I1547 | (I1546 << 3);
        if (I1547) {
            (*I1541) = (((*I1541) & ~(((U )((1 << (5)) - 1)) << (3))) | ((I1547) << (3)));
            *(FP1  **)(I1540 + 0U) = (FP1  *)(rmaSched0UpdateEvTrigFnPtr);
            SchedSemiLerTXP_th(pQ, (EBLK  *)I1540);
        }
    }
    RP  * I1537;
    I1537 = (RP  *)(pcode + 184);
    if (*I1537) {
        scalar  I1548;
        I1548 = X4val[val];
        Wsvvar_sched_virt_intf_eval(I1537, I1548);
        Wsvvar_callback_virt_intf(I1537);
    }
    {
        scalar  I1581;
        scalar  I1493;
        U  I1538;
        U  I1588;
        U  I1589;
        EBLK  * I1356;
        struct dummyq_struct * pQ;
        U  I1359;
        I1359 = 0;
        pQ = (struct dummyq_struct *)ref_vcs_clocks;
        I1493 = X4val[val];
        I1581 = *(pcode + 192);
        *(pcode + 192) = I1493;
        I1538 = (I1581 << 2) + I1493;
        I1538 = 1 << I1538;
        if (I1538 & 2) {
            EBLK  * I1356 = (EBLK  *)((UB  *)(pcode + 200 + 0U));
            UB  * I1123 = (UB  *)I1356->I750;
            RP  I1096 = *(RP  *)(I1123 + 8U);
            if (I1096) {
                if ((I1356->I752 == 0)) {
                    U  I1586 = (X4val[val] << ((sizeof(U ) * 8) - 3));
                    U  I1061 = *(U  *)(I1123 + 4U);
                    I1061 &= ~(0x3 << ((sizeof(U ) * 8) - 3));
                    I1061 |= I1586;
                    *(U  *)(I1123 + 4U) = I1061;
                }
            }
            if (getCurSchedRegion()) {
                SchedSemiLerTBReactiveRegion_th((struct eblk *)(pcode + 200), I1359);
            }
            else {
                sched0_th(pQ, (EBLK  *)(pcode + 200));
            }
        }
        if (I1538 & 16) {
            EBLK  * I1356 = (EBLK  *)((UB  *)(pcode + 200 + 40U));
            UB  * I1123 = (UB  *)I1356->I750;
            RP  I1096 = *(RP  *)(I1123 + 8U);
            if (I1096) {
                if ((I1356->I752 == 0)) {
                    U  I1586 = (X4val[val] << ((sizeof(U ) * 8) - 3));
                    U  I1061 = *(U  *)(I1123 + 4U);
                    I1061 &= ~(0x3 << ((sizeof(U ) * 8) - 3));
                    I1061 |= I1586;
                    *(U  *)(I1123 + 4U) = I1061;
                }
            }
            if (getCurSchedRegion()) {
                SchedSemiLerTBReactiveRegion_th((struct eblk *)(pcode + 240), I1359);
            }
            else {
                sched0_th(pQ, (EBLK  *)(pcode + 240));
            }
        }
    }
    {
        scalar  I1581;
        scalar  I1493;
        U  I1538;
        I1493 = X4val[val];
        I1581 = *(pcode + 280);
        *(pcode + 280) = I1493;
        I1538 = (I1581 << 2) + I1493;
        I1538 = 1 << I1538;
        if ((I1538 & 31710)) {
            if (getCurSchedRegion()) {
                SchedSemiLerTBReactiveRegion((struct eblk *)(pcode + 288));
            }
            else {
                sched0(pcode + 288);
            }
        }
    }
    {
        scalar  I1749 = X4val[val];
        scalar  I1750 = *(scalar  *)(pcode + 328 + 2U);
        *(scalar  *)(pcode + 328 + 2U) = I1749;
        UB  * I977 = *(UB  **)(pcode + 328 + 8U);
        if (I977) {
            U  I1751 = I1749 * 2;
            U  I1752 = 1 << ((I1750 << 2) + I1749);
            *(pcode + 328 + 0U) = 1;
            while (I977){
                UB  * I1754 = *(UB  **)(I977 + 16U);
                if ((*(US  *)(I977 + 0U)) & I1752) {
                    *(*(UB  **)(I977 + 48U)) = 1;
                    (*(FP  *)(I977 + 32U))((void *)(*(RP  *)(I977 + 40U)), (((*(scalar  *)(I977 + 2U)) >> I1751) & 3));
                }
                I977 = I1754;
            };
            *(pcode + 328 + 0U) = 0;
            rmaRemoveNonEdgeLoads(pcode + 328);
        }
    }
    {
        pcode += 368;
        (*(FP  *)(pcode + 8))(*(UB  **)(pcode + 16), globalTable1Input[(*(U  *)(pcode + 0) >> 8) + val]);
        (*(FP  *)(pcode + 32))(*(UB  **)(pcode + 40), globalTable1Input[(*(U  *)(pcode + 24) >> 8) + val]);
    }
}
#ifdef __cplusplus
extern "C" {
#endif
void SinitHsimPats(void);
#ifdef __cplusplus
}
#endif
