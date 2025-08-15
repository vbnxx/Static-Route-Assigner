# Static Route Assigner

This Python script automates the creation of loopback interfaces and static routes on a Cisco IOS-XE router using RESTCONF and RIPE Atlas measurement results. It selects the best ISP path based on the lowest RTT from either Ping or Traceroute measurements, and configures floating static routes for redundancy.

## Features

- Connects to a Cisco IOS-XE router via RESTCONF
- Retrieves measurement results from RIPE Atlas (Ping or Traceroute)
- Creates loopback interfaces for multiple ISPs
- Configures static routes with automatic failover (metrics 5 and 10)
- Allows viewing of the current static route configuration
- Ignores unsupported measurement types (DNS, HTTP, SSL)

## Requirements
- Python 3.x
- Cisco IOS-XE router with RESTCONF enabled
- RIPE Atlas measurements
- Python packages:

```bash
pip install requests ripe.atlas.sagan
```

## Usage
1. Run the script
```bash
python3 route_assign.py
```
2. Enter router IP address when prompted
3. Choose option from the menu:
   - 1. Configure static routes (requires 3 measurement IDs of the same type)
   - 2. Print current static routes
   - 3. Exit

## Notes

Default RESTCONF credentials are set to:
```makefile
username: cisco
password: cisco1234!
```
Update this prior with your own credentials.  
Measurement IDs must be from RIPE Atlas and of the same type (Ping or Traceroute).  
Assumes /24 subnets for static route configuration.
