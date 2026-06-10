# 10 Publication / Competition Narrative Tracker

## Best current narrative

The project is strongest when framed as a rigorous computational neuroscience investigation, not as a chase for a single flashy p-value.

### Proposed title

**Whole-brain connectome perturbation reveals cell-class-specific control of feeding motor output in a simulated Drosophila brain**

### Core arc

1. Start with a whole-brain biologically grounded model.
2. Add a systematic perturbation engine.
3. Map FlyWire annotations to modeled neurons so perturbations become biologically meaningful.
4. Run exploratory screens to identify candidate control layers.
5. Discover that low-trial screens can mislead, using LO as the honest example.
6. Validate strongest candidates with matched 30-trial comparisons and FDR-corrected statistics.
7. Use graph/null/pathway analysis to avoid overclaiming and refine mechanism.

## Main results to emphasize

1. **Technical contribution:** systematic cell-group output silencing framework on a full-brain fly simulation.
2. **Biological result:** feeding motor output is strongly sensitive to sensory, central, descending, AN/antennal, and ascending perturbations.
3. **Circuit motif:** disinhibition appears in multiple perturbation conditions, suggesting mixed excitatory and suppressive control.
4. **Rigor result:** LO false-positive/sign-flip demonstrates why 30-trial validation and matched baselines are necessary.
5. **Graph control:** degree-matched/null-aware analysis helps distinguish global centrality from task-specific pathway influence.

## Figure plan

| Figure | Working title | Data source | Status | Main message |
|---|---|---|---|---|
| Fig. 1 | Perturbation pipeline schematic | methods/code | planned | Whole-brain model → stimulation → silencing → motor readout. |
| Fig. 2 | Super-class motor impact screen | `motor_impact.csv` | exploratory | Broad groups differ in motor influence; screen only. |
| Fig. 3 | 30-trial validation of candidate cell classes | `hq_*.parquet`, `statistics.csv` | main | AN robust; LO revised. |
| Fig. 4 | Disinhibition motif across groups | motor-neuron delta table | main/supplement | Some motor neurons increase after upstream silencing. |
| Fig. 5 | Degree-matched graph/pathway controls | graph/path outputs | supplement/main depending results | Functional importance is not reducible to raw/global centrality. |

## Judge/reviewer questions and answers

### Why is the LO sign flip not a failure?

Because it demonstrates that the project uses validation rather than p-hacking. The initial LO finding was treated as exploratory and then corrected by a higher-quality rerun. That is scientific integrity.

### Why use silencing instead of activation only?

Activation tests whether a pathway can drive activity. Silencing tests whether a pathway is necessary for maintaining output under a given stimulus and can reveal disinhibition, which activation-only designs can miss.

### Why graph analysis if perturbation already shows effects?

Perturbation shows functional consequence. Graph analysis asks whether the consequence can be explained by network position, pathway placement, or degree. It is a control and interpretation layer, not a replacement for perturbation.

### What is the safest central claim?

The safest central claim is that systematic cell-group output silencing in a whole-brain Drosophila simulation identifies specific neuron classes whose removal significantly changes feeding motor output, with AN/antennal and ascending pathways among the robust validated effects.
