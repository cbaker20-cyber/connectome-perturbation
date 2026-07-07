# Null Model Protocol

## Purpose

The current targeted perturbation summary is not enough to support a claim. It compares named neuron groups under sugar stimulation but does not answer the obvious objection:

> Would any randomly selected group of the same size produce a similar or larger effect?

This protocol defines the first null model needed before the sugar-to-ascending-neuron result can be treated as more than a pilot prioritization signal.

## Primary null model

For a target group such as `ascending`:

1. Run or load the sugar baseline.
2. Silence the target group.
3. Compute a target effect score.
4. Sample random neuron groups with the same number of neurons.
5. Silence each random group under the same sugar input.
6. Compute the same effect score for each random group.
7. Compare the target score to the random distribution.

## Primary effect score

Use absolute output disruption first:

```text
score = sum(abs(delta_hz))
```

This avoids a weak result being hidden by positive and negative changes cancelling each other out.

Also record:

```text
signed_total_delta_hz = sum(delta_hz)
n_neurons_affected = count(abs(delta_hz) > threshold_hz)
```

## Empirical p-value

For a target score `S_target` and random scores `S_random`:

```text
p = (1 + count(S_random >= S_target)) / (1 + n_random)
```

Use the plus-one correction so the p-value is never reported as zero.

## Minimum acceptable run

Exploratory:

```text
n_random = 20
n_run per simulation = 3 to 5
```

Defensible:

```text
n_random >= 200
n_run per simulation >= 10
```

Competition-strength:

```text
n_random >= 500
n_run per simulation >= 20 to 30
```

## Required controls after the first null

The first random null only asks whether group size explains the effect. It is not enough by itself.

Next controls:

- degree-matched random groups;
- super-class-matched random groups;
- output-restricted effect score, especially motor/feeding-relevant outputs;
- seed sensitivity;
- repeated baseline runs.

## Claim rule

Before this null model is run, allowed language is:

> sugar-to-ascending-neuron pilot signal

After this null model is run and significant, allowed language becomes:

> sugar-to-ascending-neuron effect exceeds same-size random silencing under this model

Still forbidden:

> proved real fly feeding behavior
