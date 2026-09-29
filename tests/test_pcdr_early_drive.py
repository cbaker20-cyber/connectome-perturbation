import numpy as np
from scipy.sparse import csr_matrix
from scripts.pcdr_early_drive import signed_inputs
from scripts.pcdr_input_reconstruction import delayed_input


def test_signed_components_keep_cancelling_arrivals_and_sum_to_net():
    weights=csr_matrix([[2.,-2.],[0.,-3.]])
    spikes=csr_matrix([[1.,0.,1.],[1.,1.,0.]])
    positive,negative=signed_inputs(weights,spikes,1)
    assert positive[0,1]==2 and negative[0,1]==-2
    np.testing.assert_array_equal(positive+negative,delayed_input(weights,spikes,1))
    assert np.all(positive>=0) and np.all(negative<=0)
    np.testing.assert_array_equal(weights.toarray(),[[2.,-2.],[0.,-3.]])
