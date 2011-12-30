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


import random
from operator import itemgetter
from student import attribute_match
from group import valid_swap, swap
import utility
from group import Group

tries = 20



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
    return len(filter(attribute_match(attribute, values), students))

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
        
        all_values = set([s[attribute] for s in course.students])
        try: 
            all_values.remove(None)
        except KeyError:
            # ignore error if None is not present, we just want to make
            # sure it isn't
            pass         
            
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
            values = [values]
        self.values = values
        for i, value in enumerate(self.values):
            # TODO: make a proper regular expression to match (a, b, ...)
            if isinstance(value, basestring) and (value[0] == '(' and
                                                  value[-1] == ')'):
                self.values[i] = tuple((v.strip() for v in
                                        value[1:-1].split(',')))

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
        return self.check(new)

    def __str__(self):
        return "<{0} {1} {2}>".format(self.name, self.attribute, self.values)

class Cluster(Rule):
    """
    """
    name = 'Cluster'
    def _init(self, attribute, course, values = 'all', weight = None, **kwargs):
        pass

    def _check(self, students):
        return number(students, self.attribute, self.values) != 1

    def _fix(self, student, groups, students):
        if student[self.attribute] in self.values:
            # we have found the lone student, put them somewhere they will be happy
            def target_group(g):
                n = number(g, self.attribute, self.values)
                return n > 0 and n < len(g.students)
            def target_student(s):
                return s[self.attribute] not in self.values
        else:
            # we are not at the lone student, look to swap this for a
            # student with attribute==values
            def target_group(g):
                n = number(g, self.attribute, self.values)
                return n == 1 or n > 2
            def target_student(s):
                return s[self.attribute] in self.values

        targets = filter(target_group, groups)
        if len(targets) == 0:
            return False
        return find_target_and_swap(student, targets, target_student)
    
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
    specific attribute.  
    """
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
        
class Distribute(NumberBased):
    name = 'Distribute'

    def _target_numbers(self, value):
        n = self.numbers[value]
        if n % self.n_groups == 0:
            return [n/self.n_groups]
        else:
            low = n // self.n_groups
            return (low, low+1)

class Counter(dict):
    def __init__(self, in_list, key = lambda x: x):
        for item in in_list:
            self.tally(key(item))
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
    name = 'Aggregate'

    def valid_directions(self, n, attribute_val):
        halfway = self._target_numbers(attribute_val)[1]/2.0
        return n >= halfway, n <= halfway

    def _check(self, students):
        count = Counter(students, itemgetter(self.attribute))

        no_value = count.pop(None, 0)
        
        for key, number in count.iteritems():
            if (number in self._target_numbers(key) or
                # Check if the group fits accounting for phantoms and missing
                # data (which can effectively be counted as correct in this
                # case)
                number + no_value in self._target_numbers(key) or
                number + no_value > max(self._target_numbers(key))):
                pass
            else:
                if len(count.keys()) < 2:
                    import pdb; pdb.set_trace()
                return False
        return True

    def permissable_change(self, old, new):
        if self._check(new):
            return True
        if self._check(old): # Not allowed to break it if the group was already
                             # good
            return False
        # if the new group is not completely valid, check to see if it is doing
        # better than the current one
        if (Counter(old, itemgetter(self.attribute)).largest() <=
            Counter(new, itemgetter(self.attribute)).largest()):
            return True
        else:
            return False
    
    def _is(self, value):
        def match(s):
            return s[self.attribute] == value or s[self.attribute] == None
        return match
    def _is_not(self, value):
        return lambda s: s[self.attribute] != value
    
    def remedy(self, group, groups, students):
        if group.happy:
            return True
        
        count = Counter(group.students, itemgetter(self.attribute))

        # Remove None, students without a value for this attribute should be
        # sort of ignored
        if None in count:
            del count[None]

        # Try to fill the group with students having the value it has the most
        # of currently
        largest = count.largest()
        send_away = filter(self._is_not(largest), group.students)
        targets = filter(lambda g: self.can_spare(g, largest), groups)

        for student in send_away:
            find_target_and_swap(student, targets, self._is(largest))

        return group.happy
        

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
        if try_number < tries:
            return apply_rule(rule, groups, students, try_number+1)
        else:
            return False
    else:
        return True
        
        
                
def apply_rules_list(rules, groups, students):
    success = True
    for rule in rules:
        success = apply_rule(rule, groups, students) and success
        print("post: {0}: {1}".format(rule, [rules[1].check(g) for g in groups]))
    return success


class RuleNotImplemented(Exception):
    def __init__(self, r):
        self.rule = r
    def __str__(self):
        return "Sorry, we don't have a rule named: {0}\ndo you have a typo in \
your input deck?".format(self.rule)

class InvalidRuleSpecification(Exception):
    def __init__(self, spec):
        self.spec = spec
    def __str__(self):
        if _all_rules.has_key(self.spec['type']):
            return "{0} rule looks like it is specified in the old format, \
please update your input deck".format(self.spec['type'])
        return "Could not define rule with: {0}".format(self.spec)
    
_all_rules = {}
for rule in [Aggregate, Distribute, Cluster, Balance]:
    _all_rules[rule.name.lower()] = rule
    
def make_rule(input_spec, course):
    for key in input_spec.keys():
        if _all_rules.has_key(key):
            r = _all_rules[key]
            attribute = input_spec[key]
            kwargs = input_spec.copy()
            kwargs.pop(key)
            return r(attribute, course, **kwargs)
    raise InvalidRuleSpecification(input_spec)
            
