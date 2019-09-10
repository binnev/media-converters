import getopt, sys

def main(argv):
    """ 
    Define what arguments you expect to get here.
    Short arguments are the ones prefixed by one dash e.g. 
    '-h'. Those that require a value e.g. '-i <inputfile>' 
    should be followed by a ':'. 

    Long arguments are the ones prefixed by two dashes e.g. 
    --long-option. Those that require a value e.g. '--codec copy'
    should be followed by '='.
    """
    shorts = "hi:o:"  
    longs = ["help", "ifile=", "ofile="]
    helptext = "Usage: 'test.py -i <inputfile> -o <outputfile>'"
    try: 
        opts, args = getopt.getopt(argv, shorts, longs)
    except getopt.GetoptError:
        print(helptext)
        sys.exit(2)  # what does this 2 mean?
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print("you want help")
            print(helptext)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    print('Input file is:', inputfile)
    print('Output file is:', outputfile)

if __name__ == "__main__":
    main(sys.argv[1:])  # sys.argv[0] is the script name