import glob, sys, subprocess as sp
from pathlib import Path 

def main(path):
    path = Path(path).resolve()
    print("path passed is:", path)

    # if user passed a directory; search for files
    if path.is_dir():
        videos = []
        for extension in (".mkv", ".avi"):
            search = (path/f"*{extension}").as_posix()
            videos += glob.glob(search)
    elif path.is_file():
        videos = [path.as_posix()]
    else:
        print("That file doesn't exist.")
        return None
    
    if videos:
        print("I've found the following videos:", videos)
    else:
        print(f"I've found no videos in directory {path}")
        
    for video in videos:
        video_name = Path(video)
        output_name = video_name.parent / (video_name.stem + ".mp4")   
        # output_name = video.replace(".mkv", ".mp4")

        cmd = ["ffmpeg", "-i", video_name.as_posix(), "-vcodec", "copy", 
               "-strict", "-2", output_name]

        # run ffmpeg and handle exceptions
        try:
            output = sp.check_output(cmd)
        except sp.CalledProcessError as e:
            raise Exception("command {} encountered an "
                            "error code {}:\n{}".format(e.cmd, e.returncode, e.output))

if __name__ == "__main__":
    path = sys.argv[1]
    main(path)  # run main function
