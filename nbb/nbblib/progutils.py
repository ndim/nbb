########################################################################
# Utility functions
########################################################################


import os
import subprocess


def prog_stdout(call_list):
    """Run program and return stdout (similar to shell backticks)"""
    p = subprocess.Popen(call_list,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(input=None)
    return stdout.strip()


def prog_retstd(call_list):
    """Run program and return stdout (similar to shell backticks)"""
    p = subprocess.Popen(call_list,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(input=None)
    return (p.returncode, stdout.strip(), stderr.strip())


class ProgramRunError(Exception):
    """A program run returns a retcode != 0"""
    def __init__(self, call_list, retcode, cwd=None):
        self.call_list = call_list
        self.retcode = retcode
        if cwd:
            self.cwd = cwd
        else:
            self.cwd = os.getcwd()
    def __str__(self):
        return ("Error running program (%s, retcode=%d, cwd=%s)"
                % (repr(self.call_list),
                   self.retcode,
                   repr(self.cwd)))


def prog_run(call_list, context):
    """Run program showing its output. Raise exception if retcode != 0."""
    print "RUN:", call_list
    print "  in", os.getcwd()
    if context.dry_run:
        return None
    p = subprocess.Popen(call_list)
    stdout, stderr = p.communicate(input=None)
    if p.returncode != 0:
        raise ProgramRunError(call_list, p.returncode, os.getcwd())
    return p.returncode

