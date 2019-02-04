
def space_between_bytes(string, length):
    return ' '.join(string[i:i+length] for i in range(0,len(string),length))

def decode1(raw_message):

    # assumes received message has initial 8 1's to ignore, followed by 
    # pattern of 1s and 0s that is a multiple of 5 where each 5-bit pattern
    # is either 00001 or 11101

    raw_length = len(raw_message)

    #ignore 1st 8 chars
    encoded_message = raw_message[8:raw_length]

    encoded_length = len(encoded_message)

    if encoded_length %  5 != 0:
        print("Invalid message length {}, must be divisible by 5".format(encoded_length))
        exit()

    # number of bits to decode
    section_count = int(encoded_length / 5)

    decoded_message = ""
  
    for x in range(section_count):

        section_number = str(x+1)

        # start and end chars of our current substring
        start_pos = (x * 5)
        end_pos   = start_pos + 5

        # get substring
        section   = encoded_message[start_pos:end_pos]
        bit = ""
        
        if section == "00001":
            bit = "0"
        elif section == "11101":
            bit = "1"
        else:
            print("Section {} has unexpected value '{}', should either be 00001 or 11101!".format(section_number, section))
            exit()
        
        decoded_message += bit

    print(space_between_bytes(decoded_message, 8))

def print_byte_file_as_decimals(file):
    with open(file) as f:
        for line in f:
            print(int(line,2))

# old message, Ch 1 sound
msg1 = "111111110000111101000010000100001000011110100001000011110100001000010000100001000010000100001111011110111101000010000111101111010000100001000010000100001000010000100001000011110111101000011110111101111011110100001"

# new message Ch 2 sound
msg2 = "111111110000111101000010000100001000011110100001000011110100001000010000100001000010000100001111011110111101000010000111101111010000100001000010000100001000010000100001000011110111101000011110111101111011110100001"

decode1(msg1)
decode1(msg2)

print_byte_file_as_decimals('decimal-bytes.txt')