#!/usr/bin/python

# Copyright 2011, Thomas G. Dimiduk
#
# This file is part of GroupEng.
#
# GroupEng is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GroupEng is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with GroupEng.  If not, see <http://www.gnu.org/licenses/>.

"""
External GroupEng Application.  Handles user invocation and marshalls things for
use by the rest of GroupEng

.. moduleauthor:: Thomas G. Dimiduk tgd8@cornell.edu
"""

import sys
import os.path
import os
from src import controller
import logging

log = logging.getLogger('log')
log.setLevel(logging.DEBUG)
fh = logging.FileHandler('GroupEng.log')
fh.setLevel(logging.DEBUG)
log.addHandler(fh)

if len(sys.argv) > 1:
    log.debug('In command line version')
    try:
        debug = os.environ['DEBUG'].lower() == 'true'
    except KeyError:
        debug = False
    if debug:
        status, outdir = controller.run(sys.argv[1])
        if not status:
            print('Could not completely meet all rules')
    else:
        try:
            status, outdir = controller.run(sys.argv[1])
            if not status:
                print('Could not completely meet all rules')
        except Exception as e:
            print(e)
else:
    log.debug("In gui version")
    # import gui stuff only if we are going to use it
    try:
        from tkinter import *
    except ImportError:
        from Tkinter import *
    try:
        from tkinter.filedialog import askopenfilename
    except ImportError:
        from tkFileDialog import askopenfilename
    try:
        from tkinter.messagebox import showerror, showinfo
    except ImportError:
        from tkMessageBox import showerror, showinfo
    log.debug("inported gui")

    path = askopenfilename()
    log.debug("Got file path: "+path)
    d, f = os.path.split(path)
    os.chdir(d)
    log.debug("Changed directory to: "+d)
    try:
        status, outdir = controller.run(f)
        log.debug('ran groupeng, results are in: '+outdir)
    except Exception as e:
        showerror('GroupEng Error', '{0}'.format(e))

    if status:
        showinfo("GroupEng", "GroupEng Run Succesful\n Output in: {0}".format(outdir))
    else:
        showinfo("GroupEng", "GroupEng Ran Correctly but not all rules could be met\n"
                 "Output in: {0}".format(outdir))
