# Plan: Agent Budget Guard - V0.2 Delivery Loop

## Overview
This plan outlines the next phase of development for the Agent Budget Guard project, focusing on dynamic model routing and context compression.

## Goals
- [ ] **Dynamic Routing**: Implement logic to switch between Gemini-Flash and DeepSeek-V3 based on task complexity.
- [ ] **Token Optimization**: Fully integrate the `TokenOptimizer` into the main budget checking loop.
- [ ] **Automated Testing**: Achieve 80% code coverage for the core cost estimation logic.

## Steps

### 1. Model Routing Implementation
- **Action**: Update `cost_calculator.py` to include a `recommend_model` method.
- **Logic**: IF estimated cost on high-tier model > $0.10, THEN recommend low-tier model for initial validation.

### 2. Context Compression Integration
- **Action**: Integrate `TokenOptimizer.summarize_context` into the pre-flight check.
- **Output**: Optimized message payload with reduced token footprint.

### 3. CI/CD Setup
- **Action**: Use `gh` to create a GitHub Action for running `test_guard.py` on every push.

## Verification
- Run `python3 test_guard.py` and ensure all tests pass.
- Verify `gh workflow run` status.

## Status
- Version: 0.2-alpha
- Author: Water Woods (Autonomous)
