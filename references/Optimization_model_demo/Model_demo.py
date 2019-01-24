from __future__ import division
from pyomo.environ import *

# set parameters
model = AbstractModel()
model.Facilities = Set()     # node 1...J
model.Customers = Set()      # node 1...I
model.Arcs = Set(dimen=2)     # Arcs (i,j)  connecting between customer i and warehouse j

model.demand = Param(model.Customers, mutable=True)
model.Cap = Param(model.Facilities, mutable=True)
#model.trans_cost = Param(model.Arcs, mutable=True)
model.trans_cost = Param(model.Customers, model.Facilities, mutable=True)
model.act_cost = Param(model.Facilities, mutable=True)



# set variables
model.x = Var(model.Arcs, domain=NonNegativeIntegers) #units flowing on arcs
model.y = Var(model.Facilities, within=Binary)  #whether to open facility


# set objective
def obj_expression(model):
    #minimize fixed activation cost and transportation cost
    return sum(model.act_cost[j]*model.y[j] for j in model.Facilities) + \
sum(model.trans_cost[i,j]*model.x[i,j] for i in model.Customers for j in model.Facilities)


model.OBJ = Objective(rule=obj_expression, sense=minimize)



#set constraints
def demand_constraint_rule(model, i):
    # ensure that number of package to each client meets the demand
    return model.demand[i] <= sum(model.x[i,j] for j in model.Facilities)

def capacity_constraint_rule(model, j):
    # the number of packages handeled at each facility does not exceed the capacity
    return sum(model.x[i,j] for i in model.Customers) \
        <= model.Cap[j]*model.y[j]

model.DemandConstraint = Constraint(model.Customers, rule=demand_constraint_rule)
model.CapacityConstraint = Constraint(model.Facilities, rule=capacity_constraint_rule)

