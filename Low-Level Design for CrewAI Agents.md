

# **Low-Level Design Specification: Core Agent Definitions**

This document provides the definitive low-level design (LLD) for the agent crew detailed in Section 2 of the "Design Specification: An Agentic Network Management Platform with crewai." Its purpose is to translate the conceptual framework into a concrete, actionable blueprint for implementation by the software engineering team. The design is governed by three core principles:

1. **Immutable Data Contracts:** All interactions between agents and tools, and between tools and external systems, will be governed by strictly-defined, versioned data schemas using Pydantic. This ensures data integrity, system predictability, and facilitates robust error handling.  
2. **Modular Abstraction:** Tools will serve as robust abstraction layers, decoupling agent logic from the specifics of network protocols, vendor APIs, and backend data stores. This promotes modularity, testability, and long-term maintainability, allowing the system to adapt to new technologies without rewriting core agent reasoning.  
3. **Observability by Design:** All components will be instrumented with structured logging and metrics from inception. This provides deep, queryable visibility into agent behavior, tool performance, and overall system health, which is essential for operating and troubleshooting a complex autonomous system.

## **Section 1: Foundational Design Patterns and Common Components**

This section establishes the architectural standards and shared components that will be used across all agents. Adherence to these patterns is mandatory to ensure consistency, reduce code duplication, and enforce best practices throughout the platform's codebase.

### **1.1 The Abstract Agent Blueprint: A Standardized Class Structure**

To enforce a consistent structure and provide common functionalities to all agents, a base class, AbstractNetworkAgent, will be defined. All eight specialized agents specified in the design document will inherit from this abstract class.1 This approach streamlines agent initialization within the CrewAI framework and integrates essential services like logging and configuration management at a foundational level.

**Implementation Details:**

The base class will provide a standardized interface for integration into the CrewAI Process.hierarchical model, where each agent class will be instantiated to form the agents list for the "Network Operations Super-Crew".1

* **Constructor:** The \_\_init\_\_ method will accept a shared configuration object, a pre-configured logger instance, and a tool-loading mechanism. This ensures that all agents are instantiated with the necessary context and dependencies.  
* **Structured Logging:** The agent will integrate with a centralized logging framework, such as structlog. This is a non-negotiable requirement to ensure that all log entries are machine-parseable JSON. Each log record must automatically include critical contextual information, such as the agent's name, the current task ID, and a unique correlation ID for tracing workflows across multiple agents and services.  
* **Tool Initialization:** A standardized method, \_load\_tools(), will be responsible for instantiating the specific tools required by the agent. This method will read the agent's tool manifest from the central configuration, initialize each tool class with the necessary dependencies (e.g., API clients, database connections), and attach them to the agent instance.

Python

\#  
\# pseudocode/conceptual example  
\#  
import structlog  
from crewai import Agent

class AbstractNetworkAgent(Agent):  
    def \_\_init\_\_(self, agent\_config, global\_config, \*\*kwargs):  
        super().\_\_init\_\_(\*\*kwargs)  
        self.config \= agent\_config  
        self.logger \= structlog.get\_logger(agent\_name=self.role)  
        self.\_load\_tools(global\_config)

    def \_load\_tools(self, global\_config):  
        \# Logic to instantiate and attach tools based on config  
        self.tools \=)  
        \]

### **1.2 Data Contracts: The Pydantic Mandate for Structured Communication**

The universal use of Pydantic BaseModel for all data structures is mandated across the system. This is a cornerstone of the architecture, transforming the abstract concept of "context passing" into a concrete, reliable mechanism for inter-agent and agent-tool communication.1 By enforcing structured, validated data flow, the system's robustness and predictability are significantly enhanced.2

The challenge in any multi-agent system is ensuring that the output of one agent's task is a valid and expected input for the next. Unstructured string outputs require brittle parsing logic in the receiving agent, leading to a high risk of runtime errors. By leveraging Pydantic models, the "context" passed between agents becomes a self-validating, self-documenting object. This approach effectively establishes a robust, system-wide type system, which drastically reduces the likelihood of integration errors, simplifies agent logic by eliminating the need for parsing, and makes the entire system more resilient to unexpected or malformed data from external APIs and network devices.5

**Canonical Models:**

* **Tool Input Models:** Every tool must define a Pydantic model that inherits from BaseModel and specifies its expected input parameters. These models must include precise type hints, descriptive field names, and clear descriptions using Field from Pydantic. Where applicable, validators should be used to enforce constraints (e.g., valid IP address format, non-empty strings).  
* **Tool Output Models:** To standardize how agents handle the results of tool execution, a generic ToolOutput model is defined. Every tool function must return an instance of this model. This structure forces a clear separation between successful and failed executions, allowing agent logic to handle errors gracefully and predictably without relying on ambiguous return values like None or raising unhandled exceptions.  
  Python  
  \#  
  \# in a shared 'models.py' module  
  \#  
  from typing import Any, Optional, Literal  
  from pydantic import BaseModel

  class ToolOutput(BaseModel):  
      """Standardized return structure for all tools."""  
      status: Literal\['success', 'error'\]  
      data: Optional\[Any\] \= None \# Should be a specific Pydantic model for the successful result  
      error\_message: Optional\[str\] \= None  
      error\_details: Optional\[dict\] \= None

### **1.3 Secure Configuration and Secrets Management**

A centralized configuration management system, utilizing a library such as pydantic-settings, will be employed to load application settings from environment variables and/or YAML files. This ensures a consistent and predictable configuration-loading process.

A critical security requirement is the complete separation of secrets from the application configuration and source code. All sensitive information, including device credentials, API keys, and authentication tokens, **must** be managed by and retrieved from a dedicated secrets management backend (e.g., HashCorp Vault, AWS Secrets Manager, Azure Key Vault). The configuration loading mechanism will be responsible for securely fetching these secrets at application startup and injecting them into the relevant components. Storing secrets directly in Git, configuration files, or environment variables in production environments is strictly prohibited.

### **Table 1.1: Master Dependency Matrix**

This matrix provides a single, authoritative reference for the primary third-party Python dependencies required for each agent's toolset. This is an invaluable resource for project setup, dependency management (e.g., defining extras in pyproject.toml), and understanding the technological footprint of the system. It accelerates developer onboarding by clarifying the specific libraries needed for a given task and helps in assessing the impact of library upgrades or security vulnerabilities.

| Agent | Tool | Primary Python Library/Dependency |
| :---- | :---- | :---- |
| Conductor AI Agent | ITSM\_Integration\_Tool | pysnc, jira |
| Conductor AI Agent | NLI\_Parser\_Tool | spacy |
| Conductor AI Agent | RCA\_Correlation\_Tool | (Internal Logic) |
| Discovery & Inventory | LLDP\_Neighbor\_Discovery\_Tool | pysnmp |
| Discovery & Inventory | Device\_Inventory\_Tool | pysnmp, ncclient |
| Discovery & Inventory | NSOT\_Update\_Tool | httpx |
| Data Collection | gNMI\_Subscription\_Tool | pygnmi |
| Data Collection | SNMP\_Polling\_Tool | pysnmp |
| Performance Monitoring | TSDB\_Query\_Tool | httpx |
| Performance Monitoring | Optical\_Diagnostics\_Tool | pysnmp, ncclient |
| Performance Monitoring | Routing\_Health\_Tool | pysnmp, ncclient |
| Configuration Mgmt | Network\_Interaction\_Tool | ncclient, pygnmi |
| Configuration Mgmt | Version\_Control\_Tool | GitPython |
| Lifecycle Management | CVE\_Lookup\_Tool | httpx |
| Lifecycle Management | EoL\_EOS\_Check\_Tool | httpx |
| Security & Threat Detection | Flow\_Analysis\_Tool | elasticsearch-dsl or equivalent |
| Security & Threat Detection | Log\_Analysis\_Tool | elasticsearch-dsl or equivalent |
| Security & Threat Detection | Threat\_Intelligence\_Tool | httpx |
| Proactive Maintenance | Predictive\_Maintenance\_Model\_Tool | scikit-learn, xgboost |

## **Section 2: Conductor AI Agent: Low-Level Specification**

This section provides the detailed implementation blueprint for the ConductorAlAgent. As the "Master Orchestrator and AI Planning Strategist," this agent is the central intelligence of the crew, responsible for decomposing high-level intent into executable workflows.1

### **2.1 Class Definition and Initialization**

The agent will be implemented as a Python class inheriting from the common AbstractNetworkAgent.

Python

\#  
\# in 'agents/conductor.py'  
\#  
from.common import AbstractNetworkAgent, ToolOutput  
from.tools import (  
    TaskDelegationTool,  
    RCACorrelationTool,  
    ITSMIntegrationTool,  
    NLIParserTool  
)

class ConductorAlAgent(AbstractNetworkAgent):  
    """  
    Master Orchestrator and AI Planning Strategist.  
    Interprets intent, creates execution plans, delegates tasks,  
    and synthesizes results.  
    """  
    def \_\_init\_\_(self, agent\_config, global\_config):  
        super().\_\_init\_\_(  
            agent\_config=agent\_config,  
            global\_config=global\_config,  
            role="Master Orchestrator and AI Planning Strategist",  
            goal=(  
                "To interpret high-level human and system-generated intent, "  
                "decompose it into a logical sequence of actionable tasks, "  
                "delegate these tasks to a crew of specialized agents, and "  
                "synthesize their findings to achieve the overarching "  
                "objective and report back the results."  
            ),  
            backstory=(  
                "You are the central intelligence of a next-generation "  
                "network operations platform. You are an expert in AI planning, "  
                "workflow management, and systems thinking. You do not interact "  
                "with network devices directly; instead, you leverage your team "  
                "of specialists. Your primary function is to translate abstract "  
                "goals into concrete execution plans. You are also responsible "  
                "for correlating information from multiple agents to perform "  
                "advanced root cause analysis."  
            ),  
            allow\_delegation=True  
        )

**Initialization:** The constructor will be configured with policies for automated remediation. This will be implemented as a mapping in the configuration file that links specific event types or incident patterns to a boolean flag indicating whether automated remediation is permitted. This allows operators to maintain granular control over the agent's autonomy.

### **2.2 Tool Implementation Specifications**

#### **2.2.1 Task\_Delegation\_Tool**

* **Purpose:** To provide a structured and observable wrapper around CrewAI's native task delegation mechanism. While CrewAI handles delegation internally, this tool ensures that every delegation act is explicitly logged with structured context and that any failures in the delegation process itself are caught and handled uniformly.  
* **Function Signature:** def delegate\_task(self, agent: str, task\_description: str, context: dict) \-\> ToolOutput:  
* **Logic:** The tool will receive the name of the target agent and the task description. Before delegating, it will log a structured message containing the target agent, a hash of the task description, and the keys of the context dictionary. This provides an audit trail of the Conductor's decisions. It will then invoke the underlying CrewAI delegation function within a try...except block to catch any framework-level errors, returning a standardized ToolOutput object.

#### **2.2.2 RCA\_Correlation\_Tool**

* **Purpose:** To perform automated root cause analysis by correlating disparate events from multiple domains, fulfilling the critical intelligence requirement 6.3.3.1  
* **Function Signature:** def correlate\_events(self, events: List) \-\> ToolOutput:  
* **Pydantic Models:**  
  Python  
  from datetime import datetime  
  from typing import List, Literal  
  from pydantic import BaseModel, Field

  class RCAEventInput(BaseModel):  
      """Structured input for a single event to be correlated."""  
      timestamp: datetime \= Field(description="The exact UTC timestamp of the event.")  
      source\_agent: str \= Field(description="The name of the agent that reported the event.")  
      event\_type: Literal\[  
          'config\_change', 'performance\_threshold\_breach',  
          'bgp\_session\_down', 'interface\_down', 'high\_cpu', 'security\_alert'  
      \] \= Field(description="The category of the event.")  
      device: str \= Field(description="The hostname or IP of the affected device.")  
      details: dict \= Field(description="A dictionary containing event-specific data.")

  class RCAResult(BaseModel):  
      """The structured output of the correlation analysis."""  
      root\_cause\_summary: str \= Field(description="A human-readable summary of the most likely root cause.")  
      confidence\_score: float \= Field(ge=0.0, le=1.0, description="The confidence score (0.0 to 1.0) of the identified root cause.")  
      contributing\_events: List \= Field(description="The list of events that contributed to the conclusion.")

* **Logic:** The tool will implement a rule-based correlation engine. The initial implementation will focus on two primary dimensions:  
  1. **Temporal Proximity:** It will analyze events occurring within a configurable time window (e.g., 5 minutes).  
  2. Entity Correlation: It will group events related to the same entity (e.g., device hostname, interface name, BGP peer IP address).  
     A high-confidence root cause will be identified when a config\_change event is temporally and entity-correlated with a subsequent negative-impact event like bgp\_session\_down or performance\_threshold\_breach. The logic will be designed to be extensible, allowing for more sophisticated correlation rules in the future.

#### **2.2.3 ITSM\_Integration\_Tool**

* **Purpose:** To provide a standardized interface for creating, updating, and resolving tickets in external IT Service Management (ITSM) platforms like ServiceNow or Jira, fulfilling requirement 7.3.3.1  
* **Implementation:** The design of this tool is critical for the platform's adaptability in diverse enterprise environments. A hardcoded implementation for a single ITSM system would severely limit its deployability. Therefore, an **Adapter Pattern** will be implemented. A primary ITSMIntegrationTool class will be instantiated with a specific adapter (e.g., ServiceNowAdapter or JiraAdapter) based on the system's runtime configuration. This decouples the Conductor Agent's abstract intent ("create a ticket") from the concrete implementation details of a specific ITSM vendor's API. This design choice is a key business enabler, making the platform portable and reducing customer deployment friction.  
* **Jira Adapter:**  
  * **Library:** The official jira Python library will be used due to its comprehensive coverage of the Jira REST API.7  
  * **Authentication:** The adapter will be configured to use API token-based authentication, which is the standard and most secure method for programmatic access to Jira Cloud and Server.7 The user's email and API token will be retrieved from the secure secrets management backend.  
  * **Core Functions:** create\_ticket, update\_ticket\_status, add\_comment.  
* **ServiceNow Adapter:**  
  * **Library:** The pysnc library will be used.10 Its key advantage is that it provides a Pythonic interface that mimics ServiceNow's server-side  
    GlideRecord API. This makes the code more intuitive for developers who may have experience with ServiceNow scripting and simplifies interactions with the Table API.  
  * **Authentication:** The adapter will support both Basic Authentication (username/password) and OAuth 2.0, with the choice determined by configuration. Credentials will be fetched from the secrets backend.  
  * **Core Functions:** create\_ticket, update\_ticket\_status, add\_comment.  
* **Pydantic Models:**  
  Python  
  from typing import Optional, Literal  
  from pydantic import BaseModel, Field

  class TicketInput(BaseModel):  
      """Standardized input for creating or updating an ITSM ticket."""  
      title: str \= Field(description="The short summary or title of the ticket.")  
      description: str \= Field(description="The detailed description of the incident or request.")  
      priority: Literal\['Low', 'Medium', 'High', 'Critical'\]  
      affected\_device: Optional\[str\] \= Field(None, description="The primary network device involved.")  
      correlation\_id: Optional\[str\] \= Field(None, description="A unique ID for tracing this workflow.")

  class TicketOutput(BaseModel):  
      """Standardized output after a ticket operation."""  
      ticket\_id: str \= Field(description="The unique identifier of the ticket in the ITSM system.")  
      status: str \= Field(description="The current status of the ticket.")  
      url: str \= Field(description="A direct URL to view the ticket in the ITSM UI.")

#### **2.2.4 NLI\_Parser\_Tool**

* **Purpose:** To process natural language commands from users, structure them into a formal goal with identified entities, and pass this structured data to the Conductor for planning, as per section 7.1.1  
* **Library:** spaCy is the selected library for this task.11 It is chosen over alternatives like NLTK for its superior performance, modern API, and production-ready design. Its pre-trained models for Named Entity Recognition (NER) are highly effective for extracting common entities like device names and locations out-of-the-box.12 More complex deep learning approaches using TensorFlow are powerful but introduce significant complexity and are not necessary for the initial implementation.13  
* **Function Signature:** def parse\_intent(self, text: str) \-\> ToolOutput:  
* **Logic:**  
  1. **Initialization:** A pre-trained spaCy model (e.g., en\_core\_web\_lg) will be loaded once when the tool is initialized to avoid reloading it on every call.  
  2. **Intent Classification:** A rule-based matching system or a simple keyword-based classifier will be used to determine the primary *intent*. For example, the presence of words like "audit," "compliance," or "violations" will map to a get\_compliance\_report intent.  
  3. **Entity Extraction:** spaCy's built-in NER will be used to extract generic entities. This will be supplemented with custom entity recognition rules using spaCy's EntityRuler to identify domain-specific terms like "core routers," "PCI-DSS," or specific interface names.  
* **Pydantic Models:**  
  Python  
  from typing import Dict  
  from pydantic import BaseModel, Field

  class StructuredIntentOutput(BaseModel):  
      """The structured representation of a natural language command."""  
      intent: str \= Field(description="The classified primary intent of the user command.")  
      entities: Dict\[str, str\] \= Field(description="A dictionary of extracted entities, e.g., {'device\_role': 'core routers'}.")  
      original\_text: str \= Field(description="The original, unmodified user input text.")

## **Section 3: Discovery & Inventory Agent: Low-Level Specification**

This section details the implementation of the DiscoveryInventoryAgent. This agent is foundational to the entire system's intelligence, as it is responsible for populating and maintaining the Network Source of Truth (NSoT), which serves as the crew's shared, long-term memory.1

### **3.1 Class Definition and Initialization**

The agent will be implemented as a Python class inheriting from AbstractNetworkAgent.

Python

\#  
\# in 'agents/discovery.py'  
\#  
from.common import AbstractNetworkAgent  
from.tools import LLDPNeighborDiscoveryTool, DeviceInventoryTool, NSOTUpdateTool

class DiscoveryInventoryAgent(AbstractNetworkAgent):  
    """  
    Network Cartographer and Asset Accountant.  
    Continuously scans the network to discover assets and maintain the NSOT.  
    """  
    def \_\_init\_\_(self, agent\_config, global\_config):  
        super().\_\_init\_\_(  
            agent\_config=agent\_config,  
            global\_config=global\_config,  
            role="Network Cartographer and Asset Accountant",  
            goal=(  
                "To continuously scan the network, discover all connected assets, "  
                "and maintain a comprehensive, real-time Network Source of Truth "  
                "(NSOT) that includes hardware details, software versions, and "  
                "L2/L3 topology."  
            ),  
            backstory=(  
                "You are the foundational data gatherer for the entire network platform. "  
                "Your work provides the essential context that all other agents rely on. "  
                "You are meticulous and relentless in your pursuit of an accurate "  
                "network map, using protocols like LLDP to map physical connections "  
                "and querying devices directly to build a detailed inventory. Your "  
                "output is the bedrock of the system's intelligence."  
            ),  
            allow\_delegation=False  
        )

**Initialization:** The constructor will be configured with the API endpoint and authentication credentials for the NSoT's unified GraphQL API.

### **3.2 Tool Implementation Specifications**

#### **3.2.1 LLDP\_Neighbor\_Discovery\_Tool**

* **Purpose:** To build the Layer 2 topology map by gathering Link Layer Discovery Protocol (LLDP) neighbor information from network devices, fulfilling requirement 5.1.3.1  
* **Library:** pysnmp is the designated library for this task.15 It provides a robust, pure-Python implementation of an SNMP engine capable of performing the necessary  
  GET and GETNEXT operations to query the standard LLDP-MIB. Other libraries considered, such as lldpy 17 or those using  
  scapy 18, are designed for interacting with the local host's LLDP daemon or for packet crafting, which is not suitable for remotely polling a fleet of network devices.  
* **Function Signature:** def discover\_neighbors(self, device\_ip: str, snmp\_creds: dict) \-\> ToolOutput:  
* **Logic:** The tool will perform an SNMP walk (nextCmd) on the lldpRemoteSystemsData branch of the LLDP-MIB. It will parse the results to correlate the local port (lldpLocPortId) with the remote device's chassis ID (lldpRemChassisId), port ID (lldpRemPortId), and system name (lldpRemSysName). The results will be compiled into a list of LLDPNeighbor objects.  
* **Pydantic Models:**  
  Python  
  from typing import List  
  from pydantic import BaseModel, Field

  class LLDPNeighbor(BaseModel):  
      """Represents a single discovered LLDP neighbor."""  
      local\_interface: str \= Field(description="The name of the local interface where the neighbor was discovered.")  
      remote\_chassis\_id: str \= Field(description="The chassis ID (typically MAC address) of the remote device.")  
      remote\_port\_id: str \= Field(description="The port ID (e.g., interface name) of the remote device.")  
      remote\_system\_name: str \= Field(description="The hostname of the remote device.")

  class LLDPNeighborOutput(BaseModel):  
      """The complete list of LLDP neighbors for a given device."""  
      device: str \= Field(description="The device from which the neighbor data was collected.")  
      neighbors: List

#### **3.2.2 Device\_Inventory\_Tool**

* **Purpose:** To connect to devices and retrieve detailed hardware and software inventory information, including serial numbers, hardware models, and exact OS versions, fulfilling requirement 5.4.1.1  
* **Library:** This tool will use a multi-protocol approach to maximize data accuracy.  
  * pysnmp 15 will be used as the primary method for retrieving hardware information by querying standard MIBs like  
    ENTITY-MIB (entPhysicalSerialNum, entPhysicalModelName).  
  * ncclient 19 will be used as a preferred secondary method for retrieving the exact OS version from devices that support NETCONF. NETCONF often provides more precise and structured version information than the generic  
    sysDescr OID in SNMP.  
* **Function Signature:** def get\_inventory(self, device\_ip: str, creds: dict) \-\> ToolOutput:  
* **Logic:** The tool will first attempt to connect to the device using NETCONF. If successful, it will retrieve the OS version. It will then connect using SNMP to gather hardware details. If the NETCONF connection fails, it will fall back to using SNMP for the OS version as well. This preferential logic ensures the highest quality data is collected when available.  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel, Field

  class DeviceInventoryRecord(BaseModel):  
      """A structured record of a device's inventory details."""  
      device: str \= Field(description="The hostname or IP of the inventoried device.")  
      serial\_number: str \= Field(description="The primary chassis serial number.")  
      model: str \= Field(description="The hardware model number.")  
      os\_version: str \= Field(description="The exact operating system version string.")

#### **3.2.3 NSOT\_Update\_Tool**

* **Purpose:** To persist the discovered inventory and topology information into the backend NSoT databases, acting as the write-interface for the agent's findings.1  
* **Logic:** In adherence with the high-level design's data architecture (Section 5.2), this tool will **not** have direct database access.1 Direct database connections from agents would create tight coupling and security risks. Instead, the tool will act as a client to the unified GraphQL API that fronts the NSoT. This API abstracts the underlying hybrid database implementation (relational for inventory, graph for topology). The tool will use a standard, robust HTTP client library like  
  httpx to send GraphQL mutation operations to the API endpoint. This ensures a clean separation of concerns and a secure, manageable data access layer.  
* **Function Signature:** def update\_nsot(self, data: Union) \-\> ToolOutput:  
* **Pydantic Models:** The tool's input will be one of the output models from the other two discovery tools (DeviceInventoryRecord or LLDPNeighborOutput). Its own output will be a simple status model.  
  Python  
  from pydantic import BaseModel, Field

  class NSOTUpdateStatus(BaseModel):  
      """The result of an update operation to the NSOT."""  
      success: bool  
      message: str \= Field(description="A message indicating the result of the operation.")  
      object\_id: Optional\[str\] \= Field(None, description="The ID of the created or updated object in the NSOT.")

## **Section 4: Data Collection Agent: Low-Level Specification**

The DataCollectionAgent is the sensory nervous system of the platform. It operates on distributed collector nodes and is responsible for the ingestion phase of the data pipeline, establishing and maintaining data streams from thousands of network devices.1

### **4.1 Class Definition and Initialization**

Python

\#  
\# in 'agents/datacollection.py'  
\#  
from.common import AbstractNetworkAgent  
from.tools import (  
    GNMISubscriptionTool,  
    SNMPPollingTool,  
    SyslogIngestionTool,  
    FlowCollectorTool  
)

class DataCollectionAgent(AbstractNetworkAgent):  
    """  
    Distributed Data Ingestion Specialist.  
    Manages the ingestion of telemetry, SNMP, logs, and flow data.  
    """  
    def \_\_init\_\_(self, agent\_config, global\_config):  
        super().\_\_init\_\_(  
            agent\_config=agent\_config,  
            global\_config=global\_config,  
            role="Distributed Data Ingestion Specialist",  
            goal=(  
                "To manage the distributed ingestion of all network data types, "  
                "including streaming telemetry, SNMP metrics, logs, and flow data, "  
                "ensuring data is reliably collected from across the federated "  
                "architecture and forwarded to the central processing pipeline."  
            ),  
            backstory=(  
                "You are the sensory nervous system of the platform. Operating on "  
                "distributed collector nodes, you are an expert in a wide array of "  
                "network protocols, from modern gNMI to legacy SNMPv3. Your job is "  
                "to establish and maintain data streams from thousands of devices, "  
                "handling the complexities of different protocols and data formats. "  
                "You ensure that the analytics engine has a constant, "  
                "high-fidelity stream of data to work with."  
            ),  
            allow\_delegation=False  
        )

### **4.2 Tool Implementation Specifications**

#### **4.2.1 gNMI\_Subscription\_Tool**

* **Purpose:** To manage persistent gNMI subscriptions for modern, high-frequency streaming telemetry.  
* **Library:** pygnmi is the chosen library for this tool due to its pure Python implementation, active maintenance, and clear API for handling gNMI RPCs, including Subscribe.21 Alternatives like  
  cisco-gnmi-python are also viable but pygnmi is more vendor-agnostic.23  
* **Function Signature:** def manage\_subscription(self, device: str, subscriptions: List, action: Literal\['create', 'delete'\]) \-\> ToolOutput:  
* **Logic:** The tool will establish a secure gRPC channel to the target device. For a create action, it will construct a SubscribeRequest message containing the list of subscription paths and desired sample intervals. It will then initiate the subscription and manage the persistent connection, forwarding received telemetry messages to the central data bus (e.g., Kafka). For a delete action, it will terminate the corresponding gRPC stream.  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel, Field

  class GNMISubscription(BaseModel):  
      """Defines a single gNMI subscription path."""  
      path: str \= Field(description="The YANG-based gNMI path to subscribe to.")  
      sample\_interval\_ms: int \= Field(description="The desired data emission interval in milliseconds.")

  class GNMISubscriptionStatus(BaseModel):  
      """The result of a subscription management operation."""  
      device: str  
      action: str  
      status: str  
      message: Optional\[str\] \= None

#### **4.2.2 SNMP\_Polling\_Tool**

* **Purpose:** To configure and execute periodic SNMPv3 polling for metrics from legacy devices that do not support streaming telemetry.  
* **Library:** pysnmp will be used for its comprehensive support for SNMPv1/v2c/v3 and its robust, asynchronous IO capabilities, which are essential for polling a large number of devices efficiently.15  
* **Function Signature:** def manage\_polling\_job(self, device: str, oids: List\[str\], poll\_interval\_sec: int, action: Literal\['create', 'delete'\]) \-\> ToolOutput:  
* **Logic:** This tool will not perform the polling itself in a blocking manner. Instead, it will interact with a dedicated, high-performance polling engine (e.g., Telegraf with SNMP input plugin, or a custom pysnmp-based poller service). The tool's role is to manage the configuration of this engine. A create action will add a new polling job to the engine's configuration, specifying the target device, the list of OIDs to poll, the polling interval, and the SNMPv3 credentials. A delete action will remove the job.  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel

  class SNMPPollingJobStatus(BaseModel):  
      """The result of an SNMP polling job management operation."""  
      device: str  
      action: str  
      status: str  
      message: Optional\[str\] \= None

#### **4.2.3 Syslog\_Ingestion\_Tool**

* **Purpose:** To configure syslog endpoints to receive and parse incoming log messages from network devices.  
* **Logic:** Similar to the SNMPPollingTool, this tool does not implement a syslog server. It manages the configuration of a dedicated syslog ingestion service (e.g., rsyslog, syslog-ng, or Fluentd). The tool's function will be to update the configuration of this service to accept logs from a new device IP address and apply the correct parsing rules based on the device type (retrieved from the NSoT). This involves generating the appropriate configuration snippets and triggering a service reload.  
* **Function Signature:** def configure\_syslog\_source(self, device: str, device\_type: str, action: Literal\['add', 'remove'\]) \-\> ToolOutput:

#### **4.2.4 Flow\_Collector\_Tool**

* **Purpose:** To configure and manage the collection of network flow data (IPFIX, NetFlow, sFlow).  
* **Logic:** This tool manages the configuration of a dedicated flow collection engine (e.g., pmacct, Elastiflow, or a commercial collector). Its primary function is to update the collector's configuration to accept flow packets from specified device IPs and to apply appropriate sampling rates or templates. The tool will generate the necessary configuration and trigger a reload of the collector service.  
* **Function Signature:** def configure\_flow\_source(self, device: str, flow\_type: Literal\['netflow\_v9', 'ipfix', 'sflow'\], action: Literal\['add', 'remove'\]) \-\> ToolOutput:

## **Section 5: Performance Monitoring Agent: Low-Level Specification**

The PerformanceMonitoringAgent is the vigilant guardian of network service quality. It analyzes real-time and historical performance data to identify anomalies, establish dynamic baselines, and pinpoint sources of degradation.1

### **5.1 Class Definition and Initialization**

Python

\#  
\# in 'agents/performance.py'  
\#  
from.common import AbstractNetworkAgent  
\#... import tool classes

class PerformanceMonitoringAgent(AbstractNetworkAgent):  
    """  
    Network Health and Performance Analyst.  
    Analyzes performance data, identifies anomalies, and pinpoints degradation.  
    """  
    def \_\_init\_\_(self, agent\_config, global\_config):  
        super().\_\_init\_\_(  
            agent\_config=agent\_config,  
            global\_config=global\_config,  
            role="Network Health and Performance Analyst",  
            goal=(  
                "To analyze real-time and historical network performance data "  
                "from Layer 1 to Layer 4, identify anomalies, establish dynamic "  
                "performance baselines, and pinpoint sources of degradation."  
            ),  
            backstory=(  
                "You are the vigilant guardian of network service quality. You have "  
                "a deep understanding of what constitutes normal behavior and are an "  
                "expert at spotting subtle deviations that signal trouble. You analyze "  
                "everything from optical power levels in transceivers to end-to-end "  
                "application latency, using unsupervised machine learning to detect "  
                "anomalies that simpler systems would miss."  
            ),  
            allow\_delegation=False  
        )

### **5.2 Tool Implementation Specifications**

#### **5.2.1 TSDB\_Query\_Tool**

* **Purpose:** To provide a standardized interface for querying the backend time-series database (TSDB) for metrics like interface counters, CPU utilization, latency, and jitter.  
* **Library:** A standard HTTP client like httpx will be used. The tool will be configured with the API endpoint of the TSDB (e.g., Prometheus, InfluxDB, VictoriaMetrics).  
* **Function Signature:** def query\_tsdb(self, query: str) \-\> ToolOutput:  
* **Logic:** The tool will take a query string in the native language of the underlying TSDB (e.g., PromQL). It will execute this query against the TSDB's HTTP API and parse the JSON response. The raw data will be structured into a Pydantic model before being returned.  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel

  class TimeSeriesDataPoint(BaseModel):  
      """A single data point in a time series."""  
      timestamp: int \# Unix timestamp  
      value: float

  class TimeSeriesResult(BaseModel):  
      """A single time series with its labels and data points."""  
      metric: dict \# e.g., {'device': 'core-rtr-01', 'interface': 'GigabitEthernet0/0'}  
      values: List

  class TSDBQueryOutput(BaseModel):  
      """The structured result of a TSDB query."""  
      results: List

#### **5.2.2 Optical\_Diagnostics\_Tool**

* **Purpose:** To collect and analyze Digital Diagnostic Monitoring (DDM/DOM) parameters from optical transceivers, fulfilling requirement 5.1.1.1.1  
* **Library:** A combination of pysnmp and ncclient, following the multi-protocol pattern of the DeviceInventoryTool. Many vendors expose optical data via proprietary MIBs or the ENTITY-SENSOR-MIB. Modern systems often expose this data via structured YANG models (e.g., OpenConfig) accessible via NETCONF/gNMI.  
* **Function Signature:** def get\_optical\_diagnostics(self, device: str, interface: str) \-\> ToolOutput:  
* **Logic:** The tool will first attempt to retrieve optical data using NETCONF and the OpenConfig openconfig-platform-transceiver YANG model. If this fails, it will fall back to querying known SNMP MIBs. The tool will parse values for Rx/Tx power, temperature, and voltage.  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel, Field

  class OpticalLaneDiagnostics(BaseModel):  
      """Diagnostics for a single lane of an optical transceiver."""  
      lane\_id: int  
      rx\_power\_dbm: float  
      tx\_power\_dbm: float

  class OpticalDiagnosticsOutput(BaseModel):  
      """Complete optical diagnostics for a transceiver."""  
      device: str  
      interface: str  
      temperature\_celsius: float  
      voltage\_volts: float  
      lanes: List

#### **5.2.3 Routing\_Health\_Tool**

* **Purpose:** To monitor the health of routing protocols by checking OSPF/BGP session states and prefix counts, fulfilling requirement 5.2.1.1  
* **Library:** pysnmp and ncclient. Standard MIBs like BGP4-MIB and OSPF-MIB provide session state information. NETCONF/gNMI provides a more robust and structured way to query routing state using models like openconfig-bgp.  
* **Function Signature:** def get\_bgp\_summary(self, device: str) \-\> ToolOutput:  
* **Logic:** The tool will query the device for its list of BGP peers and their current state (Established, Idle, etc.) and the number of prefixes received from each peer. The logic will prioritize NETCONF/gNMI for data retrieval.  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel

  class BGPPeer(BaseModel):  
      """State of a single BGP peer."""  
      peer\_address: str  
      remote\_as: int  
      state: str  
      prefixes\_received: int  
      uptime\_sec: int

  class BGPHealthOutput(BaseModel):  
      """Summary of BGP health on a device."""  
      device: str  
      peers: List

#### **5.2.4 Anomaly\_Detection\_Model\_Tool**

* **Purpose:** To serve as a wrapper for unsupervised machine learning models that detect significant deviations from baseline performance, fulfilling requirement 6.3.2.1  
* **Logic:** This tool is an interface to a pre-trained ML model (e.g., Isolation Forest, Autoencoder) served via a model-serving framework (like MLflow or a simple Flask/FastAPI wrapper). The tool will take a stream of recent time-series data, send it to the model's API endpoint for inference, and parse the resulting anomaly score and explanation.  
* **Function Signature:** def detect\_anomaly(self, metric\_name: str, data\_stream: List) \-\> ToolOutput:  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel

  class AnomalyDetectionOutput(BaseModel):  
      """The result of an anomaly detection inference."""  
      is\_anomaly: bool  
      anomaly\_score: float  
      message: str \# e.g., "Metric deviated by 3.5 standard deviations from the 4-week baseline."

#### **5.2.5 Synthetic\_Probe\_Management\_Tool**

* **Purpose:** To deploy and manage active synthetic probes to measure latency, packet loss, and jitter across critical network paths, as per requirement 5.2.2.1  
* **Logic:** This tool will interact with the API of a synthetic monitoring system (e.g., ThousandEyes, or an open-source solution). It will have functions to create, delete, and retrieve results from probes between specified source and destination points.  
* **Function Signature:** def manage\_probe(self, source: str, destination: str, test\_type: Literal\['http', 'ping', 'path\_trace'\], action: Literal\['create', 'delete', 'get\_results'\]) \-\> ToolOutput:

## **Section 6: Configuration Management Agent: Low-Level Specification**

The ConfigurationManagementAgent is the guardian of device integrity and compliance. It governs the entire lifecycle of device configurations, ensuring stability, enforcing policy, and preventing unauthorized changes.1

### **6.1 Class Definition and Initialization**

Python

\#  
\# in 'agents/config.py'  
\#  
from.common import AbstractNetworkAgent  
\#... import tool classes

class ConfigurationManagementAgent(AbstractNetworkAgent):  
    """  
    Guardian of Device Integrity and Compliance.  
    Governs the lifecycle of device configurations.  
    """  
    def \_\_init\_\_(self, agent\_config, global\_config):  
        super().\_\_init\_\_(  
            agent\_config=agent\_config,  
            global\_config=global\_config,  
            role="Guardian of Device Integrity and Compliance",  
            goal=(  
                "To govern the entire lifecycle of device configurations, "  
                "ensuring every device is correctly configured, compliant "  
                "with policy, and free from unauthorized changes."  
            ),  
            backstory=(  
                "You are the network's source of stability and order. You believe "  
                "that most network outages are caused by misconfiguration, and your "  
                "mission is to prevent them. You maintain a version-controlled "  
                "history of every configuration, continuously audit devices against "  
                "'golden' standards, and can automatically revert unauthorized changes. "  
                "You are the enforcer of policy and the keeper of intended state."  
            ),  
            allow\_delegation=False  
        )

### **6.2 Tool Implementation Specifications**

#### **6.2.1 Config\_Backup\_Tool**

* **Purpose:** To perform backups of device configurations, triggered by detected changes, as per requirement 5.3.1.1.1  
* **Logic:** This tool will leverage the Network\_Interaction\_Tool to retrieve the full running configuration from a device. Upon retrieval, it will pass the configuration content to the Version\_Control\_Tool to be committed.  
* **Function Signature:** def backup\_config(self, device: str) \-\> ToolOutput:

#### **6.2.2 Version\_Control\_Tool**

* **Purpose:** To interface with a Git-based repository to store and version all device configurations.  
* **Library:** GitPython will be used to provide a programmatic interface to a local Git repository clone.  
* **Function Signature:** def commit\_config(self, device: str, config\_content: str, commit\_message: str) \-\> ToolOutput:  
* **Logic:** The tool will manage a local clone of the configuration repository. When called, it will write the provided configuration content to the appropriate file (e.g., configs/{device}.txt), stage the change, and commit it with a structured commit message (e.g., "AUTOBACKUP: Configuration backup for {device}"). It will then push the change to the remote repository.

#### **6.2.3 Config\_Drift\_Detection\_Tool**

* **Purpose:** To compare a device's live running configuration against its approved baseline stored in the Git repository, fulfilling requirement 5.3.2.1.1  
* **Logic:** The tool will first use the Network\_Interaction\_Tool to fetch the current running configuration. It will then retrieve the latest committed configuration for that device from the local Git repository. It will perform a textual diff between the two versions, ignoring irrelevant lines (e.g., timestamps). If a drift is detected, it will return the differences.  
* **Function Signature:** def detect\_drift(self, device: str) \-\> ToolOutput:  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel

  class ConfigDriftOutput(BaseModel):  
      """The result of a configuration drift detection check."""  
      device: str  
      is\_drifted: bool  
      diff: Optional\[str\] \= None \# The textual diff if drifted

#### **6.2.4 Compliance\_Audit\_Tool**

* **Purpose:** To use a rule-based engine to audit device configurations against predefined policies like NIST or PCI-DSS, as per requirement 5.3.3.1.1  
* **Logic:** The tool will take a device configuration as input. It will load a set of compliance rules for a specified policy (e.g., from a YAML file). Each rule will consist of a regular expression or a structured check (e.g., for a specific required line or a forbidden command). The tool will iterate through the rules, check them against the configuration, and compile a report of all violations.  
* **Function Signature:** def audit\_config(self, config\_content: str, policy\_name: str) \-\> ToolOutput:  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel

  class ComplianceViolation(BaseModel):  
      """Details of a single compliance violation."""  
      rule\_id: str  
      rule\_description: str  
      violating\_line: Optional\[str\] \= None  
      violation\_type: Literal\['missing\_required', 'found\_forbidden'\]

  class ComplianceReport(BaseModel):  
      """A full compliance audit report."""  
      policy\_name: str  
      is\_compliant: bool  
      violations: List\[ComplianceViolation\]

#### **6.2.5 Network\_Interaction\_Tool**

* **Purpose:** A powerful, multi-protocol tool for making configuration changes using modern, safe protocols like NETCONF and gNMI.1  
* **Libraries:** ncclient for NETCONF operations 19 and  
  pygnmi for gNMI operations.21  
* **Function Signature:** def set\_config(self, device: str, config\_payload: str, transactional: bool \= True) \-\> ToolOutput:  
* **Logic:** The implementation of this tool is paramount to the safety and stability of the entire platform. Automated configuration changes are inherently high-risk, and the primary mitigation is the use of transactional protocols.  
  1. The tool will first query the NSoT to determine the device's preferred management protocol.  
  2. If transactional is True, the tool must use NETCONF via ncclient. The logic will strictly adhere to the full transactional lifecycle to ensure atomicity ("all-or-nothing"):  
     a. Acquire a lock on the candidate datastore: m.lock('candidate').  
     b. Load the configuration change into the candidate datastore: m.edit\_config(target='candidate', config=config\_payload).  
     c. Commit the change: m.commit().  
     d. Release the lock: m.unlock('candidate').  
     e. A try...except...finally block is mandatory. The finally block must ensure the lock is released, even if the commit fails. The except block must issue a m.discard\_changes() command to perform an immediate rollback of the failed change. This strict adherence to the NETCONF transaction model is the central safety mechanism that makes automated remediation a viable and responsible practice.1  
  3. If transactional is False (for simple, idempotent changes), the tool may use gNMI's Set RPC via pygnmi.

## **Section 7: Lifecycle Management Agent: Low-Level Specification**

The LifecycleManagementAgent is the long-term planner and risk manager for the network fleet. It focuses on mitigating risks from software vulnerabilities and end-of-life hardware and software.1

### **7.1 Class Definition and Initialization**

Python

\#  
\# in 'agents/lifecycle.py'  
\#  
from.common import AbstractNetworkAgent  
\#... import tool classes

class LifecycleManagementAgent(AbstractNetworkAgent):  
    """  
    Network Fleet and Vulnerability Manager.  
    Manages hardware/software lifecycle, vulnerabilities, and patching.  
    """  
    def \_\_init\_\_(self, agent\_config, global\_config):  
        super().\_\_init\_\_(  
            agent\_config=agent\_config,  
            global\_config=global\_config,  
            role="Network Fleet and Vulnerability Manager",  
            goal=(  
                "To manage the hardware and software lifecycle of all network assets, "  
                "identifying risks associated with software vulnerabilities, "  
                "End-of-Life (EoL) status, and managing the automated patching process."  
            ),  
            backstory=(  
                "You are the long-term planner and risk manager for the network fleet. "  
                "While other agents focus on the here-and-now, you look to the future, "  
                "ensuring the network doesn't succumb to bit rot or unpatched "  
                "vulnerabilities. You correlate the network inventory with global "  
                "threat intelligence and vendor announcements to keep the fleet "  
                "secure, supported, and up-to-date."  
            ),  
            allow\_delegation=False  
        )

### **7.2 Tool Implementation Specifications**

#### **7.2.1 NSOT\_Query\_Tool**

* **Purpose:** To provide read-only access to the NSoT for retrieving real-time lists of devices and their software versions.  
* **Logic:** This tool is the read-only counterpart to the NSOT\_Update\_Tool. It will use httpx to send GraphQL query operations to the unified NSoT API. This provides agents with a standardized method for enriching their context with inventory and topology data.  
* **Function Signature:** def query\_nsot(self, query: str) \-\> ToolOutput:

#### **7.2.2 CVE\_Lookup\_Tool**

* **Purpose:** To integrate with vendor security advisory APIs and public CVE databases to find vulnerabilities affecting assets in the NSoT, fulfilling requirement 5.4.2.1  
* **Library:** httpx will be used to interact with the REST APIs of vulnerability databases (e.g., NIST NVD API) and vendor-specific security advisory portals.  
* **Function Signature:** def find\_vulnerabilities(self, product\_name: str, product\_version: str) \-\> ToolOutput:  
* **Logic:** The tool will take a product name (e.g., "Cisco IOS XE") and a version string as input. It will construct the appropriate API request to query the vulnerability database and retrieve a list of associated Common Vulnerabilities and Exposures (CVEs).  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel

  class CVEInfo(BaseModel):  
      """Details of a single Common Vulnerability and Exposure."""  
      cve\_id: str  
      description: str  
      cvss\_v3\_score: Optional\[float\] \= None  
      url: str

  class VulnerabilityReport(BaseModel):  
      """A report of vulnerabilities for a given software version."""  
      product\_name: str  
      product\_version: str  
      vulnerabilities: List\[CVEInfo\]

#### **7.2.3 EoL\_EOS\_Check\_Tool**

* **Purpose:** To check vendor databases for End-of-Life (EoL) and End-of-Support (EoS) announcements for hardware and software in the inventory, also fulfilling requirement 5.4.2.1  
* **Logic:** This tool will use httpx to interact with vendor-specific lifecycle information APIs. For vendors without APIs, it may need to be supplemented with web scraping capabilities (using libraries like BeautifulSoup and requests) to parse EoL/EoS tables from their support websites.  
* **Function Signature:** def check\_lifecycle\_status(self, product\_model: str) \-\> ToolOutput:

#### **7.2.4 Automated\_Patching\_Workflow\_Tool**

* **Purpose:** A complex tool that orchestrates the multi-step OS upgrade process, including pre-flight checks, image transfer, and post-flight validation, as specified in 5.4.3.1  
* **Logic:** This is not a simple tool but a meta-tool that defines and executes a workflow. It will orchestrate calls to other, more primitive tools:  
  1. **Pre-flight:** Use ITSM\_Integration\_Tool to create a change request ticket. Use PerformanceMonitoringAgent's tools to capture a baseline of the device's state (e.g., routing table size, BGP peer status). Use ConfigurationManagementAgent's Config\_Backup\_Tool.  
  2. **Execution:** Use Network\_Interaction\_Tool or a dedicated file transfer tool (e.g., using SCP/SFTP) to transfer the new OS image to the device. Use Network\_Interaction\_Tool to issue the commands to install the new image and reboot the device.  
  3. **Post-flight:** After the device reboots, use PerformanceMonitoringAgent's tools to re-check the device's state and compare it against the pre-flight baseline.  
  4. **Closure:** If post-flight checks pass, update the ITSM ticket to "Success." If they fail, raise a high-priority alert and potentially trigger an automated rollback procedure.  
* **Function Signature:** def execute\_patching\_workflow(self, device: str, target\_os\_version: str, image\_path: str) \-\> ToolOutput:

## **Section 8: Security & Threat Detection Agent: Low-Level Specification**

The SecurityThreatDetectionAgent acts as the network's immune system, continuously monitoring for threats, analyzing anomalous traffic, and initiating responses.1

### **8.1 Class Definition and Initialization**

Python

\#  
\# in 'agents/security.py'  
\#  
from.common import AbstractNetworkAgent  
\#... import tool classes

class SecurityThreatDetectionAgent(AbstractNetworkAgent):  
    """  
    Cyber-Security Sentinel.  
    Monitors for threats, analyzes traffic patterns, and initiates responses.  
    """  
    def \_\_init\_\_(self, agent\_config, global\_config):  
        super().\_\_init\_\_(  
            agent\_config=agent\_config,  
            global\_config=global\_config,  
            role="Cyber-Security Sentinel",  
            goal=(  
                "To continuously monitor the network for security threats, analyze "  
                "anomalous traffic patterns, and initiate automated responses to "  
                "contain and mitigate potential attacks."  
            ),  
            backstory=(  
                "You are the network's immune system. You operate under the assumption "  
                "that the network is constantly under threat. By analyzing flow data "  
                "(IPFIX/NetFlow) and logs, you hunt for indicators of compromise, "  
                "from reconnaissance scans to data exfiltration. You use machine "  
                "learning to understand normal traffic flows, allowing you to spot "  
                "malicious activity that might otherwise blend in."  
            ),  
            allow\_delegation=False  
        )

### **8.2 Tool Implementation Specifications**

#### **8.2.1 Flow\_Analysis\_Tool**

* **Purpose:** To query and analyze IPFIX/NetFlow data stored in a backend database to identify suspicious traffic patterns.  
* **Library:** The choice of library depends on the backend data store. If flow data is stored in Elasticsearch, elasticsearch-dsl would be used. If in ClickHouse, the clickhouse-driver would be used. The tool will abstract the specific query language.  
* **Function Signature:** def query\_flows(self, query\_filter: dict, time\_range: str) \-\> ToolOutput:  
* **Logic:** The tool will take a structured filter (e.g., {'source\_ip': '1.2.3.4', 'dest\_port': 22}) and a time range. It will construct the appropriate query for the backend datastore to find matching flows and return aggregated results (e.g., total bytes, packet counts).

#### **8.2.2 Log\_Analysis\_Tool**

* **Purpose:** To scan Syslog data for security-related events like failed logins, firewall denies, and IDS/IPS alerts.  
* **Logic:** This tool functions identically to the Flow\_Analysis\_Tool but targets the log data store (which may be the same system, e.g., Elasticsearch). It will provide a structured query interface for security events.  
* **Function Signature:** def query\_logs(self, query\_filter: dict, time\_range: str) \-\> ToolOutput:

#### **8.2.3 Threat\_Intelligence\_Tool**

* **Purpose:** To correlate observed IP addresses and traffic patterns with known malicious indicators from external threat intelligence feeds.  
* **Library:** httpx will be used to query the APIs of threat intelligence platforms (e.g., VirusTotal, AbuseIPDB, AlienVault OTX).  
* **Function Signature:** def check\_ip\_reputation(self, ip\_address: str) \-\> ToolOutput:  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel

  class IPReputation(BaseModel):  
      """Reputation details for an IP address."""  
      ip\_address: str  
      is\_malicious: bool  
      confidence\_score: Optional\[float\] \= None  
      categories: List\[str\] \# e.g.,  
      source: str \# e.g., 'VirusTotal'

#### **8.2.4 Anomaly\_Detection\_Model\_Tool**

* **Purpose:** A security-focused version of the unsupervised learning model used to detect deviations in traffic patterns that may indicate a threat, as per requirement 6.3.2.1  
* **Logic:** This tool functions identically to the one used by the Performance Monitoring agent but is trained on different data. It will be trained on network flow data (e.g., bytes per second, flows per second, protocol distribution) to detect anomalies like a sudden spike in traffic to an unusual port, which could indicate data exfiltration or a C2 channel.

#### **8.2.5 Remediation\_Action\_Tool**

* **Purpose:** To initiate basic, pre-approved security responses, such as applying an Access Control List (ACL) to block a malicious IP address.  
* **Logic:** This tool provides a critical, controlled interface for automated response. It will not contain the protocol interaction logic itself. Instead, it will formulate a configuration payload (e.g., the text for a new ACL entry) and then invoke the ConfigurationManagementAgent's Network\_Interaction\_Tool to apply it. This ensures that all configuration changes, even for security remediation, go through the same transactional, audited, and safe mechanism. The tool will only be allowed to execute actions that are explicitly permitted in its configuration, subject to the Conductor Agent's final approval.  
* **Function Signature:** def block\_ip(self, device: str, ip\_to\_block: str) \-\> ToolOutput:

## **Section 9: Proactive Maintenance Agent: Low-Level Specification**

The ProactiveMaintenanceAgent acts as a network soothsayer, using predictive analytics and machine learning to forecast failures before they impact service, enabling a shift from reactive to planned operations.1

### **9.1 Class Definition and Initialization**

Python

\#  
\# in 'agents/proactive.py'  
\#  
from.common import AbstractNetworkAgent  
\#... import tool classes

class ProactiveMaintenanceAgent(AbstractNetworkAgent):  
    """  
    Predictive Failure Analyst.  
    Uses predictive analytics to forecast network and device failures.  
    """  
    def \_\_init\_\_(self, agent\_config, global\_config):  
        super().\_\_init\_\_(  
            agent\_config=agent\_config,  
            global\_config=global\_config,  
            role="Predictive Failure Analyst",  
            goal=(  
                "To use predictive analytics and machine learning to forecast "  
                "network and device failures before they occur, enabling "  
                "maintenance to be scheduled in a non-disruptive manner."  
            ),  
            backstory=(  
                "You are a network soothsayer, using data to see the future. "  
                "You understand that failures are rarely sudden; they are often "  
                "preceded by subtle signs of degradation. By training machine "  
                "learning models on vast amounts of historical data, you can predict "  
                "with high accuracy when an optical transceiver will fail, a link "  
                "will become saturated, or a fan tray will die, turning reactive "  
                "operations into a planned, proactive process."  
            ),  
            allow\_delegation=False  
        )

### **9.2 Tool Implementation Specifications**

#### **9.2.1 TSDB\_Query\_Tool**

* **Purpose:** To gather historical time-series data required for training predictive models and for running inference on live data.  
* **Logic:** This is a shared tool, identical in implementation to the one used by the PerformanceMonitoringAgent. It provides the essential data retrieval capability needed for any time-series analysis.

#### **9.2.2 Predictive\_Maintenance\_Model\_Tool**

* **Purpose:** To serve as a wrapper for the ML models trained to predict hardware failures, link saturation, and other events, as per requirement 6.3.1.1  
* **Library:** The underlying models may be built with libraries like scikit-learn, XGBoost, or TensorFlow. The tool itself will be a client to the model serving endpoint.  
* **Function Signature:** def predict\_failure(self, device: str, component\_id: str, historical\_data: dict) \-\> ToolOutput:  
* **Logic:** The tool will take a set of historical time-series data for a specific component (e.g., the last 30 days of Rx power for an optical transceiver). It will send this data to the appropriate ML model's inference endpoint. The endpoint will return a prediction, which the tool will structure into its Pydantic output model.  
* **Pydantic Models:**  
  Python  
  from pydantic import BaseModel

  class FailurePrediction(BaseModel):  
      """The output of a predictive maintenance model."""  
      device: str  
      component\_id: str  
      failure\_probability: float \= Field(ge=0.0, le=1.0)  
      predicted\_time\_to\_failure\_hours: Optional\[int\] \= None  
      contributing\_factors: List\[str\] \# e.g.,

#### **9.2.3 Maintenance\_Scheduler\_Tool**

* **Purpose:** To integrate with the ITSM system to proactively schedule maintenance windows based on the output of the failure prediction models.  
* **Logic:** This tool will leverage the ITSM\_Integration\_Tool used by the Conductor. When the Predictive\_Maintenance\_Model\_Tool returns a high-probability failure prediction, this tool will be invoked. It will formulate the details for a new change request ticket in the ITSM system, including the predicted failure, the device and component affected, and the supporting data. It will then call the ITSM\_Integration\_Tool's create\_ticket function to formally open the proactive maintenance request.  
* **Function Signature:** def schedule\_maintenance(self, prediction: FailurePrediction) \-\> ToolOutput:

## **Section 10: Conclusions**

This low-level design specification provides a comprehensive and actionable blueprint for the implementation of the core agent crew for the agentic network management platform. By adhering to the foundational principles of immutable data contracts, modular abstraction, and built-in observability, the resulting system will be robust, maintainable, and scalable.

The key architectural decisions detailed herein are critical to the platform's success:

* The mandatory use of **Pydantic for all data contracts** establishes a system-wide type system that is essential for reliable operation in a complex, asynchronous, multi-agent environment.  
* The implementation of an **Adapter Pattern for ITSM integration** ensures the platform is adaptable to diverse enterprise customer environments, a crucial feature for commercial viability.  
* The strict adherence to the **NETCONF transactional lifecycle** for the Network\_Interaction\_Tool provides the central safety mechanism that makes autonomous configuration changes and remediation a responsible and viable capability.

The detailed specifications for each of the eight agents and their associated tools provide a clear path for development, outlining the necessary libraries, class structures, function signatures, and core logic. This document serves as the definitive technical guide for the engineering team to build a powerful, intelligent, and reliable network automation platform.

#### **Works cited**

1. CrewAI Design for Network Automation.pdf  
2. codesignal.com, accessed October 4, 2025, [https://codesignal.com/learn/courses/expanding-crewai-capabilities-and-integration/lessons/using-pydantic-models-for-structured-output\#:\~:text=Pydantic%20models%20are%20defined%20as,crucial%20for%20ensuring%20data%20integrity.](https://codesignal.com/learn/courses/expanding-crewai-capabilities-and-integration/lessons/using-pydantic-models-for-structured-output#:~:text=Pydantic%20models%20are%20defined%20as,crucial%20for%20ensuring%20data%20integrity.)  
3. Using Pydantic Models for Structured Output | CodeSignal Learn, accessed October 4, 2025, [https://codesignal.com/learn/courses/expanding-crewai-capabilities-and-integration/lessons/using-pydantic-models-for-structured-output](https://codesignal.com/learn/courses/expanding-crewai-capabilities-and-integration/lessons/using-pydantic-models-for-structured-output)  
4. Models \- Pydantic, accessed October 4, 2025, [https://docs.pydantic.dev/latest/concepts/models/](https://docs.pydantic.dev/latest/concepts/models/)  
5. How to Use a Single Pydantic Model for Structured Output with Long Documents in a Chunked RAG Pipeline? \- OpenAI Developer Community, accessed October 4, 2025, [https://community.openai.com/t/how-to-use-a-single-pydantic-model-for-structured-output-with-long-documents-in-a-chunked-rag-pipeline/1080681](https://community.openai.com/t/how-to-use-a-single-pydantic-model-for-structured-output-with-long-documents-in-a-chunked-rag-pipeline/1080681)  
6. Output \- Pydantic AI, accessed October 4, 2025, [https://ai.pydantic.dev/output/](https://ai.pydantic.dev/output/)  
7. Jira Python Integration: 2 Easy Methods \- Hevo Data, accessed October 4, 2025, [https://hevodata.com/learn/jira-python-integration/](https://hevodata.com/learn/jira-python-integration/)  
8. How to Use Python Jira Library to Retrieve Data \- Atlassian Community, accessed October 4, 2025, [https://community.atlassian.com/forums/Jira-articles/How-to-Use-Python-Jira-Library-to-Retrieve-Data/ba-p/2935853](https://community.atlassian.com/forums/Jira-articles/How-to-Use-Python-Jira-Library-to-Retrieve-Data/ba-p/2935853)  
9. jira \- PyPI, accessed October 4, 2025, [https://pypi.org/project/jira/](https://pypi.org/project/jira/)  
10. ServiceNow/PySNC: Python API for ServiceNow \- GitHub, accessed October 4, 2025, [https://github.com/ServiceNow/PySNC](https://github.com/ServiceNow/PySNC)  
11. spaCy · Industrial-strength Natural Language Processing in Python, accessed October 4, 2025, [https://spacy.io/](https://spacy.io/)  
12. Natural Language Processing With spaCy in Python \- Real Python, accessed October 4, 2025, [https://realpython.com/natural-language-processing-spacy-python/](https://realpython.com/natural-language-processing-spacy-python/)  
13. Intent Recognition using TensorFlow \- GeeksforGeeks, accessed October 4, 2025, [https://www.geeksforgeeks.org/python/intent-recognition-using-tensorflow/](https://www.geeksforgeeks.org/python/intent-recognition-using-tensorflow/)  
14. Intent Recognition using TensorFlow | by Siddhartha Sengupta \- Medium, accessed October 4, 2025, [https://medium.com/@ssgupta905/introduction-4958e0b1a432](https://medium.com/@ssgupta905/introduction-4958e0b1a432)  
15. etingof/pysnmp: Python SNMP library \- GitHub, accessed October 4, 2025, [https://github.com/etingof/pysnmp](https://github.com/etingof/pysnmp)  
16. pysnmp \- PyPI, accessed October 4, 2025, [https://pypi.org/project/pysnmp/](https://pypi.org/project/pysnmp/)  
17. lldpy · PyPI, accessed October 4, 2025, [https://pypi.org/project/lldpy/](https://pypi.org/project/lldpy/)  
18. scapy.contrib.lldp — Scapy 2.6.1 documentation, accessed October 4, 2025, [https://scapy.readthedocs.io/en/latest/api/scapy.contrib.lldp.html](https://scapy.readthedocs.io/en/latest/api/scapy.contrib.lldp.html)  
19. pypi.org, accessed October 4, 2025, [https://pypi.org/project/ncclient/\#:\~:text=ncclient%20is%20a%20Python%20library,Nilsen%2DNygaard%20(%40einarnn)%20.](https://pypi.org/project/ncclient/#:~:text=ncclient%20is%20a%20Python%20library,Nilsen%2DNygaard%20\(%40einarnn\)%20.)  
20. ncclient/ncclient: Python library for NETCONF clients \- GitHub, accessed October 4, 2025, [https://github.com/ncclient/ncclient](https://github.com/ncclient/ncclient)  
21. pygnmi \- PyPI, accessed October 4, 2025, [https://pypi.org/project/pygnmi/](https://pypi.org/project/pygnmi/)  
22. pygnmi \- Open Management, accessed October 4, 2025, [https://aristanetworks.github.io/openmgmt/examples/pygnmi/](https://aristanetworks.github.io/openmgmt/examples/pygnmi/)  
23. cisco-ie/cisco-gnmi-python \- Cisco Code Exchange, accessed October 4, 2025, [https://developer.cisco.com/codeexchange/github/repo/cisco-ie/cisco-gnmi-python/](https://developer.cisco.com/codeexchange/github/repo/cisco-ie/cisco-gnmi-python/)