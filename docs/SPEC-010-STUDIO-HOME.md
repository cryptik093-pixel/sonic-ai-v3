# SPEC-010 — Studio Home
Version: 1.0
Status: Approved
Phase: Sprint 1
Category: Feature Specification

---

# Purpose

Studio Home is the entry point into Sonic AI V3.

It is not a dashboard.

It is not a landing page.

It is the beginning of every creative session.

Its purpose is to eliminate uncertainty and immediately reconnect the creator with their work.

Within seconds of opening Sonic, the creator should understand where they left off, what deserves attention, and what the most valuable next action is.

---

# User Promise

"When I open Sonic, I immediately know where I am, where I was, and where I should go next."

---

# Primary Question

"What should I work on today?"

Everything on this screen must help answer that question.

---

# Objectives

• Continue creative momentum
• Reduce startup friction
• Surface important projects
• Show current creative context
• Offer one-click project creation
• Maintain continuity between sessions

---

# Layout

Header

↓

Today's Focus

↓

Continue Working

↓

Recent Projects

↓

Recent Activity

↓

Quick Actions

↓

Studio Insights

---

# Components

Header

Greeting

Current Creative State

Today's Focus Card

Continue Working Card

Recent Projects List

Quick Actions Panel

Studio Activity Feed

System Status

---

# Continue Working

Displays the most recent active project.

Shows:

Project Name

Creative State

Last Session

Time Since Last Open

One primary action:

Continue Session

---

# Recent Projects

Shows the five most recently accessed projects.

Each card contains:

Project Name

Artist

Status

Last Modified

Creative State

Progress

---

# Quick Actions

Create New Project

Import Project

Analyze Audio

Open Knowledge

Search Everything

---

# Studio Insights

Future feature.

Eventually displays:

Creative streak

Goals

Upcoming milestones

AI observations

Production trends

---

# AI Responsibilities

The AI should never interrupt.

It quietly observes.

It highlights.

It recommends.

Only when confidence is high.

---

# Backend Requirements

Fetch Dashboard Summary

Fetch Recent Projects

Fetch Continue Working

Fetch Activity Feed

Health Check

---

# Future Expansion

Session Resume

Notifications

Collaboration

Cloud Sync

Studio DNA

Intent

Context

---

# Acceptance Criteria

✓ Loads in under two seconds

✓ Continue Working functions

✓ Recent Projects populated

✓ Dashboard synchronized

✓ Responsive layout

✓ Keyboard accessible

✓ No console errors

✓ No empty screen state

✓ New Project launches Project Wizard