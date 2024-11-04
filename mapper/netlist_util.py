import os, math, re
from graphviz import Digraph
from collections import defaultdict
from hwtypes import Bit, BitVector
from hwtypes.adt import Tuple, Product
from metamapper.node import (
    Dag,
    Input,
    Output,
    Combine,
    Select,
    DagNode,
    IODag,
    Constant,
    Sink,
    Common,
)
from metamapper.common_passes import AddID, print_dag, gen_dag_img
from DagVisitor import Visitor, Transformer
from peak.mapper.utils import Unbound
from lassen.sim import PE_fc as lassen_fc
from mapper.netlist_graph import Node, NetlistGraph
import pythunder
import pulp

label_MEM2PE = {
    'op_hcompute_output_cgra_stencil_26$inner_compute$mul_pipelined_i6210_i1176': 7, #p180
    'op_hcompute_output_cgra_stencil_18$inner_compute$mul_pipelined_i3469_i1176': 6, #p43
    'op_hcompute_output_cgra_stencil_30$inner_compute$mul_pipelined_i7583_i1176': 5, #p249
    'op_hcompute_output_cgra_stencil_22$inner_compute$mul_pipelined_i4842_i1176': 4, #p112
    'op_hcompute_output_cgra_stencil_27$inner_compute$mul_pipelined_i6552_i1176': 3, #p197
    'op_hcompute_output_cgra_stencil_19$inner_compute$mul_pipelined_i3811_i1176': 2, #p60
    'op_hcompute_output_cgra_stencil_31$inner_compute$mul_pipelined_i7925_i1176': 1, #p266
    'op_hcompute_output_cgra_stencil_23$inner_compute$mul_pipelined_i5184_i1176': 0, #p129
    'op_hcompute_output_cgra_stencil_24$inner_compute$mul_pipelined_i5526_i1176': 8, #p146
    'op_hcompute_output_cgra_stencil_16$inner_compute$mul_pipelined_i2785_i1176': 9, #p9
    'op_hcompute_output_cgra_stencil_28$inner_compute$mul_pipelined_i6894_i1176': 10, #p214
    'op_hcompute_output_cgra_stencil_20$inner_compute$mul_pipelined_i4158_i1176': 11, #p78
    'op_hcompute_output_cgra_stencil_25$inner_compute$mul_pipelined_i5868_i1176': 12, #p163
    'op_hcompute_output_cgra_stencil_17$inner_compute$mul_pipelined_i3127_i1176': 13, #p26
    'op_hcompute_output_cgra_stencil_29$inner_compute$mul_pipelined_i7236_i1176': 14, #p231
    'op_hcompute_output_cgra_stencil_21$inner_compute$mul_pipelined_i4500_i1176': 15, #p95
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s1_pipelined_i6214_i1258': 7, #p195
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s1_pipelined_i3473_i1258': 6, #p58
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s1_pipelined_i7587_i1258': 5, #p264
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s1_pipelined_i4846_i1258': 4, #p127
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s1_pipelined_i6556_i1258': 3, #p212
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s1_pipelined_i3815_i1258': 2, #p75
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s1_pipelined_i7929_i1258': 1, #p281
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s1_pipelined_i5188_i1258': 0, #p144
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s1_pipelined_i5530_i1258': 8, #p161
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s1_pipelined_i2789_i1258': 9, #p24
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s1_pipelined_i6898_i1258': 10, #p229
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s1_pipelined_i4162_i1258': 11, #p93
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s1_pipelined_i5872_i1258': 12, #p178
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s1_pipelined_i3131_i1258': 13, #p41
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s1_pipelined_i7240_i1258': 14, #p246
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s1_pipelined_i4504_i1258': 15, #p110
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6215_i1217': 7, #p181
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3474_i1217': 6, #p44
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7588_i1217': 5, #p250
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4847_i1217': 4, #p113
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6557_i1217': 3, #p198
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3816_i1217': 2, #p61
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7930_i1217': 1, #p267
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5189_i1217': 0, #p130
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5531_i1217': 8, #p147
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2790_i1217': 9, #p10
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6899_i1217': 10, #p215
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4163_i1217': 11, #p79
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5873_i1217': 12, #p164
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3132_i1217': 13, #p27
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7241_i1217': 14, #p232
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4505_i1217': 15, #p96
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6216_i1217': 7, #p182
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3475_i1217': 6, #p45
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7589_i1217': 5, #p251
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4848_i1217': 4, #p114
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6558_i1217': 3, #p199
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3817_i1217': 2, #p62
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7931_i1217': 1, #p268
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5190_i1217': 0, #p131
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5532_i1217': 8, #p148
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2791_i1217': 9, #p11
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6900_i1217': 10, #p216
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4164_i1217': 11, #p80
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5874_i1217': 12, #p165
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3133_i1217': 13, #p28
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7242_i1217': 14, #p233
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4506_i1217': 15, #p97
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6217_i1217': 7, #p183
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3476_i1217': 6, #p46
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7590_i1217': 5, #p252
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4849_i1217': 4, #p115
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6559_i1217': 3, #p200
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3818_i1217': 2, #p63
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7932_i1217': 1, #p269
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5191_i1217': 0, #p132
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5533_i1217': 8, #p149
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2792_i1217': 9, #p12
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6901_i1217': 10, #p217
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4165_i1217': 11, #p81
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5875_i1217': 12, #p166
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3134_i1217': 13, #p29
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7243_i1217': 14, #p234
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4507_i1217': 15, #p98
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6218_i1217': 7, #p184
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3477_i1217': 6, #p47
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7591_i1217': 5, #p253
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4850_i1217': 4, #p116
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6560_i1217': 3, #p201
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3819_i1217': 2, #p64
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7933_i1217': 1, #p270
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5192_i1217': 0, #p133
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5534_i1217': 8, #p150
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2793_i1217': 9, #p13
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6902_i1217': 10, #p218
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4166_i1217': 11, #p82
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5876_i1217': 12, #p167
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3135_i1217': 13, #p30
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7244_i1217': 14, #p235
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4508_i1217': 15, #p99
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6219_i1217': 7, #p185
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3478_i1217': 6, #p48
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7592_i1217': 5, #p254
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4851_i1217': 4, #p117
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6561_i1217': 3, #p202
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3820_i1217': 2, #p65
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7934_i1217': 1, #p271
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5193_i1217': 0, #p134
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5535_i1217': 8, #p151
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2794_i1217': 9, #p14
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6903_i1217': 10, #p219
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4167_i1217': 11, #p83
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5877_i1217': 12, #p168
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3136_i1217': 13, #p31
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7245_i1217': 14, #p236
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4509_i1217': 15, #p100
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6220_i1217': 7, #p186
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3479_i1217': 6, #p49
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7593_i1217': 5, #p255
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4852_i1217': 4, #p118
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6562_i1217': 3, #p203
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3821_i1217': 2, #p66
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7935_i1217': 1, #p272
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5194_i1217': 0, #p135
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5536_i1217': 8, #p152
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2795_i1217': 9, #p15
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6904_i1217': 10, #p220
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4168_i1217': 11, #p84
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5878_i1217': 12, #p169
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3137_i1217': 13, #p32
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7246_i1217': 14, #p237
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4510_i1217': 15, #p101
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6221_i1217': 7, #p187
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3480_i1217': 6, #p50
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7594_i1217': 5, #p256
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4853_i1217': 4, #p119
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6563_i1217': 3, #p204
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3822_i1217': 2, #p67
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7936_i1217': 1, #p273
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5195_i1217': 0, #p136
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5537_i1217': 8, #p153
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2796_i1217': 9, #p16
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6905_i1217': 10, #p221
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4169_i1217': 11, #p85
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5879_i1217': 12, #p170
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3138_i1217': 13, #p33
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7247_i1217': 14, #p238
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4511_i1217': 15, #p102
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6222_i1217': 7, #p188
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3481_i1217': 6, #p51
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7595_i1217': 5, #p257
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4854_i1217': 4, #p120
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6564_i1217': 3, #p205
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3823_i1217': 2, #p68
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7937_i1217': 1, #p274
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5196_i1217': 0, #p137
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5538_i1217': 8, #p154
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2797_i1217': 9, #p17
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6906_i1217': 10, #p222
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4170_i1217': 11, #p86
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5880_i1217': 12, #p171
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3139_i1217': 13, #p34
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7248_i1217': 14, #p239
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4512_i1217': 15, #p103
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6223_i1217': 7, #p189
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3482_i1217': 6, #p52
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7596_i1217': 5, #p258
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4855_i1217': 4, #p121
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6565_i1217': 3, #p206
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3824_i1217': 2, #p69
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7938_i1217': 1, #p275
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5197_i1217': 0, #p138
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5539_i1217': 8, #p155
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2798_i1217': 9, #p18
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6907_i1217': 10, #p223
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4171_i1217': 11, #p87
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5881_i1217': 12, #p172
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3140_i1217': 13, #p35
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7249_i1217': 14, #p240
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4513_i1217': 15, #p104
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6224_i1217': 7, #p190
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3483_i1217': 6, #p53
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7597_i1217': 5, #p259
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4856_i1217': 4, #p122
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6566_i1217': 3, #p207
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3825_i1217': 2, #p70
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7939_i1217': 1, #p276
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5198_i1217': 0, #p139
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5540_i1217': 8, #p156
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2799_i1217': 9, #p19
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6908_i1217': 10, #p224
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4172_i1217': 11, #p88
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5882_i1217': 12, #p173
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3141_i1217': 13, #p36
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7250_i1217': 14, #p241
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4514_i1217': 15, #p105
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6225_i1217': 7, #p191
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3484_i1217': 6, #p54
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7598_i1217': 5, #p260
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4857_i1217': 4, #p123
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6567_i1217': 3, #p208
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3826_i1217': 2, #p71
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7940_i1217': 1, #p277
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5199_i1217': 0, #p140
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5541_i1217': 8, #p157
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2800_i1217': 9, #p20
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6909_i1217': 10, #p225
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4173_i1217': 11, #p89
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5883_i1217': 12, #p174
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3142_i1217': 13, #p37
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7251_i1217': 14, #p242
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4515_i1217': 15, #p106
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6226_i1217': 7, #p192
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3485_i1217': 6, #p55
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7599_i1217': 5, #p261
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4858_i1217': 4, #p124
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6568_i1217': 3, #p209
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3827_i1217': 2, #p72
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7941_i1217': 1, #p278
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5200_i1217': 0, #p141
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5542_i1217': 8, #p158
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2801_i1217': 9, #p21
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6910_i1217': 10, #p226
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4174_i1217': 11, #p90
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5884_i1217': 12, #p175
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3143_i1217': 13, #p38
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7252_i1217': 14, #p243
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4516_i1217': 15, #p107
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6227_i1217': 7, #p193
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3486_i1217': 6, #p56
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7600_i1217': 5, #p262
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4859_i1217': 4, #p125
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6569_i1217': 3, #p210
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3828_i1217': 2, #p73
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7942_i1217': 1, #p279
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5201_i1217': 0, #p142
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5543_i1217': 8, #p159
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2802_i1217': 9, #p22
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6911_i1217': 10, #p227
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4175_i1217': 11, #p91
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5885_i1217': 12, #p176
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3144_i1217': 13, #p39
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7253_i1217': 14, #p244
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4517_i1217': 15, #p108
    'op_hcompute_output_cgra_stencil_26$inner_compute$muladd_s0_pipelined_i6229_i1217': 7, #p194
    'op_hcompute_output_cgra_stencil_18$inner_compute$muladd_s0_pipelined_i3488_i1217': 6, #p57
    'op_hcompute_output_cgra_stencil_30$inner_compute$muladd_s0_pipelined_i7602_i1217': 5, #p263
    'op_hcompute_output_cgra_stencil_22$inner_compute$muladd_s0_pipelined_i4861_i1217': 4, #p126
    'op_hcompute_output_cgra_stencil_27$inner_compute$muladd_s0_pipelined_i6571_i1217': 3, #p211
    'op_hcompute_output_cgra_stencil_19$inner_compute$muladd_s0_pipelined_i3830_i1217': 2, #p74
    'op_hcompute_output_cgra_stencil_31$inner_compute$muladd_s0_pipelined_i7944_i1217': 1, #p280
    'op_hcompute_output_cgra_stencil_23$inner_compute$muladd_s0_pipelined_i5203_i1217': 0, #p143
    'op_hcompute_output_cgra_stencil_24$inner_compute$muladd_s0_pipelined_i5545_i1217': 8, #p160
    'op_hcompute_output_cgra_stencil_16$inner_compute$muladd_s0_pipelined_i2804_i1217': 9, #p23
    'op_hcompute_output_cgra_stencil_28$inner_compute$muladd_s0_pipelined_i6913_i1217': 10, #p228
    'op_hcompute_output_cgra_stencil_20$inner_compute$muladd_s0_pipelined_i4177_i1217': 11, #p92
    'op_hcompute_output_cgra_stencil_25$inner_compute$muladd_s0_pipelined_i5887_i1217': 12, #p177
    'op_hcompute_output_cgra_stencil_17$inner_compute$muladd_s0_pipelined_i3146_i1217': 13, #p40
    'op_hcompute_output_cgra_stencil_29$inner_compute$muladd_s0_pipelined_i7255_i1217': 14, #p245
    'op_hcompute_output_cgra_stencil_21$inner_compute$muladd_s0_pipelined_i4519_i1217': 15 #p109
}


label_IO2POND = {
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_160_garnet': 0, #M67
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_161_garnet': 1, #M68
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_162_garnet': 2, #M69
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_163_garnet': 3, #M70
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_164_garnet': 4, #M71
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_165_garnet': 5, #M72
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_166_garnet': 6, #M73
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_167_garnet': 7, #M74
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_168_garnet': 8, #M75
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_169_garnet': 9, #M76
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_170_garnet': 10, #M78
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_171_garnet': 11, #M79
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_172_garnet': 12, #M80
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_173_garnet': 13, #M81
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_174_garnet': 14, #M82
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_175_garnet': 15, #M83
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_47_garnet': 16, #M197
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_46_garnet': 17, #M196
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_45_garnet': 18, #M195
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_44_garnet': 19, #M194
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_43_garnet': 20, #M193
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_42_garnet': 21, #M192
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_41_garnet': 22, #M191
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_40_garnet': 23, #M190
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_39_garnet': 24, #M188
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_38_garnet': 25, #M187
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_37_garnet': 26, #M186
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_36_garnet': 27, #M185
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_35_garnet': 28, #M184
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_34_garnet': 29, #M183
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_33_garnet': 30, #M182
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_32_garnet': 31, #M181
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_224_garnet': 32, #M138
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_225_garnet': 33, #M139
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_226_garnet': 34, #M140
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_227_garnet': 35, #M141
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_228_garnet': 36, #M142
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_229_garnet': 37, #M143
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_230_garnet': 38, #M145
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_231_garnet': 39, #M146
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_232_garnet': 40, #M147
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_233_garnet': 41, #M148
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_234_garnet': 42, #M149
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_235_garnet': 43, #M150
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_236_garnet': 44, #M151
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_237_garnet': 45, #M152
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_238_garnet': 46, #M153
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_239_garnet': 47, #M154
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_111_garnet': 48, #M13
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_110_garnet': 49, #M12
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_109_garnet': 50, #M10
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_108_garnet': 51, #M9
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_107_garnet': 52, #M8
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_106_garnet': 53, #M7
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_105_garnet': 54, #M6
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_104_garnet': 55, #M5
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_103_garnet': 56, #M4
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_102_garnet': 57, #M3
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_101_garnet': 58, #M2
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_100_garnet': 59, #M1
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_99_garnet': 60, #M254
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_98_garnet': 61, #M253
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_97_garnet': 62, #M252
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_96_garnet': 63, #M251
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_176_garnet': 0, #M84
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_177_garnet': 1, #M85
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_178_garnet': 2, #M86
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_179_garnet': 3, #M87
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_180_garnet': 4, #M89
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_181_garnet': 5, #M90
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_182_garnet': 6, #M91
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_183_garnet': 7, #M92
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_184_garnet': 8, #M93
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_185_garnet': 9, #M94
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_186_garnet': 10, #M95
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_187_garnet': 11, #M96
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_188_garnet': 12, #M97
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_189_garnet': 13, #M98
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_190_garnet': 14, #M100
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_191_garnet': 15, #M101
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_63_garnet': 16, #M215
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_62_garnet': 17, #M214
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_61_garnet': 18, #M213
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_60_garnet': 19, #M212
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_59_garnet': 20, #M210
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_58_garnet': 21, #M209
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_57_garnet': 22, #M208
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_56_garnet': 23, #M207
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_55_garnet': 24, #M206
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_54_garnet': 25, #M205
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_53_garnet': 26, #M204
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_52_garnet': 27, #M203
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_51_garnet': 28, #M202
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_50_garnet': 29, #M201
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_49_garnet': 30, #M199
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_48_garnet': 31, #M198
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_240_garnet': 32, #M156
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_241_garnet': 33, #M157
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_242_garnet': 34, #M158
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_243_garnet': 35, #M159
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_244_garnet': 36, #M160
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_245_garnet': 37, #M161
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_246_garnet': 38, #M162
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_247_garnet': 39, #M163
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_248_garnet': 40, #M164
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_249_garnet': 41, #M165
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_250_garnet': 42, #M167
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_251_garnet': 43, #M168
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_252_garnet': 44, #M169
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_253_garnet': 45, #M170
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_254_garnet': 46, #M171
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_255_garnet': 47, #M172
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_127_garnet': 48, #M30
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_126_garnet': 49, #M29
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_125_garnet': 50, #M28
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_124_garnet': 51, #M27
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_123_garnet': 52, #M26
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_122_garnet': 53, #M25
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_121_garnet': 54, #M24
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_120_garnet': 55, #M23
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_119_garnet': 56, #M21
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_118_garnet': 57, #M20
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_117_garnet': 58, #M19
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_116_garnet': 59, #M18
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_115_garnet': 60, #M17
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_114_garnet': 61, #M16
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_113_garnet': 62, #M15
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_112_garnet': 63, #M14
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_128_garnet': 0, #M31
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_129_garnet': 1, #M32
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_130_garnet': 2, #M34
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_131_garnet': 3, #M35
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_132_garnet': 4, #M36
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_133_garnet': 5, #M37
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_134_garnet': 6, #M38
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_135_garnet': 7, #M39
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_136_garnet': 8, #M40
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_137_garnet': 9, #M41
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_138_garnet': 10, #M42
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_139_garnet': 11, #M43
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_140_garnet': 12, #M45
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_141_garnet': 13, #M46
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_142_garnet': 14, #M47
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_143_garnet': 15, #M48
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_15_garnet': 16, #M66
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_14_garnet': 17, #M55
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_13_garnet': 18, #M44
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_12_garnet': 19, #M33
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_11_garnet': 20, #M22
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_10_garnet': 21, #M11
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_9_garnet': 22, #M255
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_8_garnet': 23, #M244
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_7_garnet': 24, #M233
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_6_garnet': 25, #M222
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_5_garnet': 26, #M211
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_4_garnet': 27, #M200
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_3_garnet': 28, #M189
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_2_garnet': 29, #M178
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_1_garnet': 30, #M111
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_0_garnet': 31, #M0
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_192_garnet': 32, #M102
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_193_garnet': 33, #M103
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_194_garnet': 34, #M104
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_195_garnet': 35, #M105
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_196_garnet': 36, #M106
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_197_garnet': 37, #M107
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_198_garnet': 38, #M108
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_199_garnet': 39, #M109
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_200_garnet': 40, #M112
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_201_garnet': 41, #M113
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_202_garnet': 42, #M114
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_203_garnet': 43, #M115
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_204_garnet': 44, #M116
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_205_garnet': 45, #M117
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_206_garnet': 46, #M118
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_207_garnet': 47, #M119
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_79_garnet': 48, #M232
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_78_garnet': 49, #M231
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_77_garnet': 50, #M230
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_76_garnet': 51, #M229
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_75_garnet': 52, #M228
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_74_garnet': 53, #M227
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_73_garnet': 54, #M226
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_72_garnet': 55, #M225
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_71_garnet': 56, #M224
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_70_garnet': 57, #M223
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_69_garnet': 58, #M221
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_68_garnet': 59, #M220
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_67_garnet': 60, #M219
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_66_garnet': 61, #M218
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_65_garnet': 62, #M217
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_64_garnet': 63, #M216
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_144_garnet': 0, #M49
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_145_garnet': 1, #M50
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_146_garnet': 2, #M51
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_147_garnet': 3, #M52
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_148_garnet': 4, #M53
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_149_garnet': 5, #M54
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_150_garnet': 6, #M56
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_151_garnet': 7, #M57
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_152_garnet': 8, #M58
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_153_garnet': 9, #M59
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_154_garnet': 10, #M60
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_155_garnet': 11, #M61
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_156_garnet': 12, #M62
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_157_garnet': 13, #M63
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_158_garnet': 14, #M64
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_159_garnet': 15, #M65
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_31_garnet': 16, #M180
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_30_garnet': 17, #M179
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_29_garnet': 18, #M177
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_28_garnet': 19, #M176
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_27_garnet': 20, #M175
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_26_garnet': 21, #M174
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_25_garnet': 22, #M173
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_24_garnet': 23, #M166
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_23_garnet': 24, #M155
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_22_garnet': 25, #M144
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_21_garnet': 26, #M133
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_20_garnet': 27, #M122
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_19_garnet': 28, #M110
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_18_garnet': 29, #M99
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_17_garnet': 30, #M88
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_16_garnet': 31, #M77
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_208_garnet': 32, #M120
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_209_garnet': 33, #M121
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_210_garnet': 34, #M123
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_211_garnet': 35, #M124
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_212_garnet': 36, #M125
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_213_garnet': 37, #M126
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_214_garnet': 38, #M127
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_215_garnet': 39, #M128
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_216_garnet': 40, #M129
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_217_garnet': 41, #M130
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_218_garnet': 42, #M131
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_219_garnet': 43, #M132
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_220_garnet': 44, #M134
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_221_garnet': 45, #M135
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_222_garnet': 46, #M136
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_223_garnet': 47, #M137
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_95_garnet': 48, #M250
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_94_garnet': 49, #M249
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_93_garnet': 50, #M248
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_92_garnet': 51, #M247
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_91_garnet': 52, #M246
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_90_garnet': 53, #M245
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_89_garnet': 54, #M243
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_88_garnet': 55, #M242
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_87_garnet': 56, #M241
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_86_garnet': 57, #M240
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_85_garnet': 58, #M239
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_84_garnet': 59, #M238
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_83_garnet': 60, #M237
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_82_garnet': 61, #M236
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_81_garnet': 62, #M235
    'kernel_cgra_stencil$ub_kernel_cgra_stencil_BANK_80_garnet': 63, #M234
}



class CreateBuses(Visitor):
    def __init__(self, inst_info):
        self.inst_info = inst_info

    def doit(self, dag):
        self.i = 1
        self.bid_to_width = {}
        self.node_to_bid = {}
        self.netlist = defaultdict(lambda: [])
        self.run(dag)
        # Filter bid_to_width to contain only whats in self.netlist
        buses = {bid: w for bid, w in self.bid_to_width.items() if bid in self.netlist}
        return buses, self.netlist

    def create_buses(self, adt):
        if adt == Bit:
            bid = f"e{self.i}"
            self.bid_to_width[bid] = 1
            self.i += 1
            return bid
        elif adt == BitVector[16]:
            bid = f"e{self.i}"
            self.bid_to_width[bid] = 17
            self.i += 1
            return bid
        elif issubclass(adt, BitVector):
            return None
        elif issubclass(adt, Product):
            bids = {}
            for k, t in adt.field_dict.items():
                bid = self.create_buses(t)
                if bid is None:
                    continue
                assert isinstance(bid, str)
                bids[k] = bid
            return bids
        else:
            raise NotImplementedError(f"{adt}")

    def visit_Source(self, node):
        bid = self.create_buses(node.type)
        self.node_to_bid[node] = bid

    def visit_Constant(self, node):
        self.node_to_bid[node] = None

    def visit_Select(self, node):
        Visitor.generic_visit(self, node)
        child = list(node.children())[0]
        child_bid = self.node_to_bid[child]
        assert isinstance(child_bid, dict)
        assert node.field in child_bid
        bid = child_bid[node.field]
        self.node_to_bid[node] = bid
        self.netlist[bid].append((child, node.field))

    def visit_RegisterSource(self, node):
        bid = self.create_buses(node.type)
        self.node_to_bid[node] = bid
        self.netlist[bid].append((node, "reg"))

    def visit_RegisterSink(self, node):
        Visitor.generic_visit(self, node)
        child_bid = self.node_to_bid[node.child]
        self.netlist[child_bid].append((node, "reg"))

    def generic_visit(self, node):
        Visitor.generic_visit(self, node)
        child_bids = [self.node_to_bid[child] for child in node.children()]
        if node.node_name not in self.inst_info:
            raise ValueError(f"Missing {node.node_name} in info")
        input_t = self.inst_info[node.node_name]

        for field, child_bid in zip(input_t.field_dict.keys(), child_bids):
            if child_bid is None:
                continue
            assert child_bid in self.netlist
            self.netlist[child_bid].append((node, field))
        if not isinstance(node, Sink):
            bid = self.create_buses(node.type)
            self.node_to_bid[node] = bid

    def visit_Combine(self, node: Combine):
        Visitor.generic_visit(self, node)
        child_bids = [self.node_to_bid[child] for child in node.children()]
        input_t = node.type
        bids = {}
        for field, child_bid in zip(input_t.field_dict.keys(), child_bids):
            if child_bid is None:
                continue
            bids[field] = child_bid
        self.node_to_bid[node] = bids

    def visit_Output(self, node: Output):
        Visitor.generic_visit(self, node)
        child_bid = self.node_to_bid[node.child]
        if node.child.type == Bit:
            port = "f2io_1"
        else:
            port = "f2io_17"
        self.netlist[child_bid].append((node, port))


class CreateInstrs(Visitor):
    def __init__(self, inst_info):
        self.inst_info = inst_info

    def doit(self, dag: IODag):
        self.node_to_instr = {}
        self.run(dag)
        for src, sink in zip(dag.non_input_sources, dag.non_output_sinks):
            self.node_to_instr[src.iname] = self.node_to_instr[sink.iname]
        return self.node_to_instr

    def visit_Input(self, node):
        self.node_to_instr[node.iname] = (1,)

    def visit_Output(self, node):
        Visitor.generic_visit(self, node)
        self.node_to_instr[node.iname] = (2,)

    def visit_Source(self, node):
        pass

    def visit_Select(self, node):
        Visitor.generic_visit(self, node)

    def visit_Combine(self, node):
        Visitor.generic_visit(self, node)

    def visit_Constant(self, node):
        pass

    def visit_RegisterSource(self, node):
        pass

    def visit_RegisterSink(self, node):
        Visitor.generic_visit(self, node)
        self.node_to_instr[node.iname] = 0  # TODO what is the 'instr' for a register?

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name not in self.inst_info:
            raise ValueError(f"Need info for {node.node_name}")
        adt = self.inst_info[node.node_name]
        for instr_child in node.children():
            if isinstance(instr_child, Constant):
                break

        assert isinstance(
            instr_child, Constant
        ), f"{node.node_name} {node.iname} {instr_child.node_name}"
        self.node_to_instr[node.iname] = instr_child.value


class CreateMetaData(Visitor):
    def doit(self, dag):
        self.node_to_md = {}
        self.run(dag)
        return self.node_to_md

    def generic_visit(self, node):
        Visitor.generic_visit(self, node)
        if hasattr(node, "_metadata_"):
            self.node_to_md[node.iname] = node._metadata_


class CreateIDs(Visitor):
    def __init__(self, inst_info):
        self.inst_info = inst_info

    def doit(self, dag: IODag):
        self.tile_types = set()
        self.node_to_type = {}
        self.node_to_id = {}
        self.run(dag)
        for tile_type in self.tile_types:
            nodes = [k for k, v in self.node_to_type.items() if v == tile_type]
            nodes.sort()

            for idx, node in enumerate(nodes):
                self.node_to_id[node] = f"{tile_type}{idx}"

        return self.node_to_id

    def visit_Source(self, node):
        pass

    def visit_Output(self, node: Output):
        Visitor.generic_visit(self, node)
        child = list(node.children())[0]

        if "io16" in node.iname:
            id = f"I"
        else:
            id = f"i"
        self.node_to_type[node.iname] = id
        self.tile_types.add("I")
        self.tile_types.add("i")

    def visit_Select(self, node):
        Visitor.generic_visit(self, node)
        child = list(node.children())[0]
        if isinstance(child, Input):
            if node.type == Bit:
                id = f"i"
            elif node.type == BitVector[16]:
                id = f"I"
            else:
                raise NotImplementedError(f"{node}, {node.type}")
            self.node_to_type[child.iname] = id
            self.tile_types.add("I")
            self.tile_types.add("i")

    def visit_Combine(self, node):
        Visitor.generic_visit(self, node)

    def visit_Constant(self, node):
        pass

    def visit_RegisterSource(self, node):
        pass

    def visit_RegisterSink(self, node):
        Visitor.generic_visit(self, node)
        if node.type == Bit:
            id = f"r"
        elif node.type == BitVector[16]:
            id = f"r"
        else:
            raise NotImplementedError(f"{node}, {node.type}")
        self.node_to_type[node.iname] = id
        self.tile_types.add("r")

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name not in self.inst_info:
            raise ValueError(f"Need info for {node.node_name}")
        id = f"{self.inst_info[node.node_name]}"
        self.node_to_type[node.iname] = id
        self.tile_types.add(f"{self.inst_info[node.node_name]}")


def p(msg, adt):
    print(msg, list(adt.field_dict.items()))


def is_bv(adt):
    return issubclass(adt, (BitVector, Bit))


def flatten_adt(adt, path=()):
    if is_bv(adt):
        return {path: adt}
    elif issubclass(adt, Product):
        ret = {}
        for k in adt.field_dict:
            sub_ret = flatten_adt(adt[k], path + (k,))
            ret.update(sub_ret)
        return ret
    elif issubclass(adt, Tuple):
        ret = {}
        for i in range(len(adt.field_dict)):
            sub_ret = flatten_adt(adt[i], path + (i,))
            ret.update(sub_ret)
        return ret
    else:
        raise NotImplementedError(adt)


class IO_Input_t(Product):
    io2f_17 = BitVector[16]
    io2f_1 = Bit


class IO_Output_t(Product):
    f2io_16 = BitVector[16]
    f2io_1 = Bit


class FlattenIO(Visitor):
    def __init__(self):
        pass

    def doit(self, dag: Dag):
        input_t = dag.input.type
        output_t = dag.output.type
        ipath_to_type = flatten_adt(input_t)
        self.node_to_opaths = {}
        self.node_to_ipaths = {}
        self.node_map = {}
        self.opath_to_type = flatten_adt(output_t)

        isel = lambda t: "io2f_1" if t == Bit else "io2f_17"
        real_inputs = [
            Input(type=IO_Input_t, iname="_".join(str(field) for field in path))
            for path in ipath_to_type
        ]
        self.inputs = {
            path: inode.select(isel(t))
            for inode, (path, t) in zip(real_inputs, ipath_to_type.items())
        }
        self.outputs = {}
        self.run(dag)
        real_sources = [self.node_map[s] for s in dag.sources[1:]]
        real_sinks = [self.node_map[s] for s in dag.sinks[1:]]
        return IODag(
            inputs=real_inputs,
            outputs=self.outputs.values(),
            sources=real_sources,
            sinks=real_sinks,
        )

    def visit_Output(self, node: Output):
        Visitor.generic_visit(self, node)
        for field, child in zip(node.type.field_dict, node.children()):
            child_paths = self.node_to_opaths[child]
            for child_path, new_child in child_paths.items():
                new_path = (field, *child_path)
                assert new_path in self.opath_to_type
                child_t = self.opath_to_type[new_path]
                if child_t == Bit:
                    combine_children = [
                        Constant(type=BitVector[16], value=Unbound),
                        new_child,
                    ]
                else:
                    combine_children = [new_child, Constant(type=Bit, value=Unbound)]
                cnode = Combine(*combine_children, type=IO_Output_t)

                # Bad hack, read_en signals aren't actually connected to anything, this should be checked
                if "read_en" not in field:
                    self.outputs[new_path] = Output(
                        cnode,
                        type=IO_Output_t,
                        iname="_".join(str(field) for field in new_path),
                    )

    def visit_Combine(self, node: Combine):
        Visitor.generic_visit(self, node)
        adt = node.type
        assert issubclass(adt, (Product, Tuple))
        paths = {}
        for k, child in zip(adt.field_dict.keys(), node.children()):
            child_paths = self.node_to_opaths[child]
            for child_path, new_child in child_paths.items():
                new_path = (k, *child_path)
                paths[new_path] = new_child
        self.node_to_opaths[node] = paths

    def visit_Select(self, node: Select):
        def get_input_node(node, path=()):
            if isinstance(node, Input):
                assert path in self.inputs
                return self.inputs[path]
            elif isinstance(node, Select):
                child = list(node.children())[0]
                return get_input_node(child, (node.field, *path))
            else:
                return None

        input_node = get_input_node(node)
        if input_node is not None:
            self.node_map[node] = input_node
            return

        Visitor.generic_visit(self, node)
        new_children = [self.node_map[child] for child in node.children()]
        new_node = node.copy()
        new_node.set_children(*new_children)
        self.node_to_opaths[node] = {(): new_node}
        self.node_map[node] = new_node

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        new_children = [self.node_map[child] for child in node.children()]
        new_node = node.copy()
        new_node.set_children(*new_children)
        self.node_to_opaths[node] = {(): new_node}
        self.node_map[node] = new_node


def print_netlist_info(info, pes_with_packed_ponds, filename):
    outfile = open(filename, "w")
    print("pes with packed ponds", file=outfile)
    for k, v in pes_with_packed_ponds.items():
        print(f"  {k}  {v}", file=outfile)

    print("id to instance name", file=outfile)
    for k, v in info["id_to_name"].items():
        print(f"  {k}  {v}", file=outfile)

    print("id_to_Instrs", file=outfile)
    for k, v in info["id_to_instrs"].items():
        print(f"  {k}, {v}", file=outfile)

    print("id_to_metadata", file=outfile)
    for k, v in info["id_to_metadata"].items():
        print(f"  {k}, {v}", file=outfile)

    print("buses", file=outfile)
    for k, v in info["buses"].items():
        print(f"  {k}, {v}", file=outfile)

    print("netlist", file=outfile)
    for bid, v in info["netlist"].items():
        print(f"  {bid}", file=outfile)
        for _v in v:
            print(f"    {_v}", file=outfile)
    outfile.close()


def is_unbound_const(node):
    return isinstance(node, Constant) and node.value is Unbound


class VerifyUniqueIname(Visitor):
    def __init__(self):
        self.inames = {}

    def generic_visit(self, node):
        Visitor.generic_visit(self, node)
        if node.iname in self.inames:
            raise ValueError(
                f"{node.iname} for {node} already used by {self.inames[node.iname]}"
            )
        self.inames[node.iname] = node


class PipelineBroadcastHelper(Visitor):
    def __init__(self):
        self.sinks = {}

    def doit(self, dag: Dag):
        self.run(dag)
        for sink in dag.sinks:
            if hasattr(sink, "source"):
                self.sinks[sink] = [sink.source]
        return self.sinks

    def generic_visit(self, node: DagNode):
        for child in node.children():
            if child not in self.sinks:
                self.sinks[child] = []
            self.sinks[child].append(node)
        Visitor.generic_visit(self, node)


RegisterSource, RegisterSink = Common.create_dag_node(
    "Register",
    1,
    True,
    static_attrs=dict(input_t=BitVector[16], output_t=BitVector[16]),
)
BitRegisterSource, BitRegisterSink = Common.create_dag_node(
    "Register", 1, True, static_attrs=dict(input_t=Bit, output_t=Bit)
)


class FixInputsOutputAndPipeline(Visitor):
    def __init__(
        self,
        sinks,
        pipeline_inputs,
        harden_flush,
        max_flush_cycles,
        max_tree_leaves,
        tree_branch_factor,
    ):
        self.sinks = sinks

        self.pipeline_inputs = pipeline_inputs

        self.harden_flush = harden_flush
        self.max_flush_cycles = max_flush_cycles

        # Control IO broadcast pipelining tree creation
        self.max_tree_leaves = max_tree_leaves
        self.tree_branch_factor = tree_branch_factor

        self.max_sinks = 0
        for node, sink in sinks.items():
            self.max_sinks = max(self.max_sinks, len(sink))

        max_curr_tree_leaves = min(self.max_tree_leaves, self.max_sinks)
        self.num_stages = (
            math.ceil(math.log(max_curr_tree_leaves, self.tree_branch_factor)) + 1
        )

    def doit(self, dag: Dag):
        self.node_map = {}
        self.added_regs = 0
        self.inputs = []
        self.outputs = []
        self.dag_sources = dag.sources
        self.dag_sinks = dag.sinks
        self.run(dag)
        real_sources = [self.node_map[s] for s in self.dag_sources[1:]]
        real_sinks = [self.node_map[s] for s in self.dag_sinks[1:]]
        return IODag(
            inputs=self.inputs,
            outputs=self.outputs,
            sources=real_sources,
            sinks=real_sinks,
        )

    def _add_new_16b_reg_node(self, prev_src, reg_base_name):
        new_reg_sink = RegisterSink(
            prev_src,
            iname=reg_base_name + "$reg" + str(self.added_regs),
        )
        new_reg_source = RegisterSource(
            iname=reg_base_name + "$reg" + str(self.added_regs)
        )
        self.added_regs += 1
        self.dag_sources.append(new_reg_source)
        self.dag_sinks.append(new_reg_sink)
        self.node_map[new_reg_source] = new_reg_source
        self.node_map[new_reg_sink] = new_reg_sink
        return new_reg_source
    
    def _update_source_node(self, sink, old_source, new_source):
        children_temp = list(sink.children())
        reg_index = children_temp.index(old_source)
        children_temp[reg_index] = new_source
        sink.set_children(*children_temp)

    def create_register_tree(
        self,
        new_io_node,
        new_select_node,
        old_select_node,
        sinks,
        bit,
        min_stages=1,
    ):
        if bit:
            register_source = BitRegisterSource
            register_sink = BitRegisterSink
        else:
            register_source = RegisterSource
            register_sink = RegisterSink

        max_curr_tree_leaves = min(self.max_tree_leaves, len(sinks))
        num_stages = max(self.num_stages, min_stages)

        print(
            "Creating register tree for:",
            new_io_node.iname,
            "with",
            len(sinks),
            "sinks and",
            num_stages,
            "stages",
        )

        levels = [max_curr_tree_leaves]

        while 1 not in levels:
            levels.insert(0, math.ceil(levels[0] / self.tree_branch_factor))
        if num_stages > len(levels):
            for _ in range(num_stages - len(levels)):
                levels.insert(0, 1)

        sources = []

        new_reg_sink = register_sink(
            new_select_node, iname=new_io_node.iname + "$reg" + str(self.added_regs)
        )
        new_reg_source = register_source(
            iname=new_io_node.iname + "$reg" + str(self.added_regs)
        )

        self.added_regs += 1
        self.dag_sources.append(new_reg_source)
        self.dag_sinks.append(new_reg_sink)
        self.node_map[new_reg_source] = new_reg_source
        self.node_map[new_reg_sink] = new_reg_sink
        sources.append(new_reg_source)

        for level in levels[1:]:
            sources_idx = 0
            new_sources = []
            for idx in range(level):
                new_reg_sink = register_sink(
                    sources[sources_idx],
                    iname=new_io_node.iname + "$reg" + str(self.added_regs),
                )
                new_reg_source = register_source(
                    iname=new_io_node.iname + "$reg" + str(self.added_regs)
                )

                self.added_regs += 1
                self.dag_sources.append(new_reg_source)
                self.dag_sinks.append(new_reg_sink)
                self.node_map[new_reg_source] = new_reg_source
                self.node_map[new_reg_sink] = new_reg_sink
                new_sources.append(new_reg_source)
                if (idx + 1) % self.tree_branch_factor == 0:
                    sources_idx += 1
            sources = new_sources

        source_idx = 0
        nodes_per_leaf = math.floor((len(sinks)) / max_curr_tree_leaves)
        for idx, sink in enumerate(sinks):
            children_temp = list(sink.children())
            reg_index = children_temp.index(old_select_node)
            children_temp[reg_index] = sources[source_idx]
            if (idx + 1) % nodes_per_leaf == 0 and (source_idx + 1) < len(sources):
                source_idx += 1
            sink.set_children(*children_temp)

    def create_register_chain_IO2MEM(
        self,
        new_io_node,
        new_select_node,
        old_select_node,
        sinks,
        bit,
        min_stages=2,
        chain_branch_factor=4,
    ):
        if bit:
            register_source = BitRegisterSource
            register_sink = BitRegisterSink
        else:
            register_source = RegisterSource
            register_sink = RegisterSink

        print(
            "Creating register chain for:",
            new_io_node.iname,
            "with",
            len(sinks),
            "sinks",
        )

        # reorder MEM/Pond sinks based on the bank index for better PnR
        sinks_order_dict = {}
        for _ in range(len(sinks)):
            sink_node = sinks[_]
            reg_idx = int(re.search(r"BANK_(\d+)_", sink_node.iname).group(1))
            sinks_order_dict.update({sink_node: reg_idx})
        sorted_sinks_order_dict = sorted(sinks_order_dict.items(), key=lambda x: x[1])
        sorted_sinks_order_dict = dict(sorted_sinks_order_dict)
        sinks_seq = list(sorted_sinks_order_dict.keys())
        # control reg density of kernel broadcast
        if "io16in_kernel_host_stencil" in new_io_node.iname:
            min_stages = 1
            chain_branch_factor = 2
            regs_branch_added = 0
            half = len(sinks) // 2
            sinks = sinks_seq[:half] + sinks_seq[half:][::-1]
        # control reg density of input broadcast
        if "io16in_input_host_stencil" in new_io_node.iname:
            min_stages = 5
            chain_branch_factor = 1
            regs_branch_added = 1
            sinks = sinks_seq

        itr_sinks = [sinks]

        assert min_stages >= 1, "min_stages of reg chain must be >= 1"
        for _ in range(min_stages):
            if _ == 0:
                new_reg_sink = register_sink(
                    new_select_node,
                    iname=new_io_node.iname + "$reg" + str(self.added_regs),
                )
            else:
                new_reg_sink = register_sink(
                    new_reg_source,
                    iname=new_io_node.iname + "$reg" + str(self.added_regs),
                )
            new_reg_source = register_source(
                iname=new_io_node.iname + "$reg" + str(self.added_regs)
            )
            self.added_regs += 1
            self.dag_sources.append(new_reg_source)
            self.dag_sinks.append(new_reg_sink)
            self.node_map[new_reg_source] = new_reg_source
            self.node_map[new_reg_sink] = new_reg_sink

        chain_source = new_reg_source
        for sinks_reg in itr_sinks:
            prev_reg_source = chain_source
            for idx, sink in enumerate(sinks_reg):
                if idx and idx % chain_branch_factor == 0:
                    new_reg_sink = register_sink(
                        prev_reg_source,
                        iname=new_io_node.iname + "$reg" + str(self.added_regs),
                    )
                    new_reg_source = register_source(
                        iname=new_io_node.iname + "$reg" + str(self.added_regs)
                    )
                    self.added_regs += 1
                    self.dag_sources.append(new_reg_source)
                    self.dag_sinks.append(new_reg_sink)
                    self.node_map[new_reg_source] = new_reg_source
                    self.node_map[new_reg_sink] = new_reg_sink
                    prev_reg_source = new_reg_source

                    # Add branch registers
                    for _ in range(regs_branch_added):
                        new_reg_sink = register_sink(
                            prev_reg_source,
                            iname=new_io_node.iname + "$reg" + str(self.added_regs),
                        )
                        new_reg_source = register_source(
                            iname=new_io_node.iname + "$reg" + str(self.added_regs)
                        )
                        self.added_regs += 1
                        self.dag_sources.append(new_reg_source)
                        self.dag_sinks.append(new_reg_sink)
                        self.node_map[new_reg_source] = new_reg_source
                        self.node_map[new_reg_sink] = new_reg_sink
                        prev_reg_source = new_reg_source

                    children_temp = list(sink.children())
                    reg_index = children_temp.index(old_select_node)
                    children_temp[reg_index] = new_reg_source
                    sink.set_children(*children_temp)

                    prev_reg_source = new_reg_source
                else:
                    children_temp = list(sink.children())
                    reg_index = children_temp.index(old_select_node)
                    children_temp[reg_index] = new_reg_source
                    sink.set_children(*children_temp)

    def create_register_chain_IO2POND(
        self,
        new_io_node,
        new_select_node,
        old_select_node,
        sinks,
        bit,
        min_stages=2,
        chain_branch_factor=2,
    ):
        print(
            "Creating register chain for:",
            new_io_node.iname,
            "with",
            len(sinks),
            "sinks",
        )

        node_to_label = {}
        for sink_node in sinks:
            label = label_IO2POND[sink_node.iname]
            node_to_label[sink_node] = label
        # create a list of nodes and sort by its label
        sorted_sinks = sorted(node_to_label.keys(), key=lambda node: node_to_label[node])

        new_reg_source = self._add_new_16b_reg_node(
            prev_src=new_select_node,
            reg_base_name=new_io_node.iname
        )

        prev_reg_source = new_reg_source
        for idx, sink in enumerate(sorted_sinks):
            if idx and idx % chain_branch_factor == 0:
                new_reg_source = self._add_new_16b_reg_node(
                    prev_src=prev_reg_source,
                    reg_base_name=new_io_node.iname
                )
                self._update_source_node(
                    sink=sink,
                    old_source=old_select_node,
                    new_source=new_reg_source
                )
                prev_reg_source = new_reg_source
            else:
                self._update_source_node(
                    sink=sink,
                    old_source=old_select_node,
                    new_source=new_reg_source
                )

    def create_register_chain_MEM2PE(
        self,
        new_io_node,
        new_select_node,
        old_select_node,
        sinks,
        bit,
        chain_branch_factor=2,
    ):
        print(
            "Creating register chain for:",
            new_io_node.iname,
            "with",
            len(sinks),
            "sinks",
        )

        node_to_label = {}
        for sink_node in sinks:
            label = label_MEM2PE[sink_node.iname]
            node_to_label[sink_node] = label
        # create a list of nodes and sort by its label
        sorted_sinks = sorted(node_to_label.keys(), key=lambda node: node_to_label[node])
        sinks_left = sorted_sinks[:8]
        sinks_right = sorted_sinks[8:]

        for sinks_list in [sinks_left, sinks_right]:
            prev_reg_source = new_select_node
            for idx, sink in enumerate(sinks_list):
                if idx % chain_branch_factor == 0:
                    new_reg_source = self._add_new_16b_reg_node(
                        prev_src=prev_reg_source,
                        reg_base_name=new_io_node.iname
                    )
                    self._update_source_node(
                        sink=sink,
                        old_source=old_select_node,
                        new_source=new_reg_source
                    )
                    prev_reg_source = new_reg_source
                else:
                    self._update_source_node(
                        sink=sink,
                        old_source=old_select_node,
                        new_source=prev_reg_source
                    )

    def visit_Select(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if not (
            "hw_output" in [child.iname for child in node.children()]
            or "self" in [child.iname for child in node.children()]
        ):
            new_children = [self.node_map[child] for child in node.children()]
            io_child = new_children[0]

            # -----------------IO2MEM Pipelining-------------------- #
            if "io16in_input" in io_child.iname:
                new_node = new_children[0].select("io2f_17")
                if self.pipeline_inputs:
                    # self.create_register_tree(
                    #     io_child,
                    #     new_node,
                    #     node,
                    #     self.sinks[node],
                    #     False,
                    #     min_stages=self.max_flush_cycles,
                    # )
                    self.create_register_chain_IO2MEM(
                        io_child,
                        new_node,
                        node,
                        self.sinks[node],
                        False,
                    )
            # -----------------IO2POND Pipelining-------------------- #
            if "io16in_kernel" in io_child.iname:
                new_node = new_children[0].select("io2f_17")
                if self.pipeline_inputs:
                    self.create_register_chain_IO2POND(
                        io_child,
                        new_node,
                        node,
                        self.sinks[node],
                        False,
                    )
            # -----------------MEM2PE Pipelining-------------------- #
            elif "input_cgra_stencil" in io_child.iname:
                new_node = new_children[0].select("data_out_0")
                if self.pipeline_inputs:
                    self.create_register_chain_MEM2PE(
                        io_child,
                        new_node,
                        node,
                        self.sinks[node],
                        False,
                    )
            # output MEM to accumulation PE pipelining
            elif False:
                # elif "ub_output_cgra_stencil" in io_child.iname and "add_pipelined" in self.sinks[node][0].iname:
                new_node = new_children[0].select("data_out_0")
                if "MEM2PE_REG_CHAIN" in os.environ:
                    if self.pipeline_inputs:
                        self.create_register_chain_MEM2PE(
                            io_child,
                            new_node,
                            node,
                            self.sinks[node],
                            False,
                        )

            elif "io1in" in io_child.iname:
                new_node = new_children[0].select("io2f_1")
                if self.pipeline_inputs:
                    self.create_register_tree(
                        io_child,
                        new_node,
                        node,
                        self.sinks[node],
                        True,
                        min_stages=1,
                    )
            else:
                new_node = node.copy()

            if node not in self.node_map:
                new_node.set_children(*new_children)
                self.node_map[node] = new_node

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name == "global.IO" or node.node_name == "global.BitIO":
            if "write" in node.iname:
                new_node = Output(type=IO_Output_t, iname=node.iname)
                new_children = []

                for child in node.children():
                    if node.node_name == "global.IO":
                        new_reg_sink = RegisterSink(
                            self.node_map[child],
                            iname=node.iname + "$reg" + str(self.added_regs),
                        )
                        new_reg_source = RegisterSource(
                            iname=node.iname + "$reg" + str(self.added_regs)
                        )
                    else:
                        new_reg_sink = BitRegisterSink(
                            self.node_map[child],
                            iname=node.iname + "$reg" + str(self.added_regs),
                        )
                        new_reg_source = BitRegisterSource(
                            iname=node.iname + "$reg" + str(self.added_regs)
                        )
                    self.dag_sources.append(new_reg_source)
                    self.dag_sinks.append(new_reg_sink)
                    self.node_map[new_reg_source] = new_reg_source
                    self.node_map[new_reg_sink] = new_reg_sink
                    self.added_regs += 1
                    new_children.append(new_reg_source)

                new_node.set_children(*new_children)
                self.outputs.append(new_node)
            else:
                new_node = Input(type=IO_Input_t, iname=node.iname)
                self.inputs.append(new_node)

            self.node_map[node] = new_node
        else:
            if not (
                node.node_name == "Input"
                or "Input" in [child.node_name for child in node.children()]
            ):
                new_children = [self.node_map[child] for child in node.children()]
                new_node = node.copy()
                if node not in self.node_map:
                    new_node.set_children(*new_children)
                    self.node_map[node] = new_node


class PackRegsIntoPonds(Visitor):
    def __init__(self, sinks):
        self.sinks = sinks

    def find_pe(self, node, num_regs, reg_skip_list):
        if node.node_name == "global.PE":
            return node, num_regs, reg_skip_list

        if node not in self.sinks:
            return None, None, None
        assert len(self.sinks[node]) == 1
        new_node = self.sinks[node][0]
        if new_node.node_name == "Register":
            reg_skip_list.append(new_node)
            if not isinstance(node, Sink):
                num_regs += 1
        return self.find_pe(new_node, num_regs, reg_skip_list)

    def find_packing(self, dag):
        connections_to_nodes = {}
        connections = []
        ponds = []
        pes = []

        for pond in dag.sources:
            if pond.node_name == "cgralib.Pond":
                ponds.append(pond.iname)
                for pond_sink in self.sinks[pond]:
                    assert pond_sink.node_name == "Select"
                    pe_node, num_regs, reg_skip_list = self.find_pe(pond_sink, 0, [])
                    if pe_node is not None:
                        if pe_node.iname not in pes:
                            pes.append(pe_node.iname)

                        connections.append((pond.iname, pe_node.iname))
                    else:
                        connections.append((pond.iname, f"other_{len(connections)}"))

                    conn = connections[-1]
                    connections_to_nodes[f"{conn[0]}_{conn[1]}"] = pond_sink

        model = pulp.LpProblem("linear_programming", pulp.LpMaximize)

        pulp_vars = []
        for conn in connections:
            name = conn[0] + "_" + conn[1]
            pulp_var = pulp.LpVariable(name, lowBound=0, cat="Binary")
            pulp_vars.append(pulp_var)

            model += pulp_var

            if conn[1] not in pes:
                model += pulp_var == 0

        for pond in ponds:
            connections_from_ponds = len(
                [conn for conn in connections if conn[0] == pond]
            )
            if connections_from_ponds == 2:
                model += pulp.lpSum([var for var in pulp_vars if pond in var.name]) == 1

        for pe in pes:
            model += pulp.lpSum([var for var in pulp_vars if pe in var.name]) <= 1

        model += pulp.lpSum([var for var in pulp_vars])
        model.solve(pulp.PULP_CBC_CMD(msg=0))

        pond_node_to_port = {}

        for var in pulp_vars:
            if var.value() == 1.0:
                # Port 0
                pond_node_to_port[connections_to_nodes[var.name]] = 0
            else:
                # Port 1
                pond_node_to_port[connections_to_nodes[var.name]] = 1

        return pond_node_to_port

    def doit(self, dag: Dag):
        self.optimal_packing = self.find_packing(dag)
        self.swap_pond_ports = []
        self.skip_reg_nodes = []
        self.pe_to_pond_conns = {}
        self.pond_reg_skipped = {}
        self.node_map = {}
        self.inputs = []
        self.outputs = []
        self.dag_sources = []
        self.dag_sinks = []
        self.run(dag)
        for source in dag.sources:
            if hasattr(source, "sink"):
                self.dag_sources.append(source)
                self.dag_sinks.append(source.sink)
        real_sources = [
            self.node_map[s] for s in self.dag_sources if s in self.node_map
        ]
        real_sinks = [self.node_map[s] for s in self.dag_sinks if s in self.node_map]
        return (
            IODag(
                inputs=self.inputs,
                outputs=self.outputs,
                sources=real_sources,
                sinks=real_sinks,
            ),
            self.pond_reg_skipped,
            self.swap_pond_ports,
        )

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node in self.skip_reg_nodes:
            return

        n_node = node

        if node in self.optimal_packing:
            pond_port = f"data_out_pond_{self.optimal_packing[node]}"
            pe_node, num_regs, reg_skip_list = self.find_pe(node, 0, [])

            if pond_port == "data_out_pond_0":
                # packing in the same tile
                self.pe_to_pond_conns[pe_node] = node
                self.skip_reg_nodes += reg_skip_list
                self.pond_reg_skipped[node.child.iname] = num_regs

            n_node = node.child.select(pond_port)

            if pond_port != node.field:
                self.swap_pond_ports.append(n_node.child.iname)

        if n_node in self.pe_to_pond_conns:
            new_children = []
            for child in n_node.children():
                if child in self.node_map:
                    new_children.append(self.node_map[child])
                else:
                    new_children.append(self.pe_to_pond_conns[n_node])
            new_node = n_node.copy()
            if n_node not in self.node_map:
                new_node.set_children(*new_children)
                self.node_map[n_node] = new_node
        else:
            new_children = [self.node_map[child] for child in n_node.children()]
            new_node = n_node.copy()
            new_node.set_children(*new_children)
            self.node_map[node] = new_node
            if n_node.node_name == "Output":
                self.outputs.append(new_node)
            if n_node.node_name == "Input":
                self.inputs.append(new_node)


class CountTiles(Visitor):
    def __init__(self):
        pass

    def doit(self, dag: Dag):
        self.num_pes = 0
        self.num_mems = 0
        self.num_ponds = 0
        self.num_ios = 0
        self.num_regs = 0
        self.run(dag)
        print(f"PEs: {self.num_pes}")
        print(f"MEMs: {int(self.num_mems/2)}")
        print(f"Ponds: {int(self.num_ponds/2)}")
        print(f"IOs: {self.num_ios}")
        print(f"Regs: {int(self.num_regs/2)}")

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name == "Input" or node.node_name == "Output":
            self.num_ios += 1
        elif node.node_name == "global.PE":
            self.num_pes += 1
        elif node.node_name == "cgralib.Mem":
            self.num_mems += 1
        elif node.node_name == "cgralib.Pond":
            self.num_ponds += 1
        elif node.node_name == "Register":
            self.num_regs += 1


def create_netlist_info(
    app_dir,
    dag: Dag,
    tile_info: dict,
    load_only=False,
    harden_flush=False,
    max_flush_cycles=0,
    pipeline_input_broadcasts=False,
    input_broadcast_branch_factor=4,
    input_broadcast_max_leaves=16,
):
    if load_only:
        packed_file = os.path.join(app_dir, "design.packed")
        id_to_name = pythunder.io.load_id_to_name(packed_file)

    sinks = PipelineBroadcastHelper().doit(dag)
    fdag = FixInputsOutputAndPipeline(
        sinks,
        pipeline_input_broadcasts,
        harden_flush,
        max_flush_cycles,
        input_broadcast_max_leaves,
        input_broadcast_branch_factor,
    ).doit(dag)

    sinks = PipelineBroadcastHelper().doit(fdag)
    pdag, pond_reg_skipped, swap_pond_ports = PackRegsIntoPonds(sinks).doit(fdag)

    def tile_to_char(t):
        if t.split(".")[1] == "PE":
            return "p"
        elif t.split(".")[1] == "Mem":
            return "m"
        elif t.split(".")[1] == "Pond":
            return "M"
        elif t.split(".")[1] == "IO":
            return "I"
        elif t.split(".")[1] == "BitIO":
            return "i"

    node_info = {t: tile_to_char(t) for t in tile_info}
    nodes_to_ids = CreateIDs(node_info).doit(pdag)

    if load_only:
        names_to_ids = {name: id_ for id_, name in id_to_name.items()}
    else:
        names_to_ids = nodes_to_ids

    info = {}
    info["id_to_name"] = {id: node for node, id in names_to_ids.items()}

    node_to_metadata = CreateMetaData().doit(pdag)
    info["id_to_metadata"] = {}
    for node, md in node_to_metadata.items():
        info["id_to_metadata"][nodes_to_ids[node]] = md
        if node in swap_pond_ports:
            print(f"swapping ports for {nodes_to_ids[node]}")
            new_config = {}
            new_config["in2regfile_0"] = info["id_to_metadata"][nodes_to_ids[node]][
                "config"
            ]["in2regfile_0"]

            if "in2regfile_1" in info["id_to_metadata"][nodes_to_ids[node]]["config"]:
                new_config["in2regfile_1"] = info["id_to_metadata"][nodes_to_ids[node]][
                    "config"
                ]["in2regfile_1"]

            new_config["regfile2out_1"] = info["id_to_metadata"][nodes_to_ids[node]][
                "config"
            ]["regfile2out_0"]

            if "regfile2out_1" in info["id_to_metadata"][nodes_to_ids[node]]["config"]:
                new_config["regfile2out_0"] = info["id_to_metadata"][
                    nodes_to_ids[node]
                ]["config"]["regfile2out_1"]

            info["id_to_metadata"][nodes_to_ids[node]]["config"] = new_config

        if node in pond_reg_skipped:
            info["id_to_metadata"][nodes_to_ids[node]]["config"]["regfile2out_0"][
                "cycle_starting_addr"
            ][0] += pond_reg_skipped[node]

    nodes_to_instrs = CreateInstrs(node_info).doit(pdag)
    info["id_to_instrs"] = {
        id: nodes_to_instrs[node] for node, id in nodes_to_ids.items()
    }

    info["instance_to_instrs"] = {
        info["id_to_name"][id]: instr
        for id, instr in info["id_to_instrs"].items()
        if ("p" in id or "m" in id or "I" in id or "i" in id)
    }
    for node, md in node_to_metadata.items():
        info["instance_to_instrs"][node] = md

    node_info = {t: fc.Py.input_t for t, fc in tile_info.items()}
    bus_info, netlist = CreateBuses(node_info).doit(pdag)
    info["buses"] = bus_info
    info["netlist"] = {}

    for bid, ports in netlist.items():
        info["netlist"][bid] = [
            (nodes_to_ids[node.iname], field) for node, field in ports
        ]

    if os.path.isfile(app_dir + "manual.place"):
        os.remove(app_dir + "manual.place")

    if "MANUAL_PLACER" in os.environ:
        graph = NetlistGraph(info)
        graph.get_in_ub_latency(app_dir=app_dir)
        graph.get_compute_kernel_latency(app_dir=app_dir)

        # remove mem reg in conn for manual placement
        graph.remove_mem_reg_tree()
        # graph.generate_tile_conn(app_dir = app_dir)

        # manual placement
        graph.manualy_place_resnet(app_dir=app_dir)

    CountTiles().doit(pdag)

    return info
