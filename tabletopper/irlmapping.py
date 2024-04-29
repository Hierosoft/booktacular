
from __future__ import division
from __future__ import print_function
from collections import OrderedDict


from tabletopper import (
    find_which,
    find_any,
    endswith_any,
)

end_deg = (" ", "°")
end_minutes = ("′", "'")
end_seconds = ("″", '"')
end_longitude = ("N", "S")
end_north = "N"
end_south = "S"  # if found, change longitude to negative
end_east = "E"
end_west = "W"  # if found, change latitude to negative
end_coord = (end_north, end_south, end_east, end_west)
min_sec_pairs = ("′″", "'\"")  # order matters; 1st required if 2nd used
min_sec_marks = "".join(min_sec_pairs)


def get_precision(number):
    """Count places after the dot

    Args:
        number (str): Any number.

    Returns:
        int: Number of characters after the dot, or 0 if None.
    """
    if not isinstance(number, str):
        raise TypeError("A string is required, but got {}({})."
                        .format(type(number).__name__, number))
    number = number.strip()
    dot_i = number.find(".")
    if dot_i < 0:
        return 0
    return len(number) - (dot_i + 1)


def to_gps_coord(coord, strict=True, digits=None):
    """Convert a single coord string to a GPS float value.

    Args:
        coord (str): String such as 30 16' 13.13" E
            or 6°59′38″S
        strict (bool, optional): String must end with
            N, E, S, or W. If False, make sure the coordinate
            is already negative for West or South!
        digits (int, optional): Number of decimal places (See
            to_gps_coord). Defaults to 5 (since 1 second is .0002
            repeating 7) or auto-detect.

    """
    coord = coord.strip()
    polarity = 0
    if coord.endswith("N"):
        polarity = 1
    elif coord.endswith("E"):
        polarity = 1
    elif coord.endswith("S"):
        polarity = -1
    elif coord.endswith("W"):
        polarity = -1
    if polarity:
        # Remove N, E, S, or W.
        coord = coord[:-1].strip()
    else:
        if strict:
            raise ValueError("A non-GPS coord must end in N, W, E, or S"
                             " to determine hemisphere (direction from 0).")

        if find_any(coord, min_sec_marks) > -1:
            raise ValueError("N, E, S or W is expected if using"
                             " deg, min[, sec] marks ({})"
                             "but got \"{}\""
                             .format(min_sec_marks, coord))
    marks = None
    m_end = None
    max_decimals = None
    for try_marks in min_sec_pairs:
        m_end, mark_which = find_which(coord, try_marks)
        if m_end > -1:
            if mark_which > 0:
                raise ValueError(
                    "Got `{}` before `{}` in `{}`"
                    .format(try_marks[1], try_marks[0], coord)
                )
            marks = try_marks
            break
    # seconds = 0
    # minutes = 0
    deg = "°"
    d_end = coord.find(deg)
    if d_end < 0:
        # allow space to end it instead.
        d_end = coord.find(" ")
        if d_end > -1:
            deg = " "
    total = 0
    if marks:
        if d_end < 1:
            raise ValueError("Got `{}` but no `{}` in `{}`"
                             .format(marks[0], deg, coord))
        elif d_end > m_end:
            raise ValueError("Got `{}` before `{}` in `{}`"
                             .format(marks[0], deg, coord))
        s_end = coord.find(marks[1])
        if s_end > -1:
            # add seconds (1/3600 degrees) to total
            sec_s = coord[m_end + 1:s_end].strip()
            total += float(sec_s) / 60 / 60
            coord = coord[:m_end + 1].strip()
            max_decimals = get_precision(sec_s) + 5
            # ^ +5 more decimals for total since 1 second is
            #   .0002 repeating 7
        min_s = coord[d_end + 1:m_end].strip()
        # add minutes (1/60 degrees) to total
        total += float(min_s) / 60
        coord = coord[:d_end + 1].strip()
        if max_decimals is None:
            max_decimals = get_precision(min_s) + 3
            # ^ +3 more decimals for total since 1 minute is
            #   .01 repeating 6

    coord = coord.strip()
    if coord.endswith(deg):
        coord = coord[:-1].strip()
    if max_decimals is None:
        max_decimals = get_precision(coord)
    if digits is None:
        digits = max_decimals

    total += float(coord)
    if polarity < 0:
        return round(total * polarity, digits)
    return round(total, digits)


def clean_coords(coords_str, digits=None):
    """Convert various coordinates to two floats.

    Args:
        coords_str (str): Any global coords in a well-defined format.
            Examples:
            - "58.9929731,-3.2164469"
            - "30.85762, 46.16782"
            - "6°59′38″S 107°03′23″E"
              - Where "S" makes the longitude negative and "W" would
                make the latitude negative.
            - "40.284893,-109.9369981,24708m"
            - "25 55' 53.28" S / 30 16' 13.13" E"
        digits (int, optional): Number of decimal places (See
            to_gps_coord for details and default).
    Raises:
        ValueError: _description_
        ValueError: _description_

    Returns:
        tuple(float): 2-long (Longitude, Latitude) or 3-long (with
            elevation as 3rd element) global coordinates.
    """
    # end_decimal = ","  # if found before a space or other deg symbol,
    #  assume decimal (such as "39.5754352,21.4050767" or "30.85762, 46.16782")
    # decimal_i = coords_str.find(end_decimal)
    # deg_i = find_any(coords_str, end_deg)
    # space_i = find_any(coords_str, " ")
    splits = OrderedDict()  # ordered since "," takes priority if ", "
    for delim in (",", "/", " "):
        # / example: """25 55' 53.28" S / 30 16' 13.13" E"""
        if delim == " ":
            splits[delim] = coords_str.split()
        else:
            splits[delim] = [c.strip() for c in coords_str.split(delim)]
        parts = splits[delim]
        if len(parts) == 2:
            parts = parts
            return (
                to_gps_coord(parts[0], digits=digits,
                             strict=endswith_any(parts[0], end_coord)),
                to_gps_coord(parts[1], digits=digits,
                             strict=endswith_any(parts[1], end_coord))
            )
        elif len(parts) == 3:
            if not parts[2].endswith("m"):
                raise ValueError("'m' is expected (to denote meters)"
                                 " if elevation (3rd element) is given: {}"
                                 .format(coords_str))
            return (  # 3D global coords (3rd element is elevation in meters)
                to_gps_coord(parts[0], digits=digits,
                             strict=endswith_any(parts[0], end_coord)),
                to_gps_coord(parts[1], digits=digits,
                             strict=endswith_any(parts[1], end_coord)),
                float(parts[2][:-1]),  # -1 to remove "m" at end
            )

    if "," in coords_str:
        raise ValueError("Expected 2 or 3 (N,E,elevation) parts but got \"{}\""
                         .format(coords_str))
    if "/" in coords_str:
        raise ValueError("Expected 2 or 3 (N/E/elevation) parts but got \"{}\""
                         .format(coords_str))

    end_longitude_i = find_any(coords_str, end_longitude)
    if end_longitude_i < 0:
        raise ValueError("{} was expected in non-GPS coords: {}"
                         .format(end_longitude, coords_str))
    return (
        to_gps_coord(coords_str[:end_longitude_i + 1],  # +1 includes N/S
                     digits=digits,
                     strict=endswith_any(parts[0], end_coord)),
        to_gps_coord(coords_str[end_longitude_i + 1:].strip(),
                     digits=digits,
                     strict=endswith_any(parts[1], end_coord)),
        # ^ +1 exclude N/S
    )
