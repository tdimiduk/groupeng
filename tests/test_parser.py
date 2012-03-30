import sys
sys.path.append('../')
sys.path.append('../src')
from nose.tools import assert_equal

import time
import os
from operator import attrgetter
from group import make_initial_groups
from utility import mean, std
from rule import make_rule, apply_rules_list, Balance, Distribute
from student import load_classlist
from course import Course
import input_parser


import input_parser

input_deck = '../sample_group_specification.groupeng'

def test_parser():
    dek = input_parser.read_input(input_deck)

    gold = {'classlist': 'sample_class_1.csv',
            'group_size': '4+',
            'rules': [{'attribute': 'Gender', 'name': 'cluster', 'values': ['M']},
                      {'attribute': 'Ethnicity', 'name': 'cluster', 'values': [('B', 'H')]},
                      {'attribute': 'Project choice', 'name': 'aggregate'},
                      {'attribute': 'Major',
                       'name': 'distribute',
                       'values': ['Mech E', 'CS', 'Civ E', 'EE']},
                       {'attribute': 'Skill1', 'name': 'distribute', 'value': ['y']},
                       {'attribute': 'Skill2', 'name': 'distribute', 'value': ['y']},
                       {'attribute': 'Skill3', 'name': 'distribute', 'value': ['y']},
                       {'attribute': 'GPA', 'name': 'balance'}],
                       'student_identifier': 'ID'}

    assert_equal(dek, gold)

    
def test_course():
    dek = input_parser.read_input(input_deck)

    students = load_classlist(dek['classlist'], dek.get('student_identifier'))
    identifier = students[0].identifier
    course = Course(students, dek['group_size'], dek.get('uneven_size'))

    assert_equal(course.group_size, 5)

    assert_equal(course.uneven_size, '+')

    assert_equal(course.n_groups, 26)
