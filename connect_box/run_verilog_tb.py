import os

res = os.system('python gen_cb_16_10_1111101111_1_7.py')
assert(res == 0)

print( 'DONE with 16, 10 cb' )

res = os.system('python gen_cb_7_8_11111111_0_0.py')
assert(res == 0)
