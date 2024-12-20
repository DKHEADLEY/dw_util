from dw_util.classes import Problem, DiscreteVariable
import random

khot_problem = Problem()

# n is the number of nodes
n = 2
# k is the number of colours
k = 5


for i in range(n):
    khot_problem.add_variable(DiscreteVariable(
            name=f'n{i}',
            domain= list(range(k)),
            encoding_type='domain-wall'
        )
    )


# Generate a random graph with edge probability 0.3
edge_probability = 1
edges = []
for i in range(n):
    for j in range(i+1, n):
        if random.random() < edge_probability:
            edges.append((i,j))

# For each edge, we add a penalty if the connected nodes have the same color
for (node1, node2) in edges:
    var1 = khot_problem.discrete_variables[node1]
    var2 = khot_problem.discrete_variables[node2]
    khot_problem.add_objective_term(var1 != var2)

# Assign random costs to each colour
costs = {i: random.random() for i in range(k)}
print({k: round(v, 2) for k, v in costs.items()})

for discrete_variable in khot_problem.discrete_variables:
    for binary_variable in discrete_variable.one_hot_variables:


khot_problem.compute_bqm()

