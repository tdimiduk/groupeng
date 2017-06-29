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
Grouping rules.  Definitions and functions for fixing groups.

.. moduleauthor:: Thomas G. Dimiduk tgd8@cornell.edu
"""


import random
import re
from collections import Counter
from operator import itemgetter
from .student import attribute_match
from .group import valid_swap, swap
from . import utility
from .group import Group
from .errors import EmptyMean

tries = 20
mixing = 20

def count_items(f):
    return sum(1 for _ in f)

def number(students, attribute, values):
    """
    Count the number of students with a give attribute values

    Parameters
    ----------
    students: list<student>, or Group
        List or Group of students to count
    attribute: string
        Student attribute to count
    values: string
        values the attribute should have

    Returns
    -------
    number: int
        Number of students with the given attribute falue
    """
    # Handle input of a Group instead of a list of students
    if isinstance(students, Group):
        students = students.students
    return count_items(filter(attribute_match(attribute, values), students))

class InvalidValues(Exception):
    def __init__(self, rule, attribute, bad_values = None):
        self.rule = rule
        self.attribute = attribute
        self.bad_values = bad_values
    def __str__(self):
        return "When creating rule: <{0} : {1}>, values: {2} do not exist in \
class".format(self.rule, self.attribute, list(self.bad_values))

class AttributeNotFound(Exception):
    def __init__(self, rule, attribute, all_attributes):
        self.rule = rule
        self.attribute = attribute
        self.all_attributes = all_attributes
    def __str__(self):
        return "When creating rule <{0} : {1}> attribute {1} not found in \
class, valid attributes are: {2}".format(self.rule, self.attribute,
                                         self.all_attributes)

class NoValidValues(InvalidValues):
    def __str__(self):
        return "When creating rule: <{0} : {1}>, no values were specified".format(
            self.rule, self.attribute)

class Rule(object):
    """
    Base class for all grouping rules
    """

    def __init__(self, attribute, course, values = 'all', weight = None, **kwargs):
        self.attribute = attribute

        if attribute not in course.students[0].headers:
            raise AttributeNotFound(self.name, attribute,
                                    course.students[0].headers)

        all_values = course.attr_values(attribute)

        try:
            if values.lower() == 'all':
                values = sorted(list(all_values))
        except AttributeError:
            # Attribute error probably means values[0] is not a string, that is
            # fine, just pretend we failed the if
            pass



        try:
            values.__iter__()
        except AttributeError:
            # make sure values is always a list
            values = [values]
        self.values = values
        for i, value in enumerate(self.values):
            # use presence of a capitalize function to identify a string an a
            # python 2/3 independent way
            # Match things like (a, b, ...)
            if (hasattr(value, 'capitalize')
                and re.match("[(].*(, +.*)+[)]", value)):
                self.values[i] = tuple((v.strip() for v in
                                        value[1:-1].split(',')))

        if not isinstance(self.values, (tuple, list)):
            self.values = [self.values]

        flatten = set()
        for value in self.values:
            if isinstance(value, tuple):
                flatten = flatten.union(value)
            else:
                flatten.add(value)


        if not flatten.issubset(all_values.union(set(['phantom']))):
            raise InvalidValues(self.name, attribute,
                                flatten.difference(all_values))


        if len(self.values) == 0:
            raise NoValidValues(self.name, attribute)

        self.all_values = all_values

        # TODO add capability to collapse similar attributes

        # weight ignored for now

        self._init(attribute, course, values = 'all', weight = None, **kwargs)

    def _init(self, attribute, course, values = 'all', weight = None, **kwargs):
        raise NotImplemented

    def attribute_match(self, student, attribute=None):
        if attribute is not None:
            if student[self.attribute] == attribute:
                return 1
            else:
                return 0
        else:
            if student[self.attribute] in self.values:
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
        if isinstance(students, Group):
            students = students.students
        return self._check(students)

    def permissable_change(self, old, new):
        # default to checking if the new Group works, some subclasses
        # will instead look to see if we are making progress towards
        # meeting the rule
        return self.check(new) or not self.check(old)

    def __str__(self):
        return "<{0} {1} {2}>".format(self.name, self.attribute, self.values)


class Cluster(Rule):
    name = 'Cluster'
    def _init(self, attribute, course, values = 'all', weight = None, **kwargs):
        pass

    def _check(self, students):
        ok = True
        for value in self.values:
            ok = ok and number(students, self.attribute, value) != 1
        return ok

    def _fix(self, student, groups, students):
        success = True
        for value in self.values:
            if student[self.attribute] in self.values:
                # we have found the lone student, put them somewhere they will be happy
                def target_group(g):
                    n = number(g, self.attribute, value)
                    return n > 0 and n < len(g.students)
                def target_student(s):
                    return s[self.attribute] and s[self.attribute] not in value
            else:
                # we are not at the lone student, look to swap this for a
                # student with attribute==values
                def target_group(g):
                    n = number(g, self.attribute, value)
                    return n == 1 or n > 2
                def target_student(s):
                    return s[self.attribute] and s[self.attribute] in value

            targets = filter(target_group, groups)
            if count_items(targets) == 0:
                return False
            success = (find_target_and_swap(student, targets, target_student)
                       and success)

        return success

class Balance(Rule):
    name = 'Balance'
    def _init(self, attribute, course, value = 'all', weight = None, tol = None,
                 **kwargs):
        self.mean = utility.mean(course.students, self.get_strength)
        std = utility.std(course.students, self.get_strength)

        if not tol:
            # default to tolerance of half a standard deviation
            tol = .5
        self.tol = std*tol


    def get_strength(self, s):
        return s[self.attribute]
    def __str__(self):
        return "<Balance : {0} : tol {1}>".format(self.mean, self.tol)
    def _check(self, students):
        try: 
            return abs(utility.mean(students, self.get_strength) - self.mean) < self.tol
        # If somehow you don't have a strength for any of the students,
        # consider the group to be failing the rule
        except EmptyMean:
            return False
    def permissable_change(self, old, new):
        try: 
            b = (abs(utility.mean(old, self.get_strength) - self.mean) >
                 abs(utility.mean(new, self.get_strength) - self.mean))
        except EmptyMean:
            # If somehow one of the groups has nobody with a strength,
            # allow swapping with that group
            return True
        if self.check(new) and not b:
            # return 2 here so that caller can distinquish if they
            # care that we have "worsened" but are still within
            # tolerance
            return 2
        else:
            return b

    def _fix(self, student, groups, students):
        group = student.group
        if utility.mean(group, self.get_strength) - self.mean > 0:
            def test(x):
                try:
                    return utility.mean(x, self.get_strength) < self.mean
                except EmptyMean:
                    return True
        else:
            def test(x):
                try:
                    return utility.mean(x, self.get_strength) > self.mean
                except EmptyMean:
                    return True

        targets = [g for g in groups if test(g)]

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
    specific attribute.
    """

    # note: this is _init not __init__, it is called at the end of __init__ in
    # to do subclass specific init stuff.
    def _init(self, attribute, course, values = 'all', weight = None,
                 **kwargs):
        self.group_size = course.group_size

        self.numbers = dict([(value, number(course.students, self.attribute,
                             value)) for value in self.values])
        self.values.sort(key=lambda x: self.numbers[x])
        self.n_groups = course.n_groups


    def valid_directions(self, n, attribute_val):
        up = False
        down = False
        for m in self._target_numbers(attribute_val):
            if m > n:
                up = True
            elif m < n:
                down = True
        return up, down

    # TODO: BUG: This should may fail in cases where it shouldn't
    # (aggregate and a group with 2 for example)
    def can_spare(self, group, attribute_val):
        return (number(group, self.attribute, attribute_val) - 1) in self._target_numbers(
            attribute_val)

    def can_accept(self, group, attribute_val):
        return (number(group, self.attribute, attribute_val) + 1) in self._target_numbers(
            attribute_val)

    def _check(self, students):
        for value in self.values:
            if number(students, self.attribute, value) not in self._target_numbers(
                value):
                return False
        return True

    def _fix(self, student, groups, students):
        my_value = student[self.attribute]
        # check if my_value is the attribute value we are controlling for
        if self.numbers.get(my_value):
            # how many like me are there in the Group
            n = number(student.group, self.attribute, my_value)
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
                return False #raise NoTargets(self)
            return find_target_and_swap(student, targets)
        return True

    def _target_numbers(self, value):
        raise NotImplemented()

    def count(self, l):
        if hasattr(l, 'students'):
            l = l.students
        return Counter(s[self.attribute] for s in l)

class Distribute(NumberBased):
    name = 'Distribute'
    def _target_numbers(self, value):
        n = self.numbers[value]
        if n % self.n_groups == 0:
            return [n/self.n_groups]
        else:
            low = n // self.n_groups
            return (low, low+1)


class Aggregate(NumberBased):
    name = 'Aggregate'
    def valid_directions(self, n, attribute_val):
        halfway = self._target_numbers(attribute_val)[1]/2.0
        return n >= halfway, n <= halfway

    def _check(self, students):
        count = self.count(students)

        no_value = count.pop(None, 0)

        return len(count.keys()) == 1

    def apply(self, groups, students):
        all_values = list(self.all_values)
        random.shuffle(all_values)
        for value in all_values:
            def count(group):
                return number(group, self.attribute, value)

            go = sum(count(g) for g in groups)
            while go:
                groups = sorted(groups, key=count, reverse=True)
                group = groups[0]
                groups = groups[1:]
                group.add_rule(self)
                for s in filter(self._is_not(value), group.students):
                    targets = [g for g in groups if count(group)]
                    find_target_and_swap(s, targets, self._is(value))
                go = sum(count(g) for g in groups)

    def _is(self, value):
        def match(s):
            return s[self.attribute] == value or s[self.attribute] == None
        return match
    def _is_not(self, value):
        return lambda s: s[self.attribute] != value

    def _target_numbers(self, value):
        target = self.numbers[value]
        if target < self.group_size:
            return [0, target]
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
    random.shuffle(list(targets))
    for group in targets:
        random.shuffle(group.students)
        for other in group.students:
            if target_student(other) and valid_swap(student, other):
                return other

    return False

def all_happy(groups):
    for group in groups:
        if not group.happy:
            return False
    return True

def apply_rule(rule, groups, students, try_number=0):
    if isinstance(rule, Aggregate):
        rule.apply(groups, students)
    else:
        random.shuffle(groups)
    for group in groups:
        # add rule checks and will not add the rule twice, so we can just do
        # this
        group.add_rule(rule)
        if not group.happy:
            rule.remedy(group, groups, students)

    if not all_happy(groups):
        if try_number < tries:
            # Do a few random swaps (not allowing new rule breaks),
            # just to mix things up a bit and increase the chances of
            # finding new solutions
            for i in range(mixing):
                find_target_and_swap(random.choice(students), groups)
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


class RuleNotImplemented(Exception):
    def __init__(self, r):
        self.rule = r
    def __str__(self):
        return "Sorry, we don't have a rule named: {0}\ndo you have a typo in \
your input deck?".format(self.rule)

_all_rules = {}
for rule in [Aggregate, Distribute, Cluster, Balance]:
    _all_rules[rule.name.lower()] = rule

def make_rule(input_spec, course):
    rule_name = input_spec['name'].lower()
    if rule_name not in _all_rules:
        raise RuleNotImplemented(rule_name)
    r = _all_rules[rule_name]


    attribute = input_spec['attribute']
    kwargs = input_spec.copy()
    kwargs.pop('attribute')
    kwargs.pop('name')

    return r(attribute, course, **kwargs)
