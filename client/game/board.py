from .ship import Ship, SHIPS

class Board:
    SIZE = 10

    def __init__(self):
        self.grid = [[None for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        self.ships = []
        self.shots = {}  # (row, col) -> "hit" | "miss"

    def reset(self):
        self.grid = [[None for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        self.ships = []
        self.shots = {}

    def place_ship(self, ship: Ship, row, col, horizontal=True):
        positions = []
        for i in range(ship.size):
            r = row if horizontal else row + i
            c = col + i if horizontal else col
            if not (0 <= r < self.SIZE and 0 <= c < self.SIZE):
                return False  # Tahta dışı
            if self.grid[r][c] is not None:
                return False  # Çakışma
            positions.append((r, c))

        ship.place(positions)
        for r, c in positions:
            self.grid[r][c] = ship
        self.ships.append(ship)
        return True

    def receive_shot(self, row, col):
        """
        Rakibin bize attığı atış.
        Returns: "hit", "miss", "sunk", "already_shot"
        """
        if (row, col) in self.shots:
            return "already_shot"

        ship = self.grid[row][col]
        if ship:
            ship.is_hit(row, col)
            if ship.is_sunk():
                self.shots[(row, col)] = "hit"
                return "sunk"
            self.shots[(row, col)] = "hit"
            return "hit"
        else:
            self.shots[(row, col)] = "miss"
            return "miss"

    def all_ships_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)

    def get_ships_data(self):
        """Gemi pozisyonlarını JSON'a uygun formata çevirir"""
        data = []
        for ship in self.ships:
            data.append({
                "name": ship.name,
                "size": ship.size,
                "positions": ship.positions
            })
        return data

    def load_ships_data(self, data):
        """Karşı tarafın gemi verilerini yükler (sadece sunucu mantığı için)"""
        self.reset()
        for s in data:
            ship = Ship(s["name"], s["size"])
            ship.place([tuple(p) for p in s["positions"]])
            for r, c in ship.positions:
                self.grid[r][c] = ship
            self.ships.append(ship)