# aws-iot-dog-collar

## Purpose

Create an AWS-powered IoT dog collar that is triggered when a dog is detected getting into trash or getting on sofa when the owner is not home. 

## Overview

An AWS DeepLens is used to build and train a model that detects when a dog is getting into the trash or getting on a sofa. These, or other trained triggers, are herein referred to as "bad behavior". 

When the AWS DeepLens detects bad behavior it instructs a nearby Raspberry Pi ("pi") to send a signal to the dog's collar that triggers a vibration. 

## Status

**Complete**
* Decode RF signals from dog collar remote

**Next Steps**
* Successfully transit decoded signals, confirm they trigger the collar
* Build AWS Lambda + Greengrass solution on pi to transit signals to collar when triggered via MQTT topic on AWS IoT Core
* Build and train ML model with AWS SageMaker to detect dog on couch
* Deploy model to AWS DeepLens
* Configure DeepLens to send vibrate message to pi transmitter when it detects dog on couch

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

## Pi Wiring

The image below shows the wiring of the RF transmitter (left) and RF receiver (right). Note that the RF receiver ultimately wasn't required because I ended up using the RTL-SDR receiver instead. 

There's no requirement to use the same GPIO pins as I did on the pi, so long as you specify the proper pins in your code / utilities. 

![Raspberry Pi Wiring](images/pi.jpg)

### RF Transmitter Wiring

From left-most pin 1 to right-most pin 4:

* Pin 1 "VCC" -> 3.3V on pi
* Pin 2 "DA" -> GPIO 17 on pi
* Pin 3 "G" -> ground on pi
* Pin 4 "AN" -> not used, but I assume this is for an Antenna

### RF Receiver Wiring

This particular RF receiver seemed to have two separate sets of 4 pins each, one on the left and one on the right. In the picture above, you only see the first set of pins as I didn't use/need the second set. 

From left-most pin 1 to right-most pin 4: 

* Pin 1 "GND" -> ground on pi
* Pin 2 "Data" -> GPIO 23 on pi
* Pin 3 "DER" -> unknown; seems to be interchangeable with Pin 2
* Pin 4 "+5V" -> 3.3v on pi

**Note** - even though the receiver's power pin says "+5V", I connected it to a 3.3V pin on the pi because I read that +5V can damage the GPIO pins on the pi. Not sure how accurate this is, but I wanted to be safe. It didn't seem to affect results. 

## RF Code Mapping

Each signal transmitted by the dog collar remote sends a bit string consisting of five 8-bit bytes that vary depending on the remote settings (channel, mode, power), followed by a '1' check digit. Below is an example: 

```
01111110 01111111 00011001 11111010 10000001 1
```

### Byte 1 - Channel and Mode

The first 4 bits of byte 1 specify the channel and the second 4 bits specify the mode. 

**First 4 bits - Channel**
* ```Channel 1``` = ```0111```
* ```Channel 2``` = ```0000```

**Second 4 bits - Mode:**
* ```Beep``` = ```1011```
* ```Light``` = ```0111```
* ```Shock``` = ```1110```
* ```Vibrate``` = ```1101```

For example, if the first byte is ```01110111```, the two 4-bit halves are ```0111``` and ```0111``` which represents ```channel 1``` and ```light mode```, respectively. 

### Byte 2 & 3 - Unknown

Bytes 2nd and 3rd bytes are always ```01111111	00011001```, regardless of the channel, mode, or power selected on the collar remote. 

Perhaps these are unique to the manufacturer? Or perhaps they are unique to the specific remote+collar pair I have? We would need a second identical collar/remote pair to test. 

### Byte 4 - Power

The 4th byte of the transmitted bit string represents the power applied to the collar. 

The sound and light modes do not have a power setting and their 4th byte is always ```11111111```. 

The shock and vibrate modes do have a power setting that ranges from 0 to 100 on the remote control. The power level formula is ```desired power = 255 - (decimal value of 4th byte)```.

For example, if we set the collar remote to channel 1, shock mode, power 5 and press the send button, ```rtl_utils -A``` shows that the the full bit string is: 
```
01111110 01111111 00011001 11111010 10000001 1
```

The fourth byte controls power and has a value of ```11111010``` which is the binary representation of the decimal value ```250```. Using the power formula above, we can see:

```
desired power = 255 - (decimal value of 4th bit string)
desired power = 255 - 250
desired power = 5
```

I reversed engineered the power formula above by simply transmitting each different power setting until a pattern emerged. 

### Byte 5 - Mode and Channel

Byte 5 behaves just like byte 1 in that it encodes the mode and channel using the first and last 4 bits, respectively. 

Byte 5 is different from Byte 1 in that Byte 5 first specifies mode followed by channel, whereas Byte 1 specifies these in reverse order. 

Byte 5 is also different in that the codes themselves are not the same. 

**First 4 bits - Mode:**
* ```Beep``` = ```0010```
* ```Light``` = ```0001```
* ```Shock``` = ```1000```
* ```Vibrate``` = ```0100```

**Second 4 bits - Channel**
* ```Channel 1``` = ```0001```
* ```Channel 2``` = ```1111```

### Bit String Example

Putting all of the bit decoding info together, let's look at an example: 

```
00001110 01111111 00011001	11110101 10001111 1
```

The first byte ```00001110``` tells us ```channel 2``` (first 4 bits = ```0000```) ```shock``` mode (second 4 bits is ```1110```).

As expected, the second and third bytes are always ```01111111 00011001```.

The fourth byte is ```11110101``` which [translates](https://www.rapidtables.com/convert/number/decimal-to-binary.html?x=245) to the decimal ```245```. Using our power formula of ```power = 255 - decimal value of 4th byte```, we can see that ```power = 255 - 245```, i.e. ```power = 10```. 