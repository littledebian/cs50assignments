import csv
import sys


def main():

    # Check for command-line usage
    if len(sys.argv) != 3:
        print("Usage: dna.py large 1")
        exit(1)
    else:
        db_file = "databases/" + sys.argv[1] + ".csv"
        seq_file = "sequences/" + sys.argv[2] + ".txt"

    # Read database file into a variable
    people = []
    with open(db_file, 'r') as db:
        reader = csv.reader(db)
        for row in reader:
            people.append(row)

    ## Try doing the same using DictReader ##

    # Type convert numbers, skip header row
    l = len(people)
    for row in range(1, l):
        list = people[row]
        for i in range(1, len(list)):
            val = int(list[i])
            people[row][i] = val

    # Read DNA sequence file into a variable
    with open(seq_file, 'r') as f:
        sequence = f.read()

    # Find longest match of each STR in DNA sequence
    # STRs given by header row in people, ex-name column
    profile = []
    for i in people[0][1:]:
        profile.append(longest_match(sequence, i))

    # Check database for matching profiles
    # Sequence profile must match person row, ex-name
    for row in range(1, l):
        if people[row][1:] == profile:
            print(people[row][0])
            return

    print("No match")
    return


def longest_match(sequence, subsequence):
    """Returns length of longest run of subsequence in sequence."""

    # Initialize variables
    longest_run = 0
    subsequence_length = len(subsequence)
    sequence_length = len(sequence)

    # Check each character in sequence for most consecutive runs of subsequence
    for i in range(sequence_length):

        # Initialize count of consecutive runs
        count = 0

        # Check for a subsequence match in a "substring" (a subset of characters) within sequence
        # If a match, move substring to next potential match in sequence
        # Continue moving substring and checking for matches until out of consecutive matches
        while True:

            # Adjust substring start and end
            start = i + count * subsequence_length
            end = start + subsequence_length

            # If there is a match in the substring
            if sequence[start:end] == subsequence:
                count += 1

            # If there is no match in the substring
            else:
                break

        # Update most consecutive matches found
        longest_run = max(longest_run, count)

    # After checking for runs at each character in seqeuence, return longest run found
    return longest_run

main()