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

from .student import Student

def determine_group_size(number_of_students, group_size='3+', uneven_size=None,
                         number_of_groups=None):
    if number_of_groups is not None:
        if group_size is not None:
            print("Fixed number of groups specified, ignoring specified group size")
        n_groups = number_of_groups
        group_size = number_of_students // n_groups
        # TODO: Can this if ever fail?
        if group_size * n_groups < number_of_students:
            group_size += 1
            uneven_size = '-'
        else:
            uneven_size = '='

    else:
        try:
            group_size = int(group_size)
            if uneven_size.lower() == 'high':
                uneven_size = '+'
            elif uneven_size.lower() == 'low':
                uneven_size = '-'
            else:
                # no uneven_size specified, use default based on group size
                if group_size < 4:
                    uneven_size = '+'
                else:
                    uneven_size = '-'
        except ValueError:
            if group_size[-1] in '+-':
                uneven_size = group_size[-1]
                group_size = int(group_size[:-1])
            else:
                raise Exception("{0} cannot be interpreted as a group size".format(group_size))

        # We intentionally choose the number of groups before possibly changing
        # the group size to account for uneven size. In the case of uneven +, we
        # still want most of the groups to have the standard number of students,
        # setting the group size here will have the effect of having extra
        # groups and extra phanoms, and having only a few groups with an extra
        # student, instead of having n+ basically mimic (n+1)-.
        n_groups = number_of_students // group_size

        #TODO: check carefully that things are handled correctly in the case
        #where len(students) divides evenly into increased group size.g
        remainder = number_of_students % group_size
        if remainder:
            if uneven_size == '+':
                # add 1 to group size so most groups can have a phantom
                group_size += 1
        else:
            uneven_size = '='

        if (n_groups * group_size) < number_of_students:
            n_groups += 1

    return group_size, uneven_size, n_groups

class Course(object):
    def __init__(self, students, group_size, uneven_size, number_of_groups):
        self.students = students
        self.students_no_phantoms = list(students)

        self.group_size=group_size
        self.uneven_size=uneven_size
        self.n_groups = number_of_groups

        if self.uneven_size != '=':
            phantoms_needed = self.group_size * self.n_groups - len(self.students)
            def make_phantom():
                data = dict([(key, None) for key in self.students[0].data.keys()])
                identifier = self.students[0].identifier
                data[identifier] = 'phantom'
                return Student(data, identifier=identifier, headers =
                               self.students[0].headers)

            self.students += [make_phantom() for i in range(phantoms_needed)]

    def attr_values(self, attr):
        return remove_none(set(s[attr] for s in self.students))

def remove_none(s):
    try:
        s.remove(None)
    except KeyError:
        pass
    return s

class SubCourse(Course):
    def __init__(self, students, all_students, group_size='3+', uneven_size=None, number_of_groups=None):
        self.all_students = all_students
        super(SubCourse, self).__init__(students, group_size, uneven_size, number_of_groups)

    def attr_values(self, attr):
        return remove_none(set(s[attr] for s in self.all_students))
