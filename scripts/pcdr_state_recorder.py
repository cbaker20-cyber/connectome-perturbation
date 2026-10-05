"""Bounded, read-only state recording at three explicit Brian schedule phases."""
from pathlib import Path
import numpy as np
from scripts.pcdr_fine_sim import ticks_for
from scripts.pcdr_ccr_transfer import write


class StateRecorder:
    phases = ('before_thresholds', 'after_synapses', 'end')

    def __init__(self, out, indices, window_ms):
        self.out = Path(out)
        self.indices = list(indices)
        self.window_ms = list(window_ms)

    def setup(self, network, neurons, dt_ms, duration_s):
        if (not self.indices or len(set(self.indices)) != len(self.indices)
                or any(not isinstance(i, (int, np.integer)) or i < 0 or i >= len(neurons) for i in self.indices)):
            raise ValueError('Unique valid recording indices required')
        a, b = self.window_ms
        if not 0 <= a < b <= duration_s*1000:
            raise ValueError('Recording window outside simulation')
        self.first = ticks_for(a, dt_ms) if a else 0
        self.last = ticks_for(b, dt_ms)
        self.network, self.neurons, self.dt_ms = network, neurons, dt_ms
        self.out.mkdir(parents=True, exist_ok=False)

    def monitors(self, start, length):
        import brian2 as b
        if start >= self.last or start+length <= self.first:
            return []
        if start < self.first or start+length > self.last:
            raise ValueError('Recording window must align with chunk boundaries')
        return [b.StateMonitor(self.neurons, ['v', 'g', 'not_refractory'], record=self.indices,
                when=phase, name='diagnostic_'+phase) for phase in self.phases]

    def save(self, start, length, monitors):
        import brian2 as b
        for phase, monitor in zip(self.phases, monitors):
            ticks = np.rint(np.asarray(monitor.t/b.ms)/self.dt_ms).astype(np.int64)
            if not np.array_equal(ticks, np.arange(start, start+length)):
                raise ValueError('Diagnostic ticks differ from requested chunk')
            v, g = np.asarray(monitor.v/b.mV), np.asarray(monitor.g/b.mV)
            if not np.isfinite(v).all() or not np.isfinite(g).all():
                raise ValueError('Nonfinite recorded state')
            # One file per phase/chunk bounds memory and preserves completed chunks on interruption.
            with (self.out/f'{start:010d}_{phase}.npz').open('xb') as stream:
                np.savez_compressed(stream, tick=ticks, indices=np.asarray(self.indices, dtype=np.int64),
                    v_mV=v, g_mV=g, not_refractory=np.asarray(monitor.not_refractory, dtype=bool))
        if start == self.first:
            write(self.out/'schedule.json', {'schedule':str(self.network.scheduling_summary()),
                'dt_ms':self.dt_ms, 'window_ms':self.window_ms, 'phases':list(self.phases),
                'interpretation':'before_thresholds follows state update; after_synapses precedes reset; end follows reset.'})

    def progress(self, ticks):
        write(self.out/'progress.json', {'simulated_ms':ticks*self.dt_ms})
