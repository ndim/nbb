########################################################################
# Utility functions
########################################################################


import os
import subprocess


__all__ = ['prog_stdout', 'prog_retstd', 'ProgramRunError', 'prog_run']


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


def prog_run(call_list, context=None, env=None, env_update=None):
    """Run program showing its output. Raise exception if retcode != 0."""
    print "RUN:", call_list
    print "  in", os.getcwd()
    if context and context.dry_run:
        return None
    if not env:
        env = os.environ.copy()
    if env_update:
        env.update(env_update)
    p = subprocess.Popen(call_list, env=env)
    stdout, stderr = p.communicate(input=None)
    if p.returncode != 0:
        raise ProgramRunError(call_list, p.returncode, os.getcwd())
    return p.returncode

