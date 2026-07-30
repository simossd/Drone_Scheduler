from typing import Any
from graph import Graph


class PathFinder:
    """Plan drone routes over time while respecting zone and link capacity."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the pathfinder.

        Args:
            graph: The graph describing zones, connections, and capacities.
        """
        self.graph: Graph = graph
        self.node_reservations: dict[Any, int] = {}
        self.edge_reservations: dict[Any, int] = {}
        # dict of paths {num_of_drones: [(zone, turn)]}
        self.routes: dict[int, list[tuple[str, int]]] = {}
        self.plan_all()

    def reconstruct(
        self,
        came_from: dict[tuple[str, int], tuple[str, int]],
        goal: str,
        final_turn: int
    ) -> list[tuple[str, int]]:
        """Rebuild a path from the goal state back to the start state.

        Args:
            came_from: Parent links for the explored states.
            goal: Name of the goal zone.
            final_turn: Turn at which the goal was reached.

        Returns:
            The reconstructed path as a list of ``(location, turn)`` pairs.
        """
        path: list[tuple[str, int]] = []
        current: tuple[str, int] = (goal, final_turn)
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.append(current)
        path.reverse()
        return path

    def dijkstra(self) -> list[tuple[str, int]]:
        """Find the next valid earliest-arrival path for one drone.

        Returns:
            The chosen path as a list of ``(location, turn)`` pairs.
        """
        queue: list[tuple[int, int, str]] = []
        visited: set[tuple[str, int]] = set()
        came_from: dict[tuple[str, int], tuple[str, int]] = {}
        start: str = self.graph.start_hub
        goal: str = self.graph.end_hub
        max_turn: int = len(self.graph.zones) * 3 + self.graph.nb_drones * 5
        queue.append((0, 1, start))

        while queue:
            queue.sort()
            turn, _, zone = queue.pop(0)

            if turn > max_turn:
                continue

            if (zone, turn) in visited:
                continue
            visited.add((zone, turn))

            if zone == goal:
                return self.reconstruct(came_from, goal, turn)

            zone_obj = self.graph.zones[zone]
            next_turn: int = turn + 1

            if zone == start:
                if (zone, next_turn) not in visited:
                    queue.append((next_turn, 1, zone))
                    if (zone, next_turn) not in came_from:
                        came_from[(zone, next_turn)] = (zone, turn)
            else:
                capacity_ok: bool = (
                    self.node_reservations.get((zone, next_turn), 0)
                    < zone_obj.max_drones
                )
                if capacity_ok and (zone, next_turn) not in visited:
                    queue.append((next_turn, 1, zone))
                    if (zone, next_turn) not in came_from:
                        came_from[(zone, next_turn)] = (zone, turn)

            for neighbor in self.graph.next_to[zone]:
                neighbor_obj = self.graph.zones[neighbor]
                conn_key: Any = tuple(sorted([zone, neighbor]))
                conn = self.graph.connections[conn_key]

                if neighbor_obj.type in ('normal', 'priority'):
                    next_turn = turn + 1

                    if neighbor == goal:
                        zone_ok: bool = True
                    else:
                        zone_ok = (
                            self.node_reservations.get(
                                (neighbor, next_turn), 0)
                            < neighbor_obj.max_drones
                        )

                    edge_ok: bool = (
                        self.edge_reservations.get((conn_key, turn), 0)
                        < conn.max_link
                    )

                    is_new: bool = (neighbor, next_turn) not in visited
                    if zone_ok and edge_ok and is_new:
                        priority_rank: int = (
                            0 if neighbor_obj.type == 'priority' else 1
                        )
                        queue.append((next_turn, priority_rank, neighbor))
                        if (neighbor, next_turn) not in came_from:
                            came_from[(neighbor, next_turn)] = (zone, turn)

                elif neighbor_obj.type == 'restricted':
                    next_turn = turn + 2
                    transit: str = zone + '-' + neighbor
                    zone_ok = (
                        self.node_reservations.get((neighbor, next_turn), 0)
                        < neighbor_obj.max_drones
                    )

                    edge_ok_t0: bool = (
                        self.edge_reservations.get((conn_key, turn), 0)
                        < conn.max_link
                    )
                    edge_ok_t1: bool = (
                        self.edge_reservations.get((conn_key, turn + 1), 0)
                        < conn.max_link
                    )

                    all_ok: bool = zone_ok and edge_ok_t0 and edge_ok_t1
                    if all_ok and (neighbor, next_turn) not in visited:
                        queue.append((next_turn, 1, neighbor))
                        if (transit, turn + 1) not in came_from:
                            came_from[(transit, turn + 1)] = (zone, turn)
                        if (neighbor, next_turn) not in came_from:
                            came_from[(neighbor, next_turn)] = (
                                transit, turn + 1
                            )

        raise ValueError("No path found — map may be unsolvable")

    def reserve(self, path: list[tuple[str, int]]) -> None:
        """Reserve every node and edge used by a completed path.

        Args:
            path: The completed route to reserve.
        """
        for i in range(len(path) - 1):
            loc_now, t_now = path[i]
            loc_next, t_next = path[i + 1]

            if loc_now == self.graph.end_hub:
                continue

            is_transit_now: bool = '-' in loc_now
            is_transit_next: bool = '-' in loc_next
            arrived_from_transit: bool = (
                i > 0
                and '-' in path[i - 1][0]
                and path[i - 1][0].split('-')[1] == loc_now
                and path[i - 1][1] == t_now - 1
            )

            if (
                loc_now != self.graph.start_hub
                and not is_transit_now
                and not arrived_from_transit
            ):
                count: int = self.node_reservations.get((loc_now, t_now), 0)
                self.node_reservations[(loc_now, t_now)] = count + 1

            if not is_transit_now and not is_transit_next:
                if loc_now != loc_next:
                    edge_key: Any = tuple(sorted([loc_now, loc_next]))
                    e: int = self.edge_reservations.get((edge_key, t_now), 0)
                    self.edge_reservations[(edge_key, t_now)] = e + 1

            if not is_transit_now and is_transit_next:
                parts: list[str] = loc_next.split('-')
                edge_key = tuple(sorted(parts))
                e1: int = self.edge_reservations.get((edge_key, t_now), 0)
                self.edge_reservations[(edge_key, t_now)] = e1 + 1
                e2: int = self.edge_reservations.get((edge_key, t_now + 1), 0)
                self.edge_reservations[(edge_key, t_now + 1)] = e2 + 1

            if is_transit_now and not is_transit_next:
                if loc_next != self.graph.end_hub:
                    a: int = self.node_reservations.get((loc_next, t_next), 0)
                    self.node_reservations[(loc_next, t_next)] = a + 1

    def plan_all(self) -> None:
        """Plan routes for all drones one after another."""
        for drone_id in range(1, self.graph.nb_drones + 1):
            path: list[tuple[str, int]] = self.dijkstra()
            self.routes[drone_id] = path
            self.reserve(path)

    def build_output(self) -> dict[int, list[tuple[str, str, str]]]:
        """Convert the planned routes into turn-by-turn output data.

        Returns:
            A turn-indexed mapping of drone movements for display.
        """
        output: dict[int, list[tuple[str, str, str]]] = {}

        for drone_id, path in self.routes.items():
            for i in range(len(path)):
                location, turn = path[i]

                if turn == 0:
                    continue

                if i > 0 and location == path[i - 1][0]:
                    continue

                if '-' in location:
                    dest: str = location.split('-')[1]
                    color: str = self.graph.zones[dest].color
                else:
                    color = self.graph.zones[location].color

                drone_label: str = 'D' + str(drone_id)

                if turn not in output:
                    output[turn] = []
                output[turn].append((drone_label, location, color))

        return output
