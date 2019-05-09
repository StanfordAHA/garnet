class VirtualDoubleBuffer:
    def __init__(self, input_port, output_port, capacity, _range, stride, start, manual_switch):
        assert capacity % input_port == 0, "capacity is not divisible by input_port number!\n"
        assert capacity % output_port == 0, "capacity is not divisible by output_port number!\n"
        self._bank_num = 2
        self._select = 0
        self._input_port = input_port
        self._output_port = output_port
        self._capacity = capacity
        self.read_iterator = AccessIter(_range, stride, start)
        #no read need for empty buffer
        self.read_iterator._done = 1
        self.write_iterator = AccessIter([capacity / output_port], [1], 0)
        self.write_iterator._done = 0
        self._data = [[655355 for _ in range(self._capacity)] for _ in range(self._bank_num)]
        self._manual_switch = manual_switch

    def switch(self):
      if (self._manual_switch == 1):
        self._select= self._select ^ 1
        self.read_iterator.restart()
        self.write_iterator.restart()

    def check_switch(self):
        if self.read_iterator._done and self.write_iterator._done:
            self._select = self._select ^ 1
            self.read_iterator.restart()
            self.write_iterator.restart()

    def read(self, offset = 0):
        if(self._manual_switch == 0):
            assert self.read_iterator._done == 0, "No more read allowed!\n"
        start_addr = (self.read_iterator._addr - offset) * self._output_port
        end_addr = start_addr + self._output_port
        out = self._data[self._select][start_addr: end_addr]
        self.read_iterator.update()
        if(self._manual_switch == 0):
            self.check_switch()
        return out

    def write(self, data_in, offset = 0):
        assert self.write_iterator._done == 0, "No more write allowed!\n"
        if(self._input_port > 1):
            assert len(data_in) == self._input_port, "Input data size not match port number!\n"
        if(self._input_port > 1):
            for addr_in_word ,word_data in enumerate(data_in):
                self._data[1-self._select][(self.write_iterator._addr - offset)\
                                       * self._input_port + addr_in_word] = word_data
        else:
            self._data[1-self._select][(self.write_iterator._addr - offset)]\
                                    = data_in
        self.write_iterator.update()
        if(self._manual_switch == 0):
            self.check_switch()


class AccessPattern:
    def __init__(self, _range, stride, start):
        self._rng = _range
        self._st = stride
        self._start = start

class AccessIter(AccessPattern):
    def __init__(self, _range, stride, start):
        super().__init__(_range, stride, start)
        self._iter = [0 for _ in range(len(_range))]
        self._addr = sum([i*j for i, j in zip(self._iter, self._st)]) + self._start
        self._done = 0

    def restart(self):
        self._iter = [0 for _ in range(len(self._rng))]
        self._done = 0
        self._addr = sum([i*j for i, j in zip(self._iter, self._st)]) + self._start

    def update(self):
        # ignore done for test purpose
        #assert self._done == 0, "Error: no more read can make according to access pattern"
        for dim in range(len(self._iter)):
            self._iter[dim] += 1
            if dim > 0:
                self._iter[dim - 1] = 0
            if dim <len(self._iter) - 1:
                if self._iter[dim] < self._rng[dim]:
                    break
                elif self._rng[dim + 1] == 0:
                    self._done = 1
                    self.restart()
                    break
            else:
                if self._iter[dim] == self._rng[dim]:
                    self._done = 1
                    self.restart()
                    break
        self._addr = sum([i*j for i, j in zip(self._iter, self._st)]) + self._start



