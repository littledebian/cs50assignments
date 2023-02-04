#include <cs50.h>
#include <stdio.h>

// Mario half pyramid
//
//    #
//   ##
//  ###
// ####


int main(void)
{
    // Get height from user
    int n;
    do
        n = get_int("Height: ");
    while (n < 1 || n > 8);

    // Rows i to n
    for (int i=0; i<n; i++)
    {
        // Space
        for (int j=n-1; j>i; j--)
        {
            printf(" ");
        }
        // Hash k through i
        for (int k=0; k<=i; k++)
        {
            printf("#");
        }
        printf("\n");
    }
}