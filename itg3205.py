import math
from pyb import I2C

class i2c_itg3205:
	
	WhoAmI = 0x0
	SampleRateDivider = 0x15
	DLPFAndFullScale = 0x16
	InterruptConfig = 0x17
	InterruptStatus = 0x1A
	TempDataRegisterMSB = 0x1B
	TempDataRegisterLSB = 0x1C
	GyroXDataRegisterMSB = 0x1D
	GyroXDataRegisterLSB = 0x1E
	GyroYDataRegisterMSB = 0x1F
	GyroYDataRegisterLSB = 0x20
	GyroZDataRegisterMSB = 0x21
	GyroZDataRegisterLSB = 0x22
	PowerManagement = 0x3E
	
	# DLPF, Full Scale Setting
	FullScale_2000_sec = 0x18 # must be set at reset
	DLPF_256_8 = 0x00# Consult datasheet for explanation
	DLPF_188_1 = 0x01
	DLPF_98_1 = 0x02
	DLPF_42_1 = 0x03
	DLPF_20_1 = 0x04
	DLPF_10_1 = 0x05
	DLPF_5_1 = 0x06
	
	# Power Management Options
	PM_H_Reset = 0x80 # Reset device and internel registers to power-up-default settings
	PM_Sleep = 0x40 # Enables low power sleep mode
	PM_Standby_X = 0x20 # Put Gyro X in standby mode
	PM_Standby_Y = 0x10 # Put Gyro Y in standby mode
	PM_Standby_Z = 0x08 # Put Gyro Z in standby mode
	PM_Clock_Internal = 0x00 # Use internal oscillator
	PM_Clock_X_Gyro = 0x01
	PM_Clock_Y_Gyro = 0x02
	PM_Clock_Z_Gyro = 0x03
	PM_Clock_Ext_32_768 = 0x04
	PM_Clock_Ext_19_2 = 0x05
	
	# Interrupt Configuration
	IC_IntPinActiveLow = 0x80
	IC_IntPinOpen = 0x40
	IC_LatchUntilIntCleared = 0x20
	IC_LatchClearAnyRegRead = 0x10
	IC_IntOnDeviceReady = 0x04
	IC_IntOnDataReady = 0x01
	
	# Address will always be either 0x68 (104) or 0x69 (105)
	def __init__(self, port=1, addr=0x69):
		self.bus = I2C(port, I2C.MASTER)
		self.addr = addr
		self.setPowerManagement(0x00)
		self.setSampleRateDivider(0x07)
		self.setDLPFAndFullScale(self.FullScale_2000_sec, self.DLPF_188_1)
		self.setInterrupt(self.IC_LatchUntilIntCleared, self.IC_IntOnDeviceReady, self.IC_IntOnDataReady)
	
        def write_byte(self, register, options):
            self.bus.mem_write(options, self.addr, register)

        def read_byte(self, register):
            options = self.bus.mem_read(1, self.addr, register)
            return options[0]

        def read_s16int(self, register):
            result = self.bus.mem_read(2, self.addr, register)
            result = (result[0]<<8)+result[1]
            if (result > 32767):
                result -= (1<<16)
            return result

	def setPowerManagement(self, *function_set):
		self.setOption(self.PowerManagement, *function_set)
	
	def setSampleRateDivider(self, divider):
		self.setOption(self.SampleRateDivider, divider)
		
	def setDLPFAndFullScale(self, *function_set):
		self.setOption(self.DLPFAndFullScale, *function_set)
		
	def setInterrupt(self, *function_set):
		self.setOption(self.InterruptConfig, *function_set)
		
	def setOption(self, register, *function_set):
		options = 0x00
		for function in function_set:
			options = options | function
		self.write_byte(register, options)

	# Adds to existing options of register	
	def addOption(self, register, *function_set):
		options = self.read_byte(register)
		for function in function_set:
			options = options | function
		self.write_byte(register, options)
		
	# Removes options of register	
	def removeOption(self, register, *function_set):
		options = self.read_byte(register)
		for function in function_set:
			options = options & (function ^ 0b11111111)
		self.write_byte(register, options)
		
	def getWhoAmI(self):
		whoami = self.read_byte(self.WhoAmI)
		return whoami
		
	def getDieTemperature(self):
		temp = self.read_s16int(self.TempDataRegisterMSB) 
		temp = round(35 + (temp + 13200) / 280, 2)
		return temp
	
	def getInterruptStatus(self):
		(reserved, reserved, reserved, reserved, reserved, itgready, reserved, dataready) = self.getOptions(self.InterruptStatus)
		return (itgready, dataready)
	
	def getOptions(self, register):
		options_bin = self.read_byte(register)
		options = [False, False, False, False, False, False, False, False]

		for i in range(8):
			if options_bin & (0x01 << i):
				options[7 - i] = True
		
		return options
		
	def getAxes(self):
		gyro_x = self.read_s16int(self.GyroXDataRegisterMSB)
		gyro_y = self.read_s16int(self.GyroYDataRegisterMSB)
		gyro_z = self.read_s16int(self.GyroZDataRegisterMSB)
		return (gyro_x, gyro_y, gyro_z)
	
	def getDegPerSecAxes(self):
		(gyro_x, gyro_y, gyro_z) = self.getAxes()
		return (gyro_x / 14.375, gyro_y / 14.375, gyro_z / 14.375)
