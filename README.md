# README

This repository contains some simple command line tools for converting audio and video files. They all use [`ffmpeg`](https://ffmpeg.org), so you will need to install that and add it to your system Path variable. You will also need a working Python 3 installation. 

## audible-to-mp3

This program converts Audible `.aax` audiobook files into `.mp3` files, so that Audible users can listen to their audiobooks on their app of choice (many of which don't support `aax` files). 

You will need to obtain a 4-byte activation secret from your Audible account. [This is used by `ffmpeg` to decrypt the file](https://ffmpeg.org/ffmpeg-all.html#Audible-AAX). Searching Google for "audible activation_bytes" will yield some guides on how to do this. 

### Usage

`audible-to-mp3` is called from the command line with the following syntax: 

```
python audible-to-mp3.py <options and arguments>
```

The command line options are as follows: 

```
-h, --help
    Show this help text.

-i, --input-file=<file>
	Complete path to the file you want to convert.
	Required.

-a, --activation-bytes=<XXXXXXXX>
	Authentication key from your audible account. 
	This allows ffmpeg to decode the Audible file. 
	See https://ffmpeg.org/ffmpeg-all.html#Audible-AAX
	Required. 

-e, --extension=<ext>
	Extension / audio type to convert to. Default is mp4.

-s, --split-chapters
	Try to split the audio into chapters based on metadata
	obtained using ffprobe. Default is False.

-f, --create-destination-folder
	Create a folder (named after the input AAX file) and 
	put output files in there. 

-v, --verbose
	Print verbose information.

-y
	Force overwrite output files.
```

#### Examples

The simplest possible usage is as follows. This will generate one `mp4` file for the whole book. 

```
python audible-to-mp3.py -a XXXXXXXX -i some/directory/audiobook_file.aax
```

To split by chapter and put the outputs in a folder, do the following. The program will try to read the chapter start/end times from the `aac` file's metadata. It will create one `mp4` file for each chapter. 

```
python audible-to-mp3.py -a XXXXXXXX -i some/directory/audiobook_file.aax -s -f
```

To convert multiple `aax` files, put them in a folder and pass the path to that folder as the input file. The program will search the folder for `aax` files and process them all according to the options. The following command will create a folder for each book in `some/directory/`, and output the chapters as individual `mp4` files. 

```
python audible-to-mp3.py -a XXXXXXXX -i some/directory/ -s -f
```



## mkv-to-mp4

This program does what it says on the tin. It can handle `.avi` files as well. 

### Usage

```
python mkv-to-mp4.py path/to/file/or/folder
```

If the path points to a folder, the program will search for `mkv` and `avi` files in that folder, and convert them all to `mp4`.

