# Griductive Solver Experimental Evaluation

## Summary Metrics by Board Dimension

| Grid Size | Levels | Avg CNF Clauses | Avg SAT Calls | Avg Decisions | Avg Propagations | Avg Backtracks | Avg Runtime (ms) | Success Rate |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 3x3 | 15 | 84.9 | 48.3 | 93.0 | 369.7 | 0.0 | 4.38ms | 100.0% |
| 4x4 | 28 | 116.8 | 147.6 | 867.3 | 2123.6 | 0.0 | 19.71ms | 100.0% |
| 5x5 | 12 | 225.3 | 246.3 | 2274.8 | 5598.1 | 0.8 | 68.54ms | 100.0% |


## Complete Level Benchmark Dataset

| Level ID | Case Name | Grid | CNF Clauses | SAT Calls | Decisions | Propagations | Backtracks | Runtime (ms) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| level_01 | Case #01: Rookie Detective (3x3) | 3x3 | 56 | 46 | 93 | 342 | 0 | 3.61 |
| level_02 | Case #02: Rookie Detective (3x3) | 3x3 | 57 | 54 | 117 | 406 | 0 | 3.38 |
| level_03 | Case #03: Rookie Detective (3x3) | 3x3 | 41 | 60 | 170 | 468 | 0 | 3.83 |
| level_04 | Case #04: Rookie Detective (3x3) | 3x3 | 67 | 36 | 43 | 262 | 0 | 3.25 |
| level_05 | Case #05: Rookie Detective (3x3) | 3x3 | 65 | 46 | 69 | 352 | 0 | 2.88 |
| level_06 | Case #06: Rookie Detective (3x3) | 3x3 | 72 | 52 | 129 | 400 | 0 | 3.84 |
| level_07 | Case #07: Rookie Detective (3x3) | 3x3 | 65 | 60 | 131 | 490 | 0 | 5.4 |
| level_08 | Case #08: Rookie Detective (3x3) | 3x3 | 157 | 58 | 107 | 466 | 0 | 4.4 |
| level_09 | Case #09: Rookie Detective (3x3) | 3x3 | 71 | 38 | 55 | 282 | 0 | 2.93 |
| level_10 | Case #10: Rookie Detective (3x3) | 3x3 | 140 | 54 | 114 | 432 | 0 | 8.97 |
| level_11 | Case #11: Rookie Detective (3x3) | 3x3 | 36 | 64 | 186 | 508 | 0 | 3.67 |
| level_12 | Case #12: Rookie Detective (3x3) | 3x3 | 46 | 46 | 81 | 358 | 0 | 2.91 |
| level_13 | Case #13: Rookie Detective (3x3) | 3x3 | 163 | 42 | 31 | 318 | 0 | 5.26 |
| level_14 | Case #14: Rookie Detective (3x3) | 3x3 | 68 | 36 | 58 | 250 | 0 | 2.77 |
| level_15 | Case #15: Rookie Detective (3x3) | 3x3 | 170 | 32 | 11 | 212 | 0 | 8.58 |
| level_16 | Case #16: Senior Inspector (4x4) | 4x4 | 81 | 159 | 878 | 2314 | 0 | 14.96 |
| level_17 | Case #17: Senior Inspector (4x4) | 4x4 | 98 | 123 | 582 | 1718 | 0 | 13.22 |
| level_18 | Case #18: Senior Inspector (4x4) | 4x4 | 64 | 199 | 1395 | 2974 | 0 | 22.2 |
| level_19 | Case #19: Senior Inspector (4x4) | 4x4 | 170 | 113 | 377 | 1564 | 0 | 35.03 |
| level_20 | Case #20: Senior Inspector (4x4) | 4x4 | 146 | 139 | 830 | 1992 | 0 | 15.47 |
| level_21 | Case #21: Senior Inspector (4x4) | 4x4 | 83 | 147 | 778 | 2134 | 0 | 14.76 |
| level_22 | Case #22: Senior Inspector (4x4) | 4x4 | 182 | 141 | 728 | 2008 | 0 | 17.84 |
| level_23 | Case #23: Senior Inspector (4x4) | 4x4 | 80 | 127 | 661 | 1810 | 0 | 11.57 |
| level_24 | Case #24: Senior Inspector (4x4) | 4x4 | 75 | 153 | 943 | 2178 | 0 | 15.24 |
| level_25 | Case #25: Senior Inspector (4x4) | 4x4 | 72 | 157 | 1064 | 2242 | 0 | 15.08 |
| level_26 | Case #26: Senior Inspector (4x4) | 4x4 | 71 | 157 | 941 | 2252 | 0 | 16.81 |
| level_27 | Case #27: Senior Inspector (4x4) | 4x4 | 127 | 123 | 722 | 1726 | 0 | 16.16 |
| level_28 | Case #28: Senior Inspector (4x4) | 4x4 | 102 | 119 | 544 | 1646 | 0 | 11.9 |
| level_29 | Case #29: Senior Inspector (4x4) | 4x4 | 158 | 163 | 1035 | 2372 | 0 | 28.83 |
| level_30 | Case #30: Senior Inspector (4x4) | 4x4 | 82 | 169 | 1162 | 2452 | 0 | 15.77 |
| level_31 | Case #31: Senior Inspector (4x4) | 4x4 | 156 | 139 | 834 | 1994 | 0 | 18.29 |
| level_32 | Case #32: Senior Inspector (4x4) | 4x4 | 244 | 137 | 870 | 1950 | 0 | 20.34 |
| level_33 | Case #33: Senior Inspector (4x4) | 4x4 | 152 | 81 | 208 | 1078 | 0 | 17.19 |
| level_34 | Case #34: Senior Inspector (4x4) | 4x4 | 150 | 139 | 813 | 1982 | 0 | 23.67 |
| level_35 | Case #35: Senior Inspector (4x4) | 4x4 | 74 | 197 | 1376 | 2934 | 0 | 18.99 |
| level_36 | Case #36: Mastermind (4x4) | 4x4 | 102 | 155 | 853 | 2218 | 0 | 42.72 |
| level_37 | Case #37: Mastermind (4x4) | 4x4 | 95 | 155 | 927 | 2262 | 0 | 17.02 |
| level_38 | Case #38: Mastermind (4x4) | 4x4 | 71 | 183 | 1307 | 2694 | 0 | 18.6 |
| level_39 | Case #39: Mastermind (4x4) | 4x4 | 116 | 131 | 803 | 1860 | 0 | 17.28 |
| level_40 | Case #40: Mastermind (4x4) | 4x4 | 65 | 165 | 1005 | 2390 | 0 | 17.29 |
| level_41 | Case #41: Mastermind (4x4) | 4x4 | 206 | 177 | 1053 | 2626 | 1 | 38.07 |
| level_42 | Case #42: Mastermind (4x4) | 4x4 | 68 | 137 | 816 | 1946 | 0 | 13.71 |
| level_43 | Case #43: Mastermind (4x4) | 4x4 | 179 | 149 | 780 | 2144 | 0 | 23.94 |
| level_44 | Case #44: Mastermind (5x5) | 5x5 | 304 | 159 | 1325 | 3403 | 0 | 49.78 |
| level_45 | Case #45: Mastermind (5x5) | 5x5 | 263 | 345 | 3927 | 8041 | 0 | 104.64 |
| level_46 | Case #46: Mastermind (5x5) | 5x5 | 279 | 283 | 2394 | 6485 | 0 | 79.91 |
| level_47 | Case #47: Mastermind (5x5) | 5x5 | 167 | 221 | 2213 | 4959 | 0 | 52.24 |
| level_48 | Case #48: Mastermind (5x5) | 5x5 | 118 | 161 | 1171 | 3464 | 9 | 32.07 |
| level_49 | Case #49: Mastermind (5x5) | 5x5 | 130 | 291 | 2533 | 6695 | 0 | 58.12 |
| level_50 | Case #50: Mastermind (5x5) | 5x5 | 261 | 217 | 1609 | 4895 | 0 | 77.16 |
| level_51 | Case #51: Stress Test Suite (5x5) | 5x5 | 167 | 215 | 1791 | 4755 | 0 | 77.85 |
| level_52 | Case #52: Stress Test Suite (5x5) | 5x5 | 260 | 299 | 3161 | 6951 | 0 | 77.05 |
| level_53 | Case #53: Stress Test Suite (5x5) | 5x5 | 298 | 347 | 3038 | 8145 | 0 | 94.69 |
| level_54 | Case #54: Stress Test Suite (5x5) | 5x5 | 252 | 181 | 1899 | 3961 | 0 | 41.62 |
| level_55 | Case #55: Stress Test Suite (5x5) | 5x5 | 205 | 237 | 2236 | 5423 | 0 | 77.3 |
