import dimod


class Problem:
    def __init__(self, objective_BQM = None, constraint_BQM = None, integer_variables = [], ancillary_variables = []):
        self.integer_variables = integer_variables
        self.ancillary_variables = ancillary_variables
        self.objective_BQM = objective_BQM
        self.constraint_BQM = constraint_BQM


class IntegerVariable:
    '''
    A generic class representing an integer variable. This will contain the 
    shared attributes of the one-hot and domain wall implementations
    '''
    def __init__(self, name: str, domain: list = None, encoding_type: str = None):
        self.name = name
        self.domain = domain
        self.encoding_type = encoding_type
    
    @property
    def is_valid(self):
        raise NotImplementedError("Not yet implemented")
    
    def __str__(self):
        return self.name
        
    def __repr__(self):
        return self.__str__()

class BinaryVariable:
    def __init__(self, name: str):
        self.name = name
        self.domain = [0, 1]

    def __str__(self):
        return self.name
        
    def __repr__(self):
        return self.__str__()

if __name__ == "__main__":
    print("We are testing the codebase for a simple k-coloring problem")
    n = 4
    k = 3
    print(f"We are coloring {n} nodes with {k} colors")
    integer_variables = [IntegerVariable(name = f'node {i}', domain = [j for j in range(k)], encoding_type = "one-hot") for i in range(n)]
    print(integer_variables)
    for integer_variable in integer_variables:
        integer_variable.make_one_hot([[]])
    print("Now we define the binary variables for the one-hot encoding of the integer variables. Must correspond to the labeling of the BQM")
