#!/usr/bin/python

import os
import pprint
import re
import subprocess
import sys

import repo_tools

GIT_REPO = "rsync://umd-repo.jf.intel.com/repos/FC6/package-meta-data.git"
BASE_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))

def main():
    ENV_VARS = { "BDSSERVER" : "http://jfipscn01.intel.com/", "BDSUSER" : "john.l.villalovos@intel.com", "BDSPASSWORD" : "dorkdork" }
    for name, value in ENV_VARS.iteritems():
        os.environ[name] = value

#    cloneRepo(GIT_REPO, os.path.join(BASE_DIR, "package-meta-data"))
    project_dict = listProjects()
    for name, value in sorted(project_dict.iteritems()):
        result = re.search(r'^mid-(?P<pkgid>.*)', value)
        if result:
            value = result.group('pkgid')
        else:
            continue
        print name, value
        
#    createProject("c_mid-busybox2")
#    login()

def cloneRepo(repo_url, destination_dir):
    os.system("git clone %s %s" % (repo_url, destination_dir))

def listProjects():
    """Return back a dictionary, keyed by project_id, of the projects"""
    result = bdstoolCommand("list-projects")
    output = {}
    for line in result:
        result = re.search(r'^(?P<id>c_\S*)\s*(?P<name>.*)$', line)
        if result:
            key = result.group('id')
            name = result.group('name')
            output[key] = name
    return output

def bdstoolCommand(cmd):
    base_command = "bdstool"
    cmd = "%s %s" % (base_command, cmd)
    proc = subprocess.Popen(cmd.split(), stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, close_fds = True)
    proc.stdin.close()
    output = []
    for line in proc.stdout:
        output.append(line.rstrip())
    if proc.wait() != 0:
        print >> sys.stderr, "ERROR: executing command: %s" % cmd
        for line in proc.stdout:
            print line.strip()
        sys.exit(1)
    return output

def createProject(project_name):
    #bdstoolCommand("new-project --unattached %s" % project_name)
    bdstoolCommand("new-project %s" % project_name)

def login():
    bdstoolCommand("login")

# if [ -e package-meta-data ]; then
#    echo "re-sync package-meta-data with umd-repo.jf.intel.com? [y/n]"
#    read yesorno
# else yesorno="Y"
# fi
# 
# if [ "$yesorno" == "Y" -o "$yesorno" == "y" ]; then
#    rm -rf package-meta-data
#    git clone http://umd-repo.jf.intel.com/git/FC6/package-meta-data.git ./package-meta-data
# fi
# echo "Enter your account on jfipsca01.intel.com:"
# read username
# echo "Enter your password for the account:"
# read password
# echo "Start to login JF ProtexIP server..."
# bdstool --server jfipscn01.intel.com --user $username  --password $password login
# echo "Getting current projects..."
# prjlist=`bdstool list-projects | sed -ne "/^c_.*/p"`
# echo "$prjlist"
# cd package-meta-data
# echo "$prjlist" |
# while read row; do
#     echo Processing $row
#     prjid=${row% *}
#     echo Project $prjid
# # remove leading space   
#     gitid=`echo -n ${row#* }`
#     gitid=${gitid#mid-}
#     echo Git "$gitid"
#     gitfolder=$(find ./ -name "$gitid.spec" | tail -n 1)
#     gitfolder=${gitfolder%/*/*}
#     gitfolder=${gitfolder#*/}
#     if [ -z "$gitfolder" ]; then
#        echo no git folder
#        continue;
#     fi
#     if [ ! -e $gitfolder/info/pristine_tip ]; then
#        echo no pristine_tip will skip
#        continue;
#     fi
#     echo Git folder is $gitfolder    
#     if [ -e ../scancodes/$gitfolder/blackduck.xml ]; then
#        echo already blackducked
#        continue;
#     fi
#     rm -rf ../scancodes/$gitfolder
#     mkdir -p ../scancodes/$gitfolder
#     pristine_index=`cat $gitfolder/info/pristine_tip`
#     echo pristine_index is $pristine_index
#     git diff $pristine_index HEAD $gitfolder > ../scancodes/$gitfolder/src.c
#     echo "removing leading +,++,+-"
#     sed -ne "s/^[+-]*\(*\)*/\1/p" -i ../scancodes/$gitfolder/src.c
#     cd ../scancodes/$gitfolder
#     pwd
#     echo bdstool start _________________________________________
#     bdstool new-project $prjid
#     bdstool analyze
#     bdstool upload
#     echo bdstool end __________________________________________
#     cd -
# done

if '__main__' == __name__:
    sys.exit(main())

"""
Run 'bdstool usage' to see command line syntax.
Run 'bdstool help introduction' for a quick start with some common commands.
Run 'bdstool help overview' for an overview of the Black Duck system.
Run 'bdstool show-help-topics' to see what help topics are available.
Run 'bdstool help <topic>' for help on a specific topic, or
run 'bdstool help all' for help on everything!

Some of the help output is rather long; you may want to pipe it
through a pager.

INTRODUCTION
============

This utility provides a command line interface to much of the Black
Duck functionality.  While it has many options and commands, you only
need to know a few basics to get started.  If you're unfamiliar with
the Black Duck system read the 'bdstool help overview' information
first.  The basic life-cycle of a Black Duck project goes something
like this:

1) Login to the local Black Duck server using a web browser and setup
   an account for yourself.  You'll need a user name (an email
   address) and a password.

2) Establish your default authentication settings:
      > bdstool --server http://your.server/ --user you@your.company \
                --password fubar login

3) Create a project on the local Black Duck server and remember the
   projectID you assign to it.  In the directory you want to make
   into a Black Duck project create the local blackduck.xml project
   description file:
      > cd your-workspace
      > bdstool new-project new-project-ID

4) Edit files and then analyze them with bdstool.  To analyze the
   current project directory use:
      > bdstool analyze

   Run 'bdstool help analyze' for information on combining subproject
   plp files.

5) View the analysis in a web browser:
      > bdstool view

Repeat steps 4 and 5 as necessary!  If you want to store your results
on the local Black Duck server where other users can see them
investigate the 'bdstool upload' command.


OVERVIEW
========

Some of the terms in the introduction may not make sense without a
little background:

Directory structure:
--------------------

Black Duck projects are stored in directories, and are recognized by
the presence of a 'blackduck.xml' file.  The simple name of the
directory is the project name; projects that are uploaded to local
black duck server are further given a unique project ID.  The project
description file contains the basic information about the project
itself, as well as a list of subproject names (for local subprojects)
or identifiers (for remote subprojects).

Black Duck projects should not be nested -- if you want include other
projects as subcomponents put them in their own distinct directory
trees.  Also in the top level of a Black Duck project directory there
is a 'plp' subdirectory, where project license files (intermediate
files containing project license analysis output) are stored.

PLP files:
----------

A plp file is created for nearly every file and directory under the
project.  The plp files for files and directories in the project are
merged together bottom-up, and finally plp files for subprojects are
mixed in to produce the top level or 'project' plp, stored in
'plp/.plp'.

Issues are reported when a plp file is generated, similar to the way
compilers report warnings when files are compiled and applications are
linked.  To see a full list of issues use the 'view' command (run
'bdstool help view' for details), or 'upload' the plp file to the
local Black Duck server and view it there.

The Black Duck server:
----------------------

Somewhere within your organization is a local web server that acts as
central repository for your Black Duck data.  To use the server you
must know its URL and have registered a username (typically your full
email address) and a password.  Note that Black Duck passwords have no
relation to any other passwords, and it's probably a good idea _not_
to reuse your login password.

You can connect to the server using a standard web browser to perform
administrative tasks, view uploaded projects and plp files, and do
other things.  Different users have different roles and capabilities;
your Black Duck administrator can help assign you the right ones for
what you need to accomplish.

Command line options:
---------------------

Values for command line options can come from a number of places.  In
decreasing order of precedence they are:

1) The command line itself.  Any options you specify explicitly
   override all other settings.

2) Options specified by the tool invocation wrapper.  These options
   are specific to bdstool.

3) Options saved via the 'save-options' command.

4) Option-specific environment variables, like: ${PROJECT}, ${BDSLOG},
   ${BDSSERVER}, ${BDSUSER}, and ${BDSPASSWORD}

5) Other option-specific fallbacks, such as the current working
   directory, passwords recorded by the 'login' command, and built-in
   fallback values.


DETAILED USAGE
==============

-- <command> [ args... ]    # execute external command with arguments
    Despite appearances this is a command, not a global option.
    This must be the last command on the command line, as all
    remaining arguments are passed to the wrapped command.

    Execute an arbitrary command after the tool finishes processing.
    The tool will attempt to exit with the subcommand's return status,
    and forward and input and output appropriately.  This may be
    useful if you wish to wrap an existing command in a Makefile,
    for example replacing 'ld' with 'bdstool analyze -- ld' by
    setting $(LD).

--dry-run                   # do not make any actual changes
    Default: unset
    Currently: unset
    Source: default value
    Setting may be retained in ~/.bdsrc; see 'save-options'

    A global option that, when set, prevents the tool from performing
    any actions that have permanent effect.  As much as possible is
    done without actually writing files or altering the database.
    See also '--live-run'.

--live-run                  # cancel --dry-run and allow changes
    Default: set
    Currently: set
    Source: default value
    Setting may be retained in ~/.bdsrc; see 'save-options'

    A global option that, when set, allows the tool to commit changes
    to files and the database.  See also '--dry-run'.

--password <password>       # specify password
    Default: BDSPASSWORD environment variable, or login data
    Currently: unset
    Source: default value

    A global option to specify the password used to authenticate the
    current user with the specified server.

--precision <precision>     # set default analysis precision
    Default: high
    Currently: high
    Source: forced value
    Setting may be retained in ~/.bdsrc; see 'save-options'

    NOTE: Support for alternate precisions has been deprecated.  All
    analysis is now done at 'high' precision regardless of settings.

--project <path>            # specify project directory
    Default: BDSPROJECT environment variable, or '.'
    Currently: /root/protexip
    Source: default value
    Setting may be retained in ~/.bdsrc; see 'save-options'

    A global option that specifies the project directory to be
    used.  The project directory contains a 'blackduck.xml' file
    at the top level with a project description, and a 'plp'
    subdirectory where project license files are stored.

--quiet                     # print less output; may be repeated
    Default: 0
    Currently: 0
    Setting may be retained in ~/.bdsrc; see 'save-options'

    Each time --quiet is specified the tool's verbosity level is
    decreased.  Negative verbosity levels attempt to report nothing.
    The default verbosity level reports errors and warnings.  Higher
    verbosity levels report debugging and trace information.
    See also '--verbose' and '--silent'.

--server <url>              # specify server URL
    Default: BDSSERVER environment variable, or login data, or none
    Currently: http:///
    Source: default login entry in ~/.bdspass
    Setting may be retained; see 'save-options'

    A global option that specifies the URL of the local Black Duck
    web server.  A full URL may be specified, or just the hostname.

--user <username>           # specify user name
    Default: BDSUSER environment variable, or login data, or none
    Currently: 
    Source: default value
    Setting may be retained; see 'save-options'

    Specifies the username (typically in 'user@host.domain' format)
    to be authenticated on the local Black Duck server.  You may
    create new users by visiting the server URL in a web browser.

--verbose                   # print more output; may be repeated
    Default: 0
    Currently: 0
    Setting may be retained in ~/.bdsrc; see 'save-options'

    Each time --verbose is specified the tool's verbosity level is
    increased.  Negative verbosity levels attempt to report nothing.
    The default verbosity level reports errors and warnings.  Higher
    verbosity levels report debugging and trace information.
    See also '--quiet' and '--silent'.

analyze [ option... ]       # compute PLPs; options are:
    --accept <regex>        # analyze matching files
    --all-files             # analyze all files, ignoring extensions
    --examine <regex>       # analyze matching files unless ignored
    --force                 # ignore timestamps and force recomputation
    --ignore <regex>        # ignore matching files
    --local                 # do not recurse into subdirectories
    --output <path>         # write an extra copy of the generated PLP
    --path <path>           # project/directory/file to process
    --relink                # ignore cached subdirectory PLPs

    Generate a project license (PLP) file for a path.  Any object
    may be passed in for analysis, although .plp files and selected
    other files are ignored.  If invoked on the top level of a
    project full project analysis is done; if invoked on a
    subdirectory or file on partial analysis is done.

    Analysis is normally recursive, including all descendants of the
    designated folder.  Using '--local' will prevent recursion into
    subdirectories, although plp files for the named directory will
    still be regenerated if necessary.

    A cached plp file is considered valid if the input file has not
    been modified since the plp was generated.  The final project
    level plp file also depends on the project's blackduck.xml file.
    If you wish to ignore timestamps and force complete reanalysis
    specify '--force'.  If you merely wish to force recomputation of
    folder plp files without rescanning unchanged source files specify
    '--relink' instead.  Normally neither switch is necessary.

    See also the '--precision' global option, which controls the
    granularity of code matching.

    Normally only files and directories with 'interesting' names are
    analyzed.  If '--all-files' is specified all files and directories
    will be considered, regardless of name.  This is similar to
    specifying '--accept .*' on the command line, except that further
    modifications to the matching patterns are ignored.

    Determining which names are interesting can be controlled in many
    ways.  A file named 'bdsfiles' in the project's 'plp' directory
    can contain a list of files to process, relative to the project
    directory.  Each path must be on a separate line.  If no such file
    exists then a combination of accept, examine, and ignore patterns is
    used.  Names matching '--accept' patterns are always interesting,
    regardless of other matches.  Names matching '--examine' patterns
    are potentially interesting, as are all directories.  They are
    processed unless they match an '--ignore' pattern.  Patterns are
    full case-sensitive java regular expressions, and match against
    the simple file or directory name, not its entire path.  Pattern
    lists are composed from (in order) built-in bootstrap values,
    project-specific values (e.g. 'plp/bdsignore' under the project
    directory), user-specific values (e.g. '.bdsignore' in your home
    directory), environment values (e.g. 'BDSIGNORE'), directory-
    specific values (e.g. '.bdsignore' in each directory processed),
    and finally command line switches.  (The file and variable names
    for 'accept' and 'examine' patterns are analagous to those given
    above for 'ignore' patterns.)  The special pattern '!' will clear
    all previous patterns.  Input is parsed as a whitespace-separated
    list of patterns, and lines beginning with '#' are ignored.

    The '--output' option will cause an extra copy of the final PLP
    file to be written to the designated location.  This can be useful
    for exporting copies of the PLP along with copies of binaries.

    You must authenticate yourself with the local Black Duck
    server to use this command; see the 'login' command.

codeprint [ option... ]     # create custom project codeprints; options are:
    --accept <regex>        # codeprint matching files
    --all-files             # codeprint all files, ignoring extensions
    --examine <regex>       # codeprint matching files unless ignored
    --force                 # ignore timestamps and force recomputation
    --ignore <regex>        # ignore matching files
    --local                 # do not recurse into subdirectories
    --no-files              # do not process any files
    --no-source-upload      # do not upload reference source files
    --path <path>           # project/directory/file to process
    --reset-all             # discard existing codeprints and reference source
    --reset-source          # discard existing reference source

    Upload reference source and codeprints for a path.  Any object
    may be passed in for analysis, although .plp files and selected
    other files are ignored.

    Analysis is normally recursive, including all descendants of the
    designated folder.  Using '--local' will prevent recursion into
    subdirectories.

    Existing codeprints are considered valid if the input file has not
    been modified since the codeprints were generated.  If you wish to
    ignore timestamps and force complete reanalysis specify '--force'.

    The '--reset-all' option causes all previously uploaded reference
    source files and codeprints for the project to be removed before
    codeprinting begins (causing re-analysis of all files), while
    '--reset-source' removes only the uploaded source files and does
    normal incremental analysis.  You must combine these options with
    '--no-files' to discard old information without uploading anything
    else.  For example to undo all earlier codeprinting (perhaps to
    flush deleted files) use '--reset-all --no-files'.

    By default a copy of each file codeprinted is uploaded to the
    server if and only if new codeprints are uploaded (perhaps because
    the file changed, '--force' was specified, or '--reset-all'
    discarded the old codeprints).  This reference source file is
    displayed by the code match comparison tool.  To prevent this
    source upload specify '--no-source-upload'.

    Normally only files and directories with 'interesting' names are
    codeprinted.  If '--all-files' is specified all files and
    directories will be considered, regardless of name.  This is like
    specifying '--accept .*' on the command line, except that all
    other name matching directives are ignored.

    The '--no-files' option causes all files and directories to be
    ignored, and is typically only used with the '--reset-all' or
    '--reset-source' options described above.  This is similar to
    giving the '--path' to an empty directory.  Use '--dry-run'
    instead to test commands.

    Determining which names are interesting can be controlled in many
    ways.  Names matching '--accept' patterns are always interesting,
    regardless of other matches.  Names matching '--examine' patterns
    are potentially interesting, as are all directories.  They are
    processed unless they match an '--ignore' pattern.  Patterns are
    full case-sensitive java regular expressions, and match against
    the simple file or directory name, not its entire path.  Pattern
    lists are composed from (in order) built-in bootstrap values,
    project-specific values (e.g. 'plp/bdsignore' under the project
    directory), user-specific values (e.g.  '.bdsignore' in your home
    directory), environment values (e.g. 'BDSIGNORE'), directory-
    specific values (e.g. '.bdsignore' in each directory processed),
    and finally command line switches.  (The file and variable names
    for 'accept' and 'examine' patterns are analagous to those given
    above for 'ignore' patterns.)  The special pattern '!' will clear
    all previous patterns.  Input is parsed as a whitespace-separated
    list of patterns, and lines beginning with '#' are ignored.

    You must authenticate yourself with the local Black Duck
    server to use this command; see the 'login' command.

default-login <number>      # set the default login entry
    Rearrange the stored password information to select a
    different default login entry.  Use the 'show-logins'
    command to see valid choices.

help <topic>                # show more detailed usage info
    Display help on a specific topic.  If an unrecognized
    topic is given help for the help command will be shown.
    See 'show-help-topics' for choices, or 'usage' for a
    shorter summary.  'help introduction', 'help overview',
    and 'help all' are also useful general topics.

list-projects [ --all | --assigned | --authorized | --standard ] # list projects
    If '--assigned' is specified (the default) list projects
    to which you are assigned.  If '--authorized' is specified
    show assigned projects that do not have a local blackduck.xml
    project description file (see the 'new-project' command).

    Specifying '--standard' will display a list of standard
    projects, and '--all' will list all visible projects.

    You must authenticate yourself with the local Black Duck server
    to use this command; see the 'login' command.

list-versions               # display version information
    Display current version information.

    Although you do not need to authenticate yourself with the
    local Black Duck server to use this command, you do need to
    identify it.  See the 'login' command for an explanation of
    how the current server URL may be specified.

login                       # login to the server and update ~/.bdspass
    Last login server: (none)
    Last login user: (none)
    Currently: not authenticated

    Attempt to authenticate the current user with the local black duck
    server (see the '--user', '--server', and '--password' options).
    If password-based authentication succeeds an entry will be added
    to the encrypted ~/.bdspass file so that you do not need to
    specify the password again.

    See also 'show-logins' and 'logout'.

logout [ <number> ]         # logout and remove entry from ~/.bdspass
    Remove a password entry from the encrypted ~/.bdspass file.
    If a number is supplied that entry is removed, otherwise
    information for the current username and server is deleted
    (see the '--user' and '--server' options).

    Note that removing entries renumbers the remainder; run
    'show-logins' before removing by position.

    See also 'show-logins' and 'login'.

new-project [ --attach | --unattached ] <projectID> # create blackduck.xml
    Create a new 'blackduck.xml' project description file for an
    existing project.  To create or modify a project visit the local
    Black Duck server in a web browser.  Use the 'list-projects'
    command to see what projects are available.

    Normally new projects are marked as having source code attached so
    that other users cannot create competing 'blackduck.xml' files
    with unrelated source code.  Specifying '--unattached' will
    override this behavior and suppress recording the existence of the
    new project description file.

reset-analysis [ option... ] # force full reanalysis; options are:
    --path <path>           # project/directory/file to process
    --reset-server          # reset server-side state too

    Expert-mode command

    Remove all locally cached analysis results for a project, forcing
    the next 'analyze' command to do full analysis.  The --path option
    merely identifies a location within the project directory.

    If --reset-server is specified an attempt will be made to clear
    cached state on the server.  You must authenticate yourself with the
    local Black Duck server to use this option; see the 'login' command.

save-options                # save global options in ~/.bdsrc
    Retain global option settings in ~/.bdsrc

    As a time-saving measure you may retain various global
    option settings in your ~/.bdsrc file by using this
    command.  Retained settings behave as if they had been
    specified at the start of each command line, and override
    any environment variables or fall-back values.

    See 'show-options' to display current retained settings.
    You may unset options either by specifying and saving
    a new value or by editing the ~/.bdsrc file directly.

show-help-topics            # show help topics
    Show available help topics.  See also 'help' and 'usage'.

show-logins                 # show login entries in ~/.bdspass
    Show the user/server pairs for which passwords are
    being kept in the encrypted ~/.bdspass file.  These
    passwords are automatically used when the tool needs
    to authenticate itself with the local black duck server.
    Login entries are numbered in the output, and the default
    login entry is marked with a '*'.  Use the 'default-login'
    command to rearrange the list to have a different default
    login entry.

    See also the 'login' command, which creates entries,
    the 'logout' command, which removes them, and the
    '--server', '--user', and '--password' options, which
    override the default or stored value.

show-options                # show global options
    Show global saved option settings.  The exact syntax
    display may not match the options themselves (for example
    '--quiet' and '--verbose' both modify a stored verbosity
    level, and are not stored directly).

    Global options are stored in ~/.bdsrc, which is read
    automatically when the tool starts.

    See also 'save-options' and the various global options.

show-project                # show current project settings
    Show the current project attributes and settings in
    the project's blackduck.xml file.  The local Black Duck
    web server will present a much nicer display of the
    information if the project has been uploaded.

update-project [ --attach ] # refresh project description file
    Replace an existing 'blackduck.xml' file with a fresh copy
    downloaded from the local Black Duck server, bringing the local
    project description file back into synch with the server.

    If the existence of the project description file wasn't recorded
    when it was created you can specify '--attach' to do so now.
    Attaching source files to a project prevents multiple users from
    doing unrelated analyses for the project, which would produce
    confusing results.

upload                      # upload project PLP to server
    Store the current project description and plp file
    on the local black duck server, where they may be used
    as remote subprojects or viewed by authorized users.

    Projects must have a unique ID and non-empty label
    before they can be uploaded.

    You must authenticate yourself with the local Black Duck
    server to use this command; see the 'login' command.

usage                       # show a brief command summary
    Display a brief usage summary, giving the main tool
    command and option syntax.

view [ --raw ] [ <plp-path> ] # view PLP in a web browser
    Display a plp file, or the current project's PLP if no
    explicit file is specified, in a web browser.  Unlike the
    'upload' command these plp files are not stored permanently,
    and the associated project need not have an ID or label.

    Normally the PLP is processed with the project's resolved
    issue list and other information.  Setting '--raw' will
    cause the unmodified PLP to be displayed instead.

    On Linux and UNIX systems an attempt will be made to open
    a new window in a running web browser.  If that fails a
    variety of fallback values are attempted.  To customize
    this set your BROWSER environment variable.  On Windows
    systems the default web browser is launched.

    You must authenticate yourself with the local Black Duck
    server to use this command; see the 'login' command.
"""

if '__main__' == __name__:
    sys.exit(main())
