#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2013             mk@mathias-kettner.de |
# +------------------------------------------------------------------+
#
# This file is part of Check_MK.
# The official homepage is at http://mathias-kettner.de/check_mk.
#
# check_mk is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

register_notification_parameters("mail",
    Dictionary(
        elements = [
            ( "from",
              TextAscii(
                  title = _("From: Adress"),
                  size = 40,
                  allow_empty = False,
              )
            ),
            ( "reply_to",
              TextAscii(
                  title = _("Reply-To: Adress"),
                  size = 40,
                  allow_empty = False,
              )
            ),
            ( "host_subject",
              TextUnicode(
                  title = _("Subject for host notifications"),
                  help = _("Here you are allowed to use all macros that are defined in the "
                           "notification context."),
                  default_value = "Check_MK: $HOSTNAME$ - $EVENT_TXT$",
                  size = 64,
               )
            ),
            ( "service_subject",
              TextUnicode(
                  title = _("Subject for service notifications"),
                  help = _("Here you are allowed to use all macros that are defined in the "
                           "notification context."),
                  default_value = "Check_MK: $HOSTNAME$/$SERVICEDESC$ $EVENT_TXT$",
                  size = 64,
               )
            ),
            ( "elements",
              ListChoice(
                  title = _("Information to be displayed in the email body"),
                  choices = [
                      ( "address",  _("IP Address of Host") ),
                      ( "abstime",  _("Absolute Time of Alert") ),
                      ( "reltime",  _("Relative Time of Alert") ),
                      ( "longoutput", _("Additional Plugin Output") ),
                      ( "perfdata", _("Performance Data") ),
                      ( "graph",    _("Performance Graphs") ),
                  ],
                  default_value = [ "perfdata", "graph", "abstime", "address", "longoutput" ],
              )
            ),
            ( "url_prefix",
              TextAscii(
                  title = _("URL prefix for links to Multisite"),
                  help = _("If you specify an URL prefix here, then several parts of the "
                           "email body are armed with hyperlinks to your Multisite GUI, so "
                           "that the recipient of the email can directly visit the host or "
                           "service in question in Multisite. Specify an absolute URL including "
                           "the <tt>.../check_mk/</tt>"),
                  regex = "^(http|https)://.*/check_mk/$",
                  regex_error = _("The URL must begin with <tt>http</tt> or "
                                  "<tt>https</tt> and end with <tt>/check_mk/</tt>."),
                  size = 64,
                  default_value = "http://" + socket.gethostname() + "/" + (
                          defaults.omd_site and defaults.omd_site + "/" or "") + "check_mk/",
              )
            )
        ]
    )
)
register_notification_parameters("asciimail",
    Dictionary(
        elements = [
            ( "from",
              TextAscii(
                  title = _("From: Adress"),
                  size = 40,
                  allow_empty = False,
              )
            ),
            ( "reply_to",
              TextAscii(
                  title = _("Reply-To: Adress"),
                  size = 40,
                  allow_empty = False,
              )
            ),
            ( "host_subject",
              TextUnicode(
                  title = _("Subject for host notifications"),
                  help = _("Here you are allowed to use all macros that are defined in the "
                           "notification context."),
                  default_value = "Check_MK: $HOSTNAME$ - $EVENT_TXT$",
                  size = 64,
               )
            ),
            ( "service_subject",
              TextUnicode(
                  title = _("Subject for service notifications"),
                  help = _("Here you are allowed to use all macros that are defined in the "
                           "notification context."),
                  default_value = "Check_MK: $HOSTNAME$/$SERVICEDESC$ $EVENT_TXT$",
                  size = 64,
               )
            ),
            ( "common_body",
              TextAreaUnicode(
                  title = _("Body head for both host and service notifications"),
                  rows = 7,
                  cols = 58,
                  monospaced = True,
                  default_value = """Host:     $HOSTNAME$
Alias:    $HOSTALIAS$
Address:  $HOSTADDRESS$
""",
              )
            ),
            ( "host_body",
              TextAreaUnicode(
                  title = _("Body tail for host notifications"),
                  rows = 9,
                  cols = 58,
                  monospaced = True,
                  default_value = """Event:    $EVENT_TXT$
Output:   $HOSTOUTPUT$
Perfdata: $HOSTPERFDATA$
$LONGHOSTOUTPUT$
""",
              )
            ),
            ( "service_body",
              TextAreaUnicode(
                  title = _("Body tail for service notifications"),
                  rows = 11,
                  cols = 58,
                  monospaced = True,
                  default_value = """Service:  $SERVICEDESC$
Event:    $EVENT_TXT$
Output:   $SERVICEOUTPUT$
Perfdata: $SERVICEPERFDATA$
$LONGSERVICEOUTPUT$
""",
              )
            ),
        ]
    )
)



register_notification_parameters("mkeventd",
    Dictionary(
        elements = [
            ( "facility",
              DropdownChoice(
                  title = _("Syslog Facility to use"),
                  help = _("The notifications will be converted into syslog message with "
                           "the facility that you choose here. In the Event Console you can "
                           "later create a rule matching this facility."),
                  choices = syslog_facilities,
              )
            ),
            ( "remote",
              IPv4Address(
                  title = _("IP Address of remote Event Console"),
                  help = _("If you set this parameter then the notifications will be sent via "
                           "syslog/UDP (port 514) to a remote Event Console or syslog server."),
              )
            ),
        ]
    )
)