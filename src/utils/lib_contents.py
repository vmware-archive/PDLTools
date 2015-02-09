'''
This file takes output of the kind produced by
pdlpack clean-install
(which it expects as stdin input)
reformats and creates from it the ".content" files that appear in the
DSTOOLS/src/ports/<platform>/modules/*
directories.
It requires the path to the DSTOOLS base directory as input.

When creating a new version of PDL Tools, this helper script can be used to
update these files.
If the files already exist, it will overwrite them, and will report on
stdout whether it detected incompatibilities on the interface level.
(Calling interfaces in the old version that are no longer supported in the
new version.) This is meant to help the developer update the ".compatibility"
files for each module. Note, however, that the script does not check for
incompatibilities that may result from implementation changes that do not
have an associated change of interface.


Usage:
python lib_contents.py <DSTOOLS path> [-v] < verbose_install_output.txt

Options:
-v -- Enable verbose output.
'''


import sys,os,re
import argparse

path=None
verbose=None

def print_usage():
  print '''
    This file takes output of the kind produced by
    pdlpack clean-install
    (which it expects as stdin input)
    reformats and creates from it the ".content" files that appear in the
    DSTOOLS/src/ports/<platform>/modules/*
    directories.
    It requires the path to the DSTOOLS base directory as input.
    
    When creating a new version of PDL Tools, this helper script can be used to
    update these files.
    If the files already exist, it will overwrite them, and will report on
    stdout whether it detected incompatibilities on the interface level.
    (Calling interfaces in the old version that are no longer supported in the
    new version.) This is meant to help the developer update the ".compatibility"
    files for each module. Note, however, that the script does not check for
    incompatibilities that may result from implementation changes that do not
    have an associated change of interface.
    
    Usage:
    python lib_contents.py <DSTOOLS path> [-v] < verbose_install_output.txt

    Options:
    -v -- Enable verbose output.
    '''
 
def notification(message,print_level=0):
  if print_level<=verbose:
    print "lib_contents.py:",message

def check_file(filename):
  notification("Checking file "+filename+".",1)
  if not os.path.exists(filename):
    notification("File "+filename+" does not exist. Creating.",1)
    notification("Checking for file create right.",1)
    try:
      f=file(filename,"w")
      f.close()
      notification("File created.",1)
    except:
      notification("Cannot create file "+filename+". Aborting.")
      raise
  elif not os.path.isfile(filename):
    notification(filename+" is not a regular file. Aborting.")
    raise Exception
  else:
    try:
      notification("Checking for file read rights.",1)
      f=file(filename,"r")
      f.close()
    except:
      notification("Cannot read file "+filename+". Aborting.")
      raise
    try:
      notification("Checking for file write rights.",1)
      f=file(filename,"a")
      f.close()
    except:
      notification("Cannot write into file "+filename+". Aborting.")
      raise
  notification("File "+filename+" appears good.",1)

def handle_input(lines,path):
  modules=set([x[0] for x in lines])
  new_modules=dict([(m,set()) for m in modules])
  for x in lines:
    new_modules[x[0]].add(x[1])
  base_path=path+"/src"
  if not os.path.isdir(base_path):
    notification("Path not found: "+base_path+". Aborting.")
    exit(2)
  for m in modules:
    mod_path=base_path+m
    if not os.path.isdir(mod_path):
      notification("Module path not found: "+mod_path+". Aborting.")
      exit(2)
  try:
    for m in modules:
      mod_name=m.rsplit('/',1)[-1]
      check_file(base_path+m+"/"+mod_name+".content")
  except:
    notification("Input validation failed. Aborting.")
    exit(2)
  try:
    curr_modules={}
    for m in modules:
      mod_name=m.rsplit('/',1)[-1]
      notification("Reading "+mod_name+" module content file.",1)
      curr_modules[m]=set(file(base_path+m+"/"+mod_name+".content").readlines())
  except:
    notification("Unexpected error reading module files. Aborting.")
    exit(2)
  for m in modules:
    mod_name=m.rsplit('/',1)[-1]
    diff=curr_modules[m].difference(new_modules[m])
    if len(diff)!=0:
      notification("Module "+mod_name+" not compatible.")
      notification("Retired interfaces:",1)
      for d in diff:
        notification("> "+d,1)
  try:
    for m in modules:
      mod_name=m.rsplit('/',1)[-1]
      notification("Updating "+mod_name+" content file.")
      f=file(base_path+m+"/"+mod_name+".content","w")
      for l in new_modules[m]:
        f.write(l)
      f.close()
  except Exception, e:
    notification("Error writing content files. Aborting. Content files may be corrupt")
    notification("Original error message: ")
    print e
    exit(2)


def main():
  global path, verbose

  parser = argparse.ArgumentParser(
                description='Update utility for PDL Tools ".content" files.',
                argument_default=False,
                formatter_class=argparse.RawTextHelpFormatter,
                usage="""
This file takes output of the kind produced by
pdlpack clean-install
(which it expects as stdin input)
reformats and creates from it the ".content" files that appear in the
DSTOOLS/src/ports/<platform>/modules/*
directories.
It requires the path to the DSTOOLS base directory as input.

When creating a new version of PDL Tools, this helper script can be used to
update these files.
If the files already exist, it will overwrite them, and will report on
stdout whether it detected incompatibilities on the interface level.
(Calling interfaces in the old version that are no longer supported in the
new version.) This is meant to help the developer update the ".compatibility"
files for each module. Note, however, that the script does not check for
incompatibilities that may result from implementation changes that do not
have an associated change of interface.


Usage:
python lib_contents.py <DSTOOLS path> [-v] < verbose_install_output.txt

Options:
-v -- Enable verbose output.
""",
                epilog="""Example:

  $ lib_contents ~/from_stash/dstools/ < verbose_install.out

  This will update all .content files in ~/from_stash/dstools/src/ports/greenplum/modules/*/ directories.
  Stdout will report on interface-level incompatibilities with existing versions.
""")

  parser.add_argument(
        'path', metavar='PATH', nargs=1,
        help = "Path to PDL Tools source directory."
    )

  parser.add_argument('-v', '--verbose', dest='verbose',
                        action="store_true", help="Verbose mode.")

  args = parser.parse_args()

  path=args.path[0]
  verbose=args.verbose

  prefix="pdlpack.py : INFO : MODULE("
  lines=[x[len(prefix):].split("): ",1) for x in sys.stdin.readlines()
           if len(x)>len(prefix) and x[:len(prefix)]==prefix]
  lines=[x for x in lines if len(x)==2]
  if len(lines)==0:
    notification("No valid input lines found. Exiting.")
    print_usage()
    exit(1)
  handle_input(lines,path)

if __name__ == '__main__':
  main()
