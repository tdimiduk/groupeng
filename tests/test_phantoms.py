import sys
sys.path.append('../src')

import time
import os
from operator import attrgetter
from group import make_initial_groups
from utility import mean, std
from rule import make_rule, apply_rules_list, Balance, Distribute
from student import load_classlist
from course import Course
import input_parser

import numpy as np
from numpy import array
from numpy.testing import assert_equal

from src import controller



def test_phantoms():
    input_deck = 'test_group_size.groupeng'
    dek = input_parser.read_input(input_deck)
    
    students = load_classlist(dek['classlist'], dek.get('student_identifier'))
    identifier = students[0].identifier
    course = Course(students, dek['group_size'], dek.get('uneven_size'))

    rules = [make_rule(r, course) for r in dek['rules']]

    balance_rules = filter(lambda x: isinstance(x, Balance), rules)

    gpas = array(sorted(s['GPA'] for s in students))

    groups = make_initial_groups(course, balance_rules)

    gpas_after_phantoms = array(sorted(s['GPA'] for s in course.students))

    assert_equal(gpas.min(), gpas_after_phantoms.min())
    assert_equal(gpas.max(), gpas_after_phantoms.max())
    

    rules = [Distribute(identifier, course, 'phantom')] + rules

    suceeded = apply_rules_list(rules, groups, course.students)

    groups.sort(key = attrgetter('group_number'))

    gpas_after_grouping = array(sorted(s['GPA'] for s in course.students))

    assert_equal(gpas.min(), gpas_after_grouping.min())
    assert_equal(gpas.max(), gpas_after_grouping.max())

    def failures(r):
        return reduce(lambda x, y: x+(1-r.check(y)), groups, 0)

    if failures(rules[0]) !=  0:
        raise UnevenGroups()
