
import sys
import asyncio
import gc
# import time

from array import array
from asyncio import Event
from micropython import RingIO
from machine import ADC
from machine import Pin

from lib.compat import Queue

from afsk.mod import AFSKModulator
from ax25.ax25 import AX25
from afsk.demod import AFSKDemodulator
from ax25.from_afsk import AX25FromAFSK
from afsk.func import afsk_detector
from upy.afsk import in_afsk
from upy.afsk import out_afsk
from cdsp import i16tobs

import lib.upydash as _
from lib.compat import print_exc

# afsk sample frequency
_FOUT = 11_025
# _FOUT = const(22_050)
# _FOUT = const(44_100)

_AFSK_IN_PIN = const(2)

async def demod_core(in_rx, ax25_q):
    try:
        bits_q = Queue()
        async with AFSKDemodulator(sampling_rate = _FOUT,
                                   in_rx         = in_rx,
                                   stream_type   = 'u16',
                                   bits_out_q    = bits_q,
                                   is_embedded   = True,
                                   options       = {},
                                   verbose       = False,
                                   ) as afsk_demod:
            async with AX25FromAFSK(bits_in_q      = bits_q,
                                    ax25_q         = ax25_q,
                                    verbose        = False):
                await Event().wait()
                # await in_rx.join()
                # await bits_q.join()
    except asyncio.CancelledError:
        raise
    except KeyboardInterrupt:
        return
    except Exception as err:
        print_exc(err)

async def consume_ax25(ax25_q, 
                       is_quite = False, # suppress stdout
                       ):
    try:
        count = 1
        while True:
            ax25 = await ax25_q.get()
            if not is_quite:
                try:
                    sys.stdout.write('[{}] {}\n'.format(count, ax25))
                except UnicodeDecodeError:
                    sys.stdout.write('[{}] ERR\n'.format(count))
                # sys.stdout.flush()
            count += 1
            ax25_q.task_done()
            await asyncio.sleep(0)
    except asyncio.CancelledError:
        raise
    except KeyboardInterrupt:
        return
    except Exception as err:
        print_exc(err)


async def start():

    tasks = []
    try:
        # in_rx = Queue()
        in_rx = RingIO(1024*2*1000)
        ax25_q = Queue()
        adc = ADC(Pin(_AFSK_IN_PIN, Pin.IN))

        #create ax25 consumer
        tasks.append(asyncio.create_task(consume_ax25(ax25_q   = ax25_q,)))
        tasks.append(asyncio.create_task(in_afsk(adc = adc, rio = in_rx,)))
        tasks.append(asyncio.create_task(demod_core(in_rx = in_rx, 
                                                    ax25_q    = ax25_q)))

        await asyncio.gather(*tasks, return_exceptions=True)

    except asyncio.CancelledError:
        raise
    except KeyboardInterrupt:
        return
    except Exception as err:
        print_exc(err)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*[t for t in tasks if not t.done()], return_exceptions=True)

def main():
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        pass
    except Exception as err:
        print_exc(err)
    finally:
        asyncio.new_event_loop()  # Clear retained state
main()
