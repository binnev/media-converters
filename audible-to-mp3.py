"""
useful inspo: https://stackoverflow.com/questions/30305953/is-there-an-elegant-way-to-split-a-file-by-chapter-using-ffmpeg

TODO:
    [ ] Take activation_bytes out of the script; add an input for that
    [ ] add to Github and write a readme.
    [ ] if the script receives a directory instead of a file; glob for .aac files in that dir. 
    [ ] add option to create destination folder for output files. 
    [ ] make split by chapters true by default. 
    [ ] let the script show help if -i flag not passed. 
    [ ] suppress ffmpeg output and show progress somehow -- chapter x of xx
    [ ] write a function for checking mandatory flags
"""

import subprocess as sp, json, sys, getopt
from pathlib import Path

def parse_chapters(file, verbose):
    if verbose: print("Trying to get the chapters from file:", file)

    # use ffprobe on file, and output metadata in json format
    cmd = ["ffprobe", "-i", file.as_posix(), "-print_format", "json", "-show_chapters",
           "-loglevel", "error",]
    if verbose: print("using ffprobe command:", " ".join(cmd))

    try:
        output = sp.check_output(cmd)
    except sp.CalledProcessError as e:
        raise Exception("command {} encountered an "
                        "error code {}:\n{}".format(e.cmd, e.returncode, e.output))

    # prepare output for converting to json
    """ TODO: replace below with regex """
    for token in ("\\n", " ", "b\'", "\'"):  # remove newlines, whitespace, single quotes
        output = str(output).replace(token, "")

    output = json.loads(output)  # convert json to dict

    chapters = output.get("chapters")  # get chapters. Will return None if not present
    # if "chapters" isn't in the output but there was no error in the ffprobe cmd,
    # return None. Otherwise, continue processing the chapters
    if chapters is None:
        if verbose: print("I didn't find any chapters!")
        return None

    if verbose: print(f"I found {len(chapters)} chapters")
    for chapter in chapters:
        # convert start_time and end_time properties to float.
        """ TODO: fix this in the json load """
        for key in ("start_time", "end_time"):
            chapter[key] = float(chapter[key])

        # add path to original file
        chapter["orig_file"] = file

        # create output file path for this chapter
        out_file = file.parent / (file.stem+f"_part{chapter['id']}")
        chapter["out_file"] = out_file
    return chapters


def handle_file_overwrite(file, cmd, overwrite):
    file = Path(file)
    if not file.is_file():
        return None
    if overwrite is True:
        cmd.append("-y")
    else:
        if input(f"File {file} already exists. Overwrite? [y/N]") == "y":
            cmd.append("-y")
        else:
            raise Exception("File already exists and you didn't want to overwrite."
                            " Exiting.")

def convert_chapters(file, extension, overwrite, verbose, activation_bytes):
    chapters = parse_chapters(file, verbose)  # get chapter data
    for ii, chapter in enumerate(chapters):
        if verbose: print(f"converting chapter {ii} of {len(chapters)}")
        out_file = chapter["out_file"].as_posix()+extension
        cmd = ["ffmpeg",
               "-activation_bytes", activation_bytes,
               "-i", chapter["orig_file"].as_posix(),
               "-vn",
               "-acodec", "copy",
               "-ss", str(chapter["start_time"]),
               "-to", str(chapter["end_time"]),
               out_file,
               ]

        handle_file_overwrite(out_file, cmd, overwrite)

        if verbose: print("using ffmpeg command:", " ".join(cmd))
        try:
            output = sp.check_output(cmd)
        except sp.CalledProcessError as e:
            raise Exception("command {} encountered an "
                            "error code {}:\n{}".format(e.cmd, e.returncode, e.output))

def convert(file, extension, overwrite, verbose, activation_bytes):
    if verbose: print("converting file", file)
    out_file = file.parent / (file.stem+extension)  #  construct output file
    # build ffmpeg command
    cmd = ["ffmpeg",
           "-activation_bytes", activation_bytes,
           "-i", file.as_posix(),
           "-vn",
           "-acodec", "copy",
           out_file.as_posix()]

    handle_file_overwrite(out_file, cmd, overwrite)

    if verbose: print("using ffmpeg command:", " ".join(cmd))
    # run ffmpeg and handle exceptions
    try:
        output = sp.check_output(cmd)
    except sp.CalledProcessError as e:
        raise Exception("command {} encountered an "
                        "error code {}:\n{}".format(e.cmd, e.returncode, e.output))

def main(argv):

    # define expected arguments
    shorts = "shi:a:e:vy"  # colon means parameter required after flag
    longs = ["split-chapters", "help", "input-file=", "activation-bytes=", "extension=", "verbose"]
    helptext = """USAGE:
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

        -v, --verbose
            Print verbose information.

        -y
            Force overwrite output files.
            """
    try:
        optargs, _ = getopt.getopt(argv, shorts, longs)
        opts = tuple(opt for opt, arg in optargs)
        args = tuple(arg for opt, arg in optargs)
    except getopt.GetoptError:  # if the user passed unrecognised flags
        print(helptext)         # print the help text
        sys.exit(2)             # and exit with an error

    # if the user passed the help flag, show the help and exit 
    if opt in ('-h', "--help"):
        print(helptext)
        sys.exit()  # don't do any other actions if help flag is passed. 

    # make sure user passes input file flag
    if ("-i" not in opts) and ("--input-file" not in opts):
        print("The input file flag ('-i' or '--input-file') is required!")
        sys.exit(2)

    # make sure user passes activation bytes
    if ("-a" not in opts) and ("--activation-bytes" not in opts):
        print("The activation-bytes flag ('-a' or '--activation-bytes') is required!")
        sys.exit(2)

    # default values
    split_chapters = True
    extension = ".mp4"
    verbose = False
    overwrite = False

    # parse flags
    for opt, arg in optargs:
        
        if opt in ("-i", "--input-file"):
            file = arg
        elif opt in ("-e", "--extension"):
            extension = arg
        elif opt in ("-s", "--split-chapters"):
            split_chapters = True
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-y",):
            overwrite = True
        elif opt in ("-a", "--activation-bytes"):
            activation_bytes = arg

    if verbose: print("opts:", opts)
    if verbose: print("args:", args)

    # housekeeping
    file = Path(file)                           # convert to Path object
    extension = "."+extension.replace(".", "")  # make sure there is exactly one dot

    if split_chapters:
        if verbose: print("Splitting chapters...")
        convert_chapters(file, extension, overwrite, verbose, activation_bytes)
    else:
        if verbose: print("Converting file...")
        convert(file, extension, overwrite, verbose, activation_bytes)


if __name__ == "__main__":
    main(sys.argv[1:])