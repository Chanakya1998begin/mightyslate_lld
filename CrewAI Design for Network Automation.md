

# **Design Specification: An Agentic Network Management Platform with crewai**

## **Section 1: System Architecture in the crewai Framework**

This section establishes the high-level mapping of the functional specification's architecture to crewai constructs, focusing on the overall philosophy and operational model for the agentic Al-powered network monitoring and management platform.

### **1.1. The Hierarchical Crew Model**

The functional specification describes a system centered around a "Conductor AI Agent" that orchestrates a team of specialized agents.1 This structure is inherently hierarchical, making the

crewai framework's Process.hierarchical model the ideal implementation choice. A primary Crew, designated as the "Network Operations Super-Crew," will be defined. The manager\_agent for this crew will be the **Conductor AI Agent**, granting it explicit authority to delegate tasks and manage complex workflows. The agents list for this crew will consist of the seven specialized agents detailed in the specification. This configuration directly mirrors the specification's architectural intent, ensuring the Conductor can effectively manage task sequencing, context sharing, and collaborative problem-solving.

A critical aspect of this design is recognizing that the Conductor Agent must function as a sophisticated planner, not merely a task dispatcher. The functional specification requires the Conductor to translate high-level, declarative intents—such as "Ensure video conferencing quality for the executive team"—into a series of specific, sequenced tasks for subordinate agents.1 Furthermore, it is responsible for automated root cause analysis (RCA) by correlating disparate events from multiple domains, such as performance metrics, configuration changes, and system logs.1

A simple task dispatcher would be incapable of fulfilling these requirements. The intent "Ensure video conferencing quality" is not a single, atomic task that can be handed to one agent. It necessitates a multi-step execution plan that involves reasoning and dynamic adaptation. For instance, the Conductor must first identify the executive users and their associated network traffic. Next, it must determine the network paths this traffic traverses. Following that, it must query the current performance metrics (latency, jitter, packet loss) along those paths. Concurrently, it might need to check the existing Quality of Service (QoS) configurations on the relevant network devices. Finally, based on this synthesized information, it may need to generate and apply new or modified QoS policies to meet the user's intent. This sequence demonstrates that the Conductor's primary function is to create and manage a dynamic execution graph, adapting the plan based on the results of intermediate steps. Therefore, the Conductor Agent's core implementation will be centered on an AI planning engine. Its primary goal will be defined as: "Analyze user intent, formulate a multi-step execution plan, delegate tasks to specialized agents, and synthesize the results to achieve the stated goal."

### **1.2. Agent Communication and Context Passing**

The functional specification mandates that the Conductor ensure agents "share relevant context" to collaborate effectively.1 The system's intelligence is predicated on a "Network Source of Truth (NSoT)" and a data enrichment pipeline that provides critical context to all operations.1 In the

crewai framework, this will be achieved through a combination of built-in context-passing mechanisms and a robust, shared data layer. The output of one agent's task will serve as the input context for the subsequent task in a sequence.

More fundamentally, the NSoT will function as the crew's shared, long-term memory. Maintaining a consistent worldview is a significant challenge in any multi-agent system; without a shared state, agents risk operating on stale or conflicting information, leading to incorrect actions. The NSoT, which is the responsibility of the Discovery & Inventory Agent, solves this problem by providing a canonical source for all network asset and topology information.1 It serves as the ground truth for the entire system.

This elevates the role of the Discovery & Inventory Agent beyond that of a mere specialist; it becomes the foundational agent responsible for maintaining the crew's collective memory. Its tasks to scan the network and update the NSoT will be scheduled to run continuously to ensure the data is always current. To facilitate access to this shared memory, all other agents will be equipped with a standardized set of NSoT\_Query\_Tools. An agent's standard operating procedure, before executing any task on a network device, will be to use these tools to enrich its understanding. For example, it will fetch the device's role, physical location, software version, and any known security vulnerabilities, ensuring every action is taken with the fullest possible context.

### **1.3. Overall System Workflow: Proactive and Reactive Triggers**

The platform must support both proactive functions, such as predictive maintenance and scheduled compliance auditing, and reactive functions, such as responding to real-time alerts and user-initiated intents.1 To accommodate this, the system will be architected around an external "Workflow Trigger Service" that initiates all

crewai workflows. This service will support two primary operational modes:

1. **Proactive/Scheduled Workflows:** A robust scheduling component, similar to cron, will be integrated into the Workflow Trigger Service. This scheduler will trigger the Conductor Agent with predefined Tasks at regular, configurable intervals. Example tasks include "Initiate daily PCI-DSS compliance audit across all production firewalls" or "Generate the weekly network capacity and utilization report for the data center core."  
2. **Reactive/Event-Driven Workflows:** The Workflow Trigger Service will expose an API gateway and connect to a message bus (e.g., Kafka, RabbitMQ) to listen for asynchronous, external events. Inputs such as Syslog messages, SNMP traps, webhooks from IT Service Management (ITSM) platforms, and parsed commands from the Natural Language Interface (NLI) will be received by this service. It will then normalize these events, translate them into formal crewai Task objects, and pass them to the Conductor Agent for immediate analysis and execution.

This dual-trigger architecture ensures the agentic system can operate autonomously on a schedule while remaining highly responsive to the dynamic and unpredictable events characteristic of a large enterprise network.

\!([https://i.imgur.com/vHq077w.png](https://i.imgur.com/vHq077w.png))

## **Section 2: Core Agent Definitions**

This section provides the complete crewai persona and capability definition for the Conductor AI Agent and the seven specialized agents, as derived from the functional specification.

### **2.1. Conductor AI Agent**

* **Role:** Master Orchestrator and AI Planning Strategist.  
* **Goal:** To interpret high-level human and system-generated intent, decompose it into a logical sequence of actionable tasks, delegate these tasks to a crew of specialized agents, and synthesize their findings to achieve the overarching objective and report back the results.  
* **Backstory:** You are the central intelligence of a next-generation network operations platform. You are an expert in AI planning, workflow management, and systems thinking. You do not interact with network devices directly; instead, you leverage your team of specialists, each an expert in their domain. Your primary function is to translate abstract goals into concrete execution plans, ensuring the right agent performs the right task at the right time. You are also responsible for correlating information from multiple agents to perform advanced root cause analysis, as required by the system's intelligence engine.1  
* **Tools:**  
  * Task\_Delegation\_Tool: A wrapper around the crewai delegation mechanism to assign tasks to specialized agents.  
  * RCA\_Correlation\_Tool: A tool that takes structured inputs from multiple agents (e.g., a performance alert, a configuration change log, a syslog message) and uses a correlation engine to identify the most likely root cause of an incident, fulfilling requirement 6.3.3.1  
  * ITSM\_Integration\_Tool: A tool to create, update, and resolve tickets in platforms like ServiceNow or Jira, fulfilling requirement 7.3.3.1  
  * NLI\_Parser\_Tool: A tool to process natural language input from users (as per section 7.1) and structure it into a formal goal description for planning.1

### **2.2. Discovery & Inventory Agent**

* **Role:** Network Cartographer and Asset Accountant.  
* **Goal:** To continuously scan the network, discover all connected assets, and maintain a comprehensive, real-time Network Source of Truth (NSoT) that includes hardware details, software versions, and L2/L3 topology.  
* **Backstory:** You are the foundational data gatherer for the entire network platform. Your work provides the essential context that all other agents rely on. You are meticulous and relentless in your pursuit of an accurate network map, using protocols like LLDP to map physical connections and querying devices directly to build a detailed inventory.1 Your output is the bedrock of the system's intelligence.  
* **Tools:**  
  * LLDP\_Neighbor\_Discovery\_Tool: Uses SNMP or gNMI to gather LLDP neighbor information from network devices to build the L2 topology map, as specified in requirement 5.1.3.1  
  * Device\_Inventory\_Tool: Connects to devices to retrieve serial numbers, hardware models, and exact OS/firmware versions, fulfilling requirement 5.4.1.1  
  * NSoT\_Update\_Tool: A tool with write-access to the backend relational (inventory) and graph (topology) databases to persist the discovered information.1

### **2.3. Data Collection Agent**

* **Role:** Distributed Data Ingestion Specialist.  
* **Goal:** To manage the distributed ingestion of all network data types, including streaming telemetry, SNMP metrics, logs, and flow data, ensuring data is reliably collected from across the federated architecture and forwarded to the central processing pipeline.  
* **Backstory:** You are the sensory nervous system of the platform. Operating on distributed collector nodes, you are an expert in a wide array of network protocols, from modern gNMI to legacy SNMPv3. Your job is to establish and maintain data streams from thousands of devices, handling the complexities of different protocols and data formats.1 You ensure that the analytics engine has a constant, high-fidelity stream of data to work with.  
* **Tools:**  
  * gNMI\_Subscription\_Tool: Manages persistent gNMI subscriptions for streaming telemetry.1  
  * SNMP\_Polling\_Tool: Configures and executes SNMPv3 polling for metrics from legacy devices.1  
  * Syslog\_Ingestion\_Tool: Configures syslog endpoints to receive and parse incoming log messages.1  
  * Flow\_Collector\_Tool: Configures and manages the collection of IPFIX, NetFlow, and sFlow data.1

### **2.4. Performance Monitoring Agent**

* **Role:** Network Health and Performance Analyst.  
* **Goal:** To analyze real-time and historical network performance data from Layer 1 to Layer 4, identify anomalies, establish dynamic performance baselines, and pinpoint sources of degradation.  
* **Backstory:** You are the vigilant guardian of network service quality. You have a deep understanding of what constitutes normal behavior and are an expert at spotting subtle deviations that signal trouble. You analyze everything from optical power levels in transceivers to end-to-end application latency, using unsupervised machine learning to detect anomalies that simpler systems would miss.1  
* **Tools:**  
  * TSDB\_Query\_Tool: Queries the time-series database for metrics like interface counters, CPU, latency, and jitter.1  
  * Optical\_Diagnostics\_Tool: Collects and analyzes Digital Diagnostic Monitoring (DDM/DOM) parameters from transceivers, per requirement 5.1.1.1  
  * Routing\_Health\_Tool: Monitors OSPF/BGP session states and prefix counts, per requirement 5.2.1.1  
  * Anomaly\_Detection\_Model\_Tool: A wrapper for the unsupervised learning models that detect significant deviations from baseline performance, fulfilling requirement 6.3.2.1  
  * Synthetic\_Probe\_Management\_Tool: Deploys and manages probes to actively measure latency, packet loss, and jitter across critical paths, per requirement 5.2.2.1

### **2.5. Configuration Management Agent**

* **Role:** Guardian of Device Integrity and Compliance.  
* **Goal:** To govern the entire lifecycle of device configurations, ensuring every device is correctly configured, compliant with policy, and free from unauthorized changes.  
* **Backstory:** You are the network's source of stability and order. You believe that most network outages are caused by misconfiguration, and your mission is to prevent them. You maintain a version-controlled history of every configuration, continuously audit devices against "golden" standards, and can automatically revert unauthorized changes.1 You are the enforcer of policy and the keeper of intended state.  
* **Tools:**  
  * Config\_Backup\_Tool: Performs change-triggered backups of device configurations using NETCONF or legacy methods, per requirement 5.3.1.1  
  * Version\_Control\_Tool: Interfaces with a Git-based repository to store and version all configurations.  
  * Config\_Drift\_Detection\_Tool: Compares a device's running configuration against its approved baseline in the repository, fulfilling requirement 5.3.2.1  
  * Compliance\_Audit\_Tool: Uses a rule-based engine to audit configurations against policies like NIST, PCI-DSS, etc., per requirement 5.3.3.1  
  * Network\_Interaction\_Tool: A powerful tool capable of making configuration changes using NETCONF (for transactional changes) or gNMI (for simple sets).1

### **2.6. Lifecycle Management Agent**

* **Role:** Network Fleet and Vulnerability Manager.  
* **Goal:** To manage the hardware and software lifecycle of all network assets, identifying risks associated with software vulnerabilities, End-of-Life (EoL) status, and managing the automated patching process.  
* **Backstory:** You are the long-term planner and risk manager for the network fleet. While other agents focus on the here-and-now, you look to the future, ensuring the network doesn't succumb to bit rot or unpatched vulnerabilities. You correlate the network inventory with global threat intelligence and vendor announcements to keep the fleet secure, supported, and up-to-date.1  
* **Tools:**  
  * NSoT\_Query\_Tool: To get a real-time list of all devices and their software versions from the inventory database.  
  * CVE\_Lookup\_Tool: Integrates with vendor security advisory APIs and public CVE databases to find vulnerabilities affecting assets in the NSoT, per requirement 5.4.2.1  
  * EoL\_EoS\_Check\_Tool: Checks vendor databases for End-of-Life and End-of-Support announcements, also per requirement 5.4.2.1  
  * Automated\_Patching\_Workflow\_Tool: A complex tool that orchestrates the OS upgrade process, including pre-flight checks, image transfer, and post-flight validation, as specified in 5.4.3.1

### **2.7. Security & Threat Detection Agent**

* **Role:** Cyber-Security Sentinel.  
* **Goal:** To continuously monitor the network for security threats, analyze anomalous traffic patterns, and initiate automated responses to contain and mitigate potential attacks.  
* **Backstory:** You are the network's immune system. You operate under the assumption that the network is constantly under threat. By analyzing flow data (IPFIX/NetFlow) and logs, you hunt for indicators of compromise, from reconnaissance scans to data exfiltration. You use machine learning to understand normal traffic flows, allowing you to spot malicious activity that might otherwise blend in.1  
* **Tools:**  
  * Flow\_Analysis\_Tool: Queries and analyzes IPFIX/NetFlow data to identify suspicious traffic patterns.  
  * Log\_Analysis\_Tool: Scans Syslog data for security-related events (e.g., failed logins, firewall denies).  
  * Threat\_Intelligence\_Tool: Correlates observed IP addresses and traffic patterns with known malicious actors from external threat feeds.  
  * Anomaly\_Detection\_Model\_Tool: A security-focused version of the unsupervised learning model to detect deviations in traffic patterns, per requirement 6.3.2.1  
  * Remediation\_Action\_Tool: Can initiate basic security responses, such as applying an Access Control List (ACL) to block a malicious IP, subject to Conductor approval.

### **2.8. Proactive Maintenance Agent**

* **Role:** Predictive Failure Analyst.  
* **Goal:** To use predictive analytics and machine learning to forecast network and device failures *before* they occur, enabling maintenance to be scheduled in a non-disruptive manner.  
* **Backstory:** You are a network soothsayer, using data to see the future. You understand that failures are rarely sudden; they are often preceded by subtle signs of degradation. By training machine learning models on vast amounts of historical data, you can predict with high accuracy when an optical transceiver will fail, a link will become saturated, or a fan tray will die, turning reactive operations into a planned, proactive process.1  
* **Tools:**  
  * TSDB\_Query\_Tool: To gather historical time-series data for model training and inference.  
  * Predictive\_Maintenance\_Model\_Tool: A wrapper for the ML models trained to predict hardware failures (optics, fans), link saturation, and other events, as per requirement 6.3.1.1  
  * Maintenance\_Scheduler\_Tool: Integrates with the ITSM system to proactively schedule maintenance windows based on failure predictions.

## **Section 3: Tool and Capability Specification**

This section provides detailed specifications for the Tools that bridge the agents' reasoning capabilities with the external network environment and data platforms.

### **3.1. Network Interaction Tools**

The functional specification mandates support for a mix of modern protocols like gNMI and NETCONF alongside legacy protocols like SNMPv3.1 A core design principle is that the

Tool layer must serve as a protocol abstraction layer. Forcing each agent to be aware of which protocol to use for a specific device would violate the principles of modularity and vendor-agnosticism.1 An agent should request a capability, such as "get interface metrics," and the tool should transparently handle the underlying implementation.

This leads to the design of a unified NetworkInteraction toolset. For example, a single Get\_Operational\_State\_Tool will encapsulate the protocol selection logic. When invoked, it will first query the NSoT to determine the target device's supported protocols and YANG models. It will then attempt to use the most efficient, modern protocol available, following a preferential order: gNMI with OpenConfig models, gNMI with native vendor models, NETCONF, and finally falling back to SNMPv3 for legacy devices. This approach keeps the agents' logic clean, portable, and focused on "what" to do, while the tools handle "how" to do it.

* **Tool Specifications:**  
  * Get\_Operational\_State\_Tool(device: str, path: str) \-\> dict: Retrieves operational state data. The path argument will be a standardized, model-agnostic path (e.g., 'interfaces/interface\[name=GigabitEthernet0/0\]/state'). The tool is responsible for translating this path into the correct protocol-specific format (e.g., XPath for NETCONF, gNMI Path, or OID for SNMP).  
  * Set\_Configuration\_Tool(device: str, config\_payload: dict, transactional: bool \= True) \-\> bool: Applies configuration to a device. If transactional is True, the tool MUST use NETCONF to leverage its candidate datastore, locking, and commit/rollback features for operational safety, as required by section 4.2.1.1 If  
    False, it may use gNMI Set RPCs or RESTCONF for simpler, idempotent changes.  
  * Subscribe\_To\_Telemetry\_Tool(device: str, path: str, frequency: int) \-\> str: Establishes a persistent streaming telemetry subscription using gNMI, the preferred protocol for this function.1 It returns a subscription ID for management.

### **3.2. Data Processing and Analysis Tools**

These tools provide agents with access to the various backend datastores where processed and normalized network data resides.

* **Specifications:**  
  * TSDB\_Query\_Tool(query: str) \-\> dict: Executes a query in the native language of the underlying time-series database (e.g., PromQL, InfluxQL) and returns the results.1  
  * GraphDB\_Query\_Tool(query: str) \-\> dict: Executes a query in the native language of the graph database (e.g., Cypher, Gremlin) to retrieve network topology information, such as finding all paths between two endpoints.1  
  * RelationalDB\_Query\_Tool(query: str) \-\> dict: Executes a standard SQL query against the relational database to retrieve inventory, compliance status, or other structured data.1  
  * CVE\_Lookup\_Tool(software\_product: str, software\_version: str) \-\> list: Queries public and private vulnerability databases for a given OS product and version, returning a list of associated Common Vulnerabilities and Exposures (CVEs).1

### **3.3. AI/ML Model Integration Tools**

These tools serve as wrappers, allowing agents to easily invoke complex machine learning models without needing to understand their internal architecture.

* **Specifications:**  
  * Predictive\_Maintenance\_Model\_Tool(device: str, metric\_history: dict) \-\> dict: Takes a dictionary of historical time-series data for a device or component and returns a failure probability score and a predicted time-to-failure.  
  * Anomaly\_Detection\_Model\_Tool(data\_stream: list, context: dict) \-\> dict: Takes a list of new data points (e.g., traffic volume over the last 5 minutes) and returns an anomaly score, a description of the deviation, and its statistical significance.

### **3.4. Table 3.1: Agent-to-Tool Mapping Matrix**

This matrix provides an authoritative reference for the capabilities of each agent by mapping them to the tools they require. This is essential for planning development sprints and identifying shared tool components that require prioritized implementation.

| Agent | Get\_Operational\_State\_Tool | Set\_Configuration\_Tool | TSDB\_Query\_Tool | NSoT\_Update\_Tool | NSoT\_Query\_Tool | CVE\_Lookup\_Tool | Anomaly\_Detection\_Model\_Tool | Predictive\_Maintenance\_Model\_Tool | ITSM\_Integration\_Tool |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **Conductor AI Agent** |  |  |  |  |  |  |  |  | X |
| **Discovery & Inventory Agent** | X |  |  | X |  |  |  |  |  |
| **Data Collection Agent** |  |  |  |  |  |  |  |  |  |
| **Performance Monitoring Agent** | X |  | X |  | X |  | X |  |  |
| **Configuration Management Agent** | X | X |  |  | X |  |  |  |  |
| **Lifecycle Management Agent** |  |  |  |  | X | X |  |  |  |
| **Security & Threat Detection Agent** |  |  |  |  | X |  | X |  |  |
| **Proactive Maintenance Agent** |  |  | X |  | X |  |  | X | X |

## **Section 4: Task and Workflow Implementation Blueprints**

This section provides concrete examples of how high-level operational goals are translated into crewai Tasks and executed by the agent crew, illustrating the system in action.

### **4.1. Intent-Based Task Decomposition: "Audit all core routers for PCI-DSS compliance"**

This workflow demonstrates how the system translates a high-level user intent into a detailed compliance report.

1. **User Input (NLI):** A network administrator inputs the command: "Show me all PCI-DSS compliance violations on core routers".1  
2. **Conductor Task 1 (Planning):** The Conductor Agent receives this structured intent from the NLI Parser. Its first task is to formulate an execution plan.  
   * **Step 1:** The Conductor must first identify which devices in the network are classified as "core routers." It uses its Task\_Delegation\_Tool to assign a sub-task to the Configuration Management Agent, which has access to the NSoT: Use the NSoT\_Query\_Tool with a query like 'SELECT device\_name FROM inventory WHERE role \= 'core-router''.  
   * **Step 2:** Once it receives the list of core routers, the Conductor determines that the next step is to retrieve the current running configuration for each device.  
   * **Step 3:** For each retrieved configuration, it must be audited against the predefined PCI-DSS policy rules.  
   * **Step 4:** The results of the audit must be consolidated into a single, structured report detailing any violations.  
   * **Step 5:** The final report must be formatted for human readability and presented back to the user.  
3. **Delegation:** The Conductor creates and delegates a single, high-level task to the most appropriate specialist.  
   * **Task for Configuration Management Agent:** Task(description='For the list of devices \[router-1, router-2,...\], retrieve their current configuration and audit it against the 'pci-dss-v3.2' compliance policy. Return a structured list of all violations found, including the device name, the non-compliant configuration line, and the specific PCI-DSS rule it violates.', agent=ConfigurationManagementAgent).  
4. **Execution:** The Configuration Management Agent receives the task. It iterates through the list of devices. For each device, it uses its Network\_Interaction\_Tool to fetch the configuration and its Compliance\_Audit\_Tool to perform the analysis against the specified policy.1 It compiles all findings into the requested structured format.  
5. **Conductor Task 2 (Synthesis):** The Conductor receives the structured data from the Configuration Management Agent. It then formats this data into a clear, human-readable report and delivers it to the user via the NLI.

### **4.2. Event-Driven Remediation Workflow: "BGP Peer Session Down"**

This workflow demonstrates the system's ability to react to a network event, perform root cause analysis, and execute automated remediation.

1. **Event Trigger:** A Syslog message arrives at the central collector: %BGP-5-ADJCHANGE: neighbor 192.0.2.2 Down on device core-rtr-01. The Workflow Trigger Service parses this, identifies it as a critical event, and creates a Task for the Conductor: "Investigate and resolve BGP session down event for neighbor 192.0.2.2 on device core-rtr-01".1  
2. **Conductor Task 1 (RCA):** The Conductor immediately initiates a root cause analysis workflow, parallelizing data collection by delegating tasks to multiple specialists.  
   * **Delegation 1 (Performance Agent):** Task(description='On device core-rtr-01, check the operational status and error counters for the physical interface associated with BGP neighbor 192.0.2.2. Also, query the TSDB for any latency or packet loss anomalies on the path to this neighbor in the last 30 minutes.', agent=PerformanceMonitoringAgent).  
   * **Delegation 2 (Configuration Agent):** Task(description='Check for any configuration changes committed to device core-rtr-01 in the last 60 minutes. Report any changes related to BGP or routing policy.', agent=ConfigurationManagementAgent).  
3. **Execution & Synthesis:** The Conductor waits for the results from both agents.  
   * The Performance Agent reports back: "Interface eth-0/1 is up/up with zero input/output errors. No anomalous latency or packet loss detected on the path to 192.0.2.2."  
   * The Configuration Agent reports back: "Unauthorized configuration change detected 15 minutes ago by user 'jdoe'. A new prefix-list 'DENY\_CUSTOMER\_PREFIXES' was applied to the BGP neighbor session for 192.0.2.2."  
4. **Conductor Task 2 (Remediation):** The Conductor's RCA\_Correlation\_Tool processes these two inputs. It correlates the timing of the configuration change with the BGP down event and concludes with high confidence that the unauthorized change is the root cause.1 Based on a predefined policy for this type of event, it formulates a remediation plan.  
   * **Delegation 3 (ITSM Integration):** Using its ITSM\_Integration\_Tool, the Conductor creates a high-priority incident ticket in ServiceNow, automatically populating it with the device name, event time, a summary of the investigation, and the identified root cause.1  
   * **Delegation 4 (Configuration Agent):** Task(description='Roll back the last unauthorized configuration change on device core-rtr-01. Policy requires automated remediation for this event type. Confirm BGP session re-establishes post-rollback.', agent=ConfigurationManagementAgent).  
5. **Resolution:** The Configuration Agent uses its Network\_Interaction\_Tool to revert the change. The BGP session is restored. The agent confirms this and reports success to the Conductor, which then updates the ITSM ticket to a "Resolved" state, closing the loop on the automated incident response.

## **Section 5: Data Architecture and Integration Strategy**

This section details the interaction between the crewai agents and the underlying data platform that supports their operations.

### **5.1. Data Ingestion and Normalization Pipeline**

The functional specification outlines a multi-stage data processing pipeline: Ingestion \-\> Normalization \-\> Enrichment \-\> Storage.1 In this architecture, the

Data Collection Agent is responsible solely for the **Ingestion** step. It runs on distributed collectors and is an expert at pulling data from network devices using a variety of protocols.

The subsequent stages—Normalization, Enrichment, and Storage—will be handled by a dedicated, high-throughput data engineering pipeline, likely built on technologies such as Kafka Streams, Apache Flink, or a cloud-native equivalent. This pipeline is crucial for vendor-agnosticism. It will transform vendor-specific data (e.g., a Cisco-native YANG model output) into a standardized format based on the OpenConfig YANG models.1 This ensures that when the

crewai agents query the backend datastores, they can do so using a uniform, standardized schema, regardless of the source device's vendor. This design cleanly separates the real-time task of data collection from the complex, stream-processing task of data transformation, adhering to the principle of modularity.

### **5.2. Agent Access to the Network Source of Truth (NSoT)**

The NSoT is the cornerstone of the system's contextual awareness. As specified, it will be physically implemented using a hybrid model: a relational database (e.g., PostgreSQL) for structured inventory data (serial numbers, software versions, asset tags) and a graph database (e.g., Neo4j) for modeling the complex, interconnected relationships of the network topology (L2/L3 connections).1

To provide a clean and unified access layer for the agents, these two databases will be fronted by a single, unified GraphQL API. The NSoT\_Query\_Tools provided to the agents will be clients for this API. This approach offers several advantages: it decouples the agents from the specific underlying database technologies, preventing the need to rewrite agents if a database is changed. It also provides a powerful and flexible query language, allowing an agent to request exactly the data it needs in a single query, rather than making multiple round trips to different REST endpoints.

### **5.3. Northbound Integration and User Interfaces**

The platform must provide several northbound interfaces for human operators and other IT systems, including a Natural Language Interface (NLI), a Unified Dashboard, and ITSM integration.1

* **Natural Language Interface (NLI):** A dedicated microservice will be responsible for the NLI. This service will handle speech-to-text conversion and use a Natural Language Understanding (NLU) model to classify the user's intent and extract key entities. It will then translate this into a structured JSON object representing the goal and pass it to the Conductor Agent via the Workflow Trigger Service's API.  
* **Unified Dashboard:** The dashboard will be a standalone web application. To maintain a strict separation of concerns between the control plane (the agents) and the presentation layer, the dashboard will not interact with the agents directly. Instead, it will query the same backend datastores (TSDB for metrics, NSoT databases for inventory and topology) that the agents use. This ensures the dashboard is a read-only view of the network state, preventing any possibility of it interfering with the agents' operations.  
* **ITSM Integration:** The ITSM\_Integration\_Tool used by the Conductor Agent will communicate with platforms like ServiceNow or Jira via their standard, published REST APIs. This aligns with the specification's support for RESTCONF for integrations with other IT systems and DevOps toolchains, providing a standardized method for northbound communication.1

#### **Works cited**

1. Functional Specification.pdf