# SDN Link Failure Detection and Recovery

# Problem Statement

In traditional networks, devices operate independently and lack a centralized view of the network. 
This makes it difficult to detect link failures and adapt dynamically. 
When a link fails, the network may experience packet loss or require manual reconfiguration.

This project implements a Software Defined Networking (SDN) solution using Mininet and the Ryu controller to detect link failures and respond dynamically. 
The controller monitors the network topology, detects failures in real time, and updates network behavior accordingly.

---

# Objective

* Detect link failures dynamically
* Demonstrate centralized control using SDN
* Implement flow rule management (match-action)
* Simulate network behavior using Mininet
* Add access control using firewall rules

---

# Tools & Technologies

* Mininet– Network simulation
* Ryu Controller – SDN controller
* Python – Controller logic
* NetworkX – Graph-based path computation

---

# Implementation

# 1. Learning Switch (Forwarding)

* Handles `packet_in` events
* Learns MAC addresses
* Installs flow rules dynamically

# 2. Firewall (Access Control)

* Blocks traffic between selected hosts
* Example: h1 → h3 is blocked

# 3. Link Failure Detection

* Uses Ryu topology events
* Detects when a link goes down

# 4. Path Recalculation

* Uses NetworkX to recompute shortest paths
* Displays updated network paths

# 5. Monitoring & Logging

* Logs events such as:

  * Link failures
  * Path recomputation
  * Blocked traffic

---

# Test Scenarios

# Scenario 1: Normal Operation

Command:

```
mininet> pingall
```

Result:

* 0% packet loss
* All hosts can communicate

---

# Scenario 2: Link Failure

Command:

```
mininet> link s1 s2 down
mininet> pingall
```

Result:

* Increased packet loss
* Controller detects failure
* Logs show recomputation

---

# Scenario 3: Firewall Rule

* Traffic from h1 to h3 is blocked
* Verified using ping

---

# Observations

* Before failure → network works normally
* After failure → packet loss increases
* Controller detects topology changes in real time
* No alternate path exists in linear topology → connectivity loss occurs
* Firewall successfully blocks specified traffic

---

# Output (Screenshots)

Include:

* Controller logs (link failure detected
<img width="336" height="292" alt="{3214C37B-DBD4-4FA0-89C3-EBEBE55B8672}" src="https://github.com/user-attachments/assets/1003aa75-597b-41a0-b943-86d508e1c86e" />


* pingall before failure
  <img width="246" height="78" alt="{05B8B5A1-8DA7-4AA7-867E-A7F002D0AAA0}" src="https://github.com/user-attachments/assets/8517c445-ad94-483e-b5fb-22185908c528" />

* pingall after failure
  <img width="243" height="76" alt="{CB974CC0-5B0B-4009-A487-77901CEB25F4}" src="https://github.com/user-attachments/assets/b6518d87-e2a1-406e-bfb3-f4782844d995" />

* Firewall blocking output

---

# How to Run

# 1. Start Controller

```
source ryu38-env/bin/activate
ryu-manager --observe-links controller.py
```

# 2. Start Mininet

```
sudo mn --topo linear,3 --controller remote
```

# 3. Test Network

```
mininet> pingall
mininet> link s1 s2 down
mininet> pingall
```

---

# Key Concepts Demonstrated

* SDN architecture (controller + switches)
* OpenFlow-based communication
* Centralized control
* Dynamic network adaptation
* Flow rule management

---

# Conclusion

This project demonstrates how SDN enables dynamic network management through centralized control. 
The system successfully detects link failures, updates network behavior, and enforces access control policies. 
It highlights the advantages of SDN over traditional networking in terms of flexibility, programmability, and real-time responsiveness.
