# Go-Back-N ARQ Protocol Simulation

## Overview

This assignment simulates a reliable data transmission protocol using Go-Back-N Automatic Repeat reQuest (ARQ). The system manages data transmission, acknowledgments, timeouts, and retransmissions within a sliding window protocol. It simulates packet loss and tracks events via a logger, ensuring proper retransmission of unacknowledged packets.

## Objectives

- Implement the Go-Back-N ARQ protocol for reliable transmission.
- Manage packet transmission, acknowledgment, and timeouts.
- Simulate packet loss and retransmissions.
- Implement a sliding window to manage flow control.
- Log all events including sends, ACKs, drops, and timeouts.

## Features

- Packet segmentation from an input file.
- Sliding window based sender with configurable window size.
- Acknowledgment tracking and retransmission logic.
- Packet drop simulation every nth packet.
- Logging of all major sender side events.
- Threaded architecture using Python's `threading` and `queue` modules.

## How It Works

- The sender reads from an input file and breaks the content into fixed length packets.
- It sends up to `window_size` packets at a time.
- A packet is marked for retransmission if an acknowledgment is not received before `timeout_interval`.
- Every nth packet (as defined by `nth_packet`) is simulated to drop, forcing retransmission.
- Events are logged consistently using the provided logger.

## Running the Simulation

### Requirements

- Python 3.x

### Configuration Parameters

- `input_file`: Path to the file to transmit
- `window_size`: Size of the sliding window
- `packet_len`: Number of characters per packet
- `nth_packet`: Frequency of dropped packets (simulated)
- `timeout_interval`: Timeout duration for retransmissions
- `send_queue` and `ack_queue`: Queues to simulate the sender receiver channel
- `logger`: Logger instance for tracking events

### Example Usage

```python
sender = GBN_sender(
    input_file="data.txt",
    window_size=4,
    packet_len=10,
    nth_packet=5,
    send_queue=send_q,
    ack_queue=ack_q,
    timeout_interval=2.0,
    logger=your_logger
)
```

## Notes

- Adheres to the Go-Back-N ARQ protocol.
- Logs must be formatted consistently to allow result tracking.
- Use timeouts and exception handling to prevent blocking and crashes.
- Designed for educational simulation purposes, not real time transmission.

## License

This project is part of CS 3357A, Assignment 3 - Computer Networks I at Western University. For academic use only.
