

# Import of the pyomo module
from __future__ import division
from pyomo.environ import *
# Creation of a Concrete Model
model = AbstractModel()


# ## Declare Constant

# In[204]:


# declare constant
M=100000000
model.Max_Capital_Cost=Param(within=NonNegativeReals)
model.Mile_Cost=Param(within=NonNegativeReals)
model.Truck_Size=Param(within=NonNegativeReals)
###need input
model.Load_Cost=Param(within=NonNegativeReals)
###need input
model.Unload_Cost=Param(within=NonNegativeReals)
model.Hops=Param(within=NonNegativeIntegers)
model.Fixed_Trucks_Cost=Param(within=NonNegativeReals)




# ## Declare Set

# In[205]:


# declare set
## Define sets ##
#  Sets
#       L   All location   / Syracuse, NY, Buffalo, Elizabeth, Ithaca /
#       I   Customer warehouse          / Syracuse / ;
#       J   PB facility   /  NY, Buffalo, Elizabeth /
#       K   USPS or Courier hubs          / Ithaca / ;
#       I   Customer warehouse          / Syracuse / ;
#       h   hops day  /  0,1,2 / ;
#       S   PB facility sizes         / small, medium, large / ;
#       T   PB facility types   /  deliver, return, both / ;
#       F   PB facility features         / ingest, both / ;
def counthops (model):
    return(i for i in range(0,model.Hops+1))
model.H=Set(initialize=counthops)
def counthops1 (model):
    return(i for i in range(1,model.Hops+1))
model.H1=Set(initialize=counthops1)

model.MaxH=Set()
model.L=Set()
model.I=Set()
model.J=Set()
model.K=Set()
model.S=Set()
model.T=Set()
model.F=Set()


# ## Declare Parameters

# In[206]:


## Define parameters ##
#   Parameters
#       capacity(j,s,t,f)  amount of capital needed to build a hub at location J, size S, type T, feature F;
#       utility(j,s,t,f) Operating cost for a hub;
#       distance(l,l') distance between location l and location l';
#       hub_capacity(s) hub capacity of different size;
#       deliver(i,k)  the number of deliver packages from i to k;
#       repackage(k,i)  the number of return packages from k to i;
#       sorting(j)      the sorting cost in location j

model.capital = Param(model.J,model.S)

model.utility = Param(model.J,model.S)

model.distance = Param(model.L,model.L, initialize = 0)

model.hub_capacity=Param(model.S)

model.package = Param(model.I|model.K,model.I|model.K, initialize = 0)

model.sorting = Param(model.J)

def max_trans_cost_init(model,l,l1):
    return max(model.Fixed_Trucks_Cost, model.distance[l,l1]*model.Mile_Cost)
model.max_trans_cost = Param(model.L,model.L,initialize = max_trans_cost_init)





# ## Declare Variable

# In[207]:


## Define variables ##
#  Variables
#       y(j,s,t,f)  Binary variable indicates whether to open a facility
#       truck(l,l)       the number of truck from l to l ;
#       n(l,l',l'',h)   the number of packages at current location l 
                     #going to location l' next, with a final destination of l'' and h hops left.
model.y=Var(model.J,model.S,model.T,model.F, within=Binary)
model.truck=Var(model.L,model.L, within=NonNegativeIntegers)
def n_index_init(model):
    n_init=[]
    for l1 in model.L:
        for l2 in model.L:
            for l3 in model.I|model.K:
                for h in model.H:
                    if l1==l2:
                        continue
                    if l1 in model.I and l3 in model.I:
                        continue
                    if l1 in model.K and l3 in model.K:
                        continue
                    if l1 in model.I|model.K and l2 not in model.J:
                        continue
                    if l2 in model.I|model.K and l2!=l3:
                        continue
                    if l1 in model.I and l3 in model.K:
                        if model.package[l1,l3]==0:
                            continue
                    n_init.append((l1,l2,l3,h))

    return n_init
#     
#model.n_index = Set(initialize = [(l1,l2,l3,h) for l1 in model.L for l2 in model.L for l3 in model.I|model.K for h in model.H if l1!=l2 and ])
model.n_index=Set(initialize = n_index_init,dimen = 4)
model.n=Var(model.n_index, within=NonNegativeReals)


# ## Objective Function


# operations cost + transportation cost
#(2)
#(3)
#(4)
def obj_expression(model):
    utility_cost=sum((model.utility[j,s] * model.y[j,s,t,f]) for j in model.J for s in model.S for t in model.T for f in model.F)
    loading_cost=sum((model.Load_Cost * model.n[j,l,l1,h]) for j in model.J for l in model.L for l1 in (model.I|model.K) for h in model.H if (j,l,l1,h) in model.n_index)
    unloading_cost=sum((model.Unload_Cost * model.n[l,j,l1,h]) for l in model.L for j in model.J for l1 in (model.I|model.K) for h in model.H if (l,j,l1,h) in model.n_index) 
    sorting_cost=sum((model.sorting[j] * model.n[j,k,k,h]) for j in model.J for k in model.K for h in model.H if (j,k,k,h) in model.n_index) 
    transportation_cost=sum(model.max_trans_cost[l,l1] * model.truck[l,l1] for l in model.L for l1 in model.L) #(3)
    return utility_cost + loading_cost + unloading_cost + sorting_cost + transportation_cost
model.OBJ = Objective(rule=obj_expression, sense = minimize, doc='Define objective function')


# ## Constraints


# Define contrains ##
# capital_constrains   the sum of the capital cost

# #(1)
def capital_constraints(model):
    return (sum(model.capital[j,s]*sum(model.y[j,s,t,f] for t in model.T for f in model.F)for j in model.J for s in model.S)<=model.Max_Capital_Cost)
model.max_cap = Constraint(rule = capital_constraints, doc = "max capital constraint")

def existing_facility_elizabeth_rule(model):
        return(model.y['F101','large','deliver','both']==1)
model.existing_facility = Constraint(rule = existing_facility_elizabeth_rule)

def existing_facility_york_rule(model):
        return(model.y['F102','large','both','both']==1)
model.existing_facility_york = Constraint(rule = existing_facility_york_rule)
def existing_facility_shelton_rule(model):
        return(model.y['F103','large','both','both']==1)
model.existing_facility_shelton = Constraint(rule = existing_facility_shelton_rule)
def fix_facility_rule(model):
        return(sum(model.y['F104',s,t,f]for s in model.S for t in model.T for f in model.F)==1)
model.fix_facility = Constraint(rule = fix_facility_rule)
###5)
def truck_size_constraints(model,l,l1):
    return(sum(model.n[l,l1,l2,h] for l2 in (model.I|model.K) for h in model.H if (l,l1,l2,h) in model.n_index)<=model.Truck_Size*model.truck[l,l1])
model.truck_size_con = Constraint(model.L,model.L,rule = truck_size_constraints, doc = "truck size constraint")

# # #(6)
def inbound_equal_rule(model,j, h, l1):
      return (sum(model.n[l,j,l1,h] for l in model.L if (l,j,l1,h) in model.n_index)
          == sum(model.n[j,l2,l1,h-1] for l2 in model.L if (j,l2,l1,h-1) in model.n_index))
model.inbound_equal = Constraint(model.J,model.H1,model.I|model.K, rule = inbound_equal_rule, doc = "inbound package equal")



# #(7)
# #2nd demand contransts
def initialization_demand_rule(model,l,l1,h):
    if model.package[l,l1]!= 0:
        return (sum(model.n[l,j,l1,h] for j in model.J if (l,j,l1,h) in model.n_index) == model.package[l,l1])
    else:
        return Constraint.Skip
model.initialization_demand = Constraint(model.I|model.K,model.I|model.K,model.MaxH,rule = initialization_demand_rule)



# # #(8)
def destination_demand_rule(model, l):
    return (sum(model.n[j,l,l,h] for j in model.J for h in model.H if (j,l,l,h) in model.n_index) == sum(model.package[l1,l] for l1 in model.I|model.K))
model.destination_demand = Constraint(model.I|model.K, rule=destination_demand_rule)


def total_package_equal_rule(model):
    return (sum(model.n[j,l1,l1,h] for j in model.J for l1 in model.I|model.K for h in model.H if (j,l1,l1,h) in model.n_index) == sum(model.package[l2,l1] for l2 in model.I|model.K for l1 in model.I|model.K))
model.total_package_equal_rule = Constraint(rule=total_package_equal_rule)


# # #(9)
def num_of_hubs_opened_perlocation(model,j):
    return(sum(model.y[j,s,t,f] for s in model.S for t in model.T for f in model.F)<=1)
model.num=Constraint(model.J,rule=num_of_hubs_opened_perlocation,doc="constraint on num of hubs opened per location")



# # #(10)
def delivery_hub_rule(model,j,k,l):
    return (sum(model.n[l,j,k,h] for h in model.H if (l,j,k,h) in model.n_index)
           <= (M * sum(model.y[j,s,'deliver',f]+model.y[j,s,'both',f] for s in model.S for f in model.F)))
model.delivery_hub = Constraint(model.J,model.K,model.I|model.J, rule = delivery_hub_rule, doc = "ensure delivery packages handled by delivery hub")



# # #(11)
def delivery_sort_hub_rule(model,j,k):
    return (sum(model.n[j,k,k,h] for h in model.H if (j,k,k,h) in model.n_index)
           <= (M * sum(model.y[j,s,'deliver','both']+model.y[j,s,'both','both'] for s in model.S)))
model.delivery_sort_hub = Constraint(model.J,model.K, rule = delivery_sort_hub_rule, doc = "ensure last delivery packages handled by sort-delivery hub")




# #(12)
def return_hub_rule(model,i,j,k,l):
    return (sum(model.n[l,j,i,h] for h in model.H if (l,j,i,h) in model.n_index)
           <= (M * sum(model.y[j,s,'return',f]+model.y[j,s,'both',f] for s in model.S for f in model.F)))
model.return_hub = Constraint(model.I,model.J,model.K,model.L, rule = return_hub_rule, doc = "ensure return packages handled by return hub")



# # #(13)
def hub_capacity_constraint(model,j):
    return sum(model.n[l,j,l1,h] for l in model.L for l1 in (model.I|model.K) for h in model.H if (l,j,l1,h) in model.n_index)<=sum(model.hub_capacity[s]*model.y[j,s,t,f] for s in model.S for t in model.T for f in model.F)
model.hub_capacity_constraint=Constraint(model.J, rule=hub_capacity_constraint,doc="hub capacity constraint")

# #(14)constraints : 
# def initial_destination_demand_rule(model,l,l1,h):
#     return(model.n[l,l,l1,h]==0)
# model.initial_destination_demand = Constraint(model.L,model.I|model.K,model.H, rule=initial_destination_demand_rule, doc="current location is origin and next location is destination = 0")


#(15) constraint : if next location is a set of I or K but does not match the final destination,then it must be 0.
# def destination_zero_demand_rule(model,j,l,l1,h):
#     if (j,l,l1,h) in model.n_index:
#         if l!=l1:
#             return(model.n[j,l,l1,h]==0)
#         else:
#             return(model.n[j,l,l1,h]>=0)
# model.destination_zero_demand= Constraint(model.J,model.I|model.K,model.I|model.K,model.H, rule=destination_zero_demand_rule, doc="destination zero demand")
# # #(16) constraint : if there is a package delivery from initial location l to final destination l1.
# def no_package_rule(model,l,l2):
#     if model.package(l,l2) == 0:
#         return(sum(model.n[l,l1,l2,h]for l1 in model.L for h in model.H)==0)
#     else:
#         return(sum(model.n[l,l1,l2,h]for l1 in model.L for h in model.H)>=0)
# model.no_package = Constraint(model.I|model.K,model.I|model.K,rule = no_package_rule, doc = "number of packages from l to l2")
#(17) constraint : the number of packages at initial_location of set Is to final destination of set Is should be 0.
# def initial_location_destination_i_rule(model,i,j,i1,h):
#     return(model.n[i,j,i1,h]==0)
# model.initial_location_destination_i = Constraint(model.I,model.J,model.I,model.H, rule = initial_location_destination_i_rule, doc="number of packages at initial_location i to final destination i should be 0")

# #(18) (maybe not with constraint 17) constraint : the number of packages at initial_location of set K to final destination of set K should be 0.
# def initial_location_destination_k_rule(model,k,j,k1,h):
#     return(model.n[k,j,k1,h]==0)
# model.initial_location_destination_k = Constraint(model.K,model.J,model.K,model.H, rule = initial_location_destination_k_rule, doc="number of packages at initial_location k to final destination k should be 0")

