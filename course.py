# Copyright 2011, Thomas G. Dimiduk
#
# This file is part of GroupEng.
#
# Holopy is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Holopy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with GroupEng.  If not, see <http://www.gnu.org/licenses/>.

class Course(object):
    def __init__(self, students, group_size='3+', uneven_size=None):
        self.students = students
        self.students_no_phantoms = list(students)

        # parse group size
        if isinstance(group_size, basestring) and group_size[-1] in '+-':
            self.uneven_size = group_size[-1]
            self.group_size = int(group_size[:-1])
        else:
            self.group_size = int(group_size)
            if uneven_size.lower() == 'high':
                self.uneven_size = '+'
            elif self.uneven_size.lower() == 'low':
                self.uneven_size = '-'
            else:
                # no uneven_size specified, use default based on group size
                if self.group_size < 4:
                    self.uneven_size = '+'
                else:
                    self.uneven_size = '-'

        self.n_groups = len(students) // self.group_size

        remainder = len(students) % self.group_size
        if remainder:
            if uneven_size == '+':
                # add 1 to group size so most groups can have a phantom
                self.group_size += 1
                
        if self.n_groups * self.group_size < len(students):
            self.n_groups += 1
