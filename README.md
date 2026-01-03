# Power BI Refresh Monitoring Platform

## Overview
This project is a containerized, event-driven data engineering platform for monitoring Power BI dataset refreshes using the Power BI REST API.

The system periodically collects refresh metadata, streams refresh events through Kafka, persists historical state for analysis, and exposes refresh status through Power BI dashboards and automated alerts.

It is designed as a learning-focused but production-inspired project that reflects common patterns used in modern data engineering teams.

---

## Architecture
The platform follows a decoupled architecture where orchestration, data collection, streaming, persistence, and alerting are separated into independent components.

### High-level flow
1. Apache Airflow schedules and triggers refresh monitoring jobs  
2. A collector service polls the Power BI REST API  
3. Refresh events are published to Kafka / Redpanda  
4. Consumer services process events:
   - State writer persists refresh history to PostgreSQL
   - Alert engine evaluates rules and sends notifications
5. Power BI connects to PostgreSQL to visualize refresh status and trends  

---

## Technology Stack
- Language: Python  
- Orchestration: Apache Airflow  
- Streaming: Kafka  
- Database: PostgreSQL  
- BI & Visualization: Power BI  
- Authentication: Azure AD (MSAL)  
- Containerization: Docker & Docker Compose  
- Observability (optional): Prometheus, Grafana  

---

## Key Features
- Monitor Power BI dataset refresh status and history
- Track refresh duration, failures, and SLA breaches
- Event-driven processing with Kafka
- Idempotent consumers and retry-safe polling
- Automated alerts for failed or long-running refreshes
- Fully containerized for local development and easy deployment
