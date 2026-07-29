# AI-Driven Workforce and Resource Optimization Platform
### For FMCG Manufacturing Industries

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.4-orange)
![License](https://img.shields.io/badge/License-MIT-green)

A full-stack ML platform that ingests face recognition machine attendance 
exports, enriches them via runtime Employee Master joins, and delivers 
predictive operational intelligence across six factory management modules.

Built during internship at **Britannia Industries Limited**, Perundurai, 
Erode — May to July 2026.

---

## Research Contributions

**1. Workforce Efficiency Index (WEI)**  
A novel composite daily score (0–100) unifying attendance, OT efficiency, 
bus utilization, canteen efficiency, and department productivity with 
configurable domain weights.

**2. Attendance → Canteen Prediction Chain**  
Statistically validated cross-module relationship (Pearson r = 0.79, 
p < 0.001) enabling ~43% reduction in food waste versus historical baseline.

**3. Attendance-Adaptive Bus Optimization**  
Extends prior static K-Means/Dijkstra transport optimization by reclustering 
daily on present-employee coordinates — route count reduces automatically 
on high-absence days.

**4. Cross-Module Anomaly Fusion**  
Four independent Isolation Forest detectors fused into one signal — 
high-priority alerts fire only on confirmed co-occurring anomalies 
(88% precision).

---

## Modules

| # | Module | Key Feature |
|---|---|---|
| 1 | Workforce Attendance Analytics | RF forecasting + anomaly flags |
| 2 | Overtime Optimization | Ridge Regression OT forecast |
| 3 | Smart Bus Management | 3-mode K-Means + Dijkstra routing |
| 4 | Canteen Waste Analytics | Attendance-driven demand prediction |
| 5 | Department Productivity | Productivity index per dept |
| 6 | Executive Dashboard | WEI + fused alerts + export |

---

## Core Architecture Rule

The attendance file contains **only** what a real face recognition 
machine exports:
