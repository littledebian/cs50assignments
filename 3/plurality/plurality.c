#include <cs50.h>
#include <stdio.h>
#include <string.h>

// Max number of candidates
#define MAX 9

// Candidates have name and vote count
typedef struct
{
    string name;
    int votes;
}
candidate;

// Array of candidates
candidate candidates[MAX];

// Number of candidates
int candidate_count;

// Function prototypes
bool vote(string name);
void print_winner(void);

int main(int argc, string argv[])
{
    // Check for invalid usage
    if (argc < 2)
    {
        printf("Usage: plurality [candidate ...]\n");
        return 1;
    }

    // Populate array of candidates
    candidate_count = argc - 1;
    if (candidate_count > MAX)
    {
        printf("Maximum number of candidates is %i\n", MAX);
        return 2;
    }
    for (int i = 0; i < candidate_count; i++)
    {
        candidates[i].name = argv[i + 1];
        candidates[i].votes = 0;
    }

    int voter_count = get_int("Number of voters: ");

    // Loop over all voters
    for (int i = 0; i < voter_count; i++)
    {
        string name = get_string("Vote: ");

        // Check for invalid vote
        if (!vote(name))
        {
            printf("Invalid vote.\n");
        }
    }

    // Display winner of election
    print_winner();
}

// Update vote totals given a new vote
bool vote(string name)
{
    // Check name is in candidates
    for (int i = 0; i < candidate_count; i++)
    {
        if (strcmp(name, candidates[i].name) == 0)
        {
            candidates[i].votes += 1;
            return true;
        }
    }
    return false;
}

// Print the winner (or winners) of the election
void print_winner(void)
{
    int n = candidate_count;
    int sorted = 0; // first unsorted idx
    candidate swapped;
    int swap_idx;

    // While unsorted
    while (sorted < n-1)
    {
        candidate lo_name = candidates[sorted];
        int lo_count = candidates[sorted].votes;
        int c = 0;

        // For each element in unsorted part
        for (int i = sorted; i < n; i++)
        {
            // Locate smallest
            if (candidates[i].votes < lo_count)
            {
                lo_name = candidates[i];
                swapped = candidates[sorted];
                swap_idx = i;
                c++;
            }
        }

        // Execute swap
        if (c > 0)
        {
            candidates[sorted] = lo_name;
            candidates[swap_idx] = swapped;
        }

        // Increment current good i
        sorted++;
    }

    // Return winner(s)
    candidate winner = candidates[n-1];
    printf("%s\n", winner.name);

    for (int i = 0; i < n-1; i++)
    {
        if (candidates[i].votes == winner.votes)
        {
            printf("%s\n", candidates[i].name);
        }
    }
}