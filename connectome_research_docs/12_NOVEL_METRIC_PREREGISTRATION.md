# Novel Metric Preregistration: Behavioral Opponent Routing Analysis

## Project question
Can a connectome-derived metric predict neurons that switch activity allocation between mutually exclusive behaviors, specifically feeding versus grooming, better than standard graph centrality metrics?

## Motivation
Previous analyses showed that AN / ascending neurons are not enriched for whole-brain betweenness, weighted degree, or broad sugar-to-all-motor source-target betweenness under degree-matched null models. These negative controls motivate a behavior-contrastive framework rather than more generic centrality tests.

## Primary hypothesis
Neurons that gate feeding versus grooming will be enriched for source-conditioned opponent routing from sugar sensory inputs to feeding versus grooming motor outputs.

## Primary metric
Behavioral Opponent Routing Analysis, BORA:

BORA(v) = source_exposure(v) * [downstream_feeding(v) - downstream_grooming(v)]

Large positive values indicate sugar-conditioned routing toward feeding.
Large negative values indicate sugar-conditioned routing toward grooming.
Large absolute values indicate opponent-output gate-like positions.

## Required curated inputs
- metadata/feeding_motor_ids.txt
- metadata/grooming_motor_ids.txt

## Primary null model
Degree-matched bootstrap null using central neurons as the control pool.

## Number of bootstrap iterations
1,000

## Multiple testing correction
Benjamini-Hochberg FDR correction.

## Primary success criterion
BORA predicts dynamic perturbation-defined switch effects better than weighted degree, global betweenness, and broad source-target betweenness.

## Anti-p-hacking rule
The primary metric, null model, and output target sets must be documented before interpreting production results.
