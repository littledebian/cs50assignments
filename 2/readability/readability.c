#include <cs50.h>
#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

// index = 0.0588 * L - 0.296 * S - 15.8
// L: avg letters /100 words
// S: avg sentences /100 words


int count_letters(string text);
int count_words(string text);
int count_sentences(string text);

int main(void)
{
    // Prompt user for text
    string text = get_string("Text: ");

    int letters = count_letters(text);
    int words = count_words(text);
    int sentences = count_sentences(text);

    float l = (float) letters / (float) words * 100;
    float s = (float) sentences / (float) words * 100;
    int level = round(0.0588 * l - 0.296 * s - 15.8);

    if (level < 1)
    {
        printf("Below Grade 1\n");
    }
    else if (level > 15)
    {
        printf("Grade 16+\n");
    }
    else
    {
        printf("Grade %i\n", level);
    }
}

// Count num letters in text
int count_letters(string text)
{
    int l = strlen(text);
    int sum = 0;
    for (int i = 0; i < l; i++)
    {
        char c = text[i];
        if (isupper(c) || islower(c))
        {
            sum++;
        }
    }
    return sum;
}

// Count num words
int count_words(string text)
{
    // If ascii is 32, char is a space
    // Assume num words is num spaces +1
    int l = strlen(text);
    int sum = 0;
    for (int i = 0; i < l; i++)
    {
        char c = text[i];
        if (c == 32)
        {
            sum++;
        }
    }
    return (sum + 1);
}

// Count num sentences
int count_sentences(string text)
{
    // If char is in [. ! ?] then count it
    int l = strlen(text);
    int sum = 0;
    for (int i = 0; i < l; i++)
    {
        char c = text[i];
        if (c == 33 || c == 46 || c == 63)
        {
            sum++;
        }
    }
    return sum;
}