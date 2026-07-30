from enum import Enum
from typing import Any
from parsing import Parsing


class Zonetype(Enum):
    """Enumerate the supported zone types."""
    NORMAL = 'normal'
    BLOCKED = 'blocked'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'


class Zone:
    """Store the parsed data for a zone."""

    def __init__(self, zones: dict[str, Any]) -> None:
        """Create a zone from parsed metadata.

        Args:
            zones: Parsed zone definition.
        """
        self.zones: dict = zones
        self.name: str = ''
        self.type: str = Zonetype.NORMAL.value
        self.color: str = 'white'
        self.max_drones: int = 1
        self.generating_values()

    def generating_values(self) -> None:
        """Populate the zone fields from metadata."""
        self.name = self.zones.get('name', '')
        metadata = self.zones.get('metadata', {})
        for data, val in metadata.items():
            if data == 'color':
                self.color = val
            if data == 'max_drones':
                self.max_drones = val
            if data == 'zone':
                self.type = Zonetype(val).value


class Connection:
    """Store the parsed data for a connection."""

    def __init__(self, connections: dict[str, Any]) -> None:
        """Create a connection from parsed metadata.

        Args:
            connections: Parsed connection definition.
        """
        self.connections: dict[str, Any] = connections
        self.name: str = ''
        self.zone1: str = ''
        self.zone2: str = ''
        self.max_link: int = 1
        self.zone_fill()

    def zone_fill(self) -> None:
        """Populate the connection endpoints and capacity."""
        self.name = self.connections.get('name', '')
        zones = self.connections.get('connection', [])
        self.zone1 = zones[0]
        self.zone2 = zones[1]
        cap = self.connections.get('max_link_capacity')
        if cap is not None:
            self.max_link = cap


class Graph:
    """Build the routing graph from parsed map data."""

    def __init__(self, parsed_data: Parsing) -> None:
        """Create the graph representation from parsed data.

        Args:
            parsed_data: Parsed map contents.
        """
        self.p_data: Parsing = parsed_data
        self.nb_drones: int = 0
        self.start_hub: str = ''
        self.end_hub: str = ''
        self.zones: dict[str, Zone] = {}
        self.connections: dict[tuple[str, str], Connection] = {}
        self.next_to: dict[str, list[str]] = {}
        self.graph_fill()

    def graph_fill(self) -> None:
        """Load zones, endpoints, and connections into the graph."""
        assert self.p_data.nb_drones is not None
        self.nb_drones = self.p_data.nb_drones

        assert self.p_data.start_hub is not None
        start_zone = Zone(self.p_data.start_hub)
        self.zones[start_zone.name] = start_zone
        self.start_hub = start_zone.name

        assert self.p_data.end_hub is not None
        end_zone = Zone(self.p_data.end_hub)
        self.zones[end_zone.name] = end_zone
        self.end_hub = end_zone.name

        for name, val in self.p_data.hub.items():
            self.zones[name] = Zone(val)

        self.build_connections()
        self.build_next_to()

    def build_connections(self) -> None:
        """Create connection objects from the parsed connections."""
        for val in self.p_data.connection.values():
            conn = Connection(val)
            zone_a, zone_b = sorted([conn.zone1, conn.zone2])
            key: tuple[str, str] = (zone_a, zone_b)
            self.connections[key] = conn

    def build_next_to(self) -> None:
        """Build the adjacency list for all non-blocked zones."""
        for name in self.zones:
            self.next_to[name] = []

        for (zone_a, zone_b) in self.connections:
            if self.is_blocked(zone_a) or self.is_blocked(zone_b):
                continue
            if zone_a not in self.next_to[zone_b]:
                self.next_to[zone_b].append(zone_a)
            if zone_b not in self.next_to[zone_a]:
                self.next_to[zone_a].append(zone_b)

    def is_blocked(self, zone_name: str) -> bool:
        """Return whether a zone is blocked."""
        return self.zones[zone_name].type == Zonetype.BLOCKED.value
