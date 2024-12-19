from dw_util.classes import Problem, DiscreteVariable
import random

khot_problem = Problem()

# We are going to create a problem with 5 nodes and 3 colours
# This means there will be 5 discrete variables, each with a domain of [0, 1, 2]
k = 2
n = 2


for i in range(n):
    khot_problem.add_variable(DiscreteVariable(
            name=f'n{i}',
            domain= ['r', 'b'],
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
    
    # Add penalty term to objective - actual BQM construction will happen later
    # This just stores the variables that need to be constrained
    khot_problem.add_objective_term(var1 != var2)


print("objective terms:", khot_problem.objective_terms)
khot_problem.compute_bqm()

print(khot_problem.BQM)
# print('Problem:', khot_problem)
# print('Objective terms:', khot_problem.objective_terms)



# # Visualize the graph using networkx
# import networkx as nx
# import matplotlib.pyplot as plt

# G = nx.Graph()
# G.add_nodes_from(range(n))
# G.add_edges_from(edges)

# plt.figure(figsize=(8,6))
# pos = nx.spring_layout(G)
# nx.draw(G, pos, with_labels=True, node_color='lightblue', 
#         node_size=500, font_size=16, font_weight='bold')
# plt.title("Graph to be colored")
# plt.show()