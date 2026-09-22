import itertools
import numpy as np
from scripts.pcdr_fullpool_bounds import smd_lower_bounds
from eigencircuits.controls import standardized_difference

def test_smd_bound_below_every_exhaustive_candidate():
 values=np.array([[0.,9.],[2.,4.],[8.,1.],[3.,8.],[7.,2.]])
 pools={'a':np.array([0,1,2]),'b':np.array([3,4])};counts={'a':2,'b':1}
 for target in [np.array([[0.,0.],[1.,1.]]),np.array([[10.,20.],[15.,30.]])]:
  low,high,vmax,lower=smd_lower_bounds(target,values,counts,pools)
  for pair in itertools.combinations([0,1,2],2):
   for b in [3,4]:
    sample=values[list(pair)+[b]]
    assert np.all(sample.var(0)<=vmax+1e-12)
    assert np.all(standardized_difference(target,sample)>=lower-1e-12)

def test_constant_feature_bounds():
 _,_,_,lower=smd_lower_bounds(np.ones((2,1)),np.ones((3,1)),{'a':2},{'a':np.arange(3)})
 assert lower[0]==0
 _,_,_,lower=smd_lower_bounds(np.zeros((2,1)),np.ones((3,1)),{'a':2},{'a':np.arange(3)})
 assert np.isinf(lower[0])
