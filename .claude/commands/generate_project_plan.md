# Project Implementation Plan Generator

You are tasked with creating comprehensive project implementation plans through an interactive, iterative process. You should be thorough, analytical, and work collaboratively with the user to produce high-quality technical roadmaps for entire projects.

## Initial Response

When this command is invoked:

1. **Check if a project path was provided**:
   - If a project directory or specific documentation files were provided as parameters, skip the default message
   - Immediately read any provided files FULLY
   - Begin the project analysis process

2. **If no parameters provided**, respond with:
```
I'll help you create a comprehensive project implementation plan. Let me start by understanding your project structure and goals.

Please provide:
1. The project root directory or main documentation files (README.md, docs/, etc.)
2. Project type/technology stack if not evident from files
3. Any specific goals, constraints, or timeline requirements
4. Links to existing documentation, specifications, or requirements

I'll analyze the project structure and work with you to create a complete implementation roadmap.

Tip: You can invoke this command with a project directory: `/create_project_plan ./my-project`
For deeper analysis, try: `/create_project_plan analyze thoroughly ./my-project`
```

Then wait for the user's input.

## Process Steps

### Step 1: Project Discovery & Analysis

1. **Read all project documentation immediately and FULLY**:
   - `README.md` and any variation (`readme.md`, `README.txt`, etc.)
   - `CONTRIBUTING.md`, `DEVELOPMENT.md`, `SETUP.md`
   - Documentation directories (`docs/`, `documentation/`, `.github/`)
   - Configuration files (`package.json`, `requirements.txt`, `Cargo.toml`, `pom.xml`, etc.)
   - Architecture documents, API specs, design documents
   - **IMPORTANT**: Use the Read tool WITHOUT limit/offset parameters to read entire files
   - **CRITICAL**: DO NOT spawn sub-tasks before reading these core files yourself
   - **NEVER** read files partially - if a file is mentioned, read it completely

2. **Analyze project structure and technology**:
   - Identify the primary technology stack
   - Understand the project architecture
   - Determine project maturity (new, in-progress, legacy)
   - Identify key components and modules
   - Map dependencies and integrations

3. **Spawn parallel research tasks for comprehensive analysis**:

   **For codebase understanding:**
   - **project-structure-analyzer** - To map the overall project organization
   - **dependency-analyzer** - To understand external and internal dependencies
   - **architecture-analyzer** - To identify design patterns and architectural decisions

   **For development environment:**
   - **build-system-analyzer** - To understand build processes, CI/CD, and deployment
   - **test-strategy-analyzer** - To identify testing approaches and coverage
   - **development-setup-analyzer** - To understand local development requirements

   **For project context:**
   - **requirements-analyzer** - To extract functional and non-functional requirements
   - **documentation-analyzer** - To identify gaps in documentation and specifications

4. **Read all files identified by research tasks**:
   - After research tasks complete, read ALL files they identified as important
   - Read them FULLY into the main context
   - This ensures complete understanding before proceeding

5. **Present comprehensive project understanding**:
   ```
   Based on my analysis of your project, I understand:

   **Project Overview:**
   - Technology Stack: [languages, frameworks, tools]
   - Architecture: [monolith/microservices/etc.]
   - Current State: [development stage, completeness]
   - Primary Purpose: [what the project does]

   **Key Components I've Identified:**
   - [Component 1]: [purpose and current state]
   - [Component 2]: [purpose and current state]
   - [Component 3]: [purpose and current state]

   **Development Infrastructure:**
   - Build System: [tools and processes]
   - Testing: [current test setup and coverage]
   - Deployment: [current deployment strategy]

   **Questions for Clarification:**
   - [Specific question about project goals]
   - [Question about priorities or constraints]
   - [Question about team size or timeline]
   ```

### Step 2: Requirements & Goals Clarification

After presenting initial understanding:

1. **Gather specific project goals**:
   - What are the main objectives?
   - Are there specific milestones or deadlines?
   - What defines "done" for this project?
   - Are there performance, scalability, or other non-functional requirements?

2. **Understand constraints**:
   - Team size and skill levels
   - Technology constraints or preferences
   - Budget or time limitations
   - Integration requirements with existing systems

3. **Identify priorities**:
   - Must-have vs nice-to-have features
   - Critical path dependencies
   - Risk tolerance

### Step 3: Gap Analysis & Strategic Planning

1. **Create a comprehensive gap analysis**:
   ```
   **Current State vs Desired State Analysis:**

   **What Exists:**
   - [Component/feature with current implementation level]
   - [Infrastructure with current maturity]
   - [Documentation with current coverage]

   **What's Missing:**
   - [Critical missing components]
   - [Infrastructure gaps]
   - [Documentation needs]

   **What Needs Improvement:**
   - [Areas requiring refactoring or enhancement]
   - [Performance bottlenecks]
   - [Technical debt areas]
   ```

2. **Identify implementation phases**:
   ```
   **Proposed Implementation Phases:**

   **Phase 1: Foundation** (X weeks)
   - [Core infrastructure and setup]
   - [Essential tooling and processes]

   **Phase 2: Core Features** (X weeks)
   - [Primary functionality implementation]
   - [Key user-facing features]

   **Phase 3: Integration & Polish** (X weeks)
   - [System integration]
   - [Performance optimization]
   - [Documentation and deployment]

   Does this phasing align with your priorities and constraints?
   ```

### Step 4: Detailed Implementation Plan Creation

After agreement on phases and approach:

1. **Write the comprehensive plan** to `PROJECT_IMPLEMENTATION_PLAN.md`
2. **Use this template structure**:

```markdown
# [Project Name] Implementation Plan

## Executive Summary

[Brief overview of the project, its goals, and the implementation approach]

## Project Overview

### Current State
[Detailed analysis of what exists now]

### Target State
[Comprehensive description of the desired end state]

### Success Criteria
[How we'll know the project is complete and successful]

### Key Stakeholders
[Who's involved and their roles]

## Architecture & Technical Approach

### Technology Stack
[Confirmed technologies and rationale]

### System Architecture
[High-level architecture decisions and patterns]

### Key Design Decisions
[Important architectural and design choices with rationale]

## What We're NOT Doing

[Explicitly define scope boundaries to prevent scope creep]

## Implementation Roadmap

### Phase 1: Foundation & Setup (Week 1-X)

#### Objectives
[What this phase accomplishes and why it's first]

#### Deliverables
- [ ] [Specific deliverable with acceptance criteria]
- [ ] [Another deliverable]
- [ ] [Documentation deliverable]

#### Key Tasks

##### Development Environment Setup
**Estimated Effort**: X days
- Set up local development environment
- Configure build and deployment pipelines
- Establish code quality tools (linting, formatting, testing)

##### Core Infrastructure
**Estimated Effort**: X days
- [Infrastructure component with specific requirements]
- [Database setup with schema design]
- [API foundation with authentication]

#### Success Criteria

##### Automated Verification:
- [ ] Build system runs successfully: `[command]`
- [ ] All setup scripts execute without error
- [ ] Basic CI/CD pipeline functional
- [ ] Code quality checks pass: `[commands]`

##### Manual Verification:
- [ ] Development environment works on all team machines
- [ ] Basic application starts and responds
- [ ] Documentation is accessible and complete

#### Dependencies & Risks
- [External dependencies needed]
- [Potential blocking issues]
- [Mitigation strategies]

---

### Phase 2: Core Implementation (Week X-Y)

[Similar detailed structure for each phase...]

---

### Phase 3: Integration & Optimization (Week Y-Z)

[Similar detailed structure...]

---

### Phase 4: Deployment & Launch (Week Z-End)

[Final phase with deployment, monitoring, and launch activities...]

## Development Standards & Guidelines

### Code Quality
- [Coding standards and conventions]
- [Review processes]
- [Testing requirements]

### Documentation Requirements
- [Code documentation standards]
- [User documentation needs]
- [API documentation requirements]

### Version Control & Collaboration
- [Branching strategy]
- [Commit message conventions]
- [Pull request processes]

## Testing Strategy

### Testing Pyramid
- **Unit Tests**: [Coverage goals and key areas]
- **Integration Tests**: [Critical integration points]
- **End-to-End Tests**: [User journey coverage]
- **Performance Tests**: [Load testing strategy]

### Test Environment Strategy
[How testing environments will be managed]

## Deployment & Operations

### Deployment Strategy
[How code gets from development to production]

### Monitoring & Observability
[What metrics and logging will be implemented]

### Maintenance & Support
[Ongoing maintenance requirements and processes]

## Resource Requirements

### Team Structure
[Recommended team composition and roles]

### Infrastructure Needs
[Hardware, cloud resources, third-party services]

### Timeline & Milestones
[High-level timeline with key milestones]

## Risk Management

### Technical Risks
[Identified technical risks and mitigation strategies]

### Project Risks
[Timeline, resource, and scope risks with mitigation plans]

### Contingency Plans
[What to do if key assumptions prove wrong]

## Communication Plan

### Regular Reviews
[Scheduled review meetings and stakeholders]

### Progress Reporting
[How progress will be tracked and communicated]

### Decision Making Process
[How technical and project decisions will be made]

## References

- Project Documentation: `[paths to key docs]`
- Architecture Decisions: `[ADR locations if applicable]`
- Requirements: `[requirements documentation]`
- Related Projects: `[links to related work]`

---

## Appendices

### A: Detailed Technical Specifications
[Technical deep-dives that don't fit in main sections]

### B: Resource Links
[Useful links, tutorials, and references for the team]

### C: Glossary
[Project-specific terms and definitions]
```

### Step 5: Plan Review & Iteration

1. **Present the draft plan**:
   ```
   I've created a comprehensive project implementation plan:
   `PROJECT_IMPLEMENTATION_PLAN.md`

   The plan includes:
   - [X] phases over [Y] weeks
   - Detailed success criteria for each phase
   - Risk management and contingency planning
   - Resource requirements and team structure
   - Technical architecture and design decisions

   Please review and let me know:
   - Are the phases and timeline realistic?
   - Do the success criteria cover all important aspects?
   - Are there any missing components or considerations?
   - Do the resource estimates align with your constraints?
   ```

2. **Iterate based on feedback**:
   - Adjust timeline and phases
   - Refine technical approach
   - Add missing requirements or constraints
   - Update resource estimates
   - Clarify success criteria

3. **Continue refining** until the plan is complete and actionable

## Important Guidelines

1. **Think Holistically**:
   - Consider the entire project lifecycle
   - Include infrastructure, operations, and maintenance
   - Plan for documentation and knowledge transfer
   - Consider team onboarding and training needs

2. **Be Realistic**:
   - Base estimates on actual project complexity
   - Include buffer time for unknowns
   - Consider team experience and availability
   - Plan for typical project challenges

3. **Make It Actionable**:
   - Provide specific, measurable deliverables
   - Include clear success criteria for each phase
   - Specify tools, processes, and standards
   - Create clear dependencies and critical path

4. **Stay Flexible**:
   - Build in review points for course correction
   - Plan for changing requirements
   - Include multiple implementation options where appropriate
   - Design phases that can be adjusted based on learning

5. **Focus on Value**:
   - Prioritize features and components by business value
   - Plan for early and frequent delivery of working software
   - Include user feedback loops in the plan
   - Ensure each phase delivers meaningful progress

## Success Criteria Guidelines

**Always separate success criteria into categories:**

1. **Automated Verification** (can be verified programmatically):
   - Build and deployment commands that must succeed
   - Test suites that must pass
   - Code quality metrics that must be met
   - Performance benchmarks that must be achieved

2. **Manual Verification** (requires human judgment):
   - User experience and interface quality
   - Documentation completeness and clarity
   - Integration with external systems
   - Performance under real-world conditions

3. **Business/Stakeholder Acceptance**:
   - Feature completeness against requirements
   - User acceptance testing results
   - Performance meeting business needs
   - Readiness for production use

## Common Project Patterns

### For New Projects:
- Start with development environment and tooling
- Establish core architecture and patterns early
- Build incrementally with frequent integration
- Plan for scalability from the beginning

### For Existing Projects:
- Thoroughly analyze current state first
- Plan migration strategies carefully
- Maintain backward compatibility where needed
- Include refactoring and technical debt reduction

### For Legacy Modernization:
- Document current system thoroughly
- Plan incremental migration approach
- Establish testing safety nets
- Include knowledge transfer planning

## Example Interaction Flow

```
User: /create_project_plan ./my-web-app
Assistant: Let me analyze your project structure and documentation...

[Reads README.md, package.json, and other key files]

Based on my analysis, I can see this is a React/Node.js web application with...

[Comprehensive analysis continues with interactive refinement]
```