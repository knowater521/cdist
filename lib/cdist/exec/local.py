# -*- coding: utf-8 -*-
#
# 2011 Steven Armstrong (steven-cdist at armstrong.cc)
# 2011 Nico Schottelius (nico-cdist at schottelius.org)
#
# This file is part of cdist.
#
# cdist is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cdist is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cdist. If not, see <http://www.gnu.org/licenses/>.
#
#

# FIXME: common base class with Remote?

import io
import os
import sys
import subprocess
import shutil
import logging

import cdist
from cdist import core


class LocalScriptError(cdist.Error):
    def __init__(self, script, command, script_content):
        self.script = script
        self.command = command
        self.script_content = script_content

    def __str__(self):
        return "Local script execution failed: %s %s" % (self.script, self.command)


class Local(object):
    """Execute commands locally.

    All interaction with the local side should be done through this class.
    Directly accessing the local side from python code is a bug.

    """
    def __init__(self, target_host, local_base_path, out_path):
        self.target_host = target_host
        self.base_path = local_base_path

        # Local input
        self.cache_path = os.path.join(self.base_path, "cache")
        self.conf_path = os.path.join(self.base_path, "conf")
        self.global_explorer_path = os.path.join(self.conf_path, "explorer")
        self.manifest_path = os.path.join(self.conf_path, "manifest")
        self.type_path = os.path.join(self.conf_path, "type")
        # FIXME: should not be needed anywhere
        self.lib_path = os.path.join(self.base_path, "lib")

        # Local output
        self.out_path = out_path
        self.bin_path = os.path.join(self.out_path, "bin")
        self.global_explorer_out_path = os.path.join(self.out_path, "explorer")
        self.object_path = os.path.join(self.out_path, "object")

        self.log = logging.getLogger(self.target_host)
    
    def create_directories(self):
        self.mkdir(self.out_path)
        self.mkdir(self.bin_path)

    def rmdir(self, path):
        """Remove directory on the local side."""
        self.log.debug("Local rmdir: %s", path)
        shutil.rmtree(path)

    def mkdir(self, path):
        """Create directory on the local side."""
        self.log.debug("Local mkdir: %s", path)
        os.makedirs(path, mode=0o700, exist_ok=True)

    def run(self, command, env=None):
        """Run the given command with the given environment.
        Return the output as a string.

        """
        assert isinstance(command, (list, tuple)), "list or tuple argument expected, got: %s" % command
        self.log.debug("Local run: %s", command)
        try:
            return subprocess.check_output(command, env=env).decode()
        except subprocess.CalledProcessError:
            raise cdist.Error("Command failed: " + " ".join(command))
        except OSError as error:
            raise cdist.Error(" ".join(*args) + ": " + error.args[1])

    def run_script(self, script, env=None):
        """Run the given script with the given environment.
        Return the output as a string.

        """
        command = ["/bin/sh", "-e"]
        command.append(script)

        self.log.debug("Local run script: %s", command)
        if env:
            self.log.debug("Local run script env: %s", env)
        
        try:
            return subprocess.check_output(command, env=env).decode()
        except subprocess.CalledProcessError as error:
            script_content = self.run(["cat", script])
            self.log.error("Code that raised the error:\n%s", script_content)
            raise LocalScriptError(script, command, script_content)
        except EnvironmentError as error:
            raise cdist.Error(" ".join(command) + ": " + error.args[1])

    def link_emulator(self, exec_path):
        """Link emulator to types"""
        src = os.path.abspath(exec_path)
        for cdist_type in core.Type.list_types(self.type_path):
            dst = os.path.join(self.bin_path, cdist_type.name)
            self.log.debug("Linking emulator: %s to %s", src, dst)

            # FIXME: handle exceptions
            os.symlink(src, dst)
