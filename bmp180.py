import pyb
from struct import unpack as unp

# BMP180 default address
BMP180_I2CADDR          = 0x77
# Operating Modes
BMP180_ULTRALOWPOWER    = 0
BMP180_STANDARD         = 1
BMP180_HIGHRES          = 2
BMP180_ULTRAHIGHRES     = 3
# BMP180 Registers 
BMP180_CAL_AC1          = 0xAA
BMP180_CAL_AC2          = 0xAC
BMP180_CAL_AC3          = 0xAE
BMP180_CAL_AC4          = 0xB0
BMP180_CAL_AC5          = 0xB2
BMP180_CAL_AC6          = 0xB4
BMP180_CAL_B1           = 0xB6
BMP180_CAL_B2           = 0xB8
BMP180_CAL_MB           = 0xBA
BMP180_CAL_MC           = 0xBC
BMP180_CAL_MD           = 0xBE
BMP180_CONTROL          = 0xF4
BMP180_TEMPDATA         = 0xF6
BMP180_PRESSUREDATA     = 0xF6
# Commands
BMP180_READTEMPCMD      = 0x2E
BMP180_READPRESSUREDCMD = 0x34

class BMP180():
    def __init__(self, bus=1, address=BMP180_I2CADDR, mode=BMP180_STANDARD):
        self._mode = mode
        self._address = address
        self._bus = pyb.I2C(bus, pyb.I2C.MASTER)
        # Load calibration values
        self._load_calibration()
    def _read_byte(self, cmd):
        return self._bus.mem_read(1,self._address,cmd)[0]
        #return unp('>h',self._bus.mem_read(1,self._address, cmd))[0]
    def _read_u16(self, cmd):
        result = self._bus.mem_read(2,self._address,cmd)
        return (result[0]<<8)+result[1]
#        return unp('>h',self._bus.mem_read(2,self._address, cmd))[0]
    def _read_s16(self, cmd):
        result = self._read_u16(cmd)
        if result > 32767:
            result -= (1<<16)
        return result
    def _read_u24(self, cmd):
        result = self._bus.mem_read(3,self._address,cmd)
        #print(result)
        return (result[0]<<16)+(result[1]<<8)+result[2]
    def _write_byte(self, cmd, val):
        self._bus.mem_write(val, self._address, cmd)
    def _load_calibration(self):
        "load calibration"
        self.cal_AC1 = self._read_s16(BMP180_CAL_AC1)
        self.cal_AC2 = self._read_s16(BMP180_CAL_AC2)
        self.cal_AC3 = self._read_s16(BMP180_CAL_AC3)
        self.cal_AC4 = self._read_u16(BMP180_CAL_AC4)
        self.cal_AC5 = self._read_u16(BMP180_CAL_AC5)
        self.cal_AC6 = self._read_u16(BMP180_CAL_AC6)
        self.cal_B1 = self._read_s16(BMP180_CAL_B1)
        self.cal_B2 = self._read_s16(BMP180_CAL_B2)
        self.cal_MB = self._read_s16(BMP180_CAL_MB)
        self.cal_MC = self._read_s16(BMP180_CAL_MC)
        self.cal_MD = self._read_s16(BMP180_CAL_MD)

    def read_raw_temp(self):
        """Reads the raw (uncompensated) temperature from the sensor."""
        self._write_byte(BMP180_CONTROL, BMP180_READTEMPCMD)
        pyb.udelay(4500)
        raw = self._read_s16(BMP180_TEMPDATA)
        return raw

    def read_raw_pressure(self):
        """Reads the raw (uncompensated) pressure level from the sensor."""
        conversion_time = [5000, 8000, 14000, 26000]
        self._write_byte(BMP180_CONTROL, BMP180_READPRESSUREDCMD+(self._mode<<6))
        pyb.udelay(conversion_time[self._mode])
        raw = self._read_u24(BMP180_PRESSUREDATA)>>(8-self._mode)
        #MSB = self._read_byte(BMP180_PRESSUREDATA)
        #LSB = self._read_byte(BMP180_PRESSUREDATA+1)
        #XLSB = self._read_byte(BMP180_PRESSUREDATA+2)
        #raw = ((MSB << 16) + (LSB << 8) + XLSB) >> (8 - self._mode)
        return raw

    def read_temperature(self):
        """Gets teh compensated temperature in degrees celsius."""
        UT = self.read_raw_temp()
        X1 = ((UT-self.cal_AC6) * self.cal_AC5) >> 15
        X2 = (self.cal_MC << 11) / (X1 + self.cal_MD)
        B5 = X1 + X2
        #print('B5 = ',B5)
        temp = (int(B5 + 8) >> 4) / 10.0
        return temp

    def read_pressure(self):
        """Gets the compensated pressure in Pascals."""
        UT = self.read_raw_temp()
        UP = self.read_raw_pressure()
        X1 = ((UT -self.cal_AC6) * self.cal_AC5) >> 15
        X2 = (self.cal_MC << 11) / (X1 + self.cal_MD)
        B5 = X1 + X2
        # Pressure Calculations
        B6 = int(B5 - 4000)
        X1 = (self.cal_B2 * (B6 * B6) >> 12) >> 11
        X2 = (self.cal_AC2 * B6) >> 11
        X3 = X1 + X2
        B3 = (((self.cal_AC1 * 4 + X3) << self._mode) + 2) / 4
        X1 = (self.cal_AC3 * B6) >> 13
        X2 = (self.cal_B1 * ((B6 * B6) >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (self.cal_AC4 * (X3 + 32768)) >> 15
        B7 = (UP - B3) * (50000 >> self._mode)
        if B7 < 0x80000000:
            p = int((B7 * 2) / B4)
        else:
            p = int((B7 / B4) * 2)
        X1 = (p >> 8) * (p >> 8)
        X1 = (X1 * 3038) >> 16
        X2 = (-7357 * p) >> 16
        p = p + ((X1 + X2 + 3791) >> 4)
        return p

    def read_altitude(self, sealevel_pa = 101325.0):
        """Calculates the altitude in meters."""
        #Calculation taken straight from section 3.6 of the datasheet
        pressure = float(self.read_pressure())
        altitude = 44330.0 * (1.0 - pow(pressure / sealevel_pa, (1.0 /5.255)))
        return altitude 

    def read_sealevel_pressure(self, altitude_m=0.0):
        """Calculates the pressure at sealevel when given a know 
        altitude in meters. Returns a value in Pascals."""
        pressure = float(self.read_pressure())
        p0 = pressure / pow(1.0 - altitude_m/4433.0, 5.255)
        return p0
