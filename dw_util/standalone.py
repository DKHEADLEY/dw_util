import dimod

def substitute_bqm_variables(bqm: dimod.BinaryQuadraticModel, variable, linear_combination):
    linear_bias = bqm.linear[variable]
    quadratic = {k:v for k,v in bqm.quadratic.items() if variable in k} 
    bqm.remove_variable(variable)
    for var, new_bias in linear_combination.items():
        bqm.add_variable(var, new_bias * linear_bias)
        for (var1, var2), original_bias in quadratic.items():
            if var1 == variable:
                bqm.add_quadratic(var, var2, original_bias * new_bias)
            elif var2 == variable:
                bqm.add_quadratic(var1, var, original_bias * new_bias)
            else:
                bqm.add_quadratic(var1, var2, original_bias * new_bias)
    return bqm

