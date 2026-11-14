# 10. Risks and Mitigation

| Risk | Mitigation |
| :--- | :--- |
| **Delay in stable build delivery in Sprint 1** | Request early smoke builds and run automated unit tests on every pull request. |
| **Test environment downtime or corruption** | Maintain containerized Docker setup and automated database seed restore scripts. |
| **Database deadlocks under 200 concurrent transactions** | Execute early k6 load tests, optimize DB connection pooling and column indexing. |
