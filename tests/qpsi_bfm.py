

import os
import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
from cocotbext.axi import AxiMaster, AxiBus, AxiBurstType

from cocotb.clock import Clock
from cocotbext.qspi import QspiBus, QspiMaster, QspiSlave, QspiConfig
# from cocotbext.qspi.qspi_flash import QspiFlash
from cocotb.triggers import Timer
import logging
import vsc
from enum import Enum, auto
import random

@vsc.randobj
class qspi_item(object):

    def __init__(self):
        self.data = vsc.rand_bit_t(8)
    
@vsc.covergroup
class my_covergroup(object):
    def __init__(self):
        self.with_sample(
            data=vsc.bit_t(8)
        )
        self.cp1 = vsc.coverpoint(self.data, cp_t=vsc.uint8_t())


class QSPIFlash:
    def __init__(self, dut_bsoc):
        # Initialize QSPIFlash class with the dut_bsoc (Device Under Test)
        self.dut_bsoc = dut_bsoc
        
        # Initialize QSPI bus using the prefix 'qspi' from the dut_bsoc signals
        self.qspi_bus = QspiBus.from_prefix(dut_bsoc, "qspi0")
        
        # Configure QSPI communication parameters
        self.qspi_config = QspiConfig(
            word_width=8,
            sclk_freq=25e6,  # SCLK frequency of 25 MHz
            cpol=False,      # Clock polarity (CPOL) = 0
            cpha=False,      # Clock phase (CPHA) = 0
              # Most significant bit first
            cs_active_low=True  # Chip select is active low
        )
        
        # Initialize QSPI master with the configured bus and settings
        self.qspi_master = QspiMaster(self.qspi_bus, self.qspi_config)

    async def reset(self):
        # Reset the device by toggling the reset_n signal
        self.dut_bsoc.reset_n.value = 0
        await Timer(100, units='ns')  # Wait for 100 ns
        self.dut_bsoc.reset_n.value = 1
        await Timer(100, units='ns')  # Wait for another 100 ns

    async def initialize(self):
        # Start the clock with a period of 10 ns
        cocotb.start_soon(Clock(self.dut_bsoc.clk, 10, units='ns').start())
        
        # Call the reset method to initialize the device
        await self.reset()

    async def write(self, address, data):
        # Send a write command along with address and data
        command = [0x02]  # Write command
        address_bytes = [(address >> i) & 0xFF for i in (16, 8, 0)]  # Split address into bytes
        data_bytes = [data]  # Convert data to bytes
        await self.qspi_master.write(command + address_bytes + data_bytes)  # Send command, address, and data
        await self.qspi_master.wait()  # Wait for QSPI transaction to complete

    async def read(self, address):
        # Send a read command along with address to read data
        command = [0x03]  # Read command
        address_bytes = [(address >> i) & 0xFF for i in (16, 8, 0)]  # Split address into bytes
        # await self.qspi_master.write(command + address_bytes)  # Send command and address
        # await self.qspi_master.wait()  # Wait for QSPI transaction to complete
        
        # Read one byte of data from QSPI
        read_data = await self.qspi_master.read(1)
        print("the valueread :",read_data)
        # Handle high-impedance state by resolving to 0xFF
        # read_data_resolved = int(read_data[0].value) if read_data[0].value.is_resolvable else 0xFF
        if isinstance(read_data[0], cocotb.binary.BinaryValue):
            read_data_resolved = int(read_data[0].value) if read_data[0].value.is_resolvable else 0xFF
        else:
            read_data_resolved = read_data[0] if read_data[0] is not None else 0xFF
        print("the valueread1 :",read_data_resolved)
        return read_data_resolved

    async def erase(self, address):
        # Send a sector erase command along with address
        command = [0x20]  # Sector erase command
        address_bytes = [(address >> i) & 0xFF for i in (16, 8, 0)]  # Split address into bytes
        await self.qspi_master.write(command + address_bytes)  # Send command and address
        await self.qspi_master.wait()  # Wait for QSPI transaction to complete

class Testbench:
  def __init__(self, dut_bsoc, clk_freq, axi_baud_value):
    self.dut_bsoc = dut_bsoc
    self.txrx = qspi_item()

    # Calculate the Baud Rate based on the baud_value and clk_freq
    self.baud_rate = clk_freq // (16 * axi_baud_value)
    
    self.log = logging.getLogger("cocotb.tb")
    self.log.setLevel(logging.DEBUG)
    print("signals: ",dut_bsoc.soc)
    self.qspi =QSPIFlash(dut_bsoc.soc)
    self.cg = my_covergroup()

@cocotb.test()
async def test_peripherals(dut):
    
    dut_flash=dut.qspi_flash
    dut_bsoc=dut.mkTbSoc
    """Test to verify qspi through AXI4 transactions"""
    clock = Clock(dut_bsoc.CLK, 100, units="ns")  # Create a 10us period clock on port clk
    # Start the clock. Start it low to avoid issues on the first RisingEdge
    cocotb.start_soon(clock.start(start_high=False))
    dut_bsoc.RST_N.value = 0
    for i in range(0,400):
        await RisingEdge(dut_bsoc.CLK)

    dut_bsoc.RST_N.value = 1
    dut_bsoc._log.info('Incrementing')
    for i in range(0,10):
        await RisingEdge(dut_bsoc.CLK)
    dut_bsoc._log.info('HLOO1')

   # Set clock frequency and baud value
    clk_freq = 1000_0000  # 10 MHz clock
    axi_baud_value = 5  # Given baud value

    for i in range(0,10):
        await RisingEdge(dut_bsoc.CLK)

    tb = Testbench(dut_bsoc, clk_freq, axi_baud_value)
    print("after tb ")

    
    
    address = 0x90
    # await RisingEdge(tb.dut_bsoc.soc.qspi0.io_ncs_o)
    for _ in range(10):
        await RisingEdge(tb.dut_bsoc.CLK)
    # await FallingEdge(tb.dut_bsoc.soc.qspi0.io_ncs_o)
    # tb.dut_bsoc.soc.qspi0.qspi_rg_address =13
    dut_bsoc._log.info('TX_REG value to be read:')
    # read_data = await tb.qspi.read(address)
    # dut_bsoc._log.info('TX_REG valued at:',read_data)
    for _ in range(100):
        await RisingEdge(tb.dut_bsoc.CLK)
    dut_bsoc._log.info('TX_REG value to be read:')
    # read_data = await tb.qspi.read(address)
    # dut_bsoc._log.info('TX_REG valued at:',read_data)
    # await RisingEdge(dut_bsoc.soc.uart_cluster.uart1.SOUT)
    # Wait a few cycles to ensure previous transactions complete
    for _ in range(10000):
        await RisingEdge(tb.dut_bsoc.CLK)
    dut_bsoc._log.info('The end value to be written:')

    vsc.write_coverage_db('cov.xml')
