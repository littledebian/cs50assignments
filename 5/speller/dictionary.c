// Implements a dictionary's functionality
#include <cs50.h>
#include <ctype.h>
#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#include "dictionary.h"


// Represents a node in a hash table
typedef struct node
{
    char word[LENGTH + 1];
    struct node *next;
}
node;

// myFunc
void free_list(node *n);
void free_many(node *cur);

/* Choose number of buckets in hash table */
const unsigned int N = 2886;

// Hash table
node *table[N];

// Number of words in dict
int lines = 0;

// Returns true if word is in dictionary, else false
bool check(const char *word)
{
    // Hash word from text
    unsigned int i = hash(word);
    node *n = table[i];

    // Traverse list at i
    while (n != NULL)
    {
        if (strcasecmp(word, n->word) == 0)
        {
            return true;
        }
        n = n->next;
    }
    return false;
}

// Hashes word to a number
unsigned int hash(const char *word)
{
    // For first three chars, find distance to 'A', times 10^i and return sum,
    // trivially handling apostrophe.
    // upper bound is (2600 + 260 + 26)
    int sum = 0;
    int c, x;
    for (int i = 0; i < 3; i++)
    {
        if (word[i] == '\0') break;
        if (word[i] == '\'')
        {
            sum += 1;
        }
        else
        {
            c = toupper(word[i]) - 64;
            x = pow(10, i);
            sum += (c * x);
        }
    }
    return sum;
}

// Loads dictionary into memory, returning true if successful, else false
bool load(const char *dictionary)
{
    // Open file
    FILE *fp = fopen(dictionary, "r");
    if (fp != NULL)
    {
        // Read lines
        char word[LENGTH + 1];
        while (fscanf(fp, "%s", word) != EOF)
        {
            // Create node
            node *n = malloc(sizeof(node));
            if (n == NULL)
            {
                free(n);
                return false;
            }
            strcpy(n->word, word);

            // Hash word and insert
            unsigned int i = hash(word);
            if (table[i] == NULL)
            {
                table[i] = n;
                n->next = NULL;
            }
            else
            {
                n->next = table[i];
                table[i] = n;
            }
            lines++;
        }
        fclose(fp);
        return true;
    }
    return false;
}

// Returns number of words in dictionary if loaded, else 0 if not yet loaded
unsigned int size(void)
{
    return lines;
}

// Unloads dictionary from memory, returning true if successful, else false
bool unload(void)
{
    // For row in table, free linked lists
    // TODO: check for failure state?
    for (int i = 0; i < N; i++)
    {
        if (table[i] != NULL)
        {
            free_list(table[i]);
            // free_many(table[i]);
        }
    }
    return true;
}

// Free recursively: unload() calls free_list() on table[i]
void free_list(node *n)
{
    if (n->next != NULL)
    {
        free_list(n->next);
    }

    free(n);
    return;
}

/* Alternate implementation */
// Free individual list nodes: unload() calls free_many() on table[i]
void free_many(node *cur)
{
    node *tmp = NULL;
    while (cur != NULL)
    {
        tmp = cur;
        cur = cur->next;
        free(tmp);
    }
    return;
}
