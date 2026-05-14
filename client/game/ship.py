class Ship:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.positions = []  # [(row, col), ...]
        self.hits = set()

    def place(self, positions):
        self.positions = positions
        self.hits = set()

    def is_hit(self, row, col):
        if (row, col) in self.positions:
            self.hits.add((row, col))
            return True
        return False

    def is_sunk(self):
        return len(self.hits) == len(self.positions)

    def __repr__(self):
        return f"{self.name}(size={self.size}, sunk={self.is_sunk()})"


# Amiral Battı standart gemi seti
SHIPS = [
    {"name": "Uçak Gemisi", "size": 5},
    {"name": "Zırhlı",      "size": 4},
    {"name": "Kruvazör",    "size": 3},
    {"name": "Destroyer",   "size": 3},
    {"name": "Denizaltı",   "size": 2},
]