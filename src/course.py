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

from __future__ import division
import math

from .student import Student

def sizer_from_dek(dek):
    return GroupSizer(dek.get('group_size'), dek.get('uneven_size'),
                      dek.get('number_of_groups'))



class GroupSizer:
    def __init__(self, group_size='3+', uneven_size=None, n_groups=None):
        self._n_groups = n_groups
        if self._n_groups:
            if group_size is not None:
                print("Fixed number of groups specified, ignoring specified group size")
            self._group_size = None
            self._uneven_size = None
        else:
            try:
                self._group_size = int(group_size)
                if uneven_size.lower() == 'high' or uneven_size == '+':
                    self._uneven_size = '+'
                elif uneven_size.lower() == 'low' or uneven_size == '-':
                    self._uneven_size = '-'
                else:
                    # no uneven_size specified, use default based on group size
                    if group_size < 4:
                        self._uneven_size = '+'
                    else:
                        self._uneven_size = '-'
            except ValueError: # group_size is not a bare int
                if group_size[-1] in '+-':
                    self._uneven_size = group_size[-1]
                    self._group_size = int(group_size[:-1])
                else:
                    raise Exception("{0} cannot be interpreted as a group size".format(group_size))

    def group_size(self, number_of_students):
        if self._n_groups:
            return math.ceil(number_of_students / self._n_groups)

        if (number_of_students % self._group_size) and (self._uneven_size == '+'):
            return self._group_size + 1

        return self._group_size

    def n_groups(self, number_of_students):
        if self._n_groups:
            return self._n_groups
        group_size = self.group_size(number_of_students)
        n = number_of_students // group_size
        if (n * group_size) < number_of_students:
            n += 1

        return n

    def describe(self, number_of_students):
        return "Using: {} groups of size {} for {} students, uneven_size: {}".format(
            self.n_groups(number_of_students),
            self.group_size(number_of_students),
            number_of_students,
            self._uneven_size)

    def __repr__(self):
        return "GroupSizer(group_size={}, uneven_size='{}', n_groups={})".format(
            self._group_size,
            self._uneven_size,
            self._n_groups)

class SplitSizer:
    def __init__(self, sizer, n_full_class):
        self.sizer = sizer
        self.n_full_class = n_full_class

    def n_groups(self, number_of_students):
        if self.sizer._n_groups:
            return math.round(self._n_groups * (number_of_students/self.n_full_class))
        else:
            return self.sizer.n_groups(number_of_students)

    def group_size(self, number_of_students):
        if self.sizer._n_groups:
            return math.ceil(number_of_students/self.n_groups(number_of_students))

        return self.sizer.group_size(number_of_students)

class Course(object):
    def __init__(self, students, sizer):
        self.students = students
        self.students_no_phantoms = list(students)

        n = len(students)
        self.group_size = sizer.group_size(n)
        self.n_groups = sizer.n_groups(n)

        phantoms_needed = self.group_size * self.n_groups - n
        def make_phantom():
            data = dict([(key, None) for key in self.students[0].data.keys()])
            identifier = self.students[0].identifier
            data[identifier] = 'phantom'
            return Student(data, identifier=identifier, headers =
                           self.students[0].headers)

        self.students += [make_phantom() for i in range(int(phantoms_needed))]

    def attr_values(self, attr):
        return remove_none(set(s[attr] for s in self.students))

def remove_none(s):
    try:
        s.remove(None)
    except KeyError:
        pass
    return s

class SubCourse(Course):
    def __init__(self, students, all_students, sizer):
        self.all_students = all_students
        super(SubCourse, self).__init__(students, SplitSizer(sizer, len(all_students)))

    def attr_values(self, attr):
        return remove_none(set(s[attr] for s in self.all_students))
