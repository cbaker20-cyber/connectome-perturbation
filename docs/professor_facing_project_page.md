# Drosophila Connectome Perturbation Project

## One-sentence version

This project uses FlyWire-derived connectivity and a Brian2 whole-brain simulation framework to ask whether corrected sugar input produces a context-specific AN-linked motor-output effect.

## Current status

This is not a finished biological claim. The strongest current result is a pilot result from a targeted validation matrix. It appears useful because it came after a real technical correction, but it still needs a cleaner higher-trial rerun.

## What changed technically

The main technical issue was a source-ID parsing bug. Some 18-digit FlyWire root IDs were being converted through floating point before integer conversion. That can silently corrupt the final digits of the ID.

After switching to direct integer parsing, the corrected sugar source set recovered to 21/21 IDs and matched the connectivity table properly.

## Main pilot result

After the ID correction, a small targeted Brian2 validation matrix compared sugar, gustatory, mechanosensory, and sensory_ascending input contexts against AN and brain_motor_neuron perturbation targets.

The strongest preliminary result was sugar-specific:

- sugar to AN
- mean_abs_motor_delta = 1.4706
- l2_motor_delta = 35.0888
- top10_motor_shift = 104.0
- 22/85 motor neurons affected

AN effects were weak in mechanosensory and sensory_ascending contexts. That matters because it argues against a broad AN story and points instead toward a context-specific perturbation question.

## Careful interpretation

This result does not prove that ANs causally mediate sugar behavior in a living fly. The more careful interpretation is that, in the corrected model, the sugar context produced the strongest AN-linked motor-output shift in the pilot matrix.

That is enough to justify better controls. It is not enough to claim a final mechanism.

## Next computational step

The next step is to rerun the key sugar and gustatory comparisons with more trials, keep one backend, and refine the AN subset instead of treating all ANs as one large group.

## Possible wet-lab bridge

A result like this could eventually point toward calcium imaging, targeted neuronal perturbation, or behavioral tracking. The hard part is not naming those techniques. The hard part is mapping a broad computational AN group onto a clean biological target, such as a smaller subset with an existing driver line.

## What feedback would help most

The most useful feedback would be whether this is a biologically reasonable direction, whether the AN subset should be refined computationally first, and who locally would be best suited to advise on the wet-lab constraints.
