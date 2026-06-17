# Logistics Service App — Role Features

A cargo logistics platform where customers book orders to move goods between locations. The system handles cargo vehicles, warehouse packing operations, and full supply chain coordination across 6 roles.

---

## 1. Customer (Individual)

The end customer who books moving or delivery orders and tracks them end-to-end.

| Feature | Description |
|---|---|
| Dashboard | Real-time overview of upcoming moves, active orders, and wallet balance at a glance. |
| Book Move | Create a new moving order by specifying pickup/delivery locations, dates, cargo type, and vehicle preference. |
| AI Estimator | Upload room photos and Gemini Vision auto-detects items and generates an instant cost estimate for the move. |
| My Orders | View all past and current orders with full status history (Pending → Confirmed → In Transit → Delivered). |
| Order Quotes | Browse and manage saved price quotes; convert any quote into an actual booked order. |
| Live Tracking | Real-time GPS map view of the assigned driver's current location with live ETA updates. |
| Payments | View itemised payment history per order and manage linked payment methods. |
| Wallet | Prepaid wallet to top up balance, pay for orders, and view full transaction history. |
| Damage Report | Submit a post-delivery damage claim with photos and item descriptions for review. |
| Support Tickets | Raise a support issue, browse the FAQ, and chat directly with a support agent. |
| Profile | Update personal details, saved addresses, email, and phone number. |
| Settings | Control notification preferences, privacy settings, and account deletion. |
| Notifications | Receive and manage real-time order status updates and system announcements. |

---

## 2. Driver

The field driver who executes pickups and deliveries via the dedicated mobile app.

| Feature | Description |
|---|---|
| Pre-Shift Safety Check | Complete a mandatory vehicle safety review covering fuel, tyres, lights, and mirrors before the shift begins. |
| Vehicle Binding | Link yourself to an assigned vehicle at shift start and maintain that link throughout the day. |
| Vehicle Inspection | Perform a detailed multi-point inspection of the vehicle before starting delivery operations. |
| Job Type Selection | Select the shift job type — standard delivery, pickup, or house-shift move — at the start of each run. |
| Manifest View | See the full ordered list of jobs for the day with stop sequence and priority. |
| Stop Details | View the address, item list, and any special handling instructions for each individual stop. |
| Live Navigation | GPS turn-by-turn navigation from the app directly to each delivery or pickup address. |
| Geofence Arrival | App auto-detects when you enter a delivery zone and prompts for the next required action. |
| Item Scanning | Scan item barcodes or QR codes to verify cargo before loading or after unloading. |
| Proof of Delivery (POD) | Capture a delivery photo to serve as digital proof of successful delivery. |
| Customer Signature | Collect an on-screen customer signature at the point of delivery. |
| Delivery Exception | Report a failed delivery with reason code, supporting photo, and details sent to the dispatcher. |
| Damage Report | Document damaged items with photos and description directly from the mobile app. |
| COD Payment | Handle cash-on-delivery collection, verify the amount, and mark the order as paid before completion. |
| Service Checklist | Complete service-specific checklists required for special-handling or assembly jobs. |
| House Move — Packing Progress | Track items as they are packed at the customer's origin location during a house-shift job. |
| House Move — Loading Inventory | Confirm each item is loaded onto the vehicle against the job's item list. |
| House Move — Unloading Inventory | Confirm each item is unloaded at the destination and reconcile against the loaded list. |
| House Move — Final Walkthrough | Inspect and document the delivery site condition after the house-shift is complete. |
| Customer Sign-Off | Collect the customer's final acknowledgment signature after a house-shift completion. |
| Packing Return | Track packing materials and return items being sent back to the warehouse after a job. |
| Crew Management | Check in crew members assigned to a house-shift job and monitor their task activity. |
| Gate Exit | Record gate exit time when leaving the warehouse or depot at the start or end of a shift. |
| Dispatch Chat | Real-time in-app messaging with the dispatcher for updates, queries, and issue resolution. |
| Manager Chat | Direct messaging channel with logistics managers for escalations and approvals. |
| Crisis Mode / SOS | Send an emergency alert to dispatch with current GPS location in case of an incident on the road. |
| Route Deviation | Report and document any deviation from the planned delivery route with reason. |
| Shift Summary | End-of-day report showing total orders completed, distance driven, and earnings for the shift. |
| Vehicle Return | Submit end-of-shift vehicle details including odometer reading, fuel level, and condition notes. |
| Fuel Receipt | Upload fuel receipts from the app for company reimbursement. |
| Driver Wallet | View total earnings, pending balance, and full transaction history. |
| Cashout Request | Request a payout or withdrawal of available earnings to a bank account. |
| Hours of Service (HOS) | Maintain a compliance log of driving hours for regulatory reporting. |
| Offline Queue | Jobs and completed actions are stored locally when offline and automatically synced when reconnected. |
| Voice Assistant | Hands-free voice commands let you navigate the app safely while driving. |
| Load Verification | Verify all cargo is correctly loaded onto the vehicle before departure from the warehouse. |
| Pickup Arrival | Check in at a pickup location via geofence detection to signal arrival. |
| Pickup Scanning | Scan items at the pickup location to confirm they match the order manifest. |
| Pickup Signature | Collect a signature from the sender at the pickup point. |
| Warehouse Return | Process the return of items back to the warehouse with inventory confirmation. |
| Unload Verification | Verify cargo is fully unloaded and accounted for at the final destination. |
| Pickup Completion | Mark a pickup job as complete with a final summary review. |
| Audit Log | View a complete timestamped audit trail of all shift activities and changes. |
| Settings | Configure app preferences, notification rules, and account settings. |

---

## 3. Dispatcher

The dispatcher assigns orders to drivers, optimises routes, and monitors fleet activity in real time.

| Feature | Description |
|---|---|
| Dashboard | Real-time view of active drivers on map, in-transit orders, completion rate, and fleet response time. |
| Pending Dispatch Queue | List of confirmed orders waiting for driver assignment, sortable by priority and proximity. |
| Order Clustering | AI groups nearby orders within a configurable radius into a single efficient multi-stop route. |
| Route Optimisation | Generate the shortest or fastest delivery sequence for a cluster and visualise it on a map. |
| Driver Management | Monitor driver GPS locations, update availability status, and suspend or reactivate drivers. |
| Manifest Center | Package orders into a delivery manifest and push it directly to the assigned driver's mobile app. |
| Service Moves | Manage special-service orders that require assembly, installation, or additional handling steps. |
| Order Status Control | Manually override or correct an order's status to handle edge cases and exceptions. |
| Crisis Management | Monitor incoming SOS alerts from drivers and coordinate the emergency response in real time. |
| Smart Driver Assignment | AI picks the best available free driver for each vehicle-locked ready order released by the Warehouse Manager; includes a Dispatch Readiness Queue, AI coverage tracking, and dropoff delay predictions. |
| Smart Dispatcher (AI) | Gemini-powered assistant recommends optimal driver assignments and cluster configurations automatically. |
| Performance Metrics | Track personal dispatcher stats — orders assigned, route efficiency score, and delivery success rate. |
| Communication | Send direct messages and notifications to drivers and the logistics management team. |
| Meeting Room | Virtual meeting space for dispatcher to join or host team calls with logistics managers and warehouse staff. |

---

## 4. Warehouse Manager

Controls all inbound and outbound goods flow, inventory, staff, and dock scheduling inside the warehouse.

| Feature | Description |
|---|---|
| Dashboard | Live warehouse KPIs: inbound queue size, picking progress, packing queue depth, dock availability, and staff utilisation. |
| New Orders | Accept incoming orders from the dispatch queue and assign them to warehouse staff for fulfilment. |
| Inventory | View current stock levels per zone and storage location; receive low-stock reorder alerts. |
| Inbound Receiving | Receive vendor shipments, verify quantities and condition against the Advance Shipment Notice (ASN). |
| Inbound AI Plan | Get an AI-recommended receiving and put-away plan for an incoming shipment. |
| Inbound Mismatch Report | Record and report discrepancies between received goods and the ASN documentation. |
| Inbound Damage Report | Document damage discovered during the receiving process with photos and descriptions. |
| Floor Plan | Interactive visual map of the warehouse showing rack zones, storage locations, and live occupancy. |
| Picking Management | Assign and start pick tasks, track real-time picking progress per order, and confirm items via scan. |
| Pick List Generation | Generate an optimised pick list for one or more orders to minimise travel time on the floor. |
| Packing Materials | Manage stock of packing supplies (boxes, tape, foam, wrap); track consumption and raise restocks. |
| Packing Material Requests | Create and approve material replenishment requests for the packing station. |
| Safety Stock | Set minimum stock thresholds per item so critical inventory is never unexpectedly depleted. |
| Safety Stock Alerts | Automated alerts triggered when any item's stock level falls below its configured threshold. |
| Loading Dock | Schedule truck dock slots, assign docks to outbound orders, and release docks after loading is verified. |
| Dock Maintenance | Set a dock's status to under maintenance and schedule the maintenance window. |
| Returns Processing | Receive returned items, assess their condition, and approve or reject return claims with photo evidence. |
| Labor Management | Assign warehouse staff to specific tasks and monitor individual productivity throughout the shift. |
| Quality Checks | Create and record quality inspection results on orders before they leave the warehouse. |
| Packing Stations | Create and manage packing station assignments to organise the packing workflow. |
| Smart WMS (AI) | AI-driven recommendations for optimal picking routes and best-fit storage placement. |
| Performance Metrics | Track warehouse KPIs — picking speed, order accuracy, labour efficiency, and average order cycle time. |
| Restock Requests | Create and track requests for replenishing items that have reached low inventory levels. |
| Restock Request Escalation | Escalate an urgent restock request to the logistics manager for immediate action. |
| Take-Back Generation | Generate a take-back order for damaged or quality-rejected items to be returned to vendor. |
| Zone Metrics | Record and track operational performance metrics broken down by individual warehouse zones. |
| Communication | Internal messaging with team members and automated alerts on order status changes. |

---

## 5. Logistics Manager

Strategic oversight of the entire operation — fleet, warehouses, finance, people, and performance.

| Feature | Description |
|---|---|
| Dashboard | High-level KPIs across the full operation: fleet utilisation, order completion rate, revenue, and warehouse health. |
| Warehouse Management | Create and configure warehouses; set capacity, assign managers, and view operational health per site. |
| User Management | Create accounts for drivers, dispatchers, warehouse managers, and support staff; assign and modify roles. |
| User Suspension / Activation | Suspend or reactivate any user account to control platform access at any time. |
| Fleet Management | Add and manage vehicles (trucks, tempos, LCVs); track maintenance schedules; link vehicles to drivers. |
| Vehicle Creation & Editing | Create new vehicle records and modify vehicle details, specifications, and operational status. |
| Geofencing | Define geographic delivery zones and configure automated alerts for driver entries and exits. |
| Zone Management | Create, edit, and delete delivery zones used for geofencing and service coverage mapping. |
| Finance | Monitor total revenue, track operational expenses, review payment transactions, and manage capital records. |
| Financial Transactions | Record and audit all financial transactions across the operation. |
| Capital Investment Tracking | Track capital investments and funding allocations across the business. |
| Rate Governance | Configure all pricing rules — distance bands, vehicle-type rates, fuel surcharges, and special service fees. |
| Reverse Logistics | Oversee all customer returns — approve or reject cases, schedule reverse pickups, and issue refunds. |
| Reports | Generate custom reports on delivery performance, cost analysis, driver efficiency, and warehouse metrics. |
| AI Intelligence | Ask natural-language questions about operations and receive Gemini-powered analytics answers instantly. |
| Recovery Tickets | View and resolve escalation cases related to lost or significantly damaged shipments. |
| Communication | Create chat threads with dispatchers and warehouse managers; send broadcast notifications to any role. |
| Meetings | Schedule and track team meetings, send calendar invites, and record attendance. |
| Tasks | Create and assign operational tasks to team members with due dates and priority levels. |
| Alerts Management | Create, manage, and resolve operational alerts triggered across the platform. |
| Escalations Management | Handle logistics escalations raised by dispatchers and warehouse managers. |
| Manifests | Create and manage delivery manifests for pushing to drivers across all active routes. |
| Documents | Manage logistics documents such as contracts, permits, and compliance certificates. |
| Supply Chain Documents | Create and track supply chain-related documents including vendor agreements and shipment records. |
| Comparative Viewers | Compare performance metrics side-by-side across warehouses, time periods, or driver cohorts. |
| Notifications | Configure system-level alert rules and receive critical operational notifications in real time. |

---

## 6. Support Manager (Customer Support Team)

Handles all customer-facing issues including tickets, live chat, damage claims, and refunds.

| Feature | Description |
|---|---|
| Dashboard | Support KPIs — active ticket count, average resolution time, CSAT score, and agent workload at a glance. |
| Contact Forms | Monitor incoming customer contact form submissions and triage them to agents or queues. |
| Live Conversations | Handle real-time chat sessions with customers; view message history and typing indicators. |
| Tickets | Full ticket lifecycle — create, assign, update status, add internal notes, and close tickets. |
| Escalations | Manage high-priority issues escalated from frontline agents, with urgency flags and SLA tracking. |
| Damage Claims | Review customer-submitted damage reports; assign assessors; manage resolution and compensation. |
| Reverse Logistics | Coordinate return pickups and Return Merchandise Authorisations (RMAs) for damaged or rejected goods. |
| Refund Center | Process customer refunds, track refund status per order, and handle disputed refund requests. |
| Refund Case Flagging | Mark specific refund cases as urgent to prioritise their processing and resolution. |
| AI Chatbot | Automated Gemini-powered chat assistant that assesses damage photos and handles routine customer queries. |
| Knowledge Base | Manage internal FAQs and support articles used by agents for consistent issue resolution. |
| Analytics | Analyse ticket volume trends, resolution times, common issue categories, and CSAT over time. |
| Analytics Insights | Run AI-powered analytics queries to extract deeper business insights from support data. |
| Legal & Compliance | View and manage compliance documentation relevant to customer interactions and damage claims. |
| Support Sessions | Manage all ongoing customer support sessions and monitor agent activity across the team. |
| Session Takeover | Take over an active support session from another agent when escalation or re-assignment is needed. |
| Session Reply | Send messages directly within an active customer support session. |
| Session Escalation | Escalate an active support session to a senior agent or management. |
| Damage Report Notes | Add internal investigation notes to a damage report for the assessment team. |
| Customer History | View the complete interaction and order history of a specific customer in one place. |
| Settings | Configure SLA targets, working hours, notification rules, and team assignment settings. |

---

## 7. Vendor

A business customer (e.g. manufacturer, retailer) that ships goods in bulk through the platform using cargo vehicles and warehouse handling.

| Feature | Description |
|---|---|
| Dashboard | Real-time KPIs showing active shipments, pending dispatch count, monthly spend vs budget, and current wallet balance. |
| Create Shipment | Book a new cargo shipment by specifying origin, destination, vehicle type, cargo weight/volume, packing requirements, labor count, and payment mode. |
| My Shipments | View all active and historical shipments with full status history (Pending → Warehouse → In Transit → Delivered); reschedule, update address, or cancel directly. |
| Live Tracking | Real-time GPS map view of the assigned driver's location with a status progress bar and live ETA for each active shipment. |
| Proof of Delivery (POD) | Access and download digital POD documents per shipment, including delivery photo, receiver signature, and confirmed timestamp. |
| Bulk Upload | Upload a CSV file containing multiple shipment orders to create them in batch; error counts and processing status are reported per file. |
| Recurring Shipments | Set up recurring shipment rules (daily, weekly, or monthly) on fixed routes; toggle rules on/off, edit, or delete them at any time. |
| Invoices | View itemised invoices per shipment, track paid/unpaid/overdue balances, and make partial or full payments directly from the portal. |
| Wallet | Prepaid credit wallet to top up balance and auto-debit shipment costs; view full transaction history and current credit balance. |
| Analytics | Monthly shipment volume charts with on-time delivery rate, average transit days, cost per order, and overall shipment success rate. |
| Damage Reports | Submit post-delivery damage claims with photos and descriptions linked to a specific shipment, and track their resolution status. |
| Support Tickets | Raise support issues tied to specific shipments, reply to support agent messages in-thread, and mark tickets as resolved. |
| API Integration | Generate and revoke API keys and access API documentation to integrate shipment creation and tracking directly into your own systems. |
| Company Settings | Update company profile (name, tax ID, contact person, address) and configure notification preferences (email, SMS, push, invoice alerts). |
| Team Management | Add or remove sub-users from your vendor account so team members can access shipment data and create orders on your behalf. |
| Notifications | Receive real-time alerts on shipment status changes, auto-debit events, and overdue invoice reminders. |

---

## Summary

| Role | Feature Count |
|---|---|
| Customer | 13 |
| Driver | 44 |
| Dispatcher | 14 |
| Warehouse Manager | 27 |
| Logistics Manager | 26 |
| Support Manager | 21 |
| Vendor | 16 |
| **Total** | **161** |

---

*Source: `src/` (frontend views), `backend/app/routers/` + `services/` (API), `driver-app/src/` (mobile app)*
