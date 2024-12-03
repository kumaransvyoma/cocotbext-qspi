import cocotb
from cocotb.handle import SimHandle

class QspiBus:
    def __init__(self, sclk, cs, io0, io1, io2, io3):
        self.sclk = sclk    # Serial clock signal
        self.cs = cs        # Chip select signal
        self.io0 = io0      # Data line 0
        self.io1 = io1      # Data line 1
        self.io2 = io2      # Data line 2
        self.io3 = io3      # Data line 3


    @classmethod
    def from_prefix(cls, entity: SimHandle, prefix: str):
        # Retrieve signals based on prefix
        sclk = getattr(entity, f"{prefix}.io_clk_o")
        cs = getattr(entity, f"{prefix}.io_ncs_o")
        io0 = getattr(entity, f"{prefix}.io_io_o")
        io1 = getattr(entity, f"{prefix}.io_io_o")
        io2 = getattr(entity, f"{prefix}.io_io_o")
        io3 = getattr(entity, f"{prefix}.io_io_o")
        # io_full = getattr(entity, f"{prefix}.io_io_o")  # Access the full 4-bit signal
        # io0 = lambda: io_full.value[0]  # Bit 0
        # io1 = lambda: io_full.value[1]  # Bit 1
        # io2 = lambda: io_full.value[2]  # Bit 2
        # io3 = lambda: io_full.value[3]  # Bit 3
        return cls(sclk, cs, io0, io1, io2, io3)
