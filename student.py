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

import csv

rank = 'rank'
mtile = 'mitile'
group_number = 'Group Number'

def numberize(n):
    '''Turns a string into a number

    if the string is an integer return that integer
    if the string is a float return that float
    else return the string
    '''
    try:
        try:
            return int(n)
        except ValueError:
            try:
                return float(n)
            except ValueError:
                return n
    except TypeError:
        return n


class student(object):
    """
    """
    
    def __init__(self, data = {}, headers = [], key=None, strength=None):
        """
        
        Arguments:
        :param flags: 
        :type flags: 
        
        """
        self.key_flag = key
        self.strength_flag = strength
        self.data = data
        for key, val in self.data.items():
            if val in ['', '0']:
                self.data[key] = None
            else:
                self.data[key] = numberize(val)
            
        self.group = None
        self.headers = list(headers)
        if group_number not in self.headers:
            self.headers.append(group_number)

    def __getitem__(self, x):
        if x == group_number:
            return self.group.group_number
        return self.data.get(x)

    def __setitem__(self, x, val):
        self.data[x] = val

    @property
    def key(self):
        return self.data[self.key_flag]
        
    @property
    def strength(self):
        return self.data[self.strength_flag]
    
        
    def __str__(self):
        return "<Student : {0}>".format(self.data)

    def __repr__(self):
        return "student(data={0}, headers={1}, key={2}, strength={3})".format(
            self.data, self.headers, self.key, self.strength)
        
    def full_record(self):
        return ', '.join([str(self[h]) for h in self.headers])
    
def flag_match(flag, value):
    try:
        value.__iter__()
        return lambda x: x[flag] in value
    except AttributeError:
        return lambda x: x[flag] == value

    

def flag_differs(flag, value):
    return lambda x: x[flag] != value
    return [s for s in l if cond(s)]

def load(filename, key, strength_flag):
    inf = csv.reader(file(filename))

    # Strip excess spaces from the header names, since this can lead to tricky
    # bugs later
    headers = [h.strip() for h in inf.next()]
    # now make the students from the file
    students = []
    for s in inf:
        if set(s).issubset(set(['', ' ', None])):
            # skip blank lines
            pass
        else:
            d = {}
            for i, h  in enumerate(headers):
                d[h] = s[i]
            # make a copy of headers so student doesn't change it
            students.append(student(d, list(headers), key, strength_flag))
        
    return students

        

        
