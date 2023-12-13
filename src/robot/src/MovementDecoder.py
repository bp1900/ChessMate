import numpy as np

class BoardPositions:
    def __init__(self, x0, y0, x7, y7):
        self.coordinates_x = np.linspace(x0, x7, 8)
        self.coordinates_y = np.linspace(y0, y7, 8)

    def get_coordinates(self, row, col):
        """
        Given a row and column, returns the physical x, y coordinates.
        """
        return [self.coordinates_x[row], self.coordinates_y[col]]

    def decode_move(self, uci_move):
        """
        Given a UCI format move, returns the physical x, y coordinates of the source and target.
        """
        col1, row1, col2, row2 = [str(uci_move)[i] for i in range(4)]
        col1_idx = ord(col1) - ord('a')
        row1_idx = ord(row1) - ord('1')
        col2_idx = ord(col2) - ord('a')
        row2_idx = ord(row2) - ord('1')

        source = self.get_coordinates(row1_idx, col1_idx)
        target = self.get_coordinates(row2_idx, col2_idx)

        print(f'Source: {source}', f'Target: {target}')
        return [source[0], source[1], target[0], target[1]]