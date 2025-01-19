# IP Over Paper Aircraft Carriers

An experimental implementation of reliable data transfer protocols using physical paper airplanes as the transmission medium. This project implements a simplified TCP/IP stack with QR codes as the data carrier, demonstrating fundamental networking concepts in a tangible way.

## Overview

This project implements a custom network stack that uses printed QR codes on paper airplanes as the physical transmission medium. It includes:

- Custom reliable data transfer (RDT) protocol implementation
- Simplified TCP-like transport layer
- Basic HTTP client/server functionality
- QR code-based physical transmission layer
- Go-Back-N pipelining support

## Architecture

### Components

1. **Transport Layer**
   - Custom RDT protocol implementation
   - Acknowledgment handling
   - Go-Back-N window management
   - Packet sequencing and ordering

2. **Application Layer**
   - HTTP client implementation
   - Basic HTTP server
   - Request/response handling

3. **Physical Layer**
   - QR code generation and printing
   - QR code scanning and interpretation
   - Physical transmission via paper aircraft

### Data Flow

#### Client Side
- HTTP client generates requests
- Sender component:
  - Reads from http/outgoing
  - Generates QR codes for requests
  - Processes acknowledgment QRs
- Receiver component:
  - Scans incoming QR codes (server responses)
  - Forwards data to http/incoming
  - Generates and sends acknowledgments

#### Server Side
- Receiver component:
  - Scans incoming QR codes (client requests)
  - Forwards to http/incoming
  - Generates and sends acknowledgments
- Sender component:
  - Reads from http/outgoing
  - Generates QR codes for responses
  - Processes acknowledgment QRs

## Setup Instructions

### Prerequisites
- Python 3.x
- Printer with appropriate drivers
- Webcam or camera device
- Required Python packages (list requirements)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ip-over-paper-aircraft
cd ip-over-paper-aircraft
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the System

#### Client Side
1. Start camera server
2. Initialize printing server
3. Launch HTTP client
4. Start Sender component
5. Start Receiver component

#### Server Side
1. Initialize Camera
2. Start Printer service
3. Launch HTTP server
4. Start Receiver component
5. Start Sender component

## Technical Details

### Reliable Data Transfer
The system implements RDT 3.0 with the following features:
- Sequence numbering for packet ordering
- Acknowledgment mechanism
- Timeout-based retransmission
- Corruption detection
- Go-Back-N pipelining support

### Protocol Stack
```
Application Layer (HTTP)
        ↕
Transport Layer (Custom RDT)
        ↕
Physical Layer (QR Codes)
```

### Error Handling
- Packet loss detection and recovery
- Out-of-order packet handling
- Corruption detection via checksums
- Timeout-based retransmission logic

## Development

### Project Structure
```
project/
├── client/
│   ├── camera/
│   ├── printer/
│   ├── http_client/
│   ├── sender/
│   └── receiver/
├── server/
│   ├── camera/
│   ├── printer/
│   ├── http_server/
│   ├── sender/
│   └── receiver/
└── common/
    ├── protocols/
    └── utils/
```

### Future Improvements
- Implementation of additional protocols (DNS, ICMP)
- Network interface integration
- Enhanced pipelining mechanisms
- NAT support
- Extended HTTP protocol support

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any enhancements.

## License

[Your chosen license]

## Acknowledgments

This project was inspired by RFC 1149 (IP over Avian Carriers) and developed as an educational tool for understanding networking protocols.
