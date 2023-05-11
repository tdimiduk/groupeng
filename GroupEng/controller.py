# Copyright 2011, Thomas G. Dimiduk
#
# This file is part of GroupEng.
#
# GroupEng is free soft ware: you can redistribute it and/or modify
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

import time
import os
import csv
from operator import attrgetter
from .group import make_initial_groups
from .utility import mean, std
from .rule import make_rule, apply_rules_list, Balance, Distribute
from .student import load_classlist
from .course import Course, SubCourse, sizer_from_dek
from . import input_parser


import logging
log = logging.getLogger('log')

class InputDeckError(Exception):
    def __init__(self, e):
        self.e = e
    def __str__(self):
        return "You have a typo in your input deck.  Here is the error I got, \
see if it helps:\n{0}".format(self.e)

class UnevenGroups(Exception):
    pass

def run(input_deck):
    """
    Run GroupEng as specified by input_deck

    Parameters
    ----------
    input_deck: filename
        Input file specifying class information and grouping rules

    Output
    ------
    Output files determined by Input deck
    """
    cwd = os.getcwd()
    dek = input_parser.read_input(input_deck)
    log.debug('read input deck')
    try:
        students = load_classlist(dek['classlist'], dek.get('student_identifier'))
    except FileNotFoundError:
        # relative file structure
        head, tail = os.path.split(input_deck)
        os.chdir(head)
        students = load_classlist(dek['classlist'], dek.get('student_identifier'))
    log.debug('read class list')
    identifier = students[0].identifier
    dek_rules = dek['rules']
    tries = 5
    if 'tries' in dek:
        tries = dek['tries']
    log.debug('Allowing {} tries to get rules to work'.format(tries))

    log.debug("Using Rules: "+str(dek_rules))

    # This adds support for a "Hard" aggregate. If your first rule is
    # aggregate, we split the class on that attribute and treat each
    # value as a separate class. This ensures that we meet the rule
    # exactly (adding extra phantoms as necessary). This is useful for
    # things like needing all of the students in groups to be in the
    # same recitation section.

    sizer = sizer_from_dek(dek)
    log.debug(sizer)

    if len(dek_rules) > 0 and dek_rules[0]['name'] == 'aggregate':
        attribute = dek_rules[0]['attribute']
        # Turn back into a list to make sure ordering is preserved when we use
        # this in multiple places
        split_values = list(set(s[attribute] for s in students))
        subclasses = [[s for s in students if s[attribute] == value]
                      for value in split_values]
        subcourses = [SubCourse(sc, students, sizer) for sc in subclasses]

        dek_rules = dek_rules[1:]
        for s in subcourses:
            log.debug(sizer.describe(len(s.students_no_phantoms)))
    else:
        subcourses = [Course(students, sizer)]
        log.debug("Initialized Course")
        log.debug(sizer.describe(len(students)))

    run_name = os.path.splitext(input_deck)[0]
    # get rid of relative path
    run_name = os.path.split(run_name)[1]

    outdir = 'groups_{0}_{1}'.format(run_name,
                                     time.strftime('%Y-%m-%d_%H-%M-%S'))

    os.mkdir(outdir)
    log.debug('Made output directory')
    os.chdir(outdir)
    # return the full output directory.
    full_outdir = os.getcwd()

    def outfile(o):
        return open('{0}_{1}'.format(run_name,o),'w')

    group_number_offset = 0
    all_groups = []
    for course in subcourses:
        rules = [make_rule(r, course) for r in dek_rules]
        log.debug("Made rules")

        balance_rules = filter(lambda x: isinstance(x, Balance), rules)

        groups = make_initial_groups(course, balance_rules, group_number_offset)
        group_number_offset += course.n_groups
        log.debug("Made initial groups")
        def failures(r):
            return sum(1- r.check(g) for g in groups)



        # Add a rule to distribute phantoms to avoid having more than one phantom
        # per group, put it first so that it is highest priority
        # we have to add this after the phantoms are created by
        # group.make_initial_groups so that it can see the phantoms
        rules = [Distribute(identifier, course, 'phantom')] + rules

        suceeded = apply_rules_list(rules, groups, course.students, tries=tries)
        log.debug("applied rules")

        groups.sort(key = group_sort_key)


        if failures(rules[0]) !=  0:
            raise UnevenGroups()

        # now get rid of the phantoms so they don't affect the output
        for group in groups:
            group.students = [s for s in group.students if s.data[identifier] !=
                              'phantom']

        course.students = [s for s in course.students if s.data[identifier] != 'phantom']
        log.debug("removed phantoms")

        all_groups = all_groups + groups

    students = sorted(students, key=group_sort_key)

    ########################################################################
    # Output
    ########################################################################
    group_output(all_groups, outfile('groups.csv'), identifier)
    group_output(all_groups, outfile('groups.txt'), identifier, sep = '\n')
    statistics(rules, all_groups, students, balance_rules, input_deck, dek['classlist'], outfile('statistics.txt'))

    student_full_output(students, identifier, outfile('classlist.csv'))
    student_augmented_output(students, rules, outfile('details.csv'))
    log.debug("wrote output")

    # change back to current working directory
    os.chdir(cwd)

    return suceeded, full_outdir

def statistics(rules, groups, students, balance_rules, input_deck_name, classlist, outf):
    def failures(r):
        return sum(1- r.check(g) for g in groups)

    outf.write('Ran GroupEng on: {0} with students from {1}\n\n'.format(
            input_deck_name, classlist))

    outf.write('Made {0} groups\n\n'.format(len(groups)))

    for r in rules[1:]:
        n_fail = failures(r)
        if isinstance(r, Balance):
            group_means = sorted([mean(g, r.get_strength) for g in groups])
            attr = r.attribute
            outf.write('{0} groups failed:'.format(n_fail))
            outf.write('{0}: '.format(r))
            outf.write('Class {0} Mean: {1:3.2f}, '.format(
                    attr, mean(students, r.get_strength)))
            outf.write('Class {0} Std Dev: {1:3.2f}, '.format(
                        attr, std(students, r.get_strength)))
            outf.write('Std Dev of Group {0} Means: {1:3.2f}'.format(
                    attr, std(group_means)))
            outf.write('\n\n')
        else:
            outf.write('{0} groups failed: {1}\n\n'.format(n_fail, r))

    outf.write('Group Summaries\n')
    outf.write('---------------\n')

    for g in groups:
        outf.write('Group {0}: '.format(g.group_number))
        items = []
        for r in balance_rules:
            items.append('<{0} Mean: {1:3.2f}>'.format(
                    r.attribute, mean(g, r.get_strength)))
        for r in rules:
            if not r.check(g):
                items.append('Failed {0}'.format(r))
        outf.write(', '.join(items))
        outf.write('\n')

    outf.write('\n')

def group_sort_key(g):
    try:
        s, n = g.group_number.rsplit(None, 1)
        return s, int(n)
    except AttributeError:
        return g.group_number

def group_output(groups, outf, identifier, sep = ', '):
    for g in groups:
        students = sorted(g.students, key = lambda x: x[identifier])
        outf.write('Group {0}{1}{2}\n'.format(g.group_number, sep,
                                             sep.join([str(s[identifier]) for s in
                                                       students])))

def student_full_output(students, identifier, outf):
    writer = csv.writer(outf)
    writer.writerow((students[0].headers))
    for s in students:
        writer.writerow(s.full_record())


def student_augmented_output(students, rules, outf):
    add_headers = ['']
    balance_rules = [r for r in rules if r.name == 'Balance']
    add_headers += ["group {0} mean".format(r.attribute) for r in balance_rules]
    add_headers += ["Rules Broken"]
    headers = students[0].headers

    writer = csv.writer(outf)
    writer.writerow(headers+add_headers)

    group_number = students[0].group_number
    num_student_headers = len(students[0].headers)
    for i, s in enumerate(students):
        # write out a summary of the previous group if we have gone to the next
        # group
        if s.group_number != group_number:
            group = students[i-1].group
            summary = ['summary']
            summary += [''] * num_student_headers
            summary += [str(mean(group.students, r.get_strength)) for r in balance_rules]
            summary += ["{}: {}".format(r.name, r.attribute) for r in rules if
                        not r.check(group.students)]
            writer.writerow(summary)
            writer.writerow([])
            group_number = s.group_number

        writer.writerow(s.full_record())
