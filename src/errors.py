# Copyright 2011-2015, Thomas G. Dimiduk
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

class InputError(Exception):
    def __init__(self, line, lineno, inf):
        self.line
        self.lineno
        self.inf
    def __str__(self):
        return "Can't understand: {0} at line {1} of {2}".format(
            self.line, self.lineno, self.inf)
