# Implement Plan

You are tasked with implementing approved technical plans and task specifications. These plans contain detailed phases with specific changes and success criteria that need to be executed systematically.

## Getting Started

When given a task identifier (e.g., `TICKET-001-project-setup`):

1. **Locate the task specification**:
   - Look in the `specs/` directory for the corresponding file
   - Expected format: `specs/TICKET-XXX-task-name.md` or similar
   - Also check for related documentation like `specs/PROJECT_IMPLEMENTATION_PLAN.md`

2. **Read all relevant documentation completely**:
   - Read the specific task file fully - never use limit/offset parameters
   - Read any referenced files, tickets, or related documentation
   - Check the project's main documentation (README.md, etc.) for context
   - Look for any existing checkmarks (- [x]) to understand current progress

3. **Understand the complete context**:
   - How this task fits into the overall project
   - Dependencies on other tasks or components
   - Integration points with existing code
   - Expected outcomes and success criteria

4. **Create implementation tracking**:
   - Create a todo list to track your progress through the task
   - Note any assumptions or clarifications needed
   - Start implementing if the requirements are clear

If no task identifier is provided, respond with:
```
Please provide a task identifier to implement.

Examples:
- `/implement_plan TICKET-001-project-setup`
- `/implement_plan TASK-005-chat-ui`

I'll look for the corresponding specification file in the specs/ directory and begin implementation.
```

## Implementation Philosophy

Task specifications are carefully designed, but implementation often reveals complexities. Your approach should be:

- **Follow the specification's intent** while adapting to actual conditions
- **Implement systematically** - complete each section/phase fully before moving on
- **Verify integration** - ensure your changes work within the broader project context
- **Update progress markers** - check off completed items in the specification file
- **Maintain quality** - don't sacrifice code quality for speed

### When Reality Doesn't Match the Spec

If you encounter discrepancies between the specification and actual codebase:

1. **STOP and analyze** the situation thoroughly
2. **Document the mismatch** clearly:
   ```
   Issue in [Section/Phase]:
   Expected: [what the spec says should exist/happen]
   Found: [actual current situation]
   Impact: [how this affects the implementation]
   Recommended approach: [your suggested way forward]

   Should I proceed with this approach or do you want to adjust the specification?
   ```
3. **Wait for guidance** before proceeding if the change is significant

## Implementation Process

### Phase 1: Preparation and Setup
1. **Read and understand** the complete task specification
2. **Check current state** of the codebase related to this task
3. **Identify dependencies** and prerequisites
4. **Set up development environment** if needed
5. **Create implementation plan** based on the specification

### Phase 2: Core Implementation
1. **Follow the specification structure** (usually broken into logical sections)
2. **Implement incrementally** - make small, testable changes
3. **Test frequently** - don't wait until the end to verify functionality
4. **Update documentation** as you go
5. **Commit logical units** of work with clear messages

### Phase 3: Verification and Integration
1. **Run all specified success criteria**:
   - Automated tests and checks
   - Manual verification steps
   - Integration testing
   - Performance validation if specified

2. **Check integration points**:
   - Ensure changes don't break existing functionality
   - Verify compatibility with other components
   - Test edge cases and error handling

3. **Update progress tracking**:
   - Check off completed items in the specification file
   - Update your todo list
   - Note any deviations or issues encountered

## Verification Approach

### Automated Verification
Most projects will have standard verification commands:
- `make test` or equivalent test runner
- `make lint` or code quality checks
- `make build` or compilation verification
- Project-specific validation scripts

### Manual Verification
- Test the functionality manually according to spec requirements
- Verify user-facing changes work as expected
- Check performance under realistic conditions
- Validate error handling and edge cases

### Documentation Updates
- Update README.md if user-facing changes were made
- Update API documentation if applicable
- Add or update code comments for complex logic
- Update the specs/ files if implementation revealed needed changes

## Progress Tracking

### Update the Specification File
As you complete sections, update the original specification file:
```markdown
- [x] Set up project structure
- [x] Configure build system
- [ ] Implement core functionality  <-- Currently working on this
- [ ] Add error handling
- [ ] Write tests
```

### Maintain Your Todo List
Keep a running todo list for the current session:
```markdown
## Current Implementation Progress - TICKET-001

### Completed:
- [x] Read specification and understand requirements
- [x] Set up basic project structure
- [x] Configure pyproject.toml

### In Progress:
- [ ] Implement main.py basic structure

### Next:
- [ ] Add error handling
- [ ] Write initial tests
- [ ] Update documentation
```

## Handling Common Scenarios

### New Project Setup
- Focus on getting basic structure working first
- Ensure development environment is properly configured
- Validate that basic workflows (build, test, run) work
- Document setup instructions for other developers

### Adding New Features
- Understand how similar features are implemented
- Follow existing code patterns and conventions
- Ensure proper error handling and validation
- Add comprehensive tests for the new functionality

### Integration Tasks
- Map out all the systems that need to connect
- Test each integration point separately
- Handle failure modes gracefully
- Document the integration for future maintenance

### Refactoring or Updates
- Understand the current implementation thoroughly
- Plan changes to minimize breaking changes
- Update tests to reflect new behavior
- Ensure backward compatibility where required

## If You Get Stuck

When implementation stalls or issues arise:

1. **Re-read the specification** - make sure you understand the requirements
2. **Examine similar implementations** in the codebase for patterns
3. **Check project documentation** for architectural decisions or constraints
4. **Test your assumptions** with small experiments or prototypes

If still stuck, present the issue clearly:
```
I'm stuck on [specific part] of [task name].

What I'm trying to accomplish:
[Clear description of the goal]

What I've tried:
[List of approaches attempted]

Current blocker:
[Specific issue preventing progress]

Questions:
[Specific questions that would help unblock]
```

## Resuming Partially Completed Work

If the specification has existing checkmarks:

1. **Trust completed work** unless you find obvious issues
2. **Review recent changes** to understand the current state
3. **Pick up from the first unchecked item**
4. **Verify integration** between old and new work
5. **Run verification** to ensure nothing is broken

## Quality Standards

### Code Quality
- Follow the project's coding standards and conventions
- Write clear, readable code with appropriate comments
- Handle errors gracefully and provide helpful error messages
- Use meaningful variable and function names

### Testing
- Write tests for new functionality
- Update existing tests if behavior changes
- Ensure tests are reliable and fast
- Cover both happy path and edge cases

### Documentation
- Update user-facing documentation for new features
- Add code comments for complex logic
- Keep the specification file updated with progress
- Document any architectural decisions made during implementation

## Success Criteria

A task is complete when:

- ✅ All items in the specification are checked off
- ✅ All automated verification passes
- ✅ Manual verification confirms expected behavior
- ✅ Integration with existing code works properly
- ✅ Documentation is updated appropriately
- ✅ Code follows project quality standards

## Example Usage

```bash
# Implement a specific task
/implement_plan TICKET-001-project-setup

# Continue work on a partially completed task
/implement_plan TICKET-003-pydantic-ai-agent

# Implement with specific focus
/implement_plan TICKET-005-chat-ui focus on frontend components
```

Remember: You're not just checking boxes - you're building a working solution that integrates well with the existing project and meets the specified requirements. Keep the end goal in mind and maintain forward momentum while ensuring quality.