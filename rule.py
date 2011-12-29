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
Grouping rules.  Definitions and functions for fixing groups.  

.. moduleauthor:: Thomas G. Dimiduk tgd8@cornell.edu
"""

from student import flag_match, flag_differs
from group import valid_swap, swap
import random
import utility
from group import group

tries = 20



def number(students, flag, value):
    """
    Count the number of students with a give flag value

    Parameters
    ----------
    students: list<student>, or group
        List or group of students to count
    flag: string
        Student attribute to count
    value: string
        value the flag should have
        
    Returns
    -------
    number: int
        Number of students with the given flag falue
    """
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

    @property
    def name(self):
        return self.__class__.__name__
    
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
            return False
        return find_target_and_swap(student, targets, target_student)
    
class Balance(Rule):
    def __init__(self, weight, flag, mean, std, tol = None):
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

        short_list = filter(lambda g: abs(utility.mean(g,
                                                       self.get_strength) -
                                          self.mean) > self.tol, targets)  

        try:
            if find_target_and_swap(student, short_list):
                return True
            elif find_target_and_swap(student, targets):
                return True
            elif find_target_and_swap(student, groups):
                return True
        except SwapButNotFix:
            return False

class UnevenGroups(Exception):
    def __str__(self):
        return "Students don't add to number of groups, I haven't added \
phantoms properly somewhere"

class NoTargets(Exception):
    def __init__(self, rule):
        self.rule = rule
    def __str__(self):
        return "Could not find target groups while searching rule: {0}".format(
            self.rule)

class NumberBased(Rule):
    """
    Base class for rules that operate based on number of students with a
    specific flag.  
    """
    def __init__(self, weight, flag, flag_values, students, group_size, all_flags):
        self.weight = weight
        self.flag = flag
        self.group_size = group_size
        self.all_flags = all_flags
        try:
            flag_values.__iter__()
        except AttributeError:
            flag_values = [flag_values]
        self.flag_values = flag_values
        self.numbers = dict([(value, number(students, self.flag, value)) for
                             value in flag_values]) 
        self.flag_values = sorted(self.flag_values, key=lambda x: self.numbers[x])
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
        return (number(group, self.flag, flag_val) - 1) in self._target_numbers(
            flag_val)

    def can_accept(self, group, flag_val):
        return (number(group, self.flag, flag_val) + 1) in self._target_numbers(
            flag_val)
        
    def _check(self, students):
        for value in self.flag_values:
            if number(students, self.flag, value) not in self._target_numbers(
                value):
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
            # if we want less of the type this student is, look for groups to
            # send them to.  
            if down: # find groups we could give a student to
                targets.extend(filter(lambda g: self.can_accept(g, my_value),
                                      groups))
            # if we want more of this student, don't try to swap them, one of
            # the other iterations of rule.remedy will try to bring one in.  
            if not targets:
                import pdb; pdb.set_trace()
                return False #raise NoTargets(self)
            return find_target_and_swap(student, targets)
        return True

    def _target_numbers(self, value):
        raise NotImplemented()
        
class Distribute(NumberBased):
    def __str__(self):
        return "<Distribute : {0} {1}>".format(self.flag, self.flag_values)

    def _target_numbers(self, value):
        n = self.numbers[value]
        if n % self.n_groups == 0:
            return [n/self.n_groups]
        else:
            low = n // self.n_groups
            return (low, low+1)

class counter(dict):
    def tally(self, key):
        if self.get(key):
            self[key] += 1
        else:
            self[key] = 1

    def largest(self):
        """
        Returns the item with the largest count.

        Notes
        -----
        If multiple items have an equal count it will return one of them, which
        one is not defined
        """
        n = 0
        max_key = None
        for key, number in self.iteritems():
            if number > n:
                n = number
                max_key = key
        return max_key
        
class Aggregate(NumberBased):
    def __str__(self):
        return 'Aggregate {0}={1}'.format(self.flag, self.flag_values)

    def valid_directions(self, n, flag_val):
        halfway = self._target_numbers(flag_val)[1]/2.0
        return n >= halfway, n <= halfway

    def _check(self, students):
        count = counter()
        for student in students:
            count.tally(student[self.flag])

        phantoms = count.pop(None, 0)
        
        for key, number in count.iteritems():
            if (number in self._target_numbers(key) or
                  number + phantoms in self._target_numbers(key)):
                pass
            else:
                if len(count.keys()) < 2:
                    import pdb; pdb.set_trace()
                return False
        return True

    def _is(self, value):
        def match(s):
            return s[self.flag] == value or s[self.flag] == None
        return match
    def _is_not(self, value):
        return lambda s: s[self.flag] != value
    
    def remedy(self, group, groups, students):
        if group.happy:
            return True
        
        count = counter()
        for student in group.students:
            count.tally(student[self.flag])

        # Remove None, phantoms shouldn't affect aggregation
        if None in count:
            del count[None]

        # Try to fill the group with students having the value it has the most
        # of currently
        largest = count.largest()
        send_away = filter(self._is_not(largest), students)
        targets = filter(lambda g: self.can_spare(g, largest), groups)
        for student in send_away:
            find_target_and_swap(student, targets, self._is(largest))
        return group.happy
        

    def _target_numbers(self, value):
        target = self.numbers[value]
        if target < self.group_size:
            return [0, target]
#        elif n % self.group_size == 0:
#            return [0, self.group_size]
#        else:
#            return [0, n % self.group_size, self.group_size]
        else:
            return [0, self.group_size]

                          
        
class SwapButNotFix:
    def __init__(self, s1, s2):
        self.s1 = s1
        self.s2 = s2

def find_target_and_swap(student, targets, target_student=lambda s: True):
    target = find_swap_target(student, targets, target_student)
    if target:
        swap(student, target)
        return True
    else:
        return False

def find_swap_target(student, targets, target_student=lambda s: True):
    random.shuffle(targets)
    for group in targets:
        random.shuffle(group.students)
        for other in group.students:
            if target_student(other) and valid_swap(student, other):
                return other

    return False


def apply_rule(rule, groups, students, try_number=0):
    random.shuffle(groups)
    for group in groups:
        # add rule checks and will not add the rule twice, so we can just do
        # this
        group.add_rule(rule)
        if not group.happy:
            rule.remedy(group, groups, students)

    if not reduce(lambda x, y: x and y.happy, groups, True):
        if try_number < 20:
            return apply_rule(rule, groups, students, try_number+1)
        else:
            return False
    else:
        return True
        
        
                
def apply_rules_list(rules, groups, students):
    success = True
    for rule in rules:
        success = apply_rule(rule, groups, students) and success
     
    return success
