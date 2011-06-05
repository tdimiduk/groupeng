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

from student import flag_match, flag_differs
from group import valid_swap, swap
import random
import utility
from group import group

inner_tries = 10
outer_tries = 1000

def number(students, flag, value):
    # Handle input of a group instead of a list of students
    if isinstance(students, group):
        students = students.students
    return len(filter(flag_match(flag, value), students))

class Rule(object):
    """
    """
    
    def __init__(self):
        """
        """

    def flag_match(self, student, flag=None):
        if flag is not None:
            if student[self.flag] == flag:
                return 1
            else:
                return 0
        else:
            if student[self.flag] in self.values:
                return 1
            else:
                return 0
        
    def remedy(self, group, groups, students):
        # returns true if it managed to satisfy the rule without
        # breaking any others, returns false otherwise
        if group.happy:
            return True
        random.shuffle(group.students)
        for student in group.students:
            self._fix(student, groups, students)

        return group.happy


    def check(self, students):
        if isinstance(students, group):
            students = students.students
        return self._check(students)

    def permissable_change(self, old, new):
        # default to checking if the new group works, some subclasses
        # will instead look to see if we are making progress towards
        # meeting the rule
        return self.check(new)
class Cluster(Rule):
    """
    """
    
    def __init__(self, weight, flag, values):
        """
        
        Arguments:
        :param flag: 
        :type flag: 
        
        :param values: 
        :type values: 
        
        """
        self.name = 'Cluster'
        self.weight = weight
        self.flag = flag
        self.values = values
        
    def __str__(self):
        return "<Cluster : {0} {1}>".format(self.flag, self.values)
        
    def _check(self, students):
        return number(students, self.flag, self.values) != 1

    def _fix(self, student, groups, students):
        if student[self.flag] in self.values:
            # we have found the lone student, put them somewhere they will be happy
            def target_group(g):
                n = number(g, self.flag, self.values)
                return n > 0 and n < len(g.students)
            def target_student(s):
                return s[self.flag] not in self.values
        else:
            # we are not at the lone student, look to swap this for a
            # student with flag==values
            def target_group(g):
                n = number(g, self.flag, self.values)
                return n == 1 or n > 2
            def target_student(s):
                return s[self.flag] in self.values

        targets = filter(target_group, groups)
        if len(targets) == 0:
            print('warning failed to find swap targets')
            return False
#            raise NoTargetGroupsFound
        return try_groups(student, targets, target_student)
    
class Balance(Rule):
    def __init__(self, weight, flag, mean, std, tol = None):
        self.name = 'Balance'
        self.weight = weight
        self.flag = flag
        self.mean = mean
        if not tol:
            tol = 1
        self.tol = std*tol

    def get_strength(self, s):
        return s[self.flag]
    def __str__(self):
        return "<Balance {0} {1}>".format(self.mean, self.tol)
    def _check(self, students):
        return abs(utility.mean(students, self.get_strength) - self.mean) < self.tol
    def permissable_change(self, old, new):
        b = (abs(utility.mean(old, self.get_strength) - self.mean) >
             abs(utility.mean(new, self.get_strength) - self.mean))
        if self.check(new) and not b:
            # return 2 here so that caller can distinquish if they
            # care that we have "worsened" but are still within
            # tolerance
            return 2
        else:
            return b

    def _fix(self, student, groups, students):
        group = student.group
        if (student,utility.mean(group, self.get_strength) - self.mean) > 0:
            test = lambda x: utility.mean(x, self.get_strength) < self.mean
        else:
            test = lambda x: utility.mean(x, self.get_strength) > self.mean

        targets = filter(lambda g: test(g), groups)

        short_list = filter(lambda g: abs(utility.mean(g, self.get_strength)-self.mean) > self.tol, targets)

        try:
            if try_groups(student, short_list):
                return True
            elif try_groups(student, targets):
                return True
            elif try_groups(student, groups):
                return True
        except SwapButNotFix:
            return False

class UnevenGroups(Exception):
    def __str__(self):
        return "Students don't add to number of groups, I haven't added phantoms properly somewhere"

class NoTargets(Exception):
    def __init__(self, rule):
        self.rule = rule
    def __str__(self):
        return "Could not find target groups while searching rule: {0}".format(self.rule)

class NumberBased(Rule):
    def __init__(self, weight, flag, values, students, group_size, all_flags):
        self.weight = weight
        self.flag = flag
        self.group_size = group_size
        self.all_flags = all_flags
        try:
            values.__iter__()
        except AttributeError:
            values = [values]
        self.values = values
        self.numbers = dict([(value, number(students, self.flag, value)) for value in values])
        self.values = sorted(self.values, key=lambda x: self.numbers[x])
        self.n_groups = len(students) // group_size
        if self.n_groups * group_size != len(students):
            raise UnevenGroups

        
    def valid_directions(self, n, flag_val):
        up = False
        down = False
        for m in self._target_numbers(flag_val):
            if m > n:
                up = True
            elif m < n:
                down = True
        return up, down

    def can_spare(self, group, flag_val):
        return (number(group, self.flag, flag_val) - 1) in self._target_numbers(flag_val)

    def can_accept(self, group, flag_val):
        return (number(group, self.flag, flag_val) + 1) in self._target_numbers(flag_val)
        
    def _check(self, students):
        for value in self.values:
            if number(students, self.flag, value) not in self._target_numbers(value):
                return False
        return True

    def _fix(self, student, groups, students):
        my_value = student[self.flag]
        # check if my_value is the flag value we are controlling for
        if self.numbers.get(my_value):
            # how many like me are there in the group
            n = number(student.group, self.flag, my_value)
            if n in self._target_numbers(my_value):
                return True
            up, down = self.valid_directions(n, my_value)
            targets = []
            if up: # find groups we could steal a student from
                targets.extend(filter(lambda g: self.can_spare(g, my_value), groups))
            if down: # find groups we could give a student to
                targets.extend(filter(lambda g: self.can_accept(g, my_value), groups))
            if not targets:
                print('Warning failed to find swap targets')
                return False #raise NoTargets(self)
            return try_groups(student, targets)
        return True
        
class Distribute(NumberBased):
    def __str__(self):
        return "<Distribute : {0} {1}>".format(self.flag, self.values)

    def _target_numbers(self, value):
        n = self.numbers[value]
        if n % self.n_groups == 0:
            return [n/self.n_groups]
        else:
            low = n // self.n_groups
            return (low, low+1)

    @property
    def name(self):
        return 'Distribute'


class Aggregate(NumberBased):
    def __str__(self):
        return 'Aggregate {0}={1}'.format(self.flag, self.values)

    def _target_numbers(self, value):
        n = self.numbers[value]
        if n < self.group_size:
            return [0, n]
        elif n % self.group_size == 0:
            return [0, self.group_size]
        else:
            return [0, n % self.group_size, self.group_size]

    @property
    def name(self):
        return 'Aggregate'
        
class SwapButNotFix:
    def __init__(self, s1, s2):
        self.s1 = s1
        self.s2 = s2

def try_groups(student, targets, target_student=lambda s: True):
    random.shuffle(targets)
    for group in targets:
        random.shuffle(group.students)
        for other in group.students:
            if target_student(other) and valid_swap(student, other):
                swap(student, other)
                if not (student.group.happy and other.group.happy):
                    raise SwapButNotFix(student, other)
                return 

    return False

def apply_rule(rule, groups, students, try_number=0):
    random.shuffle(groups)
    for group in groups:
        group.add_rule(rule)
        if not group.happy:
            rule.remedy(group, groups, students)

    if not reduce(lambda x, y: x and y.happy, groups, True):
        if try_number < 20:
            return apply_rule(rule, groups, students, try_number+1)
        else:
            print('Failed to satisfy rule: {0}'.format(rule))
            return False
    else:
        return True
        
        
                
def apply_rules_list(rules, groups, students):
    success = True
    for rule in rules:
        success = apply_rule(rule, groups, students) and success
     
    return success
