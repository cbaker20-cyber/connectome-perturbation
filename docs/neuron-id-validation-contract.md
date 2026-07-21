# Neuron ID validation contract

This document defines the acceptance contract for issue #9. It is an engineering integrity check only. Passing it does not validate a dataset, connectome reconstruction, cell identity, biological interpretation, or neuroscience claim.

## Scope

The validator must treat neuron/root identifiers as opaque decimal strings. It may inspect CSV or JSON records and may emit a deterministic JSON report, but it must not rewrite the source data.

## Accepted representation

A valid identifier:

- is a JSON or CSV string value;
- contains only ASCII digits `0` through `9`;
- has no leading or trailing whitespace;
- has no sign, decimal point, exponent marker, separator, or prefix;
- remains byte-for-byte identical throughout validation;
- may exceed JavaScript's safe integer range, including values above `2^53`.

Leading zeroes are preserved because identifiers are opaque labels, not quantities. The validator should report them but must not normalize them unless a future dataset-specific contract explicitly forbids them.

## Rejected representation

Strict mode must reject:

- JSON numbers, Python integers, and floating-point values;
- scientific notation such as `9.007199254740993e15`;
- decimal forms such as `9007199254740993.0`;
- signed values such as `+123` or `-123`;
- whitespace-padded values;
- empty strings and null values;
- non-decimal characters;
- values produced by rounding or truncation when original text is available.

The validator must never convert a candidate through `float`, JavaScript `Number`, spreadsheet numeric inference, or another lossy numeric path before checking it.

## Precision-loss evidence

When both original text and a parsed/coerced representation are available, the report should distinguish:

- `valid_exact_string` — exact decimal string preserved;
- `invalid_type` — non-string representation supplied in strict mode;
- `invalid_format` — string violates the decimal-string grammar;
- `suspected_precision_loss` — parsed/coerced value cannot reproduce the original text exactly;
- `missing_value` — null or empty input.

A rounded value cannot be proven correct merely because it is syntactically valid. If provenance does not contain the original source text, the report must state that precision integrity is unverified rather than infer correctness.

## CLI behavior

The planned CLI should:

1. accept a repo-relative CSV or JSON input path and a named ID field/column;
2. default to strict string-only validation;
3. never modify the input file;
4. optionally write a repo-relative report under `results/validation/`;
5. reject absolute paths and `..` path escapes;
6. exit nonzero when invalid or unverified records are present, unless an explicit report-only mode is requested;
7. produce deterministic UTF-8 JSON for fixed input and arguments.

## Minimum report fields

```json
{
  "schema_version": "1",
  "input_path": "repo/relative/path",
  "id_field": "root_id",
  "strict_mode": true,
  "record_count": 0,
  "valid_count": 0,
  "invalid_count": 0,
  "unverified_count": 0,
  "status_counts": {},
  "records": []
}
```

Each record should contain a stable record index or source key, the conservative status, and a short reason. Reports should avoid duplicating unrelated source fields.

## Required tests

Tests should prove that:

- `"9007199254740993"` and larger decimal strings remain exact;
- JSON numeric, Python integer, and float inputs are rejected in strict mode;
- scientific notation, decimals, signs, whitespace, nulls, and non-digits are rejected;
- leading zeroes are preserved without normalization;
- suspected rounded/truncated values are flagged when original text is available;
- absolute report paths and repo-boundary escapes are rejected;
- repeated runs with fixed inputs produce byte-identical reports;
- validation does not alter the source file.

## Claim boundary

A successful report means only that the inspected identifier representation satisfies this contract. It does not establish that identifiers exist in FlyWire or another dataset, map to the intended neurons, belong to the same materialization, or support any lesion or behavioral conclusion.
