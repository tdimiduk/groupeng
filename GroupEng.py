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

if len(sys.argv) > 1:
    debug = False
    if debug:
        groups, status, outdir = controller.run(sys.argv[1])
        if not status:
            print('Could not completely meet all rules')
    else:
        try:
            groups, status, outdir = controller.run(sys.argv[1])
            if not status:
                print('Could not completely meet all rules')
        except Exception as e:
            print(e)
else:
    # import gui stuff only if we are going to use it
    from Tkinter import *
    from tkFileDialog import askopenfilename
    from tkMessageBox import showerror, showinfo

    path = askopenfilename()
    d, f = os.path.split(path)
    os.chdir(d)
    try:
        groups, status, outdir = controller.run(f)
    except Exception as e:
        showerror('GroupEng Error', '{0}'.format(e))

    if status:
        showinfo("GroupEng", "GroupEng Run Succesful\n Output in: {0}".format(outdir))
    else:
        showinfo("GroupEng", "GroupEng Ran Correctly but not all rules could be met\n"
                 "Output in: {0}".format(outdir))
