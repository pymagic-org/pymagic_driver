import pyb
from pyb import Pin, Timer

class MOTORS():

    def __init__(self):
        #设定Pin
        self._rForward = Pin('B8')
        self._rBackward = Pin('B9')
        self._lForward = Pin('B14')
        self._lBackward = Pin('B15')
        #set right motor pwm
        self._rTim = Timer(4, freq=3000)
        self._rf_ch = self._rTim.channel(3, Timer.PWM, pin=self._rForward)
        self._rb_ch = self._rTim.channel(4, Timer.PWM, pin=self._rBackward)
        #set left motor pwm
        self._lTim = Timer(12, freq=3000)
        self._lf_ch = self._lTim.channel(1, Timer.PWM, pin=self._lForward)
        self._lb_ch = self._lTim.channel(2, Timer.PWM, pin=self._lBackward)
    
    #设定右边电机的转速
    #-1 < ratio < 1
    def set_ratio_r(self, ratio):
        #check ratio
        if(ratio > 1.0):
            ratio = 1.0
        elif(ratio < -1.0):
            ratio = -1.0
        if(ratio > 0):
            self._rb_ch.pulse_width_percent(0)
            self._rf_ch.pulse_width_percent(ratio*100)
        elif(ratio < 0):
            self._rf_ch.pulse_width_percent(0)
            self._rb_ch.pulse_width_percent(-ratio*100)
        else:
            self._rf_ch.pulse_width_percent(0)
            self._rb_ch.pulse_width_percent(0)

    #设定左边电机的转速
    #-1 < ratio < 1
    def set_ratio_l(self, ratio):
        #check ratio
        if(ratio > 1.0):
            ratio = 1.0
        elif(ratio < -1.0):
            ratio = -1.0
        if(ratio > 0):
            self._lb_ch.pulse_width_percent(0)
            self._lf_ch.pulse_width_percent(ratio*100)
        elif(ratio < 0):
            self._lf_ch.pulse_width_percent(0)
            self._lb_ch.pulse_width_percent(-ratio*100)
        else:
            self._lf_ch.pulse_width_percent(0)
            self._lb_ch.pulse_width_percent(0)

    def all_stop(self):
        self.set_ratio_l(0)
        self.set_ratio_r(0)
