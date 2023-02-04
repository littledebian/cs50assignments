#include <cs50.h>
#include <stdio.h>

// Mario pyramid
//
//    #  #
//   ##  ##
//  ###  ###
// ####  ####


void bricks(int n);

int main(void)
{
    // Prompt for height n
    int n;
    do
        n = get_int("Height: ");
    while (n < 1 || n > 8);
    bricks(n);
}

// Paint bricks
void bricks(int n)
{
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

        // Gap zone
        printf("  ");

        // Hash l through i
        for (int l=0; l<=i; l++)
        {
            printf("#");
        }

        // Newline
        printf("\n");
    }
}