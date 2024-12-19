from dimod import BinaryQuadraticModel as BQM
from itertools import combinations as comb
from dw_util.abstract import AbstractVariable, AbstractTerm, AbstractCollection
from dw_util.standalone import substitute_bqm_variables


class Problem:
    def __init__(self, discrete_variables = [], ancillary_variables = []):
        self.discrete_variables = discrete_variables
        self.ancillary_variables = ancillary_variables
        self.objective_terms = []
        self.constraint_terms = []
        self._objective_bqm = BQM(vartype='BINARY')
        self._constraint_bqm = BQM(vartype='BINARY')
        self._BQM = None

        self.penalty_weight = 1

    @property
    def active_binary_variables(self):
        return [binary_variable
                for discrete_variable in self.discrete_variables
                for binary_variable in discrete_variable.binary_variables
                if not binary_variable.virtual
                ]

    @property
    def objective_bqm(self):
        return self._objective_bqm

    def compute_objective_bqm(self):
        self._objective_bqm = BQM(vartype='BINARY')
        for objective_term in self.objective_terms:
            self._objective_bqm.update(objective_term.BQM)

    @property
    def constraint_bqm(self):
        return self._constraint_bqm

    def compute_constraint_bqm(self):
        self._constraint_bqm = BQM(vartype='BINARY')
        for variable in self.discrete_variables:
            self._constraint_bqm.update(variable.BQM)
        for constraint_term in self.constraint_terms:
            self._constraint_bqm.update(constraint_term.BQM)

    def substitute_domain_wall_variables(self):
        for variable in self.discrete_variables:
            if variable.encoding_type == "domain-wall":
                for binary_variable in variable.one_hot_variable_list:
                    left, right = binary_variable.dw_neigbours
                    self._BQM = substitute_bqm_variables(
                        self._BQM, 
                        binary_variable,
                        {left: -1, right: 1}
                    )
        
    def fix_ends(self):
        for variable in self.discrete_variables:
            if variable.encoding_type == "domain-wall":
                start = variable.domain_wall_variable_list[0]
                end = variable.domain_wall_variable_list[-1]
                assert 'start' in start.name and 'end' in end.name, "The start and end variables are not the first and last in the domain wall variable list, something has gone wrong"
                self._BQM.fix_variable(start, 0)
                self._BQM.fix_variable(end, 1)

    def kill_impossible_terms(self):
        """
        If the variable penalties are satisfied, these evaluate to zero anyway and can be removed
        """
        for discrete_variable in self.discrete_variables:
            for b1, b2 in comb(discrete_variable.one_hot_variable_list, 2):
                if self._objective_bqm.get_quadratic(b1, b2, default=0) != 0:
                    self._objective_bqm.remove_interaction(b1, b2)

    def compute_bqm(self):
        self.compute_objective_bqm()
        self.compute_constraint_bqm()
        self.kill_impossible_terms()
        self._BQM = self._objective_bqm 
        + self.penalty_weight * self._constraint_bqm
        self.substitute_domain_wall_variables()
        self.fix_ends()
        self.verify_bqm()

    def verify_bqm(self):
        # Check that all variables in both BQMs are in active_binary_variables
        bqm_vars = self.BQM.variables
        invalid_vars = bqm_vars - self.active_binary_variables
        assert not invalid_vars, f"Found variables in BQMs that are not in active_binary_variables:\nBQM: {invalid_vars}"

    @property
    def BQM(self):
        return self._BQM

    def add_variable(self, variable: 'DiscreteVariable'):
        self.discrete_variables.append(variable)

    def add_objective_term(self, term):
        self.objective_terms.append(term)

    def add_constraint_term(self, term):
        self.constraint_terms.append(term)

    def __repr__(self):
        variables_str = "\n".join(
            [f"{var.name} taking values in {var.domain}" for var in self.discrete_variables]
        )
        return f"Problem(\n{variables_str}\n)"

class ConstantTerm(AbstractTerm):
    """an object representing a constant term in the objective function"""
    def __init__(self, coefficient: int = 1, description: str = "constant"):
        super().__init__([], coefficient, description=description)

    @property
    def value(self):
        return self.coefficient

    @property
    def satisfied(self):
        """a constant term is always satisfied"""
        return True

    @property
    def BQM(self):
        bqm = BQM(vartype='BINARY')
        bqm.offset += self.coefficient
        return bqm
        
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return ConstantTerm(
                self.coefficient * other,
                description=f"{self.description} * {other}"
            )
        elif isinstance(other, ConstantTerm):
            return ConstantTerm(
                self.coefficient * other.coefficient,
                description=f"{self.description} * {other.description}"
            )
        elif isinstance(other, BinaryLinearTerm):
            return BinaryLinearTerm(
                other.variables, 
                self.coefficient * other.coefficient,
                description=f"{self.description} * {other.description}"
            )
        else:
            return NotImplemented

class BinaryLinearTerm(AbstractTerm):
    """an object representing a binary variable multiplied by a coefficient"""
    def __init__(self, variables: list['BinaryVariable'], coefficient: int = 1, description: str = "binary linear"):
        super().__init__(variables, coefficient, description=description)
        assert len(variables) == 1, "BinaryLinearTerm must have a single variable"

    @property
    def satisfied(self):
        '''Only really makes sense to say that this is satisfied if variable is binary, in which case the sign of the coefficient is irrelevant'''
        return NotImplementedError("Not yet implemented")

    @property
    def value(self):
        return self.coefficient * self.variables[0].value

    @property
    def BQM(self):
        bqm = BQM(vartype='BINARY')
        bqm.add_variable(self.variables[0])
        bqm.add_linear(self.variables[0], self.coefficient)
        return bqm

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return BinaryLinearTerm(self.variables, self.coefficient * other)
        elif isinstance(other, ConstantTerm):
            return BinaryLinearTerm(self.variables, self.coefficient * other.coefficient)
        elif isinstance(other, BinaryLinearTerm):
            if other != self:   
                return BinaryQuadraticTerm(self.variables + other.variables, self.coefficient * other.coefficient)
            else:
                return BinaryLinearTerm(self.variables, self.coefficient ** 2)
        else:
            return NotImplemented

class BinaryQuadraticTerm(AbstractTerm):
    def __init__(self, variables: list['BinaryVariable'], coefficient: int = 1, description: str = "quadratic"):
        super().__init__(variables, coefficient, description=description)
        assert len(variables) == 2, "BinaryQuadraticTerm must have exactly 2 variables"

    @property
    def satisfied(self):
        NotImplementedError("Not yet implemented")

    @property
    def value(self):
        return self.coefficient * self.variables[0].value * self.variables[1].value

    @property
    def BQM(self):
        bqm = BQM(vartype='BINARY')
        bqm.add_variable(self.variables[0])
        bqm.add_variable(self.variables[1])
        bqm.add_quadratic(self.variables[0], self.variables[1], self.coefficient)
        return bqm

    def __mul__(self, other):
        if isinstance(other, (int, float, ConstantTerm)):
            return BinaryQuadraticTerm(self.variables, self.coefficient * other)
        else:
            return NotImplemented

class Collection(AbstractCollection):
    def __init__(self, terms: list[AbstractTerm]):
        super().__init__(terms)

    def __pow__(self, power: int):
        assert power == 2, "Only power of 2 is supported"
        new_terms = []
        for term1 in self.terms:
            for term2 in self.terms:
                new_terms.append(term1 * term2)
        return Collection(new_terms)   
       
class NotEqualTerm(AbstractTerm):
    """A term in the objective function that takes the value of the coefficient if the two variables are not equal, 0 otherwise"""
    def __init__(self, variables: list[AbstractVariable], coefficient: int = 1, description: str = "not equal"):
        super().__init__(variables, coefficient, is_constraint=True, description=description)
        assert len(variables) == 2, "NotEqualTerm must have exactly 2 variables"


        ### If two binary variables represent their parent variables having the same value, we need to enforce that they cannot both be 1
        self._sub_terms = [BinaryQuadraticTerm([v1, v2], coefficient)
                          for v1 in variables[0].one_hot_variable_list
                          for v2 in variables[1].one_hot_variable_list
                          if v1.represents == v2.represents
                          ]


    @property
    def value(self):
        return self.coefficient * (self.variables[0].value != self.variables[1].value)

    @property
    def BQM(self):
        return sum([sub_term.BQM for sub_term in self._sub_terms])

    def __str__(self):
        return f"{self.variables[0].name} != {self.variables[1].name}"
    
    def __repr__(self):
        return self.__str__()

class OneHotConstraint(AbstractTerm):
    """A constraint that is satisfied if the variables are one hot encoded"""
    def __init__(self, discrete_variable: 'DiscreteVariable', description: str = "one-hot"):
        super().__init__(discrete_variable.binary_variables, 1, is_constraint=True, description=description)
        self.discrete_variable = discrete_variable
        linear_terms = [BinaryLinearTerm([binary_variable]) for binary_variable in discrete_variable.binary_variables] + [ConstantTerm(-1)]
        self.collection = Collection(linear_terms) ** 2
    @property
    def satisfied(self):
        return self.collection.value == 0

    @property
    def value(self):
        return self.collection.value

    @property
    def BQM(self):
        return self.collection.BQM

class DomainWallConstraint(AbstractTerm):
    """A constraint that is satisfied if the variables are domain wall encoded"""
    def __init__(self, discrete_variable: 'DiscreteVariable', description: str = "domain wall"):
        super().__init__(discrete_variable.binary_variables, 1, is_constraint=True, description=description)
        self.discrete_variable = discrete_variable
        self.sub_constraints = [
            Forbid10Constraint(discrete_variable.domain_wall_variable_list[i:i+2])
            for i in range(len(discrete_variable.domain_wall_variable_list) - 1)
        ]

    @property
    def BQM(self):
        return sum([sub_constraint.BQM for sub_constraint in self.sub_constraints])

    @property
    def value(self):
        return sum([sub_constraint.value for sub_constraint in self.sub_constraints])

    @property
    def satisfied(self):
        return self.value == 0
    
class Forbid10Constraint(AbstractTerm):
    """A constraint that is 1 if the variables are not 1 and 0, 0 otherwise"""
    def __init__(self, variables: list[AbstractVariable], description: str = "forbid 10"):
        super().__init__(variables, 1, is_constraint=True, description=description)
        
        assert len(variables) == 2, "Forbid10Constraint must have exactly 2 variables"
        assert isinstance(variables[0], BinaryVariable) and isinstance(variables[1], BinaryVariable), "Forbid10Constraint variables must be BinaryVariable"
    
    @property
    def satisfied(self):
        if self.variables[0].value == 1 and self.variables[1].value == 0:
            return False
        else:
            return True

    @property
    def value(self):
        return self.coefficient * (self.satisfied)

    @property
    def BQM(self):
        bqm = BQM(vartype='BINARY')
        bqm.add_variable(self.variables[0])
        bqm.add_variable(self.variables[1])
        bqm.add_linear(self.variables[0], 1)
        bqm.add_quadratic(self.variables[0], self.variables[1], -1)
        return bqm

class DiscreteVariable(AbstractVariable):
    '''
    A generic class representing an integer variable. This will contain the 
    shared attributes of the one-hot and domain wall implementations
    '''
    def __init__(self, name: str, domain: list = None, encoding_type: str = None, extra_properties: dict = None):
        super().__init__(name, domain, extra_properties)
        self.encoding_type = encoding_type
        self.constraint_list = []
        
        ### Make the binary variables ###
        if encoding_type == "one-hot":
            self.one_hot_variable_list = [
                BinaryVariable(
                    name=f"{self.name} is {value}", 
                    parent_variable=self, 
                    represents=value
                ) 
                for value in self.domain
            ]
            
        if encoding_type == "domain-wall":
            self.domain_wall_variable_list = []
            self.permute_domain()
            extended_domain = ['start'] + self.domain + ['end']
            for i, value in enumerate(extended_domain[:-1]):
                self.domain_wall_variable_list.append(
                    BinaryVariable(
                        name=f"{self.name} dw[{extended_domain[i]}, {extended_domain[i+1]}]", 
                        parent_variable=self,
                        virtual=True if any(x in ['start', 'end'] for x in extended_domain[i:i+2]) else False
                    ) 
                )
            ### Now we make one hot variables linked to the domain wall variables ###
            self.one_hot_variable_list = []
            for i, value in enumerate(self.domain):
                self.one_hot_variable_list.append(
                    BinaryVariable(
                        name=f"{self.name}={value}", 
                        parent_variable=self, 
                        represents=value,
                        extra_properties={'dw_neigbours': self.domain_wall_variable_list[i:i+2]}
                    ) 
                )
            self.virtual_variable_list = self.domain_wall_variable_list[1:-1]
        
        ### Make the constraint list ###
        if encoding_type == "one-hot": self.constraint_list.append(OneHotConstraint(self))
        elif encoding_type == "domain-wall": self.constraint_list.append(DomainWallConstraint(self))


    def permute_domain(self):
        pass

    @property
    def binary_variables(self):
        if self.encoding_type == "one-hot":
            return self.one_hot_variable_list
        elif self.encoding_type == "domain-wall":
            return self.domain_wall_variable_list
        else:
            raise ValueError(f"No binary variables created for {self.name}")

    @property
    def value(self):
        '''The value that the variable is currently set to, depending on the encoding'''
        if self.encoding_type == "one-hot" and self.is_valid:
            return self.get_one_hot_value()
        elif self.encoding_type == "domain-wall" and self.is_valid:
            return self.get_domain_wall_value()
        else:
            return "Invalid"
    
    @property
    def BQM(self):
        return sum([constraint.BQM for constraint in self.constraint_list])


    @property
    def is_valid(self):
        raise NotImplementedError("Not yet implemented")
    
    def __str__(self):
        return f"{self.name}∈{self.domain}"
        
    def __repr__(self):
        return self.__str__()

    def __ne__(self, other):
        return NotEqualTerm([self, other], 1)

class BinaryVariable(AbstractVariable):
    def __init__(self, name: str, represents = None, parent_variable = None, virtual = False, extra_properties: dict = None):
        super().__init__(name, domain = [0, 1], extra_properties=extra_properties)
        self._value = None
        self.represents = represents
        self.parent_variable = parent_variable
        self.virtual = virtual

    @property   
    def value(self):
        return self._value

    @value.setter
    def value(self, value: int):
        if value not in self.domain:
            raise ValueError(f"Value {value} is not in the domain {self.domain}")
        self._value = value

    def __str__(self):
        return f'{self.name}'
        
    def __repr__(self):
        return self.__str__()
