
from ax25.defs import DecodeError

AX25_ADDR_LEN  = 7

class CallSSID():
    __slots__ = (
        'call',
        'ssid',
        '_frame',
    )
    def __init__(self, call = None,
                       ssid = None,
                       aprs = None,
                       frame = None,
                       ):
        # Initialize a callsign ssid in three ways
        #   1) By specifying call and ssid explicitly
        #   2) By specifying aprs formatted string/bytes, eg. KI5TOF-5
        #   3) By specifying frame bytes to be decoded
        self.call = call 
        self.ssid = ssid
        self._frame = None
        if frame:
            self._frame = bytes(frame)
            self.from_ax25_frame(frame)
        elif aprs:
            self.from_aprs(aprs)

    def from_aprs(self, call_ssid):
        #read in formats like KI5TOF-5
        if isinstance(call_ssid, str):
            call_ssid = call_ssid.split('-')
        elif isinstance(call_ssid, (bytes, bytearray)):
            call_ssid = call_ssid.decode('utf').split('-')
        else:
            raise Exception('unknown format '+str(call_ssid))
        self.call = call_ssid[0].upper()
        self.ssid = int(call_ssid[1]) if len(call_ssid)==2 else 0

    def to_aprs(self):
        if self.ssid:
            return str(self.call)+'-'+str(self.ssid)
        else:
            return str(self.call)

    def from_ax25_frame(self, mv):
        #read from encoded ax25 format 
        if len(mv) != 7:
            raise DecodeError('callsign bad len {} != {}'.format(len(mv),7))
        for call_len in range(6):
            if mv[call_len] == 0x40: #searching for ' ' character (still left shifted one)
                break
            call_len += 1
        self.call = bytearray(mv[:call_len]) #make bytearray copy, don't modify in place
        for i in range(call_len):
            self.call[i] = self.call[i]>>1
        self.call = self.call.decode('utf')
        self.ssid = (mv[6] & 0x17)>>1

    @property
    def frame(self):
        if self._frame:
            return self._frame
        return self.to_bytes()

    def to_bytes(self, mv = None,):
        #optional mv, write in place if provided
        #callsign exactly 6 characters
        if not mv:
            ax25 = bytearray(7)# AX25_ADDR_LEN
            mv = memoryview(ax25)
        for i in range(len(self.call)):
            mv[i] = ord(self.call[i])
            if i == 6:
                break
        for i in range(6):
            mv[i] = ord(self.call[i]) if i < len(self.call) else ord(' ')
            #shift left in place
            mv[i] = mv[i]<<1
        #SSID is is the 6th bit, shift left by one
        #the right most bit is used to indicate last address
        mv[6] = self.ssid<<1
        mv[6] |= 0x60
        return mv

    def __repr__(self):
        return self.to_aprs()


