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

import math
import group

def mean(l, key = lambda x: x):
    if isinstance(l, group.Group):
        l = l.students
    l = [x for x in l if not hasattr(x,'key') or x.key is not None]
    return reduce(lambda x, y: x+key(y), l, 0.0)/len(l)

def std(l, key = lambda x: x):
    if isinstance(l, group.Group):
        l = l.students
    l = [x for x in l if not hasattr(x,'key') or x.key is not None]
    v = [key(x) for x in l]
    m = mean(v)
    total = 0
    for x in v:
        total += (x-m)**2

    return math.sqrt(total/len(v))

