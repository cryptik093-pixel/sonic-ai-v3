# Sonic AI V3 --- AI Agent Protocol

Version: 1.0

## Purpose

This document is the governing protocol for any AI coding agent working
on Sonic AI V3.

## Core Principles

1.  Preserve a clean, modular architecture.
2.  Extend existing systems before creating new ones.
3.  Never rewrite working code without explicit instruction.
4.  Keep the project buildable after every change.
5.  Prefer maintainability over cleverness.
6.  Explain major architectural changes before implementing them.
7.  Avoid duplicate logic.
8.  Keep frontend (Next.js) and backend (FastAPI) responsibilities
    separate.
9.  Shared logic belongs in `packages/`.
10. Document significant changes.

## Workflow

1.  Read this protocol and the docs folder before coding.
2.  Understand the requested feature.
3.  Identify impacted files.
4.  Produce a short implementation plan.
5.  Make the smallest correct change.
6.  Verify the application still runs.
7.  Summarize what changed and any follow-up work.

## Coding Standards

-   Use TypeScript for the frontend.
-   Use Python/FastAPI for the backend.
-   Prefer reusable components.
-   Strong typing over `any`.
-   No dead code or placeholder logic unless clearly marked.

## Project Goals

Build Sonic AI V3 brick by brick into a production-grade Producer
Operating System with: - Project management - Asset management - AI
memory - Knowledge system - Automation - Voice control - Local-first
architecture where practical

## Non-Negotiable Rules

-   Do not sacrifice architecture for speed.
-   Do not introduce unnecessary dependencies.
-   Keep commits and changes focused.
-   Preserve code readability.
-   Leave the codebase in a better state than it was found.

## Definition of Done

A task is complete only when: - Code builds successfully. - No existing
functionality is broken. - New functionality is integrated cleanly. -
Documentation is updated if architecture changed.
