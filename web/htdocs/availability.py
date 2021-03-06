#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2014             mk@mathias-kettner.de |
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

#### TODO: Jetzt noch die Timeline, die *nicht* inline ist. Dazu der
#### choords ergänzen. Die render_timeline() Funktion malt aber ja
#### auch noch die Tabelle mit Hovercode und noch was was ich vergessen
#### habe. Auch die Tabelle muss formalisiert erzeugt werden. Dann
#### die Möglichkeit "All Timelines" schaffen und diese dann 1:1 im
#### Reporting abbilden.

import bi, views, visuals
# TODO: Get rid of import of views
# from lib import *
from valuespec import *

#   .--Declarations--------------------------------------------------------.
#   |       ____            _                 _   _                        |
#   |      |  _ \  ___  ___| | __ _ _ __ __ _| |_(_) ___  _ __  ___        |
#   |      | | | |/ _ \/ __| |/ _` | '__/ _` | __| |/ _ \| '_ \/ __|       |
#   |      | |_| |  __/ (__| | (_| | | | (_| | |_| | (_) | | | \__ \       |
#   |      |____/ \___|\___|_|\__,_|_|  \__,_|\__|_|\___/|_| |_|___/       |
#   |                                                                      |
#   '----------------------------------------------------------------------'

host_availability_columns = [
    ( "up",                        "state0",        _("UP"),          None ),
    ( "down",                      "state2",        _("DOWN"),        None ),
    ( "unreach",                   "state3",        _("UNREACH"),     None ),
    ( "flapping",                  "flapping",      _("Flapping"),    None ),
    ( "in_downtime",               "downtime",      _("Downtime"),    _("The host was in a scheduled downtime") ),
    ( "outof_notification_period", "",              _("OO/Notif"),    _("Out of Notification Period") ),
    ( "outof_service_period",      "ooservice",     _("OO/Service") , _("Out of Service Period") ),
    ( "unmonitored",               "unmonitored",   _("N/A"),         _("During this time period no monitoring data is available") ),
]

service_availability_columns = [
    ( "ok",                        "state0",        _("OK"),          None ),
    ( "warn",                      "state1",        _("WARN"),        None ),
    ( "crit",                      "state2",        _("CRIT"),        None ),
    ( "unknown",                   "state3",        _("UNKNOWN"),     None ),
    ( "flapping",                  "flapping",      _("Flapping"),    None ),
    ( "host_down",                 "hostdown",      _("H.Down"),      _("The host was down") ),
    ( "in_downtime",               "downtime",      _("Downtime"),    _("The host or service was in a scheduled downtime") ),
    ( "outof_notification_period", "",              _("OO/Notif"),    _("Out of Notification Period") ),
    ( "outof_service_period",      "ooservice",     _("OO/Service"),  _("Out of Service Period") ),
    ( "unmonitored",               "unmonitored",   _("N/A"),         _("During this time period no monitoring data is available") ),
]

bi_availability_columns = [
    ( "ok",                        "state0",        _("OK"),          None ),
    ( "warn",                      "state1",        _("WARN"),        None ),
    ( "crit",                      "state2",        _("CRIT"),        None ),
    ( "unknown",                   "state3",        _("UNKNOWN"),     None ),
    ( "in_downtime",               "downtime",      _("Downtime"),    _("The aggregate was in a scheduled downtime") ),
    ( "unmonitored",               "unmonitored",   _("N/A"),         _("During this time period no monitoring data is available") ),
]

availability_columns = {
    "host"    : host_availability_columns,
    "service" : service_availability_columns,
    "bi"      : bi_availability_columns,
}

statistics_headers = {
    "min" : _("Shortest"),
    "max" : _("Longest"),
    "avg" : _("Average"),
    "cnt" : _("Count"),
}


#.
#   .--Options-------------------------------------------------------------.
#   |                   ___        _   _                                   |
#   |                  / _ \ _ __ | |_(_) ___  _ __  ___                   |
#   |                 | | | | '_ \| __| |/ _ \| '_ \/ __|                  |
#   |                 | |_| | |_) | |_| | (_) | | | \__ \                  |
#   |                  \___/| .__/ \__|_|\___/|_| |_|___/                  |
#   |                       |_|                                            |
#   +----------------------------------------------------------------------+
#   |  Handling of all options for tuning availability computation and     |
#   |  display.                                                            |
#   '----------------------------------------------------------------------'

# Options for availability computation and rendering. These are four-tuple
# with the columns:
# 1. variable name
# 2. show in single or double height box
# 3. use this in reporting
# 4. the valuespec
def get_avoption_entries(what):
    if what == "bi":
        grouping_choices = [
          ( None,             _("Do not group") ),
          ( "host",           _("By Aggregation Group") ),
        ]
    else:
        grouping_choices = [
          ( None,             _("Do not group") ),
          ( "host",           _("By Host")       ),
          ( "host_groups",    _("By Host group") ),
          ( "service_groups", _("By Service group") ),
        ]

    return [
  # Time range selection
  ( "rangespec",
    "double",
    False,
    Timerange(
        title = _("Time Range"),
        default_value = 'd0',
    )
  ),

  # Labelling and Texts
  ( "labelling",
    "double",
    True,
    ListChoice(
        title = _("Labelling Options"),
        choices = [
            ( "omit_headers",            _("Do not display column headers")),
            ( "omit_host",               _("Do not display the host name")),
            ( "use_display_name",        _("Use alternative display name for services")),
            ( "omit_buttons",            _("Do not display icons for history and timeline")),
            ( "display_timeline_legend", _("Display legend for timeline")),
            ( "omit_av_levels",          _("Do not display legend for availability levels")),
        ]
    )
  ),

  # How to deal with downtimes
  ( "downtimes",
    "double",
    True,
    Dictionary(
        title = _("Scheduled Downtimes"),
        columns = 2,
        elements = [
            ( "include",
              DropdownChoice(
                  choices = [
                    ( "honor", _("Honor scheduled downtimes") ),
                    ( "ignore", _("Ignore scheduled downtimes") ),
                    ( "exclude", _("Exclude scheduled downtimes" ) ),
                 ],
                 default_value = "honor",
              )
            ),
            ( "exclude_ok",
              Checkbox(label = _("Treat phases of UP/OK as non-downtime"))
            ),
        ],
        optional_keys = False,
    )
  ),

  # How to deal with downtimes, etc.
  ( "consider",
    "double",
    True,
    Dictionary(
       title = _("Status Classification"),
       columns = 2,
       elements = [
           ( "flapping",
              Checkbox(
                  label = _("Consider periods of flapping states"),
                  default_value = True),
           ),
           ( "host_down",
              Checkbox(
                  label = _("Consider times where the host is down"),
                  default_value = True),
           ),
           ( "unmonitored",
              Checkbox(
                  label = _("Include unmonitored time"),
                  default_value = True),
           ),
       ],
       optional_keys = False,
    ),
  ),

  # Optionally group some states together
  ( "state_grouping",
    "double",
    True,
    Dictionary(
       title = _("Status Grouping"),
       columns = 2,
       elements = [
           ( "warn",
              DropdownChoice(
                  label = _("Treat Warning as: "),
                  choices = [
                    ( "ok",      _("OK") ),
                    ( "warn",    _("WARN") ),
                    ( "crit",    _("CRIT") ),
                    ( "unknown", _("UNKNOWN") ),
                  ],
                  default_value = "warn",
                ),
           ),
           ( "unknown",
              DropdownChoice(
                  label = _("Treat Unknown as: "),
                  choices = [
                    ( "ok",      _("OK") ),
                    ( "warn",    _("WARN") ),
                    ( "crit",    _("CRIT") ),
                    ( "unknown", _("UNKNOWN") ),
                  ],
                  default_value = "unknown",
                ),
           ),
           ( "host_down",
              DropdownChoice(
                  label = _("Treat Host Down as: "),
                  choices = [
                    ( "ok",        _("OK") ),
                    ( "warn",      _("WARN") ),
                    ( "crit",      _("CRIT") ),
                    ( "unknown",   _("UNKNOWN") ),
                    ( "host_down", _("Host Down") ),
                  ],
                  default_value = "host_down",
                ),
           ),
       ],
       optional_keys = False,
    ),
  ),

  # Visual levels for the availability
  ( "av_levels",
    "double",
    True,
    Optional(
        Tuple(
            elements = [
                Percentage(title = _("Warning below"), default_value = 99, display_format="%.3f", size=7),
                Percentage(title = _("Critical below"), default_value = 95, display_format="%.3f", size=7),
            ]
        ),
        title = _("Visual levels for the availability (OK percentage)"),
    )
  ),

  # Filter rows according to actual availability
  ( "av_filter_outages",
    "double",
    True,
    Dictionary(
        title = _("Only show objects with outages"),
        columns = 2,
        elements = [
           ( "warn",   Percentage(title = _("Show only rows with WARN of at least"), default_value = 0.0)),
           ( "crit",   Percentage(title = _("Show only rows with CRIT of at least"), default_value = 0.0)),
           ( "non-ok", Percentage(title = _("Show only rows with non-OK of at least"), default_value = 0.0)),
        ],
        optional_keys = False,
    )
  ),


  # Show colummns for min, max, avg duration and count
  ( "outage_statistics",
    "double",
    True,
    Tuple(
        title = _("Outage statistics"),
        orientation = "horizontal",
        elements = [
            ListChoice(
                title = _("Aggregations"),
                choices = [
                  ( "min", _("minimum duration" )),
                  ( "max", _("maximum duration" )),
                  ( "avg", _("average duration" )),
                  ( "cnt", _("count" )),
                ]
            ),
            ListChoice(
                title = _("For these states:"),
                columns = 2,
                choices = [
                    ( "ok",                        _("OK/Up") ),
                    ( "warn",                      _("Warn") ),
                    ( "crit",                      _("Crit/Down") ),
                    ( "unknown",                   _("Unknown/Unreach") ),
                    ( "flapping",                  _("Flapping") ),
                    ( "host_down",                 _("Host Down") ),
                    ( "in_downtime",               _("Downtime") ),
                    ( "outof_notification_period", _("OO/Notif") ),
                ]
            )
        ]
    )
  ),

  # Omit all non-OK columns
  ( "av_mode",
    "single",
    True,
    Checkbox(
        title = _("Availability"),
        label = _("Just show the availability (i.e. OK/UP)"),
    ),
  ),

  # How to deal with the service periods
  ( "service_period",
    "single",
    True,
     DropdownChoice(
         title = _("Service Time"),
         choices = [
            ( "honor",    _("Base report only on service times") ),
            ( "ignore",   _("Include both service and non-service times" ) ),
            ( "exclude",  _("Base report only on non-service times" ) ),
         ],
         default_value = "honor",
     )
  ),

  # How to deal with times out of the notification period
  ( "notification_period",
    "single",
    True,
     DropdownChoice(
         title = _("Notification Period"),
         choices = [
            ( "honor", _("Distinguish times in and out of notification period") ),
            ( "exclude", _("Exclude times out of notification period" ) ),
            ( "ignore", _("Ignore notification period") ),
         ],
         default_value = "ignore",
     )
  ),

  # Group by Host, Hostgroup or Servicegroup?
  ( "grouping",
    "single",
    True,
    DropdownChoice(
        title = _("Grouping"),
        choices = grouping_choices,
        default_value = None,
    )
  ),

  # Format of numbers
  ( "dateformat",
    "single",
    True,
    DropdownChoice(
        title = _("Format time stamps as"),
        choices = [
            ("yyyy-mm-dd hh:mm:ss", _("YYYY-MM-DD HH:MM:SS") ),
            ("epoch",               _("Unix Timestamp (Epoch)") ),
        ],
        default_value = "yyyy-mm-dd hh:mm:ss",
    )
  ),
  ( "timeformat",
    "single",
    True,
    DropdownChoice(
        title = _("Format time ranges as"),
        choices = [
            ("percentage_0", _("Percentage - XX %") ),
            ("percentage_1", _("Percentage - XX.X %") ),
            ("percentage_2", _("Percentage - XX.XX %") ),
            ("percentage_3", _("Percentage - XX.XXX %") ),
            ("seconds",      _("Seconds") ),
            ("minutes",      _("Minutes") ),
            ("hours",        _("Hours") ),
            ("hhmmss",       _("HH:MM:SS") ),
        ],
        default_value = "percentage_2",
    )
  ),

  # Short time intervals
  ( "short_intervals",
    "single",
    True,
    Integer(
        title = _("Short Time Intervals"),
        label = _("Ignore intervals shorter or equal"),
        minvalue = 0,
        unit = _("sec"),
        default_value = 0,
    ),
  ),

  # Merging
  ( "dont_merge",
    "single",
    True,
    Checkbox(
        title = _("Phase Merging"),
        label = _("Do not merge consecutive phases with equal state")),
  ),

  # Summary line
  ( "summary",
    "single",
    True,
    DropdownChoice(
        title = _("Summary line"),
        choices = [
            ( None,      _("Do not show a summary line") ),
            ( "sum",     _("Display total sum (for % the average)") ),
            ( "average", _("Display average") ),
        ],
        default_value = "sum",
    )
  ),

  # Timeline
  ( "show_timeline",
    "single",
    True,
    Checkbox(
        title = _("Timeline"),
        label = _("Show timeline of each object directly in table")),
  ),

  # Timelimit
  ( "timelimit",
    "single",
    False,
    Age(
        title = _("Query Time Limit"),
        help = _("Limit the execution time of the query, in order to "
                 "avoid a hanging system."),
        unit = _("sec"),
        default_value = 30,
    ),
   )
]

def get_default_avoptions():
    return {
        "range"               : (time.time() - 86400, time.time()),
        "rangespec"           : "d0",
        "labelling"           : [],
        "av_levels"           : None,
        "av_filter_outages"   : { "warn" : 0.0, "crit" : 0.0, "non-ok" : 0.0 },
        "outage_statistics"   : ([],[]),
        "av_mode"             : False,
        "service_period"      : "honor",
        "notification_period" : "ignore",
        "grouping"            : None,
        "dateformat"          : "yyyy-mm-dd hh:mm:ss",
        "timeformat"          : "percentage_2",
        "short_intervals"     : 0,
        "dont_merge"          : False,
        "summary"             : "sum",
        "show_timeline"       : False,
        "timelimit"           : 30,

        "downtimes" : {
            "include" : "honor",
            "exclude_ok" : False,
        },

        "consider" : {
            "flapping"    : True,
            "host_down"   : True,
            "unmonitored" : True,
        },

        "state_grouping" : {
            "warn"        : "warn",
            "unknown"     : "unknown",
            "host_down"   : "host_down",
        },
    }

#.
#   .--Computation---------------------------------------------------------.
#   |      ____                            _        _   _                  |
#   |     / ___|___  _ __ ___  _ __  _   _| |_ __ _| |_(_) ___  _ __       |
#   |    | |   / _ \| '_ ` _ \| '_ \| | | | __/ _` | __| |/ _ \| '_ \      |
#   |    | |__| (_) | | | | | | |_) | |_| | || (_| | |_| | (_) | | | |     |
#   |     \____\___/|_| |_| |_| .__/ \__,_|\__\__,_|\__|_|\___/|_| |_|     |
#   |                         |_|                                          |
#   +----------------------------------------------------------------------+
#   |  Computation of availability data into abstract data structures.     |
#   |  These are being used for rendering in HTML and also for the re-     |
#   |  porting module. Could also be a source for exporting data into      |
#   |  files like CSV or spread sheets.                                    |
#   |                                                                      |
#   |  This code might be moved to another file.                           |
#   '----------------------------------------------------------------------'

# Get raw availability data via livestatus. The result is a list
# of spans. Each span is a dictionary that describes one span of time where
# a specific host or service has one specific state.
# what is either "host" or "service" or "bi".
def get_availability_rawdata(what, filterheaders, only_sites, av_object, include_output, avoptions):
    if what == "bi":
        return get_bi_availability_rawdata(filterheaders, only_sites, av_object, include_output, avoptions)

    time_range, range_title = avoptions["range"]

    av_filter = "Filter: time >= %d\nFilter: time < %d\n" % time_range
    if av_object:
        tl_site, tl_host, tl_service = av_object
        av_filter += "Filter: host_name = %s\nFilter: service_description = %s\n" % (
                tl_host, tl_service)
        only_sites = [ tl_site ]
    elif what == "service":
        av_filter += "Filter: service_description !=\n"
    else:
        av_filter += "Filter: service_description =\n"

    query = "GET statehist\n" + av_filter
    query += "Timelimit: %d\n" % avoptions["timelimit"]

    # Add Columns needed for object identification
    columns = [ "host_name", "service_description" ]

    # Columns for availability
    columns += [
      "duration", "from", "until", "state", "host_down", "in_downtime",
      "in_host_downtime", "in_notification_period", "in_service_period", "is_flapping", ]
    if include_output:
        columns.append("log_output")
    if "use_display_name" in avoptions["labelling"]:
        columns.append("service_display_name")

    # If we group by host/service group then make sure that that information is available
    if avoptions["grouping"] not in [ None, "host" ]:
        columns.append(avoptions["grouping"])

    query += "Columns: %s\n" % " ".join(columns)
    query += filterheaders

    html.live.set_prepend_site(True)
    html.live.set_only_sites(only_sites)
    data = html.live.query(query)
    html.live.set_only_sites(None)
    html.live.set_prepend_site(False)
    columns = ["site"] + columns
    spans = [ dict(zip(columns, span)) for span in data ]
    return spans_by_object(spans)

# Sort the raw spans into a tree of dicts, so that we
# have easy access to the timeline of each object
def spans_by_object(spans):
    # Sort by site/host and service, while keeping native order
    av_rawdata = {}
    for span in spans:
        site_host = span["site"], span["host_name"]
        service = span["service_description"]
        av_rawdata.setdefault(site_host, {})
        av_rawdata[site_host].setdefault(service, []).append(span)
    return av_rawdata


# Compute an availability table. what is one of "bi", "host", "service".
def compute_availability(what, av_rawdata, avoptions):

    # Now compute availability table. We have the following possible states:
    # 1. "unmonitored"
    # 2. "monitored"
    #    2.1 "outof_notification_period"
    #    2.2 "in_notification_period"
    #         2.2.1 "in_downtime" (also in_host_downtime)
    #         2.2.2 "not_in_downtime"
    #               2.2.2.1 "host_down"
    #               2.2.2.2 "host not down"
    #                    2.2.2.2.1 "ok"
    #                    2.2.2.2.2 "warn"
    #                    2.2.2.2.3 "crit"
    #                    2.2.2.2.4 "unknown"
    availability_table = []
    os_aggrs, os_states = avoptions.get("outage_statistics", ([],[]))
    need_statistics = os_aggrs and os_states
    grouping = avoptions["grouping"]
    timeline_rows = [] # Need this as a global variable if just one service is affected
    total_duration = 0
    considered_duration = 0

    # Note: in case of timeline, we have data from exacly one host/service
    for site_host, site_host_entry in av_rawdata.iteritems():
        for service, service_entry in site_host_entry.iteritems():

            if grouping == "host":
                group_ids = [site_host]
            elif grouping:
                group_ids = set([])
            else:
                group_ids = None

            # First compute timeline
            timeline_rows = []
            total_duration = 0
            considered_duration = 0
            for span in service_entry:
                # Information about host/service groups are in the actual entries
                if grouping and grouping != "host" and what != "bi":
                    group_ids.update(span[grouping]) # List of host/service groups

                display_name = span.get("service_display_name", service)
                state = span["state"]
                consider = True

                if state == -1:
                    s = "unmonitored"
                    if not avoptions["consider"]["unmonitored"]:
                        consider = False

                elif avoptions["service_period"] != "ignore" and \
                    (( span["in_service_period"] and avoptions["service_period"] != "honor" )
                    or \
                    ( not span["in_service_period"] and avoptions["service_period"] == "honor" )):
                    s = "outof_service_period"
                    consider = False

                elif span["in_notification_period"] == 0 and avoptions["notification_period"] == "exclude":
                    consider = False

                elif span["in_notification_period"] == 0 and avoptions["notification_period"] == "honor":
                    s = "outof_notification_period"

                elif (span["in_downtime"] or span["in_host_downtime"]) and not \
                    (avoptions["downtimes"]["exclude_ok"] and state == 0) and not \
                    avoptions["downtimes"]["include"] == "ignore":
                    if avoptions["downtimes"]["include"] == "exclude":
                        consider = False
                    else:
                        s = "in_downtime"
                elif what != "host" and span["host_down"] and avoptions["consider"]["host_down"]:
                    s = "host_down"
                elif span["is_flapping"] and avoptions["consider"]["flapping"]:
                    s = "flapping"
                else:
                    if what in [ "service", "bi" ]:
                        s = { 0: "ok", 1:"warn", 2:"crit", 3:"unknown" }.get(state, "unmonitored")
                    else:
                        s = { 0: "up", 1:"down", 2:"unreach" }.get(state, "unmonitored")
                    if s == "warn":
                        s = avoptions["state_grouping"]["warn"]
                    elif s == "unknown":
                        s = avoptions["state_grouping"]["unknown"]
                    elif s == "host_down":
                        s = avoptions["state_grouping"]["host_down"]

                total_duration += span["duration"]
                if consider:
                    timeline_rows.append((span, s))
                    considered_duration += span["duration"]

            # Now merge consecutive rows with identical state
            if not avoptions["dont_merge"]:
                merge_timeline(timeline_rows)

            # Melt down short intervals
            if avoptions["short_intervals"]:
                melt_short_intervals(timeline_rows, avoptions["short_intervals"], avoptions["dont_merge"])

            # Condense into availability
            states = {}
            statistics = {}
            for span, s in timeline_rows:
                states.setdefault(s, 0)
                duration = span["duration"]
                states[s] += duration
                if need_statistics:
                    entry = statistics.get(s)
                    if entry:
                        entry[0] += 1
                        entry[1] = min(entry[1], duration)
                        entry[2] = max(entry[2], duration)
                    else:
                        statistics[s] = [ 1, duration, duration ] # count, min, max

            availability_entry = {
                "site"                : site_host[0],
                "host"                : site_host[1],
                "service"             : service,
                "display_name"        : display_name,
                "states"              : states,
                "considered_duration" : considered_duration,
                "total_duration"      : total_duration,
                "statistics"          : statistics,
                "groups"              : group_ids,
                "timeline"            : timeline_rows,
            }


            availability_table.append(availability_entry)

    availability_table.sort(cmp = cmp_av_entry)

    # Apply filters
    filtered_table = []
    for row in availability_table:
        if pass_availability_filter(row, avoptions):
            filtered_table.append(row)
    return filtered_table


def pass_availability_filter(row, avoptions):
    for key, level in avoptions["av_filter_outages"].items():
        if level == 0.0:
            continue
        if key == "warn":
            ref_value = row["states"].get("warn", 0)
        elif key == "crit":
            ref_value = row["states"].get("crit", row["states"].get("down", 0))
        elif key == "non-ok":
            ref_value = 0.0
            for key, value in row["states"].items():
                if key not in [ "ok", "up", "unmonitored" ]:
                    ref_value += value
        else:
            continue # undefined key. Should never happen
        percentage = 100.0 * ref_value / row["considered_duration"]
        if percentage < level:
            return False

    return True

# Compute a list of availability tables - one for each group.
# Each entry is a pair of group_name and availability_table.
# It is sorted by the group names
def compute_availability_groups(what, av_data, avoptions):

    grouping = avoptions["grouping"]
    if not grouping:
        return [ (None, av_data) ]

    else:
        availability_tables = []

        # Grouping is one of host/hostgroup/servicegroup

        # 1. Get complete list of all groups
        all_group_ids = get_av_groups(av_data, avoptions)

        # 2. Compute names for the groups and sort according to these names
        if grouping != "host":
            group_titles = dict(visuals.all_groups(grouping[:-7]))

        titled_groups = []
        for group_id in all_group_ids:
            if grouping == "host":
                titled_groups.append((group_id[1], group_id)) # omit the site name
            else:
                if group_id == ():
                    title = _("Not contained in any group")
                else:
                    title = group_titles.get(group_id, group_id)
                titled_groups.append((title, group_id)) ## ACHTUNG
        titled_groups.sort(cmp = lambda a,b: cmp(a[1], b[1]))

        # 3. Loop over all groups and render them
        for title, group_id in titled_groups:
            group_table = []
            for entry in av_data:
                group_ids = entry["groups"]
                if group_id == () and group_ids:
                    continue # This is not an ungrouped object
                elif group_id and group_id not in group_ids:
                    continue # Not this group
                group_table.append(entry)
            availability_tables.append((title, group_table))

        return availability_tables


def object_title(what, av_entry):
    if what == "host":
        return av_entry["host"]
    else: # service and BI
        return av_entry["host"] + " / " + av_entry["service"]


# Merge consecutive rows with same state
def merge_timeline(entries):
    n = 1
    while n < len(entries):
        if entries[n][1] == entries[n-1][1]:
            entries[n-1][0]["duration"] += entries[n][0]["duration"]
            entries[n-1][0]["until"] = entries[n][0]["until"]
            del entries[n]
        else:
            n += 1

def melt_short_intervals(entries, duration, dont_merge):
    n = 1
    need_merge = False
    while n < len(entries) - 1:
        if entries[n][0]["duration"] <= duration and \
            entries[n-1][1] == entries[n+1][1]:
            entries[n] = (entries[n][0], entries[n-1][1])
            need_merge = True
        n += 1

    # Due to melting, we need to merge again
    if need_merge and not dont_merge:
        merge_timeline(entries)
        melt_short_intervals(entries, duration, dont_merge)


#.
#   .--Layout--------------------------------------------------------------.
#   |                  _                            _                      |
#   |                 | |    __ _ _   _  ___  _   _| |_                    |
#   |                 | |   / _` | | | |/ _ \| | | | __|                   |
#   |                 | |__| (_| | |_| | (_) | |_| | |_                    |
#   |                 |_____\__,_|\__, |\___/ \__,_|\__|                   |
#   |                             |___/                                    |
#   +----------------------------------------------------------------------+
#   |                                                                      |
#   '----------------------------------------------------------------------'
# When grouping is enabled, this function is called once for each group
# TODO: range_title sollte hier überflüssig sein
# TODO: Hier jetzt nicht direkt HTML erzeugen, sondern eine saubere
# Datenstruktur füllen, welche die Daten so repräsentiert, dass sie
# nur noch 1:1 dargestellt werden müssen.
# Beispiel für einen Rückgabewert:
# {
#    "title" : "Hostgroup foobar",
#    "headers" : [ "OK, "CRIT", "Downtime" ],
#    "rows" : [ ... ],
#    "summary" : [ ("84.50%", "crit"), ("15.50%", "crit"), ("0.00%", "p"),  ("0.00%", "p") ],
# }
# row ist ein dict: {
#    "cells" : [ ("84.50%", "crit"), ("15.50%", "crit"), ("0.00%", "p"),  ("0.00%", "p") ],
#    "urls" : { "timeline": "view.py..." },
#    "object" : ( "Host123", "Foobar" ),
# }
def layout_availability_table(what, group_title, availability_table, avoptions):
    time_range, range_title = avoptions["range"]

    render_number = render_number_function(avoptions)

    show_timeline = avoptions["show_timeline"]
    labelling = avoptions["labelling"]
    av_levels = avoptions["av_levels"]
    show_summary = avoptions.get("summary")

    summary = {}
    summary_counts = {}

    av_table = {
        "title" : group_title,
        "rows" : [],
    }

    # Titles for the columns that specify the object
    if what == "bi":
        av_table["object_titles"] = [ _("Aggregate") ]
    elif what == "host":
        av_table["object_titles"] = [ _("Host") ]
    else: # service
        if "omit_host" in labelling:
            av_table["object_titles"] = [ _("Service") ]
        else:
            av_table["object_titles"] = [ _("Host"), _("Service") ]

    # Headers for availability cells
    av_table["cell_titles"] = []
    os_aggrs, os_states = avoptions.get("outage_statistics", ([],[]))
    for sid, css, sname, help in availability_columns[what]:
        if not cell_active(sid, avoptions):
            continue
        if avoptions["av_mode"]:
            sname = _("Avail.")

        av_table["cell_titles"].append((sname, help))

        if sid in os_states:
            for aggr in os_aggrs:
                title = statistics_headers[aggr]
                av_table["cell_titles"].append((title, None))

    # Actual rows
    for entry in availability_table:
        site = entry["site"]
        host = entry["host"]
        service = entry["service"]

        row = {}
        av_table["rows"].append(row)

        # Iconbuttons with URLs
        urls = []
        if not "omit_buttons" in labelling:
            if what != "bi":
                timeline_url = html.makeuri([
                       ("av_mode", "timeline"),
                       ("av_site", site),
                       ("av_host", host),
                       ("av_service", service)])
            else:
                timeline_url = html.makeuri([("av_mode", "timeline"), ("av_aggr_group", host), ("av_aggr_name", service)])
            urls.append(( "timeline", _("Timeline"), timeline_url ))
            if what != "bi":
                urls.append(("history", _("Event History"), history_url_of((site, host, service), time_range)))
        row["urls"] = urls

        # Column with host/service or aggregate name
        objectcells = [] # List of pairs of (text, url)
        if what == "bi":
            bi_url = "view.py?" + html.urlencode_vars([("view_name", "aggr_single"), ("aggr_group", host), ("aggr_name", service)])
            objectcells.append((service, bi_url))
        else:
            host_url = "view.py?" + html.urlencode_vars([("view_name", "hoststatus"), ("site", site), ("host", host)])
            if not "omit_host" in labelling or what == "host":
                objectcells.append((host, host_url))
            if what == "service":
                if "use_display_name" in labelling:
                    service_name = entry["display_name"]
                else:
                    service_name = service
                service_url = "view.py?" + html.urlencode_vars([("view_name", "service"), ("site", site), ("host", host), ("service", service)])
                objectcells.append((service_name, service_url))
        row["object"] = objectcells

        # Inline timeline
        if show_timeline:
            row["timeline"] = layout_timeline(what, entry["timeline"], entry["considered_duration"], avoptions, style="inline")


        # Actuall cells with availability data
        row["cells"] = []
        for sid, css, sname, help in availability_columns[what]:
            if not cell_active(sid, avoptions):
                continue

            number = entry["states"].get(sid, 0)
            if not number:
                css = "unused"
            elif show_summary:
                summary.setdefault(sid, 0.0)
                if avoptions["timeformat"].startswith("percentage"):
                    if entry["considered_duration"] > 0:
                        summary[sid] += float(number) / entry["considered_duration"]
                else:
                    summary[sid] += number

            # Apply visual availability levels (render OK in yellow/red, if too low)
            if number and av_levels and sid in [ "ok", "up" ]:
                css = "state%d" % check_av_levels(number, av_levels, entry["considered_duration"])

            row["cells"].append((render_number(number, entry["considered_duration"]), css))

            # Statistics?
            x_cnt, x_min, x_max = entry["statistics"].get(sid, (None, None, None))
            os_aggrs, os_states = avoptions.get("outage_statistics", ([],[]))
            if sid in os_states:
                for aggr in os_aggrs:
                    if x_cnt != None:
                        if aggr == "avg":
                            r = render_number(number / x_cnt, entry["considered_duration"])
                        elif aggr == "min":
                            r = render_number(x_min, entry["considered_duration"])
                        elif aggr == "max":
                            r = render_number(x_max, entry["considered_duration"])
                        else:
                            r = str(x_cnt)
                            summary_counts.setdefault(sid, 0)
                            summary_counts[sid] += x_cnt
                        row["cells"].append((r, css))
                    else:
                        row["cells"].append(("", ""))


    # Summary line. It has the same format as each entry in cells
    if show_summary and len(availability_table) > 0:
        summary_cells = []

        for sid, css, sname, help in availability_columns[what]:
            if not cell_active(sid, avoptions):
                continue
            number = summary.get(sid, 0)
            if show_summary == "average" or avoptions["timeformat"].startswith("percentage"):
                number /= len(availability_table)
                if avoptions["timeformat"].startswith("percentage"):
                    number *= entry["considered_duration"]
            if not number:
                css = "unused"

            if number and av_levels and sid in [ "ok", "up" ]:
                css = "state%d" % check_av_levels(number, av_levels, entry["considered_duration"])

            summary_cells.append((render_number(number, entry["considered_duration"]), css))
            if sid in os_states:
                for aggr in os_aggrs:
                    if aggr == "cnt":
                        count = summary_counts.get(sid, 0)
                        if show_summary == "average":
                            count = float(count) / len(availability_table)
                            text = "%.2f" % count
                        else:
                            text = str(count)
                        summary_cells.append((text, css))
                    else:
                        summary_cells.append(("", ""))
        av_table["summary"] = summary_cells

    return av_table

# Compute layout of timeline independent of the output device (HTML, PDF, whatever)...
# style is either "inline" or "standalone"
# Output format:
# {
#    "spans" : [ spans... ],
#    "legend" : [ legendentries... ],
# }
def layout_timeline(what, timeline_rows, considered_duration, avoptions, style):

    render_number = render_number_function(avoptions)
    time_range, range_title = avoptions["range"]
    from_time, until_time = time_range
    total_duration = until_time - from_time

    # Timeformat: show date only if the displayed time range spans over
    # more than one day.
    time_format = "%H:%M:%S"
    if time.localtime(from_time)[:3] != time.localtime(until_time-1)[:3]:
        time_format = "%Y-%m-%d " + time_format

    def render_date_func(time_format):
        def render_date(ts):
            if avoptions["dateformat"] == "epoch":
                return str(int(ts))
            else:
                return time.strftime(time_format, time.localtime(ts))
        return render_date

    render_date = render_date_func(time_format)
    spans = []
    table = []
    timeline_layout = {
        "range"        : time_range,
        "spans"        : spans,
        "time_choords" : [],
        "render_date"  : render_date,
        "table"        : table,
    }

    # Render graphical representation
    # Make sure that each cell is visible, if possible
    if timeline_rows:
        min_percentage = min(100.0 / len(timeline_rows), style == "inline" and 0.0 or 0.5)
    else:
        min_percentage = 0
    rest_percentage = 100 - len(timeline_rows) * min_percentage

    chaos_begin = None
    chaos_end = None
    chaos_count = 0
    chaos_width = 0

    def chaos_period(chaos_begin, chaos_end, chaos_count, chaos_width):
        title = _("%d chaotic state changes from %s until %s (%s)") % (
            chaos_count,
            render_date(chaos_begin), render_date(chaos_end),
            render_number(chaos_end - chaos_begin, considered_duration))
        return (None, title, chaos_width, "chaos")


    current_time = from_time
    for row_nr, (row, state_id) in enumerate(timeline_rows):
        this_from_time = row["from"]
        this_until_time = row["until"]
        if this_from_time > current_time: # GAP
            spans.append((None, "", 100.0 * (this_from_time - current_time) / total_duration, "unmonitored"))
        current_time = this_until_time

        from_text = render_date(this_from_time)
        until_text = render_date(this_until_time)
        duration_text = render_number(row["duration"], considered_duration)

        for sid, css, sname, help in availability_columns[what]:
            if sid == state_id:
                title = _("From %s until %s (%s) %s") % (from_text, until_text, duration_text, help and help or sname)
                if "log_output" in row and row["log_output"]:
                    title += " - " + row["log_output"]
                width = rest_percentage * row["duration"] / total_duration

                # Information for table of detailed events
                if style == "standalone":
                    table.append({
                        "state"         : state_id,
                        "css"           : css,
                        "state_name"    : sname,
                        "from"          : row["from"],
                        "until"         : row["until"],
                        "from_text"     : from_text,
                        "until_text"    : until_text,
                        "duration_text" : duration_text,
                    })
                    if "log_output" in row and row["log_output"]:
                        table[-1]["log_output"] = row["log_output"]

                # If the width is very small then we group several phases into
                # one single "chaos period".
                if style == "inline" and width < 0.05:
                    if not chaos_begin:
                        chaos_begin = row["from"]
                    chaos_width += width
                    chaos_count += 1
                    chaos_end = row["until"]
                    continue

                # Chaos period has ended? One not-small phase:
                elif chaos_begin:
                    # Only output chaos phases with a certain length
                    if chaos_count >= 4:
                        spans.append(chaos_period(chaos_begin, chaos_end, chaos_count, chaos_width))

                    chaos_begin = None
                    chaos_count = 0
                    chaos_width = 0

                width += min_percentage
                spans.append((row_nr, title, width, css))

    if chaos_count > 1:
        spans.append(chaos_period(chaos_begin, chaos_end, chaos_count, chaos_width))

    if style == "inline":
        timeline_layout["time_choords"] = layout_timeline_choords(time_range)

    return timeline_layout


def layout_timeline_choords(time_range):
    from_time, until_time = time_range
    duration = until_time - from_time

    # Now comes the difficult part: decide automatically, whether to use
    # hours, days, weeks or months. Days and weeks needs to take local time
    # into account. Months are irregular.
    hours = duration / 3600
    if hours < 12:
        scale = "hours"
    elif hours < 24:
        scale = "2hours"
    elif hours < 48:
        scale = "6hours"
    elif hours < 24 * 14:
        scale = "days"
    elif hours < 24 * 60:
        scale = "weeks"
    else:
        scale = "months"

    broken = list(time.localtime(from_time))
    while True:
        next_choord, title = find_next_choord(broken, scale)
        if next_choord >= until_time:
            break
        position = (next_choord - from_time) / float(duration) # ranges from 0.0 to 1.0
        yield position, title


def find_next_choord(broken, scale):
    # Elements in broken:
    # 0: year
    # 1: month (1 = January)
    # 2: day of month
    # 3: hour
    # 4: minute
    # 5: second
    # 6: day of week (0 = monday)
    # 7: day of year
    # 8: isdst (0 or 1)
    broken[4:6] = [0, 0] # always set min/sec to 00:00
    old_dst = broken[8]

    if scale == "hours":
        epoch = time.mktime(broken)
        epoch += 3600
        broken[:] = list(time.localtime(epoch))
        title = time.strftime("%H:%M",  broken)

    elif scale == "2hours":
        broken[3] = broken[3] / 2 * 2
        epoch = time.mktime(broken)
        epoch += 2 * 3600
        broken[:] = list(time.localtime(epoch))
        title = weekdays[broken[6]] + time.strftime(" %H:%M", broken)

    elif scale == "6hours":
        broken[3] = broken[3] / 6 * 6
        epoch = time.mktime(broken)
        epoch += 6 * 3600
        broken[:] = list(time.localtime(epoch))
        title = weekdays[broken[6]] + time.strftime(" %H:%M", broken)

    elif scale == "days":
        broken[3] = 0
        epoch = time.mktime(broken)
        epoch += 24 * 3600
        broken[:] = list(time.localtime(epoch))
        title = weekdays[broken[6]] + time.strftime(", %d.%m. 00:00", broken)

    elif scale == "weeks":
        broken[3] = 0
        at_00 = int(time.mktime(broken))
        at_monday = at_00 - 86400 * broken[6]
        epoch = at_monday + 7 * 86400
        broken[:] = list(time.localtime(epoch))
        title = weekdays[broken[6]] + time.strftime(", %d.%m.", broken)

    else: # scale == "months":
        broken[3] = 0
        broken[2] = 0
        broken[1] += 1
        if broken[1] > 12:
            broken[1] = 1
            broken[0] += 1
        epoch = time.mktime(broken)
        title = "%s %d" % (valuespec.month_names[broken[1]-1], broken[0])

    dst = broken[8]
    if old_dst == 1 and dst == 0:
        epoch += 3600
    elif old_dst == 0 and dst == 1:
        epoch -= 3600
    return epoch, title

#.
#   .--BI------------------------------------------------------------------.
#   |                              ____ ___                                |
#   |                             | __ )_ _|                               |
#   |                             |  _ \| |                                |
#   |                             | |_) | |                                |
#   |                             |____/___|                               |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   |  Availability computation in BI aggregates. Here we generate the     |
#   |  same availability raw data. We fill the field "host" with the BI    |
#   |  group and the field "service" with the BI aggregate's name.         |
#   '----------------------------------------------------------------------'

def get_bi_availability_rawdata(filterheaders, only_sites, av_object, include_output, avoptions):
    raise XXX

def get_bi_spans(tree, aggr_group, avoptions, timewarp):
    time_range, range_title = avoptions["range"]
    # Get state history of all hosts and services contained in the tree.
    # In order to simplify the query, we always fetch the information for
    # all hosts of the aggregates.
    only_sites = set([])
    hosts = []
    for site, host in tree["reqhosts"]:
        only_sites.add(site)
        hosts.append(host)

    columns = [ "host_name", "service_description", "from", "log_output", "state", "in_downtime", "in_service_period" ]
    html.live.set_only_sites(list(only_sites))
    html.live.set_prepend_site(True)
    html.live.set_limit() # removes limit
    query = "GET statehist\n" + \
            "Columns: " + " ".join(columns) + "\n" +\
            "Filter: time >= %d\nFilter: time < %d\n" % time_range

    # Create a specific filter. We really only want the services and hosts
    # of the aggregation in question. That prevents status changes
    # irrelevant services from introducing new phases.
    by_host = {}
    for site, host, service in bi.find_all_leaves(tree):
        by_host.setdefault(host, set([])).add(service)

    for host, services in by_host.items():
        query += "Filter: host_name = %s\n" % host
        query += "Filter: service_description = \n"
        for service in services:
            query += "Filter: service_description = %s\n" % service
        query += "Or: %d\nAnd: 2\n" % (len(services) + 1)
    if len(hosts) != 1:
        query += "Or: %d\n" % len(hosts)

    data = html.live.query(query)
    if not data:
        return [], None
        # raise MKGeneralException(_("No historical data available for this aggregation. Query was: <pre>%s</pre>") % query)

    html.live.set_prepend_site(False)
    html.live.set_only_sites(None)
    columns = ["site"] + columns
    rows = [ dict(zip(columns, row)) for row in data ]

    # Now comes the tricky part: recompute the state of the aggregate
    # for each step in the state history and construct a timeline from
    # it. As a first step we need the start state for each of the
    # hosts/services. They will always be the first consecute rows
    # in the statehist table

    # First partition the rows into sequences with equal start time
    phases = {}
    for row in rows:
        from_time = row["from"]
        phases.setdefault(from_time, []).append(row)

    # Convert phases to sorted list
    sorted_times = phases.keys()
    sorted_times.sort()
    phases_list = []
    for from_time in sorted_times:
        phases_list.append((from_time, phases[from_time]))

    states = {}
    def update_states(phase_entries):
        for row in phase_entries:
            service     = row["service_description"]
            key         = row["site"], row["host_name"], service
            states[key] = row["state"], row["log_output"], row["in_downtime"], (row["in_service_period"] != 0)


    update_states(phases_list[0][1])
    # states does now reflect the host/services states at the beginning
    # of the query range.
    tree_state = compute_tree_state(tree, states)
    tree_time = time_range[0]
    if timewarp == int(tree_time):
        timewarp_state = tree_state
    else:
        timewarp_state = None

    timeline = []
    def append_to_timeline(from_time, until_time, tree_state):
        timeline.append({
            "state"                  : tree_state[0]['state'],
            "log_output"             : tree_state[0]['output'],
            "from"                   : from_time,
            "until"                  : until_time,
            "site"                   : "",
            "host_name"              : aggr_group,
            "service_description"    : tree['title'],
            "in_notification_period" : 1,
            "in_service_period"      : tree_state[0]['in_service_period'],
            "in_downtime"            : tree_state[0]['in_downtime'],
            "in_host_downtime"       : 0,
            "host_down"              : 0,
            "is_flapping"            : 0,
            "duration"               : until_time - from_time,
        })


    for from_time, phase in phases_list[1:]:
        update_states(phase)
        next_tree_state = compute_tree_state(tree, states)
        duration = from_time - tree_time
        append_to_timeline(tree_time, from_time, tree_state)
        tree_state = next_tree_state
        tree_time = from_time
        if timewarp == tree_time:
            timewarp_state = tree_state

    # Add one last entry - for the state until the end of the interval
    append_to_timeline(tree_time, time_range[1], tree_state)

    return timeline, timewarp_state


def compute_tree_state(tree, status):
    # Convert our status format into that needed by BI
    services_by_host = {}
    hosts = {}
    for site_host_service, state_output in status.items():
        site_host = site_host_service[:2]
        service = site_host_service[2]
        if service:
            services_by_host.setdefault(site_host, []).append((
                service,         # service description
                state_output[0], # state
                1,               # has_been_checked
                state_output[1], # output
                state_output[0], # hard state (we use the soft state here)
                1,               # attempt
                1,               # max_attempts (not relevant)
                state_output[2], # in_downtime
                False,           # acknowledged
                state_output[3], # in_service_period
                ))
        else:
            hosts[site_host] = state_output

    status_info = {}
    for site_host, state_output in hosts.items():
        status_info[site_host] = [
            state_output[0],
            state_output[0], # host hard state
            state_output[1],
            state_output[2], # in_downtime
            False, # acknowledged
            state_output[3], # in_service_period
            services_by_host.get(site_host,[])
        ]


    # Finally we can execute the tree
    bi.load_assumptions()
    tree_state = bi.execute_tree(tree, status_info)
    return tree_state

#.
#   .--Various-------------------------------------------------------------.
#   |                __     __         _                                   |
#   |                \ \   / /_ _ _ __(_) ___  _   _ ___                   |
#   |                 \ \ / / _` | '__| |/ _ \| | | / __|                  |
#   |                  \ V / (_| | |  | | (_) | |_| \__ \                  |
#   |                   \_/ \__,_|_|  |_|\___/ \__,_|___/                  |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   |  Various other functions                                             |
#   '----------------------------------------------------------------------'

# Helper function, needed in row and in summary line. Determines wether
# a certain cell should be visiable. For example when WARN is mapped
# to CRIT because of state grouping, then the WARN column should not be
# displayed.
def cell_active(sid, avoptions):
    # Some columns might be unneeded due to state treatment options
    sg = avoptions["state_grouping"]
    state_groups = [ sg["warn"], sg["unknown"], sg["host_down"] ]

    if sid not in [ "up", "ok" ] and avoptions["av_mode"]:
        return False
    if sid == "outof_notification_period" and avoptions["notification_period"] != "honor":
        return False
    elif sid == "outof_service_period": # Never show this as a column
        return False
    elif sid == "in_downtime" and avoptions["downtimes"]["include"] != "honor":
        return False
    elif sid == "unmonitored" and not avoptions["consider"]["unmonitored"]:
        return False
    elif sid == "flapping" and not avoptions["consider"]["flapping"]:
        return False
    elif sid == "host_down" and not avoptions["consider"]["host_down"]:
        return False
    elif sid in [ "warn", "unknown", "host_down" ] and sid not in state_groups:
        return False
    else:
        return True

# Check if the availability of some object is below the levels
# that are configured in the avoptions.
def check_av_levels(ok_seconds, av_levels, considered_duration):
    if considered_duration == 0:
        return 0

    perc = 100 * float(ok_seconds) / float(considered_duration)
    warn, crit = av_levels
    if perc < crit:
        return 2
    elif perc < warn:
        return 1
    else:
        return 0


def get_av_groups(availability_table, avoptions):
    grouping = avoptions["grouping"]
    all_group_ids = set([])
    for entry in availability_table:
        all_group_ids.update(entry["groups"])
        if len(entry["groups"]) == 0:
            all_group_ids.add(()) # null-tuple denotes ungrouped objects
    return all_group_ids


# Sort according to host and service. First after site, then
# host (natural sort), then service
def cmp_av_entry(a, b):
    return cmp(a["site"], b["site"]) or \
           cmp(num_split(a["host"]) + (a["host"],), num_split(b["host"]) + (b["host"],)) or \
           cmp(cmp_service_name_equiv(a["service"]), cmp_service_name_equiv(b["service"])) or \
           cmp(a["service"], b["service"])

# Creates a function for rendering time values according to
# the avoptions of the report.
def render_number_function(avoptions):
    timeformat = avoptions["timeformat"]
    if timeformat.startswith("percentage_"):
        def render_number(n, d):
            if not d:
                return _("n/a")
            else:
                return ("%." + timeformat[11:] + "f%%") % ( float(n) / float(d) * 100.0)
    elif timeformat == "seconds":
        def render_number(n, d):
            return "%d s" % n
    elif timeformat == "minutes":
        def render_number(n, d):
            return "%d min" % (n / 60)
    elif timeformat == "hours":
        def render_number(n, d):
            return "%d h" % (n / 3600)
    else:
        def render_number(n, d):
            minn, sec = divmod(n, 60)
            hours, minn = divmod(minn, 60)
            return "%02d:%02d:%02d" % (hours, minn, sec)

    return render_number

def history_url_of(av_object, time_range):
    site, host, service = av_object
    from_time, until_time = time_range

    history_url_vars = [
        ("site", site),
        ("host", host),
        ("logtime_from_range", "unix"),  # absolute timestamp
        ("logtime_until_range", "unix"), # absolute timestamp
        ("logtime_from", str(int(from_time))),
        ("logtime_until", str(int(until_time)))]
    if service:
        history_url_vars += [
            ("service", service),
            ("view_name", "svcevents"),
        ]
    else:
        history_url_vars += [
            ("view_name", "hostevents"),
        ]

    return "view.py?" + html.urlencode_vars(history_url_vars)


