#
# linter.py
# Linter for SublimeLinter3, a code checking framework for Sublime Text 3
#
# Written by Jordan Hoff
# Copyright (c) 2017 Jordan Hoff
#
# License: MIT
#

"""This module exports the PhpCsFixer plugin class."""

import logging
import os
import re
import json

from SublimeLinter.lint import Linter, util


logger = logging.getLogger('SublimeLinter.plugin.php-cs-fixer')


def _find_configuration_file(file_name):
    if file_name is None:
        return None

    if not isinstance(file_name, str):
        return None

    if not len(file_name) > 0:
        return None

    checked = []
    check_dir = os.path.dirname(file_name)
    candidates = ['.php-cs-fixer.php', '.php-cs-fixer.dist.php', '.php_cs', '.php_cs.dist']
    while check_dir not in checked:
        for candidate in candidates:
            configuration_file = os.path.join(check_dir, candidate)
            if os.path.isfile(configuration_file):
                return configuration_file

        checked.append(check_dir)
        check_dir = os.path.dirname(check_dir)

    return None


class PhpCsFixer(Linter):
    """Provides an interface to php-cs-fixer."""

    defaults = {
        'selector': 'embedding.php, source.php  - text.blade'
    }
    regex = r'@@.+?-(?P<line>\d+)'
    multiline = True
    tempfile_suffix = 'php'
    error_stream = util.STREAM_STDOUT

    def split_match(self, match):
        """Extract and return values from match."""
        match, line, col, error, warning, message, near = super().split_match(match)
        if match.string:
            j = json.loads(match.string)
            diff = re.split(r'@@.+?-(\d+).+?@@', j['files'][0]['diff'])[1:]
            errors = {}
            for k, x in enumerate(diff):
                if x.isnumeric():
                    errors[int(x)] = diff[k + 1]
            diff = '\n'.join(re.findall(r'^(?:\+|-).+', errors[line + 1].strip(), re.M))
            n = re.findall(r'^-(.+)', errors[line + 1].strip(), re.M)
            c = re.findall(r'^-(\s+)', errors[line + 1].strip(), re.M)
            if c:
                col = len(c[0])
            if n:
                near = n[0][:len(n[0]) - col] if col else n[0]
        message = '{0}\n{1}'.format(j['files'][0]['appliedFixers'], diff)
        line += 3

        return match, line, col, error, warning, message, near

    def cmd(self):
        """Read cmd from inline settings."""
        if 'cmd' in self.settings:
            logger.warning('The setting `cmd` has been deprecated. '
                           'Use `executable` instead.')
            command = [self.settings.get('cmd')]
        else:
            command = ['php-cs-fixer']

        config_file = _find_configuration_file(self.view.file_name())
        if not config_file:
            if 'config_file' in self.settings:
                config_file = self.settings.get('config_file')

        command.append('fix')
        command.append('${temp_file}')
        command.append('--dry-run')
        command.append('--show-progress=none')
        command.append('--stop-on-violation')
        command.append('--diff')
        command.append('--format=json')
        command.append('--using-cache=no')
        command.append('--no-ansi')
        command.append('-vv')
        if config_file:
            command.append('--config=' + config_file)

        return command
