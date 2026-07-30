from typing import Any
import sys


class Maps_parsing(Exception):
    """Raised when a map file does not respect the expected format."""
    ...


class Parsing:
    """Parse a map file into raw drone-network data structures."""

    def __init__(self, f_path: str) -> None:
        """Load and parse a map file.

        Args:
            f_path: Path to the map file to parse.
        """
        self.f_path: str = f_path
        self.lines: list[str] = []
        self.nb_drones: int | None = None
        self.start_hub: dict[str, Any] | None = None
        self.end_hub: dict[str, Any] | None = None
        self.hub: dict[str, Any] = {}
        self.connection: dict[str, Any] = {}
        self.f_path_read()
        self.args_pars()

    def f_path_read(self) -> None:
        """Read the input file into memory."""
        try:
            with open(self.f_path, 'r') as r_path:
                self.lines = r_path.readlines()
                if (len(self.lines)) == 0:
                    print('ERROR: input file is empty')
                    sys.exit(1)
        except (FileNotFoundError, PermissionError, IOError) as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    def args_pars(self) -> None:
        """Parse the file contents and build the map data structures."""
        conn_num = 1
        data: Any
        colors: Any
        color: Any
        second: Any
        content: Any
        try:
            for line, content in enumerate(self.lines, start=1):
                if content.startswith('#') or not content.strip():
                    continue
                elif "nb_drones" == content.split(':')[0].strip():
                    if self.nb_drones is not None:
                        raise Maps_parsing("nb_drones is already defined")
                    try:
                        self.nb_drones = int(content.split(':')[1])
                        if self.nb_drones < 1:
                            raise Maps_parsing(
                                "nb_drones must be a positive integer")
                    except (ValueError, TypeError):
                        print(
                            "ERROR: nb_drones must be a valid integer"
                            f"\nLine: {line}"
                        )
                        sys.exit(1)
                elif "start_hub" == content.split(':')[0]:
                    if self.start_hub:
                        raise Maps_parsing("start_hub is already defined")
                    basic_brackets_check = {'[': 0,
                                            ']': 0}
                    if self.nb_drones is None:
                        raise Maps_parsing(
                            "nb_drones must be defined before start_hub")
                    name = 'start_hub'
                    data = content.split(':')[1].strip()
                    data = data.split(" ")
                    if len(data) not in (4, 5) or data[0] != 'start':
                        raise Maps_parsing(
                            f"{name} must have the format "
                            "'start_hub: start <x> <y> "
                            "[color=<color>] [max_drones=<n>]'")
                    try:
                        if '-' in data[0]:
                            raise Maps_parsing(
                                f"{name} identifier cannot contain '-'")
                    except (ValueError, TypeError):
                        raise Maps_parsing(
                            f"{name} identifier cannot contain '-'")
                    try:
                        x = int(data[1])
                        y = int(data[2])
                    except (ValueError, TypeError):
                        raise Maps_parsing(
                            f"{name} x and y coordinates must be integers")

                    args = []
                    for arg in data[3:]:
                        args.append(arg)
                    colors = " ".join(args)
                    if not colors.startswith('[') or not colors.endswith(']'):
                        raise Maps_parsing(
                            f"{name} metadata must be enclosed in square "
                            "brackets, e.g. [color=red max_drones=2]")
                    for char in colors:
                        if char == '[':
                            basic_brackets_check['['] += 1
                            if basic_brackets_check['['] > 1:
                                raise Maps_parsing(
                                    f"{name} metadata brackets are"
                                    " unbalanced")
                        elif char == ']':
                            basic_brackets_check[']'] += 1
                            if basic_brackets_check[']'] > 1:
                                raise Maps_parsing(
                                    f"{name} metadata brackets are"
                                    " unbalanced")
                    if basic_brackets_check['['] != basic_brackets_check[']']:
                        raise Maps_parsing(
                            f"{name} metadata brackets are unbalanced")
                    colors = colors.strip('[]').split()
                    metadata: dict[str, Any] = {}
                    for color in colors:
                        color = color.split('=')
                        if len(color) != 2:
                            raise Maps_parsing(
                                f"{name} metadata must use 'key=value' "
                                "pairs with key in ('color', 'max_drones')")
                        if color[0] not in ('color', 'max_drones'):
                            raise Maps_parsing(
                                f"{name} metadata must use 'key=value' "
                                "pairs with key in ('color', 'max_drones')")
                        if color[0] in metadata:
                            raise Maps_parsing(
                                f"{name} metadata key '{color[0]}' is"
                                " duplicated")
                        elif color[0] == 'max_drones':
                            try:
                                metadata.update({'max_drones': int(color[1])})
                            except (ValueError, TypeError):
                                raise Maps_parsing(
                                    f"{name} max_drones value must be a"
                                    " valid integer")
                        elif color[0] == 'color':
                            if not color[1]:
                                raise Maps_parsing(
                                    f"{name} color value cannot be empty")
                            metadata.update({'color': color[1]})
                    self.start_hub = {
                        'name': 'start',
                        'x_y': (x, y),
                        'metadata': metadata
                    }
                elif "end_hub" == content.split(':')[0]:
                    if self.end_hub:
                        raise Maps_parsing("end_hub is already defined")
                    basic_brackets_check = {'[': 0,
                                            ']': 0}
                    if self.nb_drones is None:
                        raise Maps_parsing(
                            "nb_drones must be defined before end_hub")
                    if not self.start_hub:
                        raise Maps_parsing(
                            "start_hub must be defined before end_hub")
                    name = 'end_hub'
                    data = content.split(':')[1].strip()
                    data = data.split(" ")
                    lend_hub = data[0]
                    if len(data) not in (4, 5):
                        raise Maps_parsing(
                            f"{name} must have the format "
                            "'end_hub: <name> <x> <y> "
                            "[color=<color>] [max_drones=<n>]'")
                    try:
                        if '-' in data[0]:
                            raise Maps_parsing(
                                f"{name} identifier cannot contain '-'")
                    except (ValueError, TypeError):
                        raise Maps_parsing(
                            f"{name} identifier cannot contain '-'")
                    try:
                        x = int(data[1])
                        y = int(data[2])
                    except (ValueError, TypeError):
                        raise Maps_parsing(
                            f"{name} x and y coordinates must be integers")

                    args = []
                    for arg in data[3:]:
                        args.append(arg)
                    colors = " ".join(args)
                    if not colors.startswith('[') or not colors.endswith(']'):
                        raise Maps_parsing(
                            f"{name} metadata must be enclosed in square "
                            "brackets, e.g. [color=red max_drones=2]")
                    for char in colors:
                        if char == '[':
                            basic_brackets_check['['] += 1
                            if basic_brackets_check['['] > 1:
                                raise Maps_parsing(
                                    f"{name} metadata brackets are"
                                    " unbalanced")
                        elif char == ']':
                            basic_brackets_check[']'] += 1
                            if basic_brackets_check[']'] > 1:
                                raise Maps_parsing(
                                    f"{name} metadata brackets are"
                                    " unbalanced")
                    if basic_brackets_check['['] != basic_brackets_check[']']:
                        raise Maps_parsing(
                            f"{name} metadata brackets are unbalanced")
                    colors = colors.strip('[]').split()
                    metadata = {}
                    for color in colors:
                        color = color.split('=')
                        if len(color) != 2:
                            raise Maps_parsing(
                                f"{name} metadata must use 'key=value' "
                                "pairs with key in ('color', 'max_drones')")
                        if color[0] not in ('color', 'max_drones'):
                            raise Maps_parsing(
                                f"{name} metadata must use 'key=value' "
                                "pairs with key in ('color', 'max_drones')")
                        if color[0] in metadata:
                            raise Maps_parsing(
                                f"{name} metadata key '{color[0]}' is"
                                " duplicated")
                        elif color[0] == 'max_drones':
                            try:
                                maxi: int = int(color[1])
                                if maxi < 1:
                                    raise Maps_parsing(
                                        "max_drones must be a positive"
                                        " integer")
                                metadata.update({'max_drones': maxi})
                            except (ValueError, TypeError):
                                raise Maps_parsing(
                                    f"{name} max_drones value must be a"
                                    " valid integer")
                        elif color[0] == 'color':
                            if not color[1]:
                                raise Maps_parsing(
                                    f"{name} color value cannot be empty")
                            metadata.update({'color': color[1]})
                    self.end_hub = {
                        'name': lend_hub,
                        'x_y': (x, y),
                        'metadata': metadata
                    }
                    if self.end_hub['x_y'] == self.start_hub['x_y']:
                        raise Maps_parsing(
                            "start_hub and end_hub cannot share the same"
                            " coordinates")
                elif "hub" == content.split(':')[0]:
                    basic_brackets_check = {'[': 0,
                                            ']': 0}
                    if self.nb_drones is None:
                        raise Maps_parsing(
                            "nb_drones must be defined before hub"
                            " declarations")
                    data = content.split(':')[1]
                    data = data.strip('\n').strip().split(' ')
                    if data[0] in self.hub:
                        raise Maps_parsing(
                            f"hub '{data[0]}' is already defined")
                    name = data[0]
                    if len(data) not in (4, 5, 6):
                        raise Maps_parsing(
                            f"{name} must have the format "
                            "'hub: <name> <x> <y> [color=<color>] "
                            "[max_drones=<n>] [zone=<type>]'")
                    try:
                        if '-' in data[0]:
                            raise Maps_parsing(
                                f"{name} identifier cannot contain '-'")
                    except (ValueError, TypeError):
                        raise Maps_parsing(
                            f"{name} identifier cannot contain '-'")
                    try:
                        x = int(data[1])
                        y = int(data[2])
                    except (ValueError, TypeError):
                        raise Maps_parsing(
                            f"{name} x and y coordinates must be integers")
                    args = []
                    for arg in data[3:]:
                        args.append(arg)
                    colors = " ".join(args)
                    if not colors.startswith('[') or not colors.endswith(']'):
                        raise Maps_parsing(
                            f"{name} metadata must be enclosed in square "
                            "brackets, e.g. [color=red max_drones=2 "
                            "zone=normal]")
                    for char in colors:
                        if char == '[':
                            basic_brackets_check['['] += 1
                            if basic_brackets_check['['] > 1:
                                raise Maps_parsing(
                                    f"{name} metadata brackets are"
                                    " unbalanced")
                        elif char == ']':
                            basic_brackets_check[']'] += 1
                            if basic_brackets_check[']'] > 1:
                                raise Maps_parsing(
                                    f"{name} metadata brackets are"
                                    " unbalanced")
                    if basic_brackets_check['['] != basic_brackets_check[']']:
                        raise Maps_parsing(
                            f"{name} metadata brackets are unbalanced")
                    colors = colors.strip('[]').split()
                    metadata = {}
                    for color in colors:
                        color = color.split('=')
                        if len(color) != 2:
                            raise Maps_parsing(
                                f"{name} metadata must use 'key=value' "
                                "pairs with key in ('color', 'max_drones', "
                                "'zone')")
                        if color[0] not in ('color', 'max_drones', 'zone'):
                            raise Maps_parsing(
                                f"{name} metadata must use 'key=value' "
                                "pairs with key in ('color', 'max_drones', "
                                "'zone')")
                        if color[0] in metadata:
                            raise Maps_parsing(
                                f"{name} metadata key '{color[0]}' is"
                                " duplicated")
                        elif color[0] == 'max_drones':
                            try:
                                mm: int = int(color[1])
                                if mm < 1:
                                    raise Maps_parsing(
                                        "max_drones must be a positive"
                                        " integer")
                                metadata.update({'max_drones': int(color[1])})
                            except (ValueError, TypeError):
                                raise Maps_parsing(
                                    f"{name} max_drones value must be a"
                                    " valid integer")
                        elif color[0] == 'color':
                            if not color[1]:
                                raise Maps_parsing(
                                    f"{name} color value cannot be empty")
                            try:
                                _ = int(color[1])
                                raise Maps_parsing(
                                    f"{name} color value cannot be numeric")
                            except (ValueError, TypeError):
                                pass
                            metadata.update({'color': color[1]})

                        elif color[0] == 'zone':
                            if color[1] not in (
                                'restricted', 'priority', 'blocked', 'normal'
                            ):
                                raise Maps_parsing(
                                    f"{name} zone type must be one of: "
                                    "normal, priority, restricted, blocked")
                            metadata.update({'zone': color[1]})
                    self.hub[name] = {
                        'name': name,
                        'x_y': (x, y),
                        'metadata': metadata
                    }
                    for hub in self.hub:
                        if hub == name:
                            pass
                        elif self.hub[name]['x_y'] == self.hub[hub]['x_y']:
                            raise Maps_parsing(
                                f"hub '{name}' has the same coordinates as"
                                f" hub '{hub}'")
                elif "connection" == content.split(':')[0]:
                    if self.end_hub is None:
                        raise Maps_parsing(
                            "connections cannot be defined before end_hub")
                    endy: str = self.end_hub['name']
                    metadata = {}
                    basic_brackets_check = {'[': 0,
                                            ']': 0}
                    if self.nb_drones is None:
                        raise Maps_parsing(
                            "nb_drones must be defined before connection"
                            " declarations")
                    if len(content.split(':')) != 2:
                        raise Maps_parsing(
                            "connection line must have exactly one ':'"
                            " separator")
                    content = content.split(':')[1].strip()
                    name = f'connection{conn_num}'
                    conn_num += 1
                    content = content.split(' ')
                    if len(content) not in (1, 2):
                        raise Maps_parsing(
                            "connection must specify a zone pair and an"
                            " optional metadata block only")
                    if '-' not in content[0]:
                        raise Maps_parsing(
                            "connection must be in the format"
                            " 'zone1-zone2'")
                    connection = content[0].split('-')
                    if len(connection) != 2:
                        raise Maps_parsing(
                            "connection must reference exactly two zones")
                    if len(content) == 2:
                        second = content[1]
                        if (not second.startswith('[')
                                or not second.endswith(']')):
                            raise Maps_parsing(
                                f"{name} metadata must be enclosed in "
                                "square brackets, e.g. "
                                "[max_link_capacity=2]")
                        for char in second:
                            if char == '[':
                                basic_brackets_check['['] += 1
                                if basic_brackets_check['['] > 1:
                                    raise Maps_parsing(
                                        f"{name} metadata brackets are"
                                        " unbalanced")
                            elif char == ']':
                                basic_brackets_check[']'] += 1
                                if basic_brackets_check[']'] > 1:
                                    raise Maps_parsing(
                                        f"{name} metadata brackets are"
                                        " unbalanced")
                        if (basic_brackets_check['[']
                                != basic_brackets_check[']']):
                            raise Maps_parsing(
                                f"{name} metadata brackets are unbalanced")
                        second = second.strip('[]')
                        if '=' not in second:
                            raise Maps_parsing(
                                f"{name} metadata must use the format"
                                " 'max_link_capacity=<value>'")
                        else:
                            second = second.split('=')
                            if second[0] != 'max_link_capacity':
                                raise Maps_parsing(
                                    f"{name} metadata key must be"
                                    " 'max_link_capacity'")
                            try:
                                second = int(second[1])
                                if second < 1:
                                    raise Maps_parsing(
                                        "max_link_capacity must be a"
                                        " positive integer")
                            except (ValueError, TypeError):
                                raise Maps_parsing(
                                    f"{name} max_link_capacity value must"
                                    " be a valid integer")
                    else:
                        second = None
                    zone_1 = [connection[0], False]
                    zone_2 = [connection[1], False]

                    if self.hub:
                        for hub_key in self.hub:
                            if (zone_1[0] == hub_key
                                    or zone_1[0] in ('start', endy)):
                                zone_1[1] = True
                            if (zone_2[0] == hub_key
                                    or zone_2[0] in ('start', endy)):
                                zone_2[1] = True
                        if not zone_1[1] or not zone_2[1]:
                            raise Maps_parsing(
                                f"{name} references an undefined zone")
                    if second and second > 50:
                        raise Maps_parsing(
                            f"{name} max_link_capacity cannot exceed 50")
                    self.connection[name] = {
                        'name': name,
                        'connection': connection,
                        'max_link_capacity': second
                    }
                    for conn in self.connection:
                        con1 = self.connection[name]['connection']
                        con2 = self.connection[conn]['connection']
                        if conn == name:
                            pass
                        else:
                            if con1 == con2:
                                raise Maps_parsing(
                                    f"connection between '{con1[0]}' and"
                                    f" '{con1[1]}' is already defined")
                            elif sorted(con1) == sorted(con2):
                                raise Maps_parsing(
                                    f"connection between '{con1[0]}' and"
                                    f" '{con1[1]}' is already defined")
                else:
                    raise Maps_parsing(
                        "unrecognized line; expected one of: nb_drones, "
                        "start_hub, end_hub, hub, connection")
        except Maps_parsing as e:
            print(f"ERROR: {e}\nLine: {line}")
            sys.exit(1)
        if self.nb_drones is None:
            print('ERROR: nb_drones is missing from the map file')
            sys.exit(1)
        if self.start_hub is None:
            print('ERROR: start_hub is missing from the map file')
            sys.exit(1)
        if self.end_hub is None:
            print('ERROR: end_hub is missing from the map file')
            sys.exit(1)