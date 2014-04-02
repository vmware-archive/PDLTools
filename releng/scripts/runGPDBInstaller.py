#!/usr/bin/env python

"""
This python script installs the greenplum-db installer to the specified dir.
"""

import os
import sys
import commands
from optparse import OptionParser
from time import sleep

#Import pexpect 
libPath = sys.path[0]
importPath = "%s/lib" % (libPath)
sys.path.append(importPath)
try:
    import pexpect
except:
    print "The pexpect module could not be imported."
    print "Exiting."
    sys.exit(1) 

## ----------------------------------------------------------------------
## ----------------------------------------------------------------------

def main():
    """
    Main. 
    Parses the command line and calls other functions.
    """
    usage = "usage: %prog [options] arg"

    parser = OptionParser()

    parser.add_option("-i", "--installer", dest="installer",
                      help="Installer bundled zipfile to run")
    parser.add_option("-b", "--installerbin", dest="installerBin",
                      help="Installer binary package to run")
    parser.add_option("-p", "--path", dest="installPath",
                      help="Path to install product to.")
    parser.add_option("-s", "--pause", dest="installPause", type="float", default=120,
                      help="Sleep duration after installation")

    (options, args) = parser.parse_args()

    if options.installer and options.installerBin:
        parser.error("options --installer and -installerBin are mutually exclusive")
        
    installer = options.installer
    installPath = options.installPath 
    installerBin = options.installerBin
    installPause = options.installPause

    if options.installer and ( os.path.isfile(installer) == False ):
        print "Error: Installer bundled zipfile %s does not exist." % (installer)
        sys.exit(1)

    if options.installerBin and ( os.path.isfile(installerBin) == False ):
        print "Error: Installer binary package %s does not exist." % (installerBin)
        sys.exit(1)

    if ( os.path.exists(installPath) == True ):
        print "Error: Install path %s already exists." % (installPath)
        print "       Either remove this directory or provide a different path."
        sys.exit(1)

    if options.installer:
        installerBin = installer.strip("zip") + "bin"
        extractZip(installer)

    install(installerBin, installPath, installPause)

    return True

## ----------------------------------------------------------------------
## ----------------------------------------------------------------------

def extractZip(installer):
    """
    If the installer is in .zip format, extract it and check for a similarly
    named .bin file, and a README_INSTALL file.
    """
    cmd = "unzip %s" % (installer)
    (exitstatus, outtext) = commands.getstatusoutput(cmd)
    if ( exitstatus != 0 ):
        print "Error unzipping %s" % (installer)
    else:
        print "Extraction of %s successful" % (installer)      

    return True

## ----------------------------------------------------------------------
## ----------------------------------------------------------------------

def install(installer, installPath, installPause):
    """
    Perform an installation of the provided installer to the provided path.
    Returns True on success, False if an error is found as the install is 
    performed.
    Requires input of the installer to run, and the install path to install to.

    Notes: Currently only the first few characters of the output from the 
           installer are matched. 
           
           The various sleep() calls are needed in order to catch the text
           from the installer.
    """

    #Run the installer with /bin/sh in case it is not executable
    installer = "/bin/sh %s" % (installer)
    installLog = "install-log.txt"
    fhLog = file(installLog, 'w')

    print ""
    print "Running Installer Package: %s" % (installer)
    print "Installing to: %s" % (installPath)
    print "Post installation pause: %s" % (installPause)
    print ""
    #Start the installer
    child = pexpect.spawn(installer)
    child.logfile = fhLog

    #License agreement
    #Check for the license acceptance string, or whitespace
    sleep(1)
    check = child.expect(['.*You must read and accept.*', ' '])
    if ( check == 0 ):
        print "License text is present."
    else:
        print "Error: No text in license agreement."
        sys.exit(1)

    #Escape out of the more session displaying the license
    sleep(1)
    child.sendline('q')

    #License agreement acceptance
    sleep(1)
    check = child.expect(['.*.', ' '])
    if ( check == 0 ):
        print "License agreement acceptance text is present." 
    else:
        print "Error: No text in license agreement."
        sys.exit(1)

    #Accept the installer license
    sleep(1)
    child.sendline('yes')

    #Installation path output
    sleep(1)
    child.expect('.*.')

    #Provide the install path, override the default install path
    sleep(1)
    child.sendline(installPath)
    child.expect('.*.')

    #Accept the install path we just provided
    sleep(1)
    child.sendline('yes')
    child.expect('.*.')

    #The path does not exist, have the installer create the install path
    sleep(1)
    child.sendline('yes')

    # Handle GPpkg upgrade optional prompt
    index = child.expect (['[Optional]', 'Extracting'])
    if index == 0:
        sleep(1)
        child.sendline('')
                            
    #This sleep may need to be modified depending on the speed of the host
    #being run on. 10 seconds works for all of the hosts currently tested. 
    #greenplum_path.sh will not be modified if pexpect finishes before
    #the installer finishes.
    #Had to up this to 120s for the sparc port...
    sleep(installPause)
    child.expect('.*.')

    #Installer is done, close child and log
    child.close()
    fhLog.close()
    print ""
    print "Install is done."
    print "Install log: %s" % (installLog)
    print "Installation located at: %s" % (installPath)

    return True

## ----------------------------------------------------------------------
## ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
