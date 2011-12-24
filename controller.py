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

import yaml
import group
import rule
import student
import utility


class RuleNotImplemented(Exception):
    def __init__(self, r):
        self.rule = r
    def __str__(self):
        return "Sorry, we don't have a rule named: {0}\ndo you have a typo in \
your input deck?".format(self.rule)

class InputDeckError(Exception):
    def __init__(self, e):
        self.e = e
    def __str__(self):
        return "You have a typo in your input deck.  Here is the error I got, \
see if it helps:\n{0}".format(self.e)
    
def run(input_deck):
    try:
        dek = yaml.load(file(input_deck))
        group_size = dek['group_size']
        primary_key = dek['identifier']
        strength_flag = dek['strength']
        students = student.load(dek['classlist'], primary_key, strength_flag)
        def get_strength(s):
            return s.strength
        
    except (TypeError, yaml.parser.ParserError) as e:
        raise InputDeckError(e)

    groups, students, group_size = group.group_setup(students, group_size,
                                                     primary_key,
                                                     dek.get('uneven_size'))

    mean = utility.mean(students, get_strength)
    std = utility.std(students, get_strength)

    rules = []
    rules.append(rule.Distribute(100, primary_key, None, students, group_size,
                                 None))
    for r in dek['rules']:
        flag = r.get('flag')
        if flag:
            flag_values = sorted(list(set([s[flag] for s in students])))
            values = r['value']
        weight = r.get('weight')
        if r.get('value'):
            try:
                values.__iter__()
            except AttributeError:
                values = [values]
            try:
                if values[0].lower() == 'all':
                    print(flag_values)
                    values = flag_values
                    try: 
                        values.remove(None)
                    except ValueError:
                        pass # ignore error if None is not present, we just want
                             # to make sure it isn't
            except AttributeError:
                # Attribute error probably means values[0] is not a string, that
                # is fine, if it isn't it can't be 'all' so just pretend the if
                # failed
                pass

            # TODO add capability to collapse similar flags

                
        if r['type'].lower() == 'cluster':
            rules.append(rule.Cluster(weight, flag, values))
        elif r['type'].lower() == 'distribute':
            rules.append(rule.Distribute(weight, flag, values, students,
                                         group_size, flag_values))
        elif r['type'].lower() == 'aggregate':
            rules.append(rule.Aggregate(weight, flag, values, students,
                                        group_size, flag_values))
        elif r['type'].lower() == 'balance':
            
            rules.append(rule.Balance(weight, strength_flag, mean, std,
                                      r.get('tol')))
        else:
            raise RuleNotImplemented(r['type'])


    
    suceeded = rule.apply_rules_list(rules, groups, students)
        
    groups = sorted(groups, key=lambda x: x.group_number)
    
    # now we are done with phantom students, remove them so they don't show up
    # in the output
    students = [s for s in students if s[primary_key] is not None]
        
    for o in dek['output']:
        def outfile(o):
            return file(o['outfile'],'w')
        if o['type'] == 'group_per_line':
            group_output(groups, outfile(o), primary_key)
        elif o['type'] == 'group_blocks':
            group_output(groups, outfile(o), primary_key, sep = '\n')
        elif o['type'] == 'full_report':
            student_full_output(students, primary_key, outfile(o))
        else:
            raise OutputTypeNotImplemented(o['type'])
        
    if dek.get('report_name'):
        report_name = dek.get('report_name')
    else:
        report_name = 'report.txt'
    report = file(report_name, 'w')
        
    report.write('Ran GroupEng on: {0}\n\n'.format(input_deck))
    
    report.write('Made {0} groups\n\n'.format(len(groups)))
    
    for r in rules:
        n_fail = reduce(lambda x, y: x+(1-r.check(y)), groups, 0)
        report.write('{0} groups failed rule : {1}\n\n'.format(n_fail, r))

    report.write('{0} Statistics\n------------------------\n'.format(
            strength_flag))
    report.write('Class Mean: {0:3.2f}\n'.format(utility.mean(students,
                                                              get_strength))) 
    report.write('Class Std Dev: {0:3.2f}\n'.format(utility.std(students,
                                                                get_strength))) 
    group_means = sorted([utility.mean(g, get_strength) for g in groups])
    report.write('Std Dev of Group Means: {0:3.2f}\n'.format(
            utility.std(group_means)))
    report.write('Group Means: {0}\n'.format(', '.join(['{0:3.2f}'.format(m) for
                                                        m in group_means]))) 
    
    report.write('Rule Failures By Group\n----------\n')
        
    for g in groups:
        report.write('Group {0}: '.format(g.group_number))
        for r in rules:
            if not r.check(g):
                report.write(str(r))
        report.write('\n')
                
    report.write('\n')
        
    return groups, True

def group_output(groups, outf, name, sep = ', '):
    groups.sort(key = lambda x: x.group_number)
    for g in groups:
        students = sorted(filter(lambda s: s.data.get(name), g.students), key =
                          lambda x: x[name]) 
        outf.write('Group {0}{1}{2}\n'.format(g.group_number, sep,
                                             sep.join([str(s[name]) for s in
                                                       students]))) 

def student_full_output(students, name, outf):
    students = filter(lambda x: x[name] != 'Empty', students)
    outf.write(', '.join(students[0].headers)+'\n')
    for s in students:
        outf.write(s.full_record()+'\n')

