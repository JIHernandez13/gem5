from __future__ import print_function
from __future__ import absolute_import

# Imports
import m5
from m5.objects import *
from caches import *
from m5.objects import Cache

# System Defined
system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = 'timing'               
system.mem_ranges = [AddrRange('512MB')]

# Create a simple CPU
system.cpu = TimingSimpleCPU()
system.membus = SystemXBar()
system.cpu.createInterruptController()

# Define L1 and L2
class L1Cache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def __init__(self, options=None):
        super(L1Cache, self).__init__()
        pass

    def connectBus(self, bus):
        self.mem_side = bus.slave

    def connectCPU(self, cpu):
        raise NotImplementedError

class L1ICache(L1Cache):
    size = '16kB'
    def __init__(self, opts=None):
        super(L1ICache, self).__init__(opts)
        if not opts or not opts.l1i_size:
            return
        self.size = opts.l1i_size

    def connectCPU(self, cpu):
        self.cpu_side = cpu.icache_port

class L1DCache(L1Cache):
    size = '64kB'
    def __init__(self, opts=None):
        super(L1DCache, self).__init__(opts)
        if not opts or not opts.l1d_size:
            return
        self.size = opts.l1d_size

    def connectCPU(self, cpu):
        self.cpu_side = cpu.dcache_port

class L2Cache(Cache):
    size = '256kB'
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12
    def __init__(self, opts=None):
        super(L2Cache, self).__init__()
        if not opts or not opts.l2_size:
            return
        self.size = opts.l2_size

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.master

    def connectMemSideBus(self, bus):
        self.mem_side = bus.slave

# Adding L1 and L2
(opts, args) = SimpleOpts.parse_args()
system.cpu.icache = L1ICache(opts)
system.cpu.dcache = L1DCache(opts)
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)
system.l2bus = L2XBar()
system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)
system.l2cache = L2Cache(opts)
system.l2cache.connectCPUSideBus(system.l2bus)
system.l2cache.connectMemSideBus(system.membus)
print('Cache L1 and L2 Added')
# For x86 only, make sure the interrupts are connected to the memory
if m5.defines.buildEnv['TARGET_ISA'] == "x86":
    system.cpu.interrupts[0].pio = system.membus.master
    system.cpu.interrupts[0].int_master = system.membus.slave
    system.cpu.interrupts[0].int_slave = system.membus.master

# Create a DDR3 memory controller and connect it to the membus
system.mem_ctrl = DDR3_1600_8x8()
system.mem_ctrl.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.master
system.system_port = system.membus.slave
isa = str(m5.defines.buildEnv['TARGET_ISA']).lower()

# set up the root SimObject and start the simulation
root = Root(full_system = False)
# instantiate all of the objects we've created above
m5.instantiate()

print("Simulation Started!")
exit_event = m5.simulate()
print('Exiting @ tick %i because %s' % (m5.curTick(), exit_event.getCause()))
