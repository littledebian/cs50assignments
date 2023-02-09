# Check if a credit card number is valid using numerical method with mod 10
#
# Luhn's algorithm: 1) Double every other digit starting from the penultimate,
#    2) Sum digits in resulting set (single digits),
#    3) Add total to sum of remaining digits,
#    if total is multiple of 10, then checksum is valid
#
# Test cards
# card = [378282246310005, 371449635398431, 5555555555554444, 5105105105105100, 4111111111111111, 4012888888881881, 1234567890]


def main():

    # Check input is an integer of 15-16 digits
    while True:
        try:
            n = int(input("Number: "))
        except:
            print('', end='')
        else:
            s = str(n)
            l = len(s)
            if l < 15 or l > 16:
                print("INVALID")
                exit(1)
            else:
                break

    # Digest number, alternating lists between
    # ultimate and penultimate digit
    ult = []
    penult = []
    while n > 0:

        # Last digit
        rem = n % 10
        ult.append(rem)
        n = (n - rem)/10

        # Penultimate digit
        rem = n % 10
        penult.append(rem)
        n = (n - rem)/10

    # Double items in penultimate
    dup = []
    for i in range(len(penult)):
        dup.append(2 * penult[i])

    # Sum doubles, splitting digits if necessary
    sum = 0
    for i in range(len(dup)):
        if dup[i] > 9:
            sum += (dup[i] - 9)
        else:
            sum += dup[i]

    # Sum total
    for i in range(len(ult)):
        sum += ult[i]

    # Check card valid
    if sum % 10 != 0:
        print("INVALID")
    else:
        if s[0] == '3' and s[1] in ['4', '7']:
            print("AMEX")
        elif s[0] == '5' and s[1] in ['1', '2', '3', '4', '5']:
            print("MASTERCARD")
        elif s[0] == '4':
            print("VISA")
        else:
            print("INVALID")
main()