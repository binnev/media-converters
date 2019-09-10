"""TODO: replace ffmpy with subprocess call """

import glob, ffmpy, sys
from pathlib import Path 

def main(path):
	path = Path(path).resolve()
	print("path passed is:", path)
	search = (path/"*.mkv").as_posix()
	videos = glob.glob(search)
	if videos:
		print("I've found the following videos:", videos)
	else:
		print(f"I've found no videos in directory {path}")
	for video in videos:  # for each video 
		# create dictionaries for ffmpy
		output_name = video.replace(".mkv", ".mp4")         # get output name (mp4)
		inputs = {video: ""}                                # no options for input
		outputs = {output_name: "-vcodec copy -strict -2"}  # this is the important bit
		ff = ffmpy.FFmpeg(inputs=inputs, outputs=outputs)   # construct the command line
		print("The ffmpy command line is:", ff.cmd)
		ff.run()                                            # run the script

if __name__ == "__main__":
	path = sys.argv[1]
	main(path)  # run main function