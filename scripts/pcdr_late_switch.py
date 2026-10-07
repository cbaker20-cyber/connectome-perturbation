"""Change selected weights at a chunk boundary, before that tick's updates."""
import numpy as np

from scripts.pcdr_ccr_transfer import write
from scripts.pcdr_fine_sim import ticks_for


class LateSwitch:
    def __init__(self, pairs, switch_ms, remove, out):
        self.pairs = list(pairs)
        if not self.pairs or len(set(self.pairs)) != len(self.pairs):
            raise ValueError('Nonempty unique connection pairs required')
        if any(len(p) != 2 or any(isinstance(i, (bool, np.bool_)) or
               not isinstance(i, (int, np.integer)) or i < 0 for i in p) for p in self.pairs):
            raise ValueError('Nonnegative integer indices required')
        self.switch_ms, self.remove, self.out = switch_ms, remove, out
        self.applied = False

    def setup(self, network, neurons, dt_ms, duration_s):
        import brian2 as b
        self.dt_ms, self.duration_ms = dt_ms, duration_s*1000
        self.switch_tick = ticks_for(self.switch_ms, dt_ms)
        if self.switch_ms >= self.duration_ms:
            raise ValueError('Switch must precede end of simulation')
        synapses = [obj for obj in network.objects if isinstance(obj, b.Synapses)]
        if len(synapses) != 1:
            raise ValueError('Expected one recurrent synapse object')
        self.syn = synapses[0]
        pre, post = np.asarray(self.syn.i[:]), np.asarray(self.syn.j[:])
        self.positions = []
        for source, target in self.pairs:
            positions = np.flatnonzero((pre == source) & (post == target))
            if len(positions) != 1:
                raise ValueError('Selected connection missing or duplicated')
            self.positions.append(int(positions[0]))
        weights = np.asarray(self.syn.w[self.positions]/b.mV)
        if not np.isfinite(weights).all() or np.any(weights == 0):
            raise ValueError('Selected connection has invalid or already zero weight')

    def monitors(self, start, length):
        import brian2 as b
        if start < self.switch_tick < start+length:
            raise ValueError('Switch must coincide with a simulation chunk boundary')
        if start == self.switch_tick:
            if self.applied:
                raise RuntimeError('Switch already applied')
            before = np.asarray(self.syn.w[self.positions]/b.mV).copy()
            # Queued events read the weight on delivery; events already delivered remain in neuron state.
            self.syn.w[self.positions] = (np.zeros_like(before) if self.remove else before)*b.mV
            after = np.asarray(self.syn.w[self.positions]/b.mV)
            write(self.out/'switch.json', dict(switch_ms=start*self.dt_ms, remove=self.remove,
                  pairs=self.pairs, weights_before_mv=before.tolist(), weights_after_mv=after.tolist()))
            self.applied = True
        return []

    def progress(self, tick):
        write(self.out/'simulation_progress.json', dict(simulated_ms=tick*self.dt_ms,
                                                       duration_ms=self.duration_ms))
