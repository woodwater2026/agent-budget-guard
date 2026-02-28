# Plan: Agent Budget Guard - V0.2 Delivery Loop

## Overview
This plan outlines the next phase of development for the Agent Budget Guard project, focusing on dynamic model routing and context compression.

## Goals
- [x] **Dynamic Routing**: Implement logic to switch between Gemini-Flash and DeepSeek-V3 based on task complexity.
- [x] **Token Optimization**: Fully integrate the `TokenOptimizer` into the main budget checking loop.
- [x] **Automated Testing**: Achieve 80% code coverage for the core cost estimation logic.

## Steps

### 1. Model Routing Implementation
- **Action**: Update `cost_calculator.py` to include a `recommend_model` method.
- [x] Completed.

### 2. Context Compression Integration
- **Action**: Integrate `TokenOptimizer.summarize_context` into the pre-flight check.
- [x] Completed in `orchestrator.py`.

### 3. CI/CD Setup
- **Action**: Use `gh` to create a GitHub Action for running `test_guard.py` on every push.
- [x] Completed. Verified success on GitHub.

## Verification
- Run `python3 test_guard.py` and ensure all tests pass.
- Verify `gh workflow run` status.

## Status
- Version: 0.3-dev
- Author: Water Woods (Autonomous)

## 🎯 V0.3 Roadmap (Next Steps)
- [ ] **Sub-agent Recruitment SOP**: Document how to hire specialist sub-agents with specific budget caps.
- [ ] **Real-time Cost Dashboard**: Create a `dashboard.md` updated by a 5-min heartbeat to show spending vs ROI.
- [ ] **Multi-Currency Metadata**: Support non-USD pricing metadata for global deployment.
