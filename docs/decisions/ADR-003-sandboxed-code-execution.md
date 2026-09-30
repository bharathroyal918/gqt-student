# ADR-003: Asynchronous Sandboxed Code Execution via External Runner

## Context
The platform supports automated code execution across five languages: **Python, Java, C, C++, and JavaScript**. Students can submit arbitrary code. Executing student code inside the primary Django web process or standard worker OS would expose the system to catastrophic security risks (arbitrary system command execution, memory exhaustion, fork bombs, disk destruction, and internal network scans). Furthermore, code execution can take seconds per testcase, which would quickly exhaust synchronous web worker threads.

## Decision
We mandate an **Asynchronous Sandboxed Code Execution Architecture**:

1. **Zero Execution on Web Host:** Untrusted code is never compiled or executed directly on the host running Django.
2. **Dedicated Sandboxed Runner Service:** Code is executed in an isolated sandbox environment (e.g. Judge0 or containerized sandbox engine leveraging Linux `cgroups`, `namespaces`, `seccomp`, and network isolation).
3. **Asynchronous Task Queue:** 
   - Submissions return HTTP `202 Accepted` immediately with a submission ID.
   - Evaluation jobs are pushed to a dedicated Redis queue (`code_execution`) processed by decoupled Celery workers.
   - The worker submits test batches to the sandboxed judge, collects results, evaluates scoring rules, updates PostgreSQL, and notifies the client via polling or WebSocket/SSE.

## Consequences
- **Positive:**
  - Absolute isolation: student code cannot compromise application servers or database instances.
  - Resilience: Slow or infinite-loop student code cannot hang web API response threads.
  - Horizontal scalability: Worker nodes and judge instances can scale independently based on assessment load.
- **Negative:**
  - Requires asynchronous state handling on the frontend (polling or reactive status updates).
  - Infrastructure footprint requires running or connecting to the sandbox service.
