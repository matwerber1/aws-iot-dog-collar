# aws-iot-dog-collar

## Purpose

Create an AWS-powered IoT dog collar that is triggered when a dog is detected getting into trash or getting on sofa when the owner is not home. 

## Overview

An AWS DeepLens is used to build and train a model that detects when a dog is getting into the trash or getting on a sofa. These, or other trained triggers, are herein referred to as "bad behavior". 

When the AWS DeepLens detects bad behavior it instructs a nearby Raspberry Pi ("pi") to send a signal to the dog's collar that triggers a vibration. 

## Materials

Links provided are to the specific products I used. Generally speaking, any similar products should work; just be sure to match the RF frequency of the collar (e.g. 433 Mhz) with the frequency of the RF transmitter.

1. [RTL-SDR Radio](https://www.amazon.com/gp/product/B01GDN1T4S/ref=ppx_yo_dt_b_asin_title_o01__o00_s01?ie=UTF8&psc=1)

2. [433 Mhz Remote-Controlled Dog Vibration and/or Shock Collar](https://www.amazon.com/gp/product/B00MQ1RBAS/ref=ppx_yo_dt_b_asin_title_o02__o00_s00?ie=UTF8&psc=1)

3. [433 Mhz RF Transmitter](https://www.amazon.com/gp/product/B00HEDRHG6/ref=ppx_yo_dt_b_asin_title_o03__o00_s00?ie=UTF8&psc=1)

4. [Raspberri Pi 3](https://www.amazon.com/gp/product/B01CD5VC92/ref=oh_aui_search_asin_title?ie=UTF8&psc=1)

5. Wires to connect Raspberry Pi to RF transmitter

## Learning

### Radio Transmission Overview

Going in to this, I had zero experience with RF transmission and a very rudimentary understanding of sound waves in general. For example, I knew the difference between frequency and amplitude modulation and understood conceptually how they could be used to encode a signal, but I had no idea of how things are done in practice. 

Even after this project, I still have a very basic understanding. That said, my hope is this document will be a helpful learning tool for someone that, like me, has little to no RF experience. 

### Signal Decoding

By modifying (aka modulating) signal characteristics like frequency and amplitude, you can encode information in radio frequency. There are a variety of ways to encode signals and they vary depending on vendor and use case.

To properly decode (aka demodulate) an RF signal and make it usable, you need to know the encoding method used in the transmission. 

If you have a simple RF Receiver [(like this one)](https://www.amazon.com/gp/product/B00HEDRHG6/ref=ppx_yo_dt_b_asin_title_o03__o00_s00?ie=UTF8&psc=1), Google searches such as "decode 433 Mhz signal with Raspberry Pi" will turn up numerous easy-to-follow walkthroughs [(like this one)](https://www.princetronics.com/how-to-read-433-mhz-codes-w-raspberry-pi-433-mhz-receiver/).

The RF walkthroughs above typically use one of handful of popular Python RF sniffer libraries, such as ninjablocks' [433Utils](https://github.com/ninjablocks/433Utils), to decode transmitted signals. 

After wiring my Pi to the simple RF transmitter linked above, I tried and repeatedly failed to pick up any signal from my dog collar's remote. I tested quite a few libraries/sniffers online and none were successful. Full disclosure, this could have been user error. 

I used a graphical utility on the Pi called [Piscope](http://abyz.me.uk/rpi/pigpio/piscope.html) to visualize activity on the RF receiver. Sure enough, I could see a very obvious signal appearing when buttons were pressed on the dog collar.

I now suspected that the remote was using an encoding that wasn't supported by the sniffer libraries I had tested. I set about to Googling and learned:
1. Most 433 Mhz devices use simple encoding methods that are addressed by the popular libraries I was using. 

2. Some 433 Mhz devices use more complicated encoding. 

3. There are USB RF receivers that are more capable than the simple RF receiver circuit I was originally using and that appeared to have more robust decoding libraries & tools available. 

The collar remote supported 4 settings (vibrate, noise, shock, and turn on a light), different levels (0 - 100) for shock level, and two separate channels (for up to 2 dogs/collars from a single remote). This further supported the idea that the remote had a more complicated encodingl

To test this theory, I ordered [a very basic three-button garage door remote](https://www.amazon.com/gp/product/B07C11TY2X/ref=ppx_od_dt_b_asin_title_o00_s01?ie=UTF8&psc=1) with the hope that the previous RF sniffers would pick it up. Sure enough, they immediately decoded the signal when the garage remote buttons were pressed. 

I therefore ordered an SDR radio with the hopes that the related utilities found online could capture my collar's signal.

Once the SDR arrived I used mernanan's [rtl_433](https://github.com/merbanan/rtl_433) utility in default receive mode which uses the first device found and listens at 433.92 MHz at a 250k sample rate:

```
$ rtl_433
```

Just like the simple 433 Mhz receiver with the Pi, the SDR receiver with rtl_433 detected the garage door opener but failed to detect the collar remote. 

I then skimmed the rtl_433 readme and saw the following option that caught my attention: 

```sh
# Enable pulse analyzer. Summarizes the timings of pulses, gaps, and periods. Can be used with -R 0 to disable decoders.
rtl_433 -A
```

"Pulse" got me thinking... when I hold down the transmit button on the dog remote, the dog collar repeatedly triggers whatever mode the transmitter is set to. E.g. it will continously beep if on the audio mode.

I ran the ```rtl_433 -A``` command, pressed the dog collar button, and saw this beatuiful result: 

```
Detected OOK package	2019-01-26 15:52:59
Analyzing pulses...
Total count:  126,  width: 159.09 ms		(39773 S)
Pulse width distribution:
 [ 0] count:    3,  width: 1576 us [1568;1588]	( 394 S)
 [ 1] count:   57,  width:  796 us [796;804]	( 199 S)
 [ 2] count:   66,  width:  284 us [280;292]	(  71 S)
Gap width distribution:
 [ 0] count:   66,  width:  752 us [752;764]	( 188 S)
 [ 1] count:   57,  width:  240 us [236;252]	(  60 S)
 [ 2] count:    2,  width: 13164 us [13164;13164]	(3291 S)
Pulse period distribution:
 [ 0] count:    3,  width: 2328 us [2320;2344]	( 582 S)
 [ 1] count:  120,  width: 1040 us [1036;1048]	( 260 S)
 [ 2] count:    2,  width: 13448 us [13448;13448]	(3362 S)
Level estimates [high, low]:  15929,     13
RSSI: -0.1 dB SNR: 30.6 dB Noise: -31.0 dB
Frequency offsets [F1, F2]:   12426,      0	(+47.4 kHz, +0.0 kHz)
Guessing modulation: Pulse Width Modulation with sync/delimiter
Attempting demodulation... short_width: 284, long_width: 796, reset_limit: 13168, sync_width: 1576
Use a flex decoder with -X 'n=name,m=OOK_PWM,s=284,l=796,r=13168,g=0,t=0,y=1576'
pulse_demod_pwm(): Analyzer Device 
bitbuffer:: Number of rows: 3 
[00] {41} 7e 7f 19 d0 81 80 : 01111110 01111111 00011001 11010000 10000001 1
[01] {41} 7e 7f 19 d0 81 80 : 01111110 01111111 00011001 11010000 10000001 1
[02] {41} 7e 7f 19 d0 81 80 : 01111110 01111111 00011001 11010000 10000001 1
```

I proceeded to change the mode (sound, light, shock, or vibrate), the channel (1 or 2), and the level of shock and made the following observations: 

1. The short_width was consistently at 280 (+/- ~5)
2. The long_width was consistently at 796 (+/- ~5)
3. The reset_limit was consistently at 13192 (+/- ~20)
4. The sync_width was consistenty at 1592 (+/- ~5)
5. For a given setting combination on the remote, the decoded bit strings were identical

At this point, I know that my remote is transmitting an OOK-encoded RF message, the widths & limits above are the paramaters needed to "tune" a signal to my remote/collar combo, and the four 8-bit codes contain all the info needed by the collar.

Next steps are to capture the bit strings for all of the setting combinations on the remote. Once I have those, I can then device a way to programmatically send the same signals out via the Pi + RF transmitter. 