import re


def parse_scan_command(command):
    """
    Accepts a BLISS SXDM command and parses it according to the XSOCS
    file structure.
    """

    _COMMAND_LINE_PATTERN = ('^(?P<command>[^ ]*)\( '
                             '(?P<motor_0>[^ ]*), '
                             '(?P<motor_0_start>[^ ]*), '
                             '(?P<motor_0_end>[^ ]*), '
                             '(?P<motor_0_steps>[^ ]*), '
                             '(?P<motor_1>[^ ]*), '
                             '(?P<motor_1_start>[^ ]*), '
                             '(?P<motor_1_end>[^ ]*), '
                             '(?P<motor_1_steps>[^ ]*), '
                             '(?P<delay>[^ ]*)\s*'
                             '.*'   
                             '$')
    cmd_rgx = re.compile(_COMMAND_LINE_PATTERN)
    cmd_match = cmd_rgx.match(command)
    if cmd_match is None:
        raise ValueError('Failed to parse command line : "{0}".'
                         ''.format(command))
    cmd_dict = cmd_match.groupdict()
    cmd_dict.update(full=command)
    return cmd_dict
