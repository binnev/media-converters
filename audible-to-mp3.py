"""
useful inspo: https://stackoverflow.com/questions/30305953/is-there-an-elegant-way-to-split-a-file-by-chapter-using-ffmpeg

TODO:
    [x] Take activation_bytes out of the script; add an input for that
    [ ] add to Github and write a readme.
    [x] if the script receives a directory instead of a file; glob for .aac files in that dir. 
    [x] add option to create destination folder for output files. 
    [x] make split by chapters true by default. 
    [x] let the script show help if -i flag not passed. 
    [ ] suppress ffmpeg output -- or make an option to show it? 
    [x] write a function for checking mandatory flags; or if a flag is passed
    [ ] merge the convert_chapters and convert functions. Add optional bit for chapters
"""

import subprocess as sp, json, sys, getopt, glob, os
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

def convert_chapters(file, extension, overwrite, verbose, activation_bytes,
    create_destination_folder):
    chapters = parse_chapters(file, verbose)  # get chapter data
    for ii, chapter in enumerate(chapters):
        if verbose: print(f"converting chapter {ii} of {len(chapters)}")

        if create_destination_folder:
            base_dir = chapter["out_file"].parent    # directory containing aac files
            destination_folder = base_dir/file.stem  # destination folder named after aac file
            chapter_name = chapter["out_file"].stem  # numbered chapter output filename
            # assemble the path to the output file; including the destination folder
            out_file = (destination_folder/chapter_name).as_posix()+extension 
            # create the folder if it doesn't already exist
            if not destination_folder.is_dir():
                os.mkdir(destination_folder.as_posix())
        else:
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

def convert(file, extension, overwrite, verbose, activation_bytes, create_destination_folder):
    if verbose: print("converting file", file)

    if create_destination_folder:
        destination_folder = file.parent/file.stem
        # assemble the path to the output file; including the destination folder
        out_file = destination_folder / (file.stem+extension) 
        # create the folder if it doesn't already exist
        if not destination_folder.is_dir():
            os.mkdir(destination_folder.as_posix())
    else:
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


def check_flag_passed(short, long, flags_passed):
    return (short in flags_passed) or (long in flags_passed)

def enforce_required_flag(short, long, description, flags_passed):
    if not check_flag_passed(short, long, flags_passed):
        print(f"The {description} ('{short}' or '{long}') is required!")
        sys.exit(2)

def main(argv):

    # define expected arguments
    shorts = "shi:a:e:vy"  # colon means parameter required after flag
    longs = ["split-chapters", "help", "input-file=", "activation-bytes=", 
             "extension=", "verbose", "create-destination-folder"]
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

        --create-destination-folder
            Create a folder (named after the input AAX file) and 
            put output files in there. 

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
    if check_flag_passed("-h", "--help", opts):
        print(helptext)
        sys.exit()  # don't do any other actions if help flag is passed. 

    # enforce required flags
    required = [("-i", "--input-file", "input file flag"),
                ("-a", "--activation-bytes", "activation-bytes flag")]
    for flag in required:
        enforce_required_flag(*flag, opts)

    # default values
    split_chapters = False
    extension = ".mp4"
    verbose = False
    overwrite = False
    create_destination_folder = False

    # parse flags
    for opt, arg in optargs:
        
        if opt in ("-i", "--input-file"):
            path = arg
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
        elif opt in ("--create-destination-folder"):
            create_destination_folder = True

    if verbose: print("opts:", opts)
    if verbose: print("args:", args)

    # check if path points to a file or directory.
    path = Path(path)
    if path.is_dir():  # if it is a directory, search for .aax files 
        files = glob.glob((path/"*.aax").as_posix())
    else:  # if it is a file, convert that file. 
        files = [path]

    # make sure there is exactly one dot in the extension
    extension = "."+extension.replace(".", "")  

    for file in files:
        file = Path(file)
        print(f"I'm going to try and deal with file {file}")
        if split_chapters:
            if verbose: print("Splitting chapters...")
            convert_chapters(file, extension, overwrite, verbose, 
                             activation_bytes, create_destination_folder)
        else:
            if verbose: print("Converting file...")
            convert(file, extension, overwrite, verbose, 
                    activation_bytes, create_destination_folder)


if __name__ == "__main__":
    main(sys.argv[1:])