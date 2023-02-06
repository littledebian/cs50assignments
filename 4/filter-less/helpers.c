#include <math.h>
#include "helpers.h"


// Convert image to grayscale
void grayscale(int height, int width, RGBTRIPLE image[height][width])
{
    // For each pixel, for each color: set all to average
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            int avg = (image[i][j].rgbtRed + image[i][j].rgbtGreen + image[i][j].rgbtBlue) / 3;
            image[i][j].rgbtRed = avg;
            image[i][j].rgbtGreen = avg;
            image[i][j].rgbtBlue = avg;
        }
    }
    return;
}

// Convert image to sepia
void sepia(int height, int width, RGBTRIPLE image[height][width])
{
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            int originalRed = image[i][j].rgbtRed;
            int originalGreen = image[i][j].rgbtGreen;
            int originalBlue = image[i][j].rgbtBlue;

            int sepiaRed = round(.393 * originalRed + .769 * originalGreen + .189 * originalBlue);
            if (sepiaRed > 255)
            {
                sepiaRed = 255;
            }

            int sepiaGreen = round(.349 * originalRed + .686 * originalGreen + .168 * originalBlue);
            if (sepiaGreen > 255)
            {
                sepiaGreen = 255;
            }

            int sepiaBlue  = round(.272 * originalRed + .534 * originalGreen + .131 * originalBlue);
            if (sepiaBlue > 255)
            {
                sepiaBlue = 255;
            }

            image[i][j].rgbtRed = sepiaRed;
            image[i][j].rgbtGreen = sepiaGreen;
            image[i][j].rgbtBlue = sepiaBlue;
        }
    }
    return;
}

// Reflect image horizontally
void reflect(int height, int width, RGBTRIPLE image[height][width])
{
    // Iterate over half the image, swap pixels
    int w = floor(width/2);
    RGBTRIPLE tmp;

    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < w; j++)
        {
            tmp = image[i][j];
            image[i][j] = image[i][width-1-j];
            image[i][width-1-j] = tmp;
        }
    }
    return;
}

// Blur image (read from copy, write to img)
void blur(int height, int width, RGBTRIPLE image[height][width])
{
    // Copy image
    RGBTRIPLE copy[height][width];

    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            copy[i][j] = image[i][j];
        }
    }

    int u, d, l, r;
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            // Handle edges
            if (i == 0)
            {
                u = i;
            }
            else
            {
                u = i - 1;
            }

            if (i == height - 1)
            {
                d = i;
            }
            else
            {
                d = i + 1;
            }

            if (j == 0)
            {
                l = j;
            }
            else
            {
                l = j - 1;
            }

            if (j == width - 1)
            {
                r = j;
            }
            else
            {
                r = j + 1;
            }
            // The above checks ensure we don't attempt to iterate beyond the boundaries of the array,
            // however pixels on the edge will be double counted in the following blur box calculation.
            // An alternative is to figure average RGBs for each of the corner and edge cases in
            // addition to the default blur box, but no progress has been made in that regard.


            // Blur box from copy
            int avgR = (copy[u][l].rgbtRed + copy[u][j].rgbtRed + copy[u][r].rgbtRed +
                        copy[i][l].rgbtRed + copy[i][j].rgbtRed + copy[i][r].rgbtRed +
                        copy[d][l].rgbtRed + copy[d][j].rgbtRed + copy[d][r].rgbtRed) / 9;

            int avgG = (copy[u][l].rgbtGreen + copy[u][j].rgbtGreen + copy[u][r].rgbtGreen +
                        copy[i][l].rgbtGreen + copy[i][j].rgbtGreen + copy[i][r].rgbtGreen +
                        copy[d][l].rgbtGreen + copy[d][j].rgbtGreen + copy[d][r].rgbtGreen) / 9;

            int avgB = (copy[u][l].rgbtBlue + copy[u][j].rgbtBlue + copy[u][r].rgbtBlue +
                        copy[i][l].rgbtBlue + copy[i][j].rgbtBlue + copy[i][r].rgbtBlue +
                        copy[d][l].rgbtBlue + copy[d][j].rgbtBlue + copy[d][r].rgbtBlue) / 9;

            // Write to image
            image[i][j].rgbtRed = avgR;
            image[i][j].rgbtGreen = avgG;
            image[i][j].rgbtBlue = avgB;
        }
    }
    return;
}
