#!/usr/bin/env python
import os
import subprocess
import gc


def open_files(pid=None, close_unused=True):
    """
    Return a dict of open files for the given process.
    The key of the dict is the file descriptor (a number).
    
    If PID is not specified, the PID of the current program is used.
    Only regular open files are returned.
    
    If close_unused is True, do garbage collection prior to getting the list
    of open files. This makes open_files() more reliable, as files which are
    no longer reachable or used, but not yet closed by the resource manager.
    
    This function relies on the external `lsof` program.
    This function may raise an OSError.
    """
    if pid is None:
        pid = os.getpid()
    if close_unused:
        # garbage collection. Ensure that unreachable files are closed, making
        # the output of open_files() more reliable.
        gc.collect()
    # lsof lists open files, including sockets, etc.
    command = ['lsof', '-nlP', '-b', '-w', '-p', str(pid), '-F', 'ftn']
    # set LC_ALL=UTF-8, so non-ASCII files are properly reported.
    env = dict(os.environ).copy()
    env['LC_ALL'] = 'UTF-8'
    # Open a subprocess, wait till it is done, and get the STDOUT result
    output = subprocess.Popen(command, stdout=subprocess.PIPE, env=env).communicate()[0]
    # decode the output and split in lines.
    output = output.decode('utf-8').split('\n')
    files = {}
    state = {'f': '', 't': ''}
    for line in output:
        try:
            linetype, line = line[0], line[1:]
        except IndexError:
            continue
        state[linetype] = line
        if linetype == 'n':
            if state['t'] == 'REG' and state['f'].isdigit():
                files[int(state['f'])] = line
                state = {'f': '', 't': ''}
    return files

