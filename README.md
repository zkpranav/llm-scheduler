This repository provides a simple **LLM batch scheduler** for the Langchain ecosystem.  
It serves as a **guide** and is **not intended for production use**.

### Design Overview
In-memory FIFO queue to **store** LLM requests.\
Condition variables for signaling within the queue.\
Futures to **signal** task completion.\
Timeout to **prevent starvation**.

In a production environment, these mechanisms would typically be replaced with **message brokers** and an **optional persistence layer**.

### Self-Hosted Model Considerations
For self-hosted models, certain components—such as the **KV cache**—scale **linearly** with **batch size** and **sequence length**.
Even with optimizations like Multi-Query Attention (MQA) and Grouped Query Attention (GQA) the linear relationship remains.

#### Potential Bottlenecks
- **Memory Capacity** – Large batches or long sequences can quickly exhaust available memory.
- **Memory Bandwidth** – High demand can lead to performance degradation.

Account for these constraints when designing the batching policy.
