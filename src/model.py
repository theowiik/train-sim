from enum import Enum
from typing import List, Tuple

from core.data import Cell, CellType, Direction, DirectionUtils
from core.map_parser import MapParser
from core.util import ArrayUtils


class TrainStates(Enum):
    OK = "OK"
    CRASHED = "CRASHED"


class Train:
    state: TrainStates = TrainStates.OK
    is_accelerating: bool = False
    _speed: float = 0
    _DEACCELERATION: float = 0.1
    _ACCELERATION: float = 0.2
    _MAX_SPEED: int = 5
    _LENGTH: int = 5

    def __init__(
        self,
        direction: Direction,
    ):
        self.direction: Direction = direction

    def accelerate_tick(self):
        if self.is_accelerating:
            self._speed += self._ACCELERATION
        else:
            self._speed -= self._DEACCELERATION

        # Clamp within [0, _max_speed]
        self._speed = max(min(self._speed, self._MAX_SPEED), 0)

    def get_rounded_speed(self):
        return int(self._speed)


class Model:
    sensor_states: dict[Tuple[int, int], bool] = {}
    _direction_utils = DirectionUtils()
    _matrix: List[List[Cell]] = MapParser.build_map()
    is_accelerating = False
    train_positions: dict[Train, list[Tuple]] = {Train(Direction.LEFT): [(24, 1)]}

    def __init__(self):
        for train, positions in self.train_positions.items():
            for _ in range(train._LENGTH - 1):
                positions.append((positions[0][0], positions[0][1]))

        # Find all sensors
        for y, row in enumerate(self._matrix):
            for x, cell in enumerate(row):
                if cell.cell_type == CellType.SENSOR:
                    self.sensor_states[(x, y)] = False

    def tick(self):
        """
        Main tick function
        """
        for train, positions in self.train_positions.items():
            self._move_train_tick(train, positions)

        self._check_collisions()

    def get_cells_train(self, x, y) -> Train | None:
        for train, positions in self.train_positions.items():
            for position in positions:
                if position[0] == x and position[1] == y:
                    return train

        return None

    def _get_cells_sensor(self, x, y) -> Cell | None:
        """
        Returns the cell at the specified coordinates, if it is a sensor.
        If the cell is not a sensor, returns None.
        """
        try:
            cell: Cell = self._matrix[y][x]
            if cell.cell_type == CellType.SENSOR:
                return cell
            else:
                return None
        except IndexError:
            return None

    def _move_train_tick(self, train: Train, positions: List[Tuple[int, int]]):
        for _ in range(train.get_rounded_speed()):
            self._move_train_one_cell(train, positions)

        train.is_accelerating = self.is_accelerating  # TODO: bad
        train.accelerate_tick()
        self._update_sensor_states()

    def _update_sensor_states(self):
        # Reset all sensors
        for position in self.sensor_states.keys():
            self.sensor_states[position] = False

        # Update sensors
        for positions in self.train_positions.values():
            for position in positions:
                sensor = self._get_cells_sensor(position[0], position[1])

                if sensor is not None:
                    self.sensor_states[(position[0], position[1])] = True

    def _move_train_one_cell(
        self, train: Train, positions: List[Tuple[int, int]]
    ) -> None:
        """
        Moves the train one cell in the direction specified by the train's current direction.
        If a valid move is found, updates the train's position and direction accordingly.
        If no valid move is found, sets the train's state to TRAIN_CRASH_STATE.

        Args:
            train (Train): The train object to move.
            positions (List[Tuple[int, int]]): The current positions of all trains.

        Returns:
            None
        """
        head = positions[0]
        current_cell: Cell = self._matrix[head[1]][head[0]]

        possible_dirs: list[Direction] = [
            train.direction
        ] + self._direction_utils.ALLOWED_TURNS[train.direction]

        dirs_to_try: list[Direction] = []
        for direction in possible_dirs:
            # Ensure it's a valid direction
            if direction in current_cell._allowed_turns:
                dirs_to_try.append(direction)

        (next_x, next_y) = (None, None)
        for direction in dirs_to_try:
            add_x, add_y = self._direction_utils.DIR_TO_COORDINATE[direction]
            new_test_x = head[0] + add_x
            new_test_y = head[1] + add_y

            if new_test_x < 0 or new_test_x >= len(self._matrix[0]):
                continue
            if new_test_y < 0 or new_test_y >= len(self._matrix):
                continue

            if self._matrix[new_test_y][new_test_x].cell_type in [
                CellType.TRACK,
                CellType.SWITCH_LEFT,
                CellType.SWITCH_RIGHT,
                CellType.SENSOR,
            ]:
                (next_x, next_y) = (new_test_x, new_test_y)
                break

        if next_x is not None and next_y is not None:
            (old_x, old_y) = head
            ArrayUtils.push_first(self.train_positions[train], (next_x, next_y))

            new_dir = self._direction_utils.COORDINATE_TO_DIR[
                (next_x - old_x, next_y - old_y)
            ]
            train.direction = new_dir
        else:
            # print("💥 no move possible, collision")
            train.state = TrainStates.CRASHED

    def _check_collisions(self):
        """
        Checks for collisions between trains and updates their states accordingly.

        This method iterates over each train and its positions, and checks if there is
        another train occupying the same position. If a collision is detected, both
        trains are set to the `TRAIN_CRASH_STATE`.

        Note: This method assumes that the train positions have already been updated.

        Returns:
            None
        """
        for train, positions in self.train_positions.items():
            for position in positions:
                train_on_cell = self.get_cells_train(position[0], position[1])

                if train_on_cell is None:
                    continue

                if train_on_cell != train:
                    # print("💥 collision with another train")
                    train.state = self._TRAIN_CRASH_STATE
                    train_on_cell.state = self._TRAIN_CRASH_STATE
