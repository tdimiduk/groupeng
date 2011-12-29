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

"""
Student Groups.  Swapping students between groups, seting up initial random
groups.  

.. moduleauthor:: Thomas G. Dimiduk tgd8@cornell.edu
"""

import yaml
import student
from student import rank, mtile
import random
import utility
from operator import attrgetter

class group(object):
    """
    """
    
    def __init__(self, students, group_number):
        """
        
        Arguments:
        :param students: 
        :type students: 
        
        """
        self.students = students
        self.group_number = group_number
        self.number = group_number
        for student in students:
            student.group = self
        self.rules = []

    def __str__(self):
        return "<Group {0}: Students {1}>".format(self.group_number,
                                                    [str(s) for s in
        self.students])

    def __repr__(self):
        return "group(students={0}, group_number={1})".format(
            [repr(s) for s in self.students], self.group_number)

    def ranksum(self):
        return reduce(lambda x, y: x+y[rank], self.students, 0)

    # TODO: OPTIMIZATION: make this stored and update when swapping students
    @property
    def happy(self):
        for rule in self.rules:
            if not rule.check(self):
                return False
        return True

    @property
    def size(self):
        return len(self.students)
    
    def can_take(self, student):
        g = set(self.students)
        g.remove(student)
        return self.meets_rules(g)

    def add_rule(self, rule):
        if rule not in self.rules:
            self.rules.append(rule)

    def add(self, s):
        s.group = self
        return self.students.append(s)

    def remove(self, s):
        if s in self.students:
            s.group = None
            return self.students.remove(s)
        else: raise AttemptToRemoveStudentNotInGroup

def valid_swap(s1, s2):
    if s1 == s2:
        return False
    if s1.group == s2.group:
        return False
    l1 = set(s1.group.students)
    l2 = set(s2.group.students)
    l1.remove(s1)
    l1.add(s2)
    l2.remove(s2)
    l2.add(s1)
    def rules_permit(rules, old, new):
        for r in rules:
            if not r.permissable_change(old, new):
                return False
        return True
               
    return (rules_permit(s1.group.rules, s1.group.students, l1) and
            rules_permit(s2.group.rules, s2.group.students, l2))




def swap(s1, s2):
    if s1 is s2:
        raise AttemptToSwapStudentWithSelf
    group1 = s1.group
    group2 = s2.group
    group1.remove(s1)
    group2.remove(s2)
    group1.add(s2)
    group2.add(s1)


def group_setup(students, group_size, name_flag, uneven_size='low'):

    strength_flag = students[0].strength_flag
    
    # Need to find out who the weakest student is, but some students
    # may not have a gpa listed, in that case ignore them and keep
    # looking
    strength = attrgetter('strength')
    students.sort(key=strength)
    min_strength = strength(min(students, key=strength))

    # fill up to an integer multiple of group_size with phantom students
    # phantom students have None's as values for most fields, this
    # should mean they never get treated as meeting any flag
    # requirement
    keys = dict([(key, None) for key in students[0].data.keys()])
    # Treat phantoms as as weak as the weakest student (some students
    # may be worse than not having no one, but ...)
    keys[strength_flag] = min_strength
    def phantom():
        return student.student(keys, key=students[0].key_flag, strength=strength_flag)

    rem = len(students) % group_size
    if rem:
        if uneven_size.lower() == 'low':
            # Fail low (make smaller groups if it doesn't fit exactly)
            for i in range(group_size - rem):
                students.append(phantom())
        else: # fail high (make some groups with an extra person)
            # make as many groups as we we can fill
            n_groups = len(students) // group_size
            # now we make the code think groups are one bigger
            group_size += 1
            # make phantoms to fill the extra slots with phantoms
            for i in range(n_groups*group_size-len(students)):
                students.append(phantom())

    students.sort(key = strength)

    n_groups = len(students)/group_size

    # assign each student their class rank and what mtile of the class
    # they are in (quartile for qroups of 4
    for i in range(len(students)):
        students[i][rank] = i
        students[i]['mtile'] = i/n_groups

    
    # randomly assort students into groups
    mtiles = [students[n_groups*i:(n_groups*(i+1))] for i in range(group_size)]

    for mtile in mtiles:
        random.shuffle(mtile)

    groups = []
    i = 0
    while i < len(mtiles[0]):
        # grab one student from each mtile
        g = group([mtile[i] for mtile in mtiles], i+1)
        groups.append(g)
        i += 1

    return groups, students, group_size
    
    
