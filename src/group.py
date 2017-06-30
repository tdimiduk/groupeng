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
Student Groups.  Swapping students between groups, seting up initial random
groups.

.. moduleauthor:: Thomas G. Dimiduk tgd8@cornell.edu
"""

from . import student
import random

class Group(object):
    """
    Group of students

    Stores a list of students and the rules that the grouping is supposed to
    obey.
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
        return "Group(students={0}, group_number={1})".format(
            [repr(s) for s in self.students], self.group_number)

    # TODO: OPTIMIZATION: make this stored and update when swapping students
    @property
    def happy(self):
        for rule in self.rules:
            if not rule.check(self):
                return False
        return True

    def satisfies_rule(self, rule):
        return rule.check(self)

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

class AttemptToRemoveStudentNotInGroup(Exception):
    pass

class AttemptToSwapStudentWithSelf(Exception):
    pass

class InternalError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return "An internal error occured: {0}".format(self.msg)


def swap(s1, s2):
    if s1 is s2:
        raise AttemptToSwapStudentWithSelf
    group1 = s1.group
    group2 = s2.group
    group1.remove(s1)
    group2.remove(s2)
    group1.add(s2)
    group2.add(s1)


def make_initial_groups(course, balance_rules, group_number_offset=0):

    def strengths(s):
        return [r.get_strength(s) for r in balance_rules]

    # Need to find out who the weakest student is, but some students
    # may not have a gpa listed, in that case ignore them and keep
    # looking
    min_strengths = strengths(min(course.students, key=strengths))

    # Treat phantoms as as weak as the weakest student (some students
    # may be worse than not having no one, but ...)
    identifier = course.students[0].identifier
    for student in course.students:
        if student[identifier] == 'phantom':
            for i, rule in enumerate(balance_rules):
                student.data[rule.attribute] = min_strengths[i]

    if len(course.students) != course.group_size * course.n_groups:
        raise InternalError("Students + Phantoms not divisible by groups")

    course.students.sort(key = strengths)

    # randomly assort students into groups
    mtiles = [course.students[course.n_groups*i:(course.n_groups*(i+1))]
              for i in range(course.group_size)]

    for mtile in mtiles:
        random.shuffle(mtile)

    groups = []
    i = 0
    while i < len(mtiles[0]):
        # grab one student from each mtile
        g = Group([mtile[i] for mtile in mtiles], i+1+group_number_offset)
        groups.append(g)
        i += 1

    return groups
