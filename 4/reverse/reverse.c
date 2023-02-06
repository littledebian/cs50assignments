#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "wav.h"
#define HEAD 44

int check_format(WAVHEADER header);
int get_block_size(WAVHEADER header);

int main(int argc, char *argv[])
{
    // Ensure proper usage
    if (argc != 3)
    {
        printf("Usage: ./reverse input.wav output.wav\n");
        return 1;
    }
    char *infile = argv[1];
    char *outfile = argv[2];

    // Open input file for reading
    FILE *inptr = fopen(infile, "r");
    if (inptr == NULL)
    {
        fclose(inptr);
        printf("Could not find input file\n");
        return 1;
    }

    // Read header into an array - little endian except where noted
    BYTE   chunkID[4];  // big
    DWORD  chunkSize;
    BYTE   format[4];   // big
    BYTE   subchunk1ID[4];   // big
    DWORD  subchunk1Size;
    WORD   audioFormat;
    WORD   numChannels;
    DWORD  sampleRate;
    DWORD  byteRate;
    WORD   blockAlign;
    WORD   bitsPerSample;
    BYTE   subchunk2ID[4];   // big
    DWORD  subchunk2Size;

    WAVHEADER header;
    BYTE head[HEAD];

    fread(&header.chunkID, sizeof(BYTE), sizeof(chunkID), inptr);
    fread(&header.chunkSize, sizeof(DWORD), 1, inptr);
    fread(&header.format, sizeof(BYTE), sizeof(format), inptr);
    fread(&header.subchunk1ID, sizeof(BYTE), sizeof(subchunk1ID), inptr);
    fread(&header.subchunk1Size, sizeof(DWORD), 1, inptr);
    fread(&header.audioFormat, sizeof(WORD), 1, inptr);
    fread(&header.numChannels, sizeof(WORD), 1, inptr);
    fread(&header.sampleRate, sizeof(DWORD), 1, inptr);
    fread(&header.byteRate, sizeof(DWORD), 1, inptr);
    fread(&header.blockAlign, sizeof(WORD), 1, inptr);
    fread(&header.bitsPerSample, sizeof(WORD), 1, inptr);
    fread(&header.subchunk2ID, sizeof(BYTE), sizeof(subchunk2ID), inptr);
    fread(&header.subchunk2Size, sizeof(DWORD), 1, inptr);

    // Use check_format to ensure WAV format
    if (check_format(header) != 0)
    {
        printf("err bad format\n");
        return 1;
    }

    // Open output file for writing
    FILE *outptr = fopen(outfile, "w");
    if (outptr == NULL)
    {
        fclose(outptr);
        printf("err getting outfile\n");
        return 1;
    }

    // Write header to file
    rewind(inptr);
    fread(&head, sizeof(BYTE), sizeof(head), inptr);

    int ret = fwrite(&head, sizeof(BYTE), sizeof(head), outptr);
    if (ret != HEAD)
    {
        printf("write err - %i/%i header bytes written", ret, HEAD);
        return 1;
    }

    // Use get_block_size to calculate size of block
    int block = get_block_size(header);
    BYTE buffer[block];

    // Set infile cursor 1 block from the end
    fseek(inptr, -1*block*sizeof(BYTE), SEEK_END);

    // Write reversed audio to file
    while (ftell(inptr) >= HEAD)
    {
        // Read 1 into buffer, write 1 to outfile
        fread(&buffer, sizeof(BYTE), block, inptr);
        fwrite(&buffer, sizeof(BYTE), block, outptr);

        // Seek back 2 blocks
        fseek(inptr, -2*block*sizeof(BYTE), SEEK_CUR);
    }

    fclose(inptr);
    fclose(outptr);
    return 0;
}

int check_format(WAVHEADER header)
{
    // WAVE 0x57415645
    if (header.format[0] == 0x57 && header.format[1] == 0x41 && header.format[2] == 0x56 && header.format[3] == 0x45)
    {
        return 0;
    }
    return 1;
}

int get_block_size(WAVHEADER header)
{
    // Block size is num channels * bits/sample /8
    // For 2 channels and 16bits/smpl, we have (2 * 16/8) = 4 bytes/block
    // This is also given by the blockAlign head attribute
    return header.blockAlign;
}