#include <cs50.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

// A character in ASCII is between 0 and 127, ie less than 2^7
// For each character in the message, we need a row of bulbs of length 8
// One solution is to iterate over the exponent for powers of 2 from 7 through 0
// if the character is greater than the square at each interval, the bit is 1.


const int BITS_IN_BYTE = 8;

void print_bulb(int bit);

int main(void)
{
    // Get string
    string msg = get_string("Your message: ");
    int l = strlen(msg);

    // For char in msg
    for (int i = 0; i < l; i++)
    {
        // Cast char to int
        int n = msg[i];

        // Check n at least a power of 2 for each exponent, decreasing n on success
        for (int x = 7; x >= 0; x--)
        {
            int bit = 0;
            int square = pow(2, x);
            if (n >= square)
            {
                bit = 1;
                n -= square;
            }

            // Print bulb
            print_bulb(bit);
        }

        // End row, new line
        printf("\n");
    }
}

void print_bulb(int bit)
{
    if (bit == 0)
    {
        // Dark emoji
        printf("\U000026AB");
    }
    else if (bit == 1)
    {
        // Light emoji
        printf("\U0001F7E1");
    }
}