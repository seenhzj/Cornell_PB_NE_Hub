
# coding: utf-8

# ## Model Version 1

# In[1]:


#! pip install pyomo


# In[36]:


#!pwd


# ## Create Model

# In[203]:


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

model.capital = Param(model.J,model.S,model.T, model.F)

model.utility = Param(model.J,model.S,model.T, model.F)

model.distance = Param(model.L,model.L)

model.hub_capacity=Param(model.S)

model.package = Param(model.I|model.K,model.I|model.K)

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
model.n=Var(model.L,model.L,model.L,model.H, within=NonNegativeReals)


# ## Objective Function

# In[208]:


# operations cost + transportation cost
#(2)
#(3)
#(4)
def obj_expression(model):
    utility_cost=sum((model.utility[j,s,t,f] * model.y[j,s,t,f]) for j in model.J for s in model.S for t in model.T for f in model.F)
    loading_cost=sum((model.Load_Cost * model.n[j,l,l1,h]) for j in model.J for l in model.L for l1 in (model.I|model.K) for h in model.H)
    unloading_cost=sum((model.Unload_Cost * model.n[l,j,l1,h]) for l in model.L for j in model.J for l1 in (model.I|model.K) for h in model.H) 
    sorting_cost=sum((model.sorting[j] * model.n[j,k,k,h]) for j in model.J for k in model.K for h in model.H) 
    transportation_cost=sum((model.max_trans_cost[l,l1] * model.truck[l,l1]) for l in model.L for l1 in model.L) #(3)
    return utility_cost + loading_cost + unloading_cost + sorting_cost + transportation_cost
model.OBJ = Objective(rule=obj_expression, sense = minimize, doc='Define objective function')


# ## Constraints

# In[209]:


## Define contrains ##
# capital_constrains   the sum of the capital cost

#(1)
def capital_constraints(model):
    return (sum(model.capital[j,s,t,f]*model.y[j,s,t,f] for j in model.J for s in model.S for t in model.T for f in model.F)<=model.Max_Capital_Cost)
model.max_cap = Constraint( rule = capital_constraints, doc = "max capital constraint")


# In[210]:


#(5)
def truck_size_constraints(model,l,l1):
    return (sum(model.n[l,l1,l2,h] for l2 in model.L for h in model.H)<=model.Truck_Size*model.truck[l,l1])
model.truck_size_con = Constraint(model.L,model.L,rule = truck_size_constraints, doc = "truck size constraint")


# In[211]:


#(6)
def inbound_equal_rule(model, j, h, l1):
      return (sum(model.n[l,j,l1,h] for l in model.L)
          == sum(model.n[j,l2,l1,h-1] for l2 in model.L))
model.inbound_equal = Constraint(model.J,model.H1,model.I|model.K, rule = inbound_equal_rule, doc = "inbound package equal")


# In[212]:


#(7)
#2nd demand contransts
def initialization_demand_rule(model,l,l1,h):
    if l == l1:
        return Constraint.Skip
    return (sum(model.n[l,j,l1,h] for j in model.J) == model.package[l,l1])
model.initialization_demand = Constraint(model.I|model.K,model.I|model.K,model.MaxH,rule = initialization_demand_rule)


# In[213]:


#(8)
def destination_demand_rule(model, l):
    return (sum(model.n[j,l,l,h] for j in model.J for h in model.H) == sum(model.package[l1,l] for l1 in model.I|model.K))
model.destination_demand_rule = Constraint(model.I|model.K, rule=destination_demand_rule)


# In[214]:


#(9)
def num_of_hubs_opened_perlocation(model,j):
    return(sum(model.y[j,s,t,f] for s in model.S for t in model.T for f in model.F)<=1)
model.num=Constraint(model.J,rule=num_of_hubs_opened_perlocation,doc="constraint on num of hubs opened per location")


# In[215]:


#(10)
def delivery_hub_rule(model,j,k,l):
    return (sum(model.n[l,j,k,h] for h in model.H)
           <= (M * sum(model.y[j,s,'deliver',f]+model.y[j,s,'both',f] for s in model.S for f in model.F)))
model.delivery_hub = Constraint(model.J,model.K,model.I|model.J, rule = delivery_hub_rule, doc = "ensure delivery packages handled by delivery hub")


# In[216]:


#(11)
def delivery_sort_hub_rule(model,j,k):
    return (sum(model.n[j,k,k,h] for h in model.H)
           <= (M * sum(model.y[j,s,'deliver','both']+model.y[j,s,'both','both'] for s in model.S)))
model.delivery_sort_hub = Constraint(model.J,model.K, rule = delivery_sort_hub_rule, doc = "ensure last delivery packages handled by sort-delivery hub")


# In[217]:


#(12)
def return_hub_rule(model,i,j,k,l):
    return (sum(model.n[l,j,i,h] for h in model.H)
           <= (M * sum(model.y[j,s,'return',f]+model.y[j,s,'both',f] for s in model.S for f in model.F)))
model.return_hub = Constraint(model.I,model.J,model.K,model.L, rule = return_hub_rule, doc = "ensure return packages handled by return hub")


# In[218]:


#(13)
def hub_capacity_constraint(model,j):
    return sum(model.n[l,j,l1,h] for l in model.L for l1 in model.I|model.K for h in model.H)<=sum(model.hub_capacity[s]*model.y[j,s,t,f] for s in model.S for t in model.T for f in model.F)
model.hub_capacity_constraint=Constraint(model.J, rule=hub_capacity_constraint,doc="hub capacity constraint")

