from abc import ABC, abstractmethod
from dimod import BQM

class AbstractVariable(ABC):
    def __init__(self, name: str, domain: list = None, extra_properties: dict = None):
        self.name = name
        self.domain = domain
        if extra_properties:
            for key, value in extra_properties.items():
                if hasattr(self, key):
                    raise AttributeError(f"Cannot add property '{key}' as it already exists on the object")
                setattr(self, key, value)

    def __str__(self):
        return f"{self.name}∈{self.domain}, {self.extra_properties if self.extra_properties else ''}"

    def __repr__(self):
        return self.__str__()

class AbstractTerm(ABC):
    def __init__(self, variables: list[AbstractVariable], coefficient: int, is_constraint: bool = False, description: str = None):
        self.variables = variables
        self.coefficient = coefficient
        self.is_constraint = is_constraint
        self.description = description

    @property
    @abstractmethod
    def value(self):
        pass

    @property
    @abstractmethod
    def BQM(self):
        pass

    def __str__(self):
        return self.description + f" | coeff: {self.coefficient} | vars: " + " | ".join([variable.name for variable in self.variables])

    def __repr__(self):
        return self.__str__()

class AbstractCollection(ABC):
    '''An abstract collection is a list of terms, metacatagory of terms'''
    def __init__(self, terms: list[AbstractTerm]):
        self.terms = terms

    @property
    def BQM(self):
        bqm = BQM(vartype='BINARY')
        for term in self.terms:
            bqm.update(term.BQM)
        return bqm

    @property
    def value(self):
        return sum([term.value for term in self.terms])

    def __str__(self):
        return "\n".join([f"{term.__str__()} (coeff: {term.coefficient})" for term in self.terms])

    def __repr__(self):
        return self.__str__()

