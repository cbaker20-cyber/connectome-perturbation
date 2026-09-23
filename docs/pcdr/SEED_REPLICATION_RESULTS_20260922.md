# Fresh seed replication completed

Completed 2026-09-22T03:52:25.212856+00:00. Verified 2026-09-22T03:54:03.199931+00:00.

- All 210 trials and 180 paired-input comparisons passed verification. All six 127,400-neuron mean footprints agree with independently recomputed rates; all recorded trial output hashes match. No reference p-values were computed.
- This 30-seed replication uses seeds 631001–631030 and the same six frozen lesion sets. It is separate from the earlier five-seed pilot. It checks stochastic-input reproducibility, not biological replication, a random-control null, or confirmation.
- MN9 belongs to the eigen-set but none of the comparisons. The eigen-set contains 13 motor cells; comparisons contain 5,4,3,3,4. Cell-class and readout membership remain unmatched. Optimized sets overlap and are not uniform random draws.

## All results on the new seeds

| Set | A Hz | F | MN9 change Hz | Motor total change Hz | Motor mean change Hz |
|---|---:|---:|---:|---:|---:|
| mode | 22.544 | 0.2312 | -82.633 | 39.267 | 0.462 |
| optimized_000 | 11.341 | 0.1855 | 0.367 | -353.800 | -4.162 |
| optimized_001 | 12.664 | 0.2168 | -1.700 | -418.033 | -4.918 |
| optimized_002 | 15.758 | 0.1968 | -16.367 | -607.800 | -7.151 |
| optimized_003 | 13.080 | 0.2079 | 0.467 | -362.433 | -4.264 |
| optimized_004 | 14.172 | 0.1867 | -19.500 | -580.867 | -6.834 |

- Eigen-set A exceeds all five comparisons: True. Eigen-set F exceeds all five: True. These are descriptive orderings, not significance tests.
- Off-support response remains 76.88% of total absolute mean response. This does not establish circuit independence.

## Pilot and replication kept separate

| Set | Pilot A | New A | Pilot F | New F |
|---|---:|---:|---:|---:|
| mode | 22.576 | 22.544 | 0.2294 | 0.2312 |
| optimized_000 | 11.486 | 11.341 | 0.1853 | 0.1855 |
| optimized_001 | 12.894 | 12.664 | 0.2162 | 0.2168 |
| optimized_002 | 16.467 | 15.758 | 0.1936 | 0.1968 |
| optimized_003 | 13.753 | 13.080 | 0.2147 | 0.2079 |
| optimized_004 | 14.502 | 14.172 | 0.1863 | 0.1867 |

## Paired seed uncertainty

| Set | A 95 percent interval | F 95 percent interval |
|---|---|---|
| mode | 22.233 to 22.816 | 0.2293 to 0.2327 |
| optimized_000 | 11.123 to 11.592 | 0.1830 to 0.1875 |
| optimized_001 | 12.363 to 12.963 | 0.2130 to 0.2193 |
| optimized_002 | 15.378 to 16.147 | 0.1944 to 0.1989 |
| optimized_003 | 12.808 to 13.392 | 0.2044 to 0.2109 |
| optimized_004 | 13.899 to 14.495 | 0.1845 to 0.1889 |

- Bootstrap intervals use 2,000 whole-pair resamples and seed 630700. They quantify seed variability conditional on the fixed sets and model, not matching or biological uncertainty. No neurons are counted as independent replicates.

## Process code and evidence

- The supervisor and collector finished independently of chat access. No extra trials, rematching, thresholds or model changes were introduced. Memory waits were permitted; the six-hour deadline was not reached.
- Created scripts/pcdr_verify_replication.py with Codex assistance by adapting the prior verifier to 210 trials, 180 pairs and this separate study. It checks every output hash and frozen seed/support/source, recomputes all six readouts and complete mean footprints, and exports all 180 per-seed records. The report uses manifest counts and does not relabel the five-seed result.
- Command: .venv/Scripts/python.exe scripts/pcdr_verify_replication.py. All assertions passed. No new significance test or simulation was run during verification.
- Scheduled inputs match in all 180 pairs; delivered-input digests match in 176/180. State-dependent delivery is distinct from the required matched schedule.
- Evidence directory: results/pcdr/seed_replication_20260921. See amendment.json, jobs.json, completion_audit.json, analysis/results.json, per_seed_readouts.csv and each trial manifest. Code and manifest hashes are in the completion audit. Prior study remains in optimized_pilot_20260921.
- Next: CCR environment and replay validation, then distributional/cell-class matching design before broader experiments. No unattended extension is queued. Completed handoff pauses this monitor.

## Every new paired seed

| Set | Seed | A single seed | F single seed | MN9 change Hz | Motor total change Hz |
|---|---:|---:|---:|---:|---:|
| mode | 631001 | 23.294 | 0.2285 | -87.0 | -1.0 |
| mode | 631002 | 22.039 | 0.2273 | -76.0 | 72.0 |
| mode | 631003 | 21.627 | 0.2296 | -82.0 | -1.0 |
| mode | 631004 | 23.216 | 0.2382 | -83.0 | -62.0 |
| mode | 631005 | 22.392 | 0.2241 | -81.0 | 35.0 |
| mode | 631006 | 22.922 | 0.2314 | -83.0 | -2.0 |
| mode | 631007 | 21.569 | 0.2295 | -83.0 | -19.0 |
| mode | 631008 | 23.627 | 0.2254 | -82.0 | 45.0 |
| mode | 631009 | 23.176 | 0.2259 | -88.0 | 36.0 |
| mode | 631010 | 21.686 | 0.2317 | -80.0 | 46.0 |
| mode | 631011 | 23.510 | 0.2218 | -85.0 | 29.0 |
| mode | 631012 | 22.549 | 0.2253 | -84.0 | 107.0 |
| mode | 631013 | 23.941 | 0.2287 | -82.0 | 69.0 |
| mode | 631014 | 23.510 | 0.2236 | -86.0 | -16.0 |
| mode | 631015 | 23.275 | 0.2292 | -91.0 | 0.0 |
| mode | 631016 | 22.490 | 0.2256 | -82.0 | 59.0 |
| mode | 631017 | 22.980 | 0.2310 | -79.0 | 77.0 |
| mode | 631018 | 21.255 | 0.2213 | -79.0 | 96.0 |
| mode | 631019 | 21.824 | 0.2273 | -78.0 | 67.0 |
| mode | 631020 | 23.176 | 0.2342 | -88.0 | 8.0 |
| mode | 631021 | 22.686 | 0.2314 | -83.0 | 77.0 |
| mode | 631022 | 22.824 | 0.2219 | -90.0 | 86.0 |
| mode | 631023 | 23.314 | 0.2225 | -87.0 | 22.0 |
| mode | 631024 | 22.451 | 0.2290 | -82.0 | 0.0 |
| mode | 631025 | 22.784 | 0.2278 | -77.0 | 40.0 |
| mode | 631026 | 23.000 | 0.2251 | -82.0 | 162.0 |
| mode | 631027 | 21.490 | 0.2315 | -83.0 | 23.0 |
| mode | 631028 | 20.980 | 0.2288 | -79.0 | -29.0 |
| mode | 631029 | 21.941 | 0.2156 | -76.0 | 134.0 |
| mode | 631030 | 20.784 | 0.2307 | -81.0 | 18.0 |
| optimized_000 | 631001 | 12.275 | 0.1820 | 0.0 | -320.0 |
| optimized_000 | 631002 | 10.922 | 0.1796 | -4.0 | -394.0 |
| optimized_000 | 631003 | 12.196 | 0.1844 | -1.0 | -436.0 |
| optimized_000 | 631004 | 12.353 | 0.1867 | 12.0 | -370.0 |
| optimized_000 | 631005 | 11.255 | 0.1795 | -8.0 | -436.0 |
| optimized_000 | 631006 | 12.255 | 0.1898 | 1.0 | -386.0 |
| optimized_000 | 631007 | 12.216 | 0.1879 | 8.0 | -390.0 |
| optimized_000 | 631008 | 11.392 | 0.1870 | 5.0 | -304.0 |
| optimized_000 | 631009 | 10.882 | 0.1786 | -9.0 | -385.0 |
| optimized_000 | 631010 | 11.588 | 0.1708 | 2.0 | -323.0 |
| optimized_000 | 631011 | 10.902 | 0.1745 | 1.0 | -325.0 |
| optimized_000 | 631012 | 10.824 | 0.1800 | -7.0 | -352.0 |
| optimized_000 | 631013 | 10.706 | 0.1760 | 7.0 | -326.0 |
| optimized_000 | 631014 | 11.882 | 0.1874 | -8.0 | -429.0 |
| optimized_000 | 631015 | 10.765 | 0.1787 | -5.0 | -392.0 |
| optimized_000 | 631016 | 11.333 | 0.1822 | 4.0 | -322.0 |
| optimized_000 | 631017 | 10.941 | 0.1827 | -4.0 | -398.0 |
| optimized_000 | 631018 | 10.549 | 0.1703 | 6.0 | -281.0 |
| optimized_000 | 631019 | 11.549 | 0.1728 | 4.0 | -333.0 |
| optimized_000 | 631020 | 11.882 | 0.1812 | -8.0 | -408.0 |
| optimized_000 | 631021 | 11.725 | 0.1808 | -2.0 | -371.0 |
| optimized_000 | 631022 | 11.118 | 0.1791 | 1.0 | -314.0 |
| optimized_000 | 631023 | 11.137 | 0.1757 | 3.0 | -345.0 |
| optimized_000 | 631024 | 12.745 | 0.1864 | 1.0 | -383.0 |
| optimized_000 | 631025 | 11.353 | 0.1764 | 11.0 | -335.0 |
| optimized_000 | 631026 | 10.216 | 0.1694 | 0.0 | -211.0 |
| optimized_000 | 631027 | 12.118 | 0.1825 | 0.0 | -304.0 |
| optimized_000 | 631028 | 12.588 | 0.1819 | 5.0 | -364.0 |
| optimized_000 | 631029 | 10.412 | 0.1654 | -1.0 | -263.0 |
| optimized_000 | 631030 | 11.647 | 0.1881 | -3.0 | -414.0 |
| optimized_001 | 631001 | 13.784 | 0.2200 | -6.0 | -442.0 |
| optimized_001 | 631002 | 11.863 | 0.2011 | 6.0 | -385.0 |
| optimized_001 | 631003 | 14.608 | 0.2238 | -1.0 | -497.0 |
| optimized_001 | 631004 | 13.941 | 0.2156 | -4.0 | -537.0 |
| optimized_001 | 631005 | 12.667 | 0.2065 | 7.0 | -374.0 |
| optimized_001 | 631006 | 13.843 | 0.2135 | -4.0 | -488.0 |
| optimized_001 | 631007 | 13.216 | 0.2062 | 6.0 | -431.0 |
| optimized_001 | 631008 | 13.275 | 0.2073 | -8.0 | -459.0 |
| optimized_001 | 631009 | 12.863 | 0.2012 | -1.0 | -403.0 |
| optimized_001 | 631010 | 12.588 | 0.2043 | 5.0 | -423.0 |
| optimized_001 | 631011 | 12.471 | 0.2076 | -5.0 | -374.0 |
| optimized_001 | 631012 | 12.216 | 0.2114 | -9.0 | -373.0 |
| optimized_001 | 631013 | 11.098 | 0.1870 | -4.0 | -377.0 |
| optimized_001 | 631014 | 13.137 | 0.2094 | -16.0 | -526.0 |
| optimized_001 | 631015 | 12.471 | 0.2037 | -9.0 | -405.0 |
| optimized_001 | 631016 | 11.980 | 0.2025 | -6.0 | -401.0 |
| optimized_001 | 631017 | 12.902 | 0.2085 | -4.0 | -445.0 |
| optimized_001 | 631018 | 11.843 | 0.2022 | 10.0 | -352.0 |
| optimized_001 | 631019 | 12.922 | 0.2018 | 9.0 | -360.0 |
| optimized_001 | 631020 | 13.843 | 0.2086 | -15.0 | -551.0 |
| optimized_001 | 631021 | 13.471 | 0.2078 | 6.0 | -363.0 |
| optimized_001 | 631022 | 12.314 | 0.2049 | -11.0 | -354.0 |
| optimized_001 | 631023 | 11.784 | 0.1924 | -4.0 | -388.0 |
| optimized_001 | 631024 | 13.216 | 0.2085 | 6.0 | -404.0 |
| optimized_001 | 631025 | 13.255 | 0.2132 | 1.0 | -425.0 |
| optimized_001 | 631026 | 10.922 | 0.2043 | -6.0 | -355.0 |
| optimized_001 | 631027 | 12.608 | 0.2103 | 8.0 | -376.0 |
| optimized_001 | 631028 | 14.020 | 0.2220 | -1.0 | -492.0 |
| optimized_001 | 631029 | 11.647 | 0.1954 | 4.0 | -339.0 |
| optimized_001 | 631030 | 13.000 | 0.2135 | -5.0 | -442.0 |
| optimized_002 | 631001 | 17.137 | 0.1976 | -18.0 | -633.0 |
| optimized_002 | 631002 | 15.020 | 0.1931 | -7.0 | -513.0 |
| optimized_002 | 631003 | 17.980 | 0.2002 | -29.0 | -717.0 |
| optimized_002 | 631004 | 17.275 | 0.2038 | -27.0 | -685.0 |
| optimized_002 | 631005 | 15.667 | 0.1998 | -2.0 | -615.0 |
| optimized_002 | 631006 | 16.667 | 0.2026 | -19.0 | -648.0 |
| optimized_002 | 631007 | 16.804 | 0.1931 | -26.0 | -692.0 |
| optimized_002 | 631008 | 15.824 | 0.1927 | -16.0 | -603.0 |
| optimized_002 | 631009 | 16.020 | 0.1999 | -26.0 | -606.0 |
| optimized_002 | 631010 | 15.373 | 0.2000 | -13.0 | -623.0 |
| optimized_002 | 631011 | 15.549 | 0.1884 | -13.0 | -586.0 |
| optimized_002 | 631012 | 15.588 | 0.1970 | -24.0 | -596.0 |
| optimized_002 | 631013 | 14.569 | 0.1798 | -17.0 | -563.0 |
| optimized_002 | 631014 | 17.255 | 0.1795 | -34.0 | -763.0 |
| optimized_002 | 631015 | 15.765 | 0.1901 | -9.0 | -548.0 |
| optimized_002 | 631016 | 15.588 | 0.1970 | -13.0 | -604.0 |
| optimized_002 | 631017 | 15.824 | 0.1927 | -17.0 | -567.0 |
| optimized_002 | 631018 | 14.529 | 0.1839 | -5.0 | -480.0 |
| optimized_002 | 631019 | 15.608 | 0.1958 | -12.0 | -576.0 |
| optimized_002 | 631020 | 16.235 | 0.2019 | -14.0 | -596.0 |
| optimized_002 | 631021 | 16.471 | 0.1855 | -20.0 | -656.0 |
| optimized_002 | 631022 | 15.529 | 0.1934 | -21.0 | -597.0 |
| optimized_002 | 631023 | 15.824 | 0.1954 | -6.0 | -525.0 |
| optimized_002 | 631024 | 16.745 | 0.1965 | -17.0 | -655.0 |
| optimized_002 | 631025 | 16.353 | 0.1971 | -5.0 | -636.0 |
| optimized_002 | 631026 | 13.000 | 0.1810 | -18.0 | -493.0 |
| optimized_002 | 631027 | 15.137 | 0.1927 | -20.0 | -627.0 |
| optimized_002 | 631028 | 17.373 | 0.1983 | -19.0 | -693.0 |
| optimized_002 | 631029 | 13.902 | 0.1942 | -7.0 | -527.0 |
| optimized_002 | 631030 | 16.039 | 0.1984 | -17.0 | -611.0 |
| optimized_003 | 631001 | 14.980 | 0.2196 | -14.0 | -427.0 |
| optimized_003 | 631002 | 13.098 | 0.2051 | 7.0 | -340.0 |
| optimized_003 | 631003 | 14.686 | 0.2184 | -8.0 | -467.0 |
| optimized_003 | 631004 | 14.137 | 0.2104 | -3.0 | -418.0 |
| optimized_003 | 631005 | 12.961 | 0.1903 | 5.0 | -320.0 |
| optimized_003 | 631006 | 14.392 | 0.2159 | 4.0 | -415.0 |
| optimized_003 | 631007 | 14.373 | 0.2143 | -7.0 | -394.0 |
| optimized_003 | 631008 | 12.686 | 0.1960 | 0.0 | -326.0 |
| optimized_003 | 631009 | 13.706 | 0.2111 | 4.0 | -374.0 |
| optimized_003 | 631010 | 12.804 | 0.1967 | 4.0 | -332.0 |
| optimized_003 | 631011 | 12.216 | 0.1954 | 0.0 | -322.0 |
| optimized_003 | 631012 | 13.020 | 0.2025 | -5.0 | -334.0 |
| optimized_003 | 631013 | 12.078 | 0.1983 | 13.0 | -321.0 |
| optimized_003 | 631014 | 13.922 | 0.2131 | -11.0 | -462.0 |
| optimized_003 | 631015 | 13.255 | 0.2130 | -5.0 | -433.0 |
| optimized_003 | 631016 | 13.216 | 0.2073 | -1.0 | -385.0 |
| optimized_003 | 631017 | 13.176 | 0.2018 | 9.0 | -303.0 |
| optimized_003 | 631018 | 11.824 | 0.1941 | 5.0 | -291.0 |
| optimized_003 | 631019 | 13.078 | 0.2003 | 3.0 | -388.0 |
| optimized_003 | 631020 | 13.392 | 0.1925 | -1.0 | -335.0 |
| optimized_003 | 631021 | 13.294 | 0.1956 | 6.0 | -314.0 |
| optimized_003 | 631022 | 12.471 | 0.1993 | -9.0 | -349.0 |
| optimized_003 | 631023 | 12.765 | 0.1924 | -1.0 | -389.0 |
| optimized_003 | 631024 | 14.314 | 0.2153 | 4.0 | -431.0 |
| optimized_003 | 631025 | 13.569 | 0.1989 | -3.0 | -359.0 |
| optimized_003 | 631026 | 11.216 | 0.2012 | 2.0 | -261.0 |
| optimized_003 | 631027 | 12.765 | 0.1943 | 2.0 | -309.0 |
| optimized_003 | 631028 | 13.765 | 0.1949 | 8.0 | -381.0 |
| optimized_003 | 631029 | 11.941 | 0.1906 | 4.0 | -301.0 |
| optimized_003 | 631030 | 13.510 | 0.2082 | 2.0 | -392.0 |
| optimized_004 | 631001 | 15.235 | 0.1849 | -14.0 | -570.0 |
| optimized_004 | 631002 | 13.863 | 0.1833 | -14.0 | -587.0 |
| optimized_004 | 631003 | 15.725 | 0.1942 | -23.0 | -644.0 |
| optimized_004 | 631004 | 15.529 | 0.1922 | -23.0 | -667.0 |
| optimized_004 | 631005 | 13.863 | 0.1960 | -16.0 | -523.0 |
| optimized_004 | 631006 | 15.510 | 0.1914 | -27.0 | -647.0 |
| optimized_004 | 631007 | 15.216 | 0.1918 | -17.0 | -609.0 |
| optimized_004 | 631008 | 14.098 | 0.1813 | -20.0 | -570.0 |
| optimized_004 | 631009 | 14.686 | 0.1880 | -26.0 | -596.0 |
| optimized_004 | 631010 | 13.765 | 0.1932 | -12.0 | -568.0 |
| optimized_004 | 631011 | 13.843 | 0.1723 | -22.0 | -556.0 |
| optimized_004 | 631012 | 14.373 | 0.1870 | -25.0 | -589.0 |
| optimized_004 | 631013 | 13.725 | 0.1716 | -21.0 | -592.0 |
| optimized_004 | 631014 | 15.137 | 0.1833 | -24.0 | -618.0 |
| optimized_004 | 631015 | 14.412 | 0.1825 | -27.0 | -603.0 |
| optimized_004 | 631016 | 14.078 | 0.1834 | -17.0 | -565.0 |
| optimized_004 | 631017 | 13.882 | 0.1812 | -17.0 | -546.0 |
| optimized_004 | 631018 | 12.961 | 0.1860 | -10.0 | -478.0 |
| optimized_004 | 631019 | 13.863 | 0.1848 | -20.0 | -585.0 |
| optimized_004 | 631020 | 14.667 | 0.1887 | -21.0 | -607.0 |
| optimized_004 | 631021 | 14.647 | 0.1801 | -21.0 | -587.0 |
| optimized_004 | 631022 | 13.608 | 0.1860 | -25.0 | -500.0 |
| optimized_004 | 631023 | 13.843 | 0.1795 | -18.0 | -566.0 |
| optimized_004 | 631024 | 15.471 | 0.1889 | -21.0 | -639.0 |
| optimized_004 | 631025 | 14.529 | 0.1880 | -7.0 | -587.0 |
| optimized_004 | 631026 | 12.255 | 0.1818 | -18.0 | -472.0 |
| optimized_004 | 631027 | 13.902 | 0.1820 | -25.0 | -609.0 |
| optimized_004 | 631028 | 15.255 | 0.1807 | -17.0 | -637.0 |
| optimized_004 | 631029 | 13.196 | 0.1844 | -14.0 | -509.0 |
| optimized_004 | 631030 | 14.451 | 0.1861 | -23.0 | -600.0 |

- Single-seed A/F above are diagnostics. Declared aggregate A/F average signed neuronal changes across seeds before taking absolute values; do not replace them with the arithmetic mean of these columns.
