import numpy as np


class MovementManager:
    def __init__(self):
        qs = np.zeros((5, 4, 6))
        qs[3,0] = [-0.46321038, -1.1664035, -1.89926729, -1.5566592, -4.78307482, 0.22392574] # Degrees transformed to radians
        # qs[3,1] = [-0.1527163, -0.93811447, -2.17363305, -1.4170328, -4.68114759, 6.1540309]
        qs[3,1] = [-0.1527163, -0.93811447, -2.17363305, -1.4170328, -4.68114759, 0.52656584]
        qs[3,2] = [0.57735492, -0.826937, -2.10155095, -1.78913702, -4.70174247, 0.52656584]
        qs[3,3] = [0.74892078, -0.826937, -2.16961879, -1.77046199, -4.60260777, 0.77562432]

        # qs[2,0] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 6.08177431]
        # qs[2,1] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 6.08177431]
        qs[2,0] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 0.3837979]
        qs[2,1] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 0.3837979]
        qs[2,2] = [0.39566614, -1.4749778, -1.5100589, -1.7442821, -4.71291258, 0.3837979]
        qs[2,3] = [0.39566614, -1.4749778, -1.5100589, -1.7442821, -4.71291258, 0.3837979]

        # qs[1,0] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 6.08177431]
        # qs[1,1] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 6.08177431]
        qs[1,0] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 0.3837979]
        qs[1,1] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 0.3837979]
        qs[1,2] = [0.39566614, -1.4749778, -1.5100589, -1.7442821, -4.71291258, 0.3837979]
        qs[1,3] = [0.39566614, -1.4749778, -1.5100589, -1.7442821, -4.71291258, 0.3837979]

        #qs[0,0] = [-0.31346113, -1.83207212, -1.5823155, -0.95207711, -4.59998978, 5.92644001]
        #qs[0,1] = [-0.07766715, -1.651256, -1.80554311, -0.89483031, -4.66770855, 6.1540309]
        qs[0,0] = [-0.31346113, -1.83207212, -1.5823155, -0.95207711, -4.59998978, 0.397586]
        qs[0,1] = [-0.07766715, -1.651256, -1.80554311, -0.89483031, -4.66770855, 0.1286308]
        qs[0,2] = [0.19757127, -1.5222762, -1.93661734, -0.89430671, -4.76492339, 0.1286308]
        qs[0,3] = [0.48205994, -1.471138, -1.97222, -0.93741634, -4.8614401, 0.397586]

        # SPECIAL: TORRES
        """
        3_0 = [-17.71, -101.70, -85.72, -101.36, -278.15, 150.25]
        3_1 = [-1.79, -89.63, -98.61, -101.97, -272.82, 165.36]
        3_2 = [15.09, -82.56, -105.15, -102.44, -266.95, 181.22]
        3_3 = [37.34, -78.27, -109.59, -99.73, -25967, 202.42]
        """
        qs[4,0] = [-0.3090978105, -1.7749998493, -1.496096234, -1.7690657298, -4.8546333144, 2.6223572011]
        qs[4,1] = [-0.0312413936, -1.5643386086, -1.7210691754, -1.7797122383, -4.7616072653, 2.8860764511]
        qs[4,2] = [0.2633701841, -1.4409438304, -1.8352137085, -1.7879152857, -4.6591564382, 3.1628856705]
        qs[4,3] = [0.6517059427, -1.3660692055, -1.9127063273, -1.740616863, -4.5320964687, 3.5328954719]

        self.qs = qs
        # self.qs_all_column = qs_all_column

        orients = np.zeros((5, 4, 3)) # RX, RY, RZ
        # orients[3,0] = [2.323, -2.313, 0.390]
        orients[3,0] = [2.202, -2.246, 0.033]
        orients[3,1] = [2.287, -2.334, 0.209]
        orients[3,2] = [2.274, -2.161, -0.017]
        # orients[3,3] = [2.147, -2.212, -0.169]
        orients[3,3] = [2.161, -2.284, -0.035]

        orients[2,0] = [2.220, -2.197, -0.009]
        orients[2,1] = [2.220, -2.197, -0.009]
        orients[2,2] = [2.220, -2.197, -0.009]
        orients[2,3] = [2.220, -2.197, -0.009]

        orients[1,0] = [2.220, -2.197, -0.009]
        orients[1,1] = [2.220, -2.197, -0.009]
        orients[1,2] = [2.220, -2.197, -0.009]
        orients[1,3] = [2.220, -2.197, -0.009]

        # orients[0,0] = [2.449, -2.308, 0.445]
        orients[0,0] = [2.337, -2.248, 0.171]
        # orients[0,1] = [2.449, -2.308, 0.445]
        # orients[0,2] = [2.449, -2.308, 0.445]

        orients[0,1] = [2.337, -2.248, 0.171]
        orients[0,2] = [2.337, -2.248, 0.171]

        # orients[0,3] = [2.449, -2.308, 0.445]
        orients[0,3] = [2.337, -2.248, 0.171]


        # SPECIAL: TORRES
        """
        orients_torres = [2.096, 2.639, -0.423]
        """
        # orients_all_column = [2.096, 2.639, -0.423]
        orients[4,0] = [2.096, 2.639, -0.423]
        orients[4,1] = [2.096, 2.639, -0.423]
        orients[4,2] = [2.096, 2.639, -0.423]
        orients[4,3] = [2.096, 2.639, -0.423]

        self.orients = orients

    def qs_orient_position(self, movement):

        col_init, row_init, col_final, row_final = split_coord2(movement)

        print(col_init, row_init, col_final, row_final)

        quadrant_init = [row_init // 2, col_init // 2]
        quadrant_final = [row_final // 2, col_final // 2]

        if (quadrant_init[0] == 0 and quadrant_final[0] == 3):
            quadrant_final[0] = 4       # quadrant_init[0]
        elif (quadrant_init[0] == 3 and quadrant_final[0] == 0):
            quadrant_init[0] = 4        # quadrant_final[0]

        print(quadrant_init)
        print(quadrant_final)

        q_init = self.qs[quadrant_init[0], quadrant_init[1]]
        q_final = self.qs[quadrant_final[0], quadrant_final[1]]

        orient_init = self.orients[quadrant_init[0], quadrant_init[1]]
        orient_final = self.orients[quadrant_final[0], quadrant_final[1]]

        print(q_init, q_final, orient_init, orient_final)

        return list(q_init), list(q_final), list(orient_init), list(orient_final)

    def winning_orientation_position(self, movement):
        col_init, row_init, col_final, row_final = split_coord2(movement)
        print(col_init, row_init, col_final, row_final)

        quadrant_init = [row_init // 2, col_init // 2]
        quadrant_final = [row_final // 2, col_final // 2]

        print(quadrant_init)
        print(quadrant_final)

        if (quadrant_init[0] == 0 or quadrant_init[0] == 3) and (quadrant_final[0] > 0 and quadrant_final[0] < 3):
            quadrant_final[0] = quadrant_init[0]
            quadrant_final[1] = quadrant_init[1]

        elif (quadrant_init[0] > 0 and quadrant_init[0] < 3) and (quadrant_final[0] == 0 or quadrant_final[0] == 3):
            quadrant_init[0] = quadrant_final[0]
            quadrant_init[1] = quadrant_final[1]

        # Change in "qs_orient_position"
        # elif (quadrant_init[0] == 0 and quadrant_final[0] == 3):
        #     quadrant_final[0] = 4       # quadrant_init[0]
        
        # elif (quadrant_init[0] == 3 and quadrant_final[0] == 0):
        #     quadrant_init[0] = 4        # quadrant_final[0]

        orient_init = self.orients[quadrant_init[0], quadrant_init[1]]
        orient_final = self.orients[quadrant_final[0], quadrant_final[1]]

        print(f'Orirnt_ini: {orient_init}')
        print(f'Orient_fi: {orient_final}')

        print(f'Winning orientation: {quadrant_init[0]}, {quadrant_init[1]}, {quadrant_final[0]}, {quadrant_final[1]} ')
        return orient_init, orient_final

def orientation_position(row_init, row_final):

    if row_init in {'1', '2'} and row_final in {'3', '4', '5', '6'}:
        row_final = row_init
    
    if row_final in {'1', '2'} and row_init in {'3', '4', '5', '6'}:
        row_init = row_final

    if row_init in {'7', '8'} and row_final in {'3', '4', '5', '6'}:
        row_final = row_init
    
    if row_final in {'7', '8'} and row_init in {'3', '4', '5', '6'}:
        row_init = row_final

    orientations = []
    for row in [row_init, row_final]:

        if row == '1' or row == '2':
            orientation = [2.326, -2.314, 0.407]

        elif row == '7' or row == '8':
            orientation = [2.115, -1.977, -0.481]

        else:
            orientation = [2.220321396090, -2.197400976034, -0.008928417774]

        orientations.append(orientation)

    return orientations


# Conversion rows and columns
conversion_table_columns = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
conversion_table_rows = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7}

# Function for splitting string into individual list elements (ie: 0153 -> ['0','1','5','3'])
def split(word):
    return [char for char in word]

def split_coord(word):
    str_list = [char for char in word]
    
    final_movement = []
    for element in str_list:
        if element.isalpha():
            element = conversion_table_columns[element]
        else:
            element = conversion_table_rows[element]
        final_movement.append(int(element))

    return final_movement

def split_coord2(word):
    col1, row1, col2, row2 = [str(word)[i] for i in range(4)]
    col1_idx = ord(col1) - ord('a')
    row1_idx = ord(row1) - ord('1')
    col2_idx = ord(col2) - ord('a')
    row2_idx = ord(row2) - ord('1')

    return [col1_idx, row1_idx, col2_idx, row2_idx]



def decode_movement(movement, cb):
    print(movement)
    str_list = split(movement)
    str_list = str_list[:-1]

    print(f'Str list: {str_list}')
    final_movement = []

    for element in str_list:
        if element.isalpha():
            element = conversion_table_columns[element]
        else:
            element = conversion_table_rows[element]
        final_movement.append(int(element))

    print(f'Final movement: {final_movement}')

    x = cb.move(final_movement[1], final_movement[0], final_movement[3], final_movement[2])
    x = x[1:-1].split(',')
    vals = []
    for val in x:
        vals.append(float(val))

    return vals