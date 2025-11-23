# QUIC Network Performance Experiments

Automated QUIC throughput testing framework using Mininet for network simulation.

## Overview

This framework automates QUIC protocol performance testing across different network conditions:

- **Topologies**: Dumbbell, Parking Lot, Multi-Bottleneck
- **Variable Parameters**: Bandwidth, delay, packet loss
- **Measurements**: Throughput, RTT
- **Protocol**: QUIC over UDP (using aioquic library)

---

## Requirements

### System Requirements

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip \
    mininet \
    openvswitch-switch \
    net-tools \
    iperf3

# Python packages
pip3 install --break-system-packages \
    aioquic \
    cryptography
```

### Verify Installation

```bash
# Check Mininet
sudo mn --version
# Expected: mininet 2.3.0+

# Check aioquic
python3 -c "import aioquic; print(aioquic.__version__)"
# Expected: 0.9.x or 1.x

# Test Mininet
sudo mn --test pingall
# Expected: 0% dropped
```

---

## Quick Start

### Run Single Experiment

```bash
# Basic dumbbell topology test
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 2 \
    --duration 60
```

### Run Batch Experiments

```bash
# Run all bandwidth variations (recommended)
./run_batch_dumbbell.sh

# Or manually:
for bw in 10 15 20 35; do
    sudo python3 experiment_runner_quic.py \
        --topo dumbbell \
        --bw $bw \
        --delay 2ms \
        --loss 2 \
        --duration 60
done
```

---

## File Structure

```
.
├── experiment_runner_quic.py    # Main experiment runner
├── helper_quic.py               # Helper functions and metrics collection
├── quic_client.py               # QUIC client implementation
├── quic_server.py               # QUIC server implementation
│
├── dumbbell.py                  # Dumbbell topology definition
├── parkinglot.py                # Parking lot topology definition
├── multibottleneck.py           # Multi-bottleneck topology definition
│
├── run_batch_dumbbell.sh        # Batch script for dumbbell experiments
├── run_batch_parkinglot.sh      # Batch script for parking lot experiments
│
└── results/                     # Output directory (created automatically)
    ├── dumbbell_bw10_delay2ms_loss2/
    │   ├── switches.csv         # Switch throughput measurements
    │   ├── rtt.csv              # RTT over time
    │   └── bytes.csv            # Bytes sent over time
    ├── dumbbell_bw15_delay2ms_loss2/
    └── ...
```

---

## Running Individual Experiments

### Basic Usage

```bash
sudo python3 experiment_runner_quic.py \
    --topo <topology> \
    --bw <bandwidth> \
    --delay <delay> \
    --loss <loss_percentage> \
    --duration <seconds>
```

### Parameters

| Parameter | Description | Default | Example Values |
|-----------|-------------|---------|----------------|
| `--topo` | Network topology | **Required** | `dumbbell`, `parkinglot`, `multibottleneck` |
| `--bw` | Bottleneck bandwidth (Mbps) | 15 | `10`, `15`, `20`, `35`, `50` |
| `--delay` | Link delay | `2ms` | `1ms`, `2ms`, `5ms`, `10ms` |
| `--loss` | Packet loss (%) | 2 | `0`, `2`, `5`, `10` |
| `--duration` | Test duration (seconds) | 60 | `30`, `60`, `120` |
| `--hosts` | Total number of hosts | 40 | `20`, `40`, `60` |
| `--output-dir` | Custom output directory | Auto-generated | `my_results/test1` |

### Examples

#### 1. Vary Bandwidth (Recommended for COL724 Project)

```bash
# Test 10 Mbps bottleneck
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 10 \
    --delay 2ms \
    --loss 2 \
    --duration 60

# Test 15 Mbps bottleneck
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 2 \
    --duration 60

# Test 20 Mbps bottleneck
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 20 \
    --delay 2ms \
    --loss 2 \
    --duration 60

# Test 35 Mbps bottleneck (will be limited by 20 Mbps host links)
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 35 \
    --delay 2ms \
    --loss 2 \
    --duration 60
```

#### 2. Vary Delay

```bash
# Low delay (1ms)
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 1ms \
    --loss 2 \
    --duration 60

# Medium delay (5ms)
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 5ms \
    --loss 2 \
    --duration 60

# High delay (10ms)
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 10ms \
    --loss 2 \
    --duration 60
```

#### 3. Vary Loss

```bash
# No loss
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 0 \
    --duration 60

# Low loss (2%)
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 2 \
    --duration 60

# Medium loss (5%)
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 5 \
    --duration 60

# High loss (10%)
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 10 \
    --duration 60
```

#### 4. Quick Test (30 seconds)

```bash
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 2 \
    --duration 30
```

#### 5. Custom Output Directory

```bash
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 2 \
    --duration 60 \
    --output-dir results/experiment_1_baseline
```

---

## Running Batch Experiments

### Dumbbell Topology - Complete Test Suite

Create `run_batch_dumbbell.sh`:

```bash
#!/bin/bash
# Comprehensive QUIC experiments for dumbbell topology

set -e  # Exit on error

echo "========================================"
echo "QUIC Dumbbell Topology - Batch Experiments"
echo "========================================"
echo ""

# Create results directory
mkdir -p results
cd results

# 1. VARY BANDWIDTH (delay=2ms, loss=2%)
echo "=== Experiment Set 1: Varying Bandwidth ==="
for bw in 10 15 20 35 50; do
    echo "Running: BW=${bw}Mbps, delay=2ms, loss=2%"
    sudo python3 ../experiment_runner_quic.py \
        --topo dumbbell \
        --bw $bw \
        --delay 2ms \
        --loss 2 \
        --duration 60 \
        --output-dir dumbbell_bw${bw}_delay2ms_loss2
    echo "Completed: BW=${bw}Mbps"
    echo ""
    sleep 5  # Cool-down between experiments
done

# 2. VARY DELAY (bw=15Mbps, loss=2%)
echo "=== Experiment Set 2: Varying Delay ==="
for delay in 1ms 2ms 5ms 10ms; do
    echo "Running: BW=15Mbps, delay=${delay}, loss=2%"
    sudo python3 ../experiment_runner_quic.py \
        --topo dumbbell \
        --bw 15 \
        --delay $delay \
        --loss 2 \
        --duration 60 \
        --output-dir dumbbell_bw15_delay${delay}_loss2
    echo "Completed: delay=${delay}"
    echo ""
    sleep 5
done

# 3. VARY LOSS (bw=15Mbps, delay=2ms)
echo "=== Experiment Set 3: Varying Loss ==="
for loss in 0 2 5 10; do
    echo "Running: BW=15Mbps, delay=2ms, loss=${loss}%"
    sudo python3 ../experiment_runner_quic.py \
        --topo dumbbell \
        --bw 15 \
        --delay 2ms \
        --loss $loss \
        --duration 60 \
        --output-dir dumbbell_bw15_delay2ms_loss${loss}
    echo "Completed: loss=${loss}%"
    echo ""
    sleep 5
done

echo "========================================"
echo "All experiments completed!"
echo "Results saved in: results/"
echo "========================================"

# Generate summary
echo ""
echo "=== Summary of Results ==="
for dir in dumbbell_*; do
    if [ -d "$dir" ] && [ -f "$dir/switches.csv" ]; then
        throughput=$(tail -n 1 "$dir/switches.csv" | cut -d',' -f2)
        echo "$dir: ${throughput} Mbps"
    fi
done
```

Make it executable and run:

```bash
chmod +x run_batch_dumbbell.sh
./run_batch_dumbbell.sh
```

### Parking Lot Topology - Batch Experiments

Create `run_batch_parkinglot.sh`:

```bash
#!/bin/bash
# QUIC experiments for parking lot topology

set -e

echo "========================================"
echo "QUIC Parking Lot Topology - Batch Experiments"
echo "========================================"
echo ""

mkdir -p results
cd results

# Vary bandwidth for parking lot topology
echo "=== Parking Lot: Varying Bandwidth ==="
for bw in 10 15 20 30; do
    echo "Running: BW=${bw}Mbps, delay=2ms, loss=2%"
    sudo python3 ../experiment_runner_quic.py \
        --topo parkinglot \
        --bw $bw \
        --delay 2ms \
        --loss 2 \
        --duration 60 \
        --output-dir parkinglot_bw${bw}_delay2ms_loss2
    echo "Completed: BW=${bw}Mbps"
    echo ""
    sleep 5
done

# Vary loss for parking lot topology
echo "=== Parking Lot: Varying Loss ==="
for loss in 0 2 5 10; do
    echo "Running: BW=15Mbps, delay=2ms, loss=${loss}%"
    sudo python3 ../experiment_runner_quic.py \
        --topo parkinglot \
        --bw 15 \
        --delay 2ms \
        --loss $loss \
        --duration 60 \
        --output-dir parkinglot_bw15_delay2ms_loss${loss}
    echo "Completed: loss=${loss}%"
    echo ""
    sleep 5
done

echo "========================================"
echo "Parking lot experiments completed!"
echo "========================================"
```

Make it executable and run:

```bash
chmod +x run_batch_parkinglot.sh
./run_batch_parkinglot.sh
```

### Custom Batch Script Template

```bash
#!/bin/bash
# Custom experiment batch script

# Define your parameter ranges
BANDWIDTHS=(10 15 20)
DELAYS=(2ms 5ms)
LOSSES=(0 2 5)

# Run experiments
for bw in "${BANDWIDTHS[@]}"; do
    for delay in "${DELAYS[@]}"; do
        for loss in "${LOSSES[@]}"; do
            echo "Running: BW=${bw}, delay=${delay}, loss=${loss}"
            
            sudo python3 experiment_runner_quic.py \
                --topo dumbbell \
                --bw $bw \
                --delay $delay \
                --loss $loss \
                --duration 60
            
            sleep 5  # Cool-down
        done
    done
done
```

---

## Topologies

### 1. Dumbbell Topology

```
Source hosts              Destination hosts
h0 ─┐                    ┌─ h20
h1 ─┤                    ├─ h21
h2 ─┤                    ├─ h22
... ├─ s1 ══[BW]══ s2 ───┤ ...
h18─┤                    ├─ h38
h19─┘                    └─ h39

20 sources → 20 destinations
Host links: 1 Mbps each
Bottleneck: Configurable (bw parameter)
```

**Use for**: Basic throughput, single bottleneck analysis

**File**: `dumbbell.py`

### 2. Parking Lot Topology

```
h0 ─┬─ s1 ══[BW1]══ s2 ══[BW2]══ s3 ─┬─ h20
h1 ─┘                                 └─ h21

Multiple bottlenecks in series
Tests compound loss and cascading congestion
```

**Use for**: Multi-hop scenarios, compound loss

**File**: `parkinglot.py`

### 3. Multi-Bottleneck Topology

```
Complex topology with multiple competing bottlenecks
Tests fairness and resource allocation
```

**Use for**: Advanced congestion control analysis

**File**: `multibottleneck.py`

---

## Output Files

### Directory Structure

Each experiment creates a directory: `{topo}_bw{bw}_delay{delay}_loss{loss}/`

Example: `dumbbell_bw15_delay2ms_loss2/`

### Generated Files

#### 1. `switches.csv`

Switch interface throughput measurements.

```csv
interface,throughput_mbps,duration_sec
s1-eth21,15.23,60
```

**Columns**:
- `interface`: Network interface monitored
- `throughput_mbps`: Measured throughput in Mbps
- `duration_sec`: Test duration

#### 2. `rtt.csv`

Average RTT over time (per second).

```csv
time_sec,avg_rtt_ms
1,65.23
2,67.45
3,68.12
...
```

**Columns**:
- `time_sec`: Time since start (seconds)
- `avg_rtt_ms`: Average RTT across all flows (milliseconds)

#### 3. `bytes.csv`

Total bytes sent per second (all flows combined).

```csv
time_sec,total_bytes_sent
1,1875000
2,1890000
3,1885000
...
```

**Columns**:
- `time_sec`: Time since start
- `total_bytes_sent`: Bytes sent in that second (all flows)

### Log Files (if enabled)

- `h0_client.log` to `h19_client.log`: Client logs
- `h20_server.log` to `h39_server.log`: Server logs (if log level is INFO)

---

## Analyzing Results

### Quick Analysis

```bash
# View throughput
cat results/dumbbell_bw15_delay2ms_loss2/switches.csv

# Calculate average RTT
awk -F',' 'NR>1 {sum+=$2; count++} END {print "Avg RTT:", sum/count, "ms"}' \
    results/dumbbell_bw15_delay2ms_loss2/rtt.csv

# Calculate average throughput (bytes to Mbps)
awk -F',' 'NR>1 {sum+=$2; count++} END {print "Avg Throughput:", (sum/count)*8/1e6, "Mbps"}' \
    results/dumbbell_bw15_delay2ms_loss2/bytes.csv
```

### Python Analysis Script

Create `analyze_results.py`:

```python
#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

def analyze_experiment(result_dir):
    """Analyze a single experiment directory"""
    result_dir = Path(result_dir)
    
    # Read switch throughput
    with open(result_dir / 'switches.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            throughput = float(row['throughput_mbps'])
            print(f"Throughput: {throughput:.2f} Mbps")
    
    # Calculate average RTT
    rtts = []
    with open(result_dir / 'rtt.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rtts.append(float(row['avg_rtt_ms']))
    
    avg_rtt = sum(rtts) / len(rtts)
    print(f"Average RTT: {avg_rtt:.2f} ms")
    print(f"Min RTT: {min(rtts):.2f} ms")
    print(f"Max RTT: {max(rtts):.2f} ms")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_results.py <result_directory>")
        sys.exit(1)
    
    analyze_experiment(sys.argv[1])
```

Usage:

```bash
python3 analyze_results.py results/dumbbell_bw15_delay2ms_loss2/
```

### Compare Multiple Experiments

```bash
#!/bin/bash
# Compare bandwidth experiments

echo "BW,Throughput,Avg_RTT"
for dir in results/dumbbell_bw*_delay2ms_loss2; do
    bw=$(echo $dir | grep -oP 'bw\K[0-9]+')
    tput=$(awk -F',' 'NR==2 {print $2}' $dir/switches.csv)
    rtt=$(awk -F',' 'NR>1 {sum+=$2; n++} END {print sum/n}' $dir/rtt.csv)
    echo "$bw,$tput,$rtt"
done
```

---

## Troubleshooting

### Common Issues

#### 1. Permission Denied

```bash
# Error: Permission denied
# Solution: Run with sudo
sudo python3 experiment_runner_quic.py --topo dumbbell --bw 15 --delay 2ms --loss 2
```

#### 2. Module Not Found: aioquic

```bash
# Error: ModuleNotFoundError: No module named 'aioquic'
# Solution: Install aioquic
pip3 install --break-system-packages aioquic cryptography
```

#### 3. Mininet Already Running

```bash
# Error: Cannot create controller
# Solution: Clean up Mininet
sudo mn -c

# Then run experiment again
```

#### 4. Throughput is Zero

**Possible causes**:
- Servers failed to start
- Network connectivity issues
- Certificate generation failed

**Solution**:
```bash
# Check server logs
cat /tmp/h20_server.log

# Test connectivity manually
sudo mn --test pingall

# Increase verbosity
# In helper_quic.py, change --log-level WARNING to INFO
```

#### 5. Results Directory Not Created

**Solution**:
```bash
# Create manually
mkdir -p results

# Or specify absolute path
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 2 \
    --output-dir /home/user/results/test1
```

#### 6. Experiment Hangs

**Solution**:
```bash
# Press Ctrl+C to stop
# Clean up Mininet
sudo mn -c

# Check for zombie processes
ps aux | grep quic
sudo pkill -f quic_client
sudo pkill -f quic_server
```

### Debug Mode

Enable verbose logging:

```python
# In experiment_runner_quic.py, line 201:
setLogLevel("info")  # Change to "debug" for more details
```

Or in helper_quic.py:

```python
# Change server/client log levels to INFO:
f"--log-level INFO "  # Instead of WARNING
```

### Verification Checklist

Before running experiments:

- [ ] Mininet installed: `sudo mn --version`
- [ ] aioquic installed: `python3 -c "import aioquic"`
- [ ] Run as root: `sudo python3 ...`
- [ ] Mininet cleaned: `sudo mn -c`
- [ ] Sufficient disk space: `df -h`
- [ ] No other experiments running: `ps aux | grep quic`

---

## Advanced Usage

### 1. Modify Host Link Bandwidth

To test bandwidths > 20 Mbps, increase host links:

```python
# In dumbbell.py, line 13:
self.addLink(hosts[i], s1, bw=5, delay="1ms")  # Change from 1 to 5 Mbps
```

Now max capacity = 20 × 5 = 100 Mbps.

### 2. Change Number of Flows

```bash
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 2 \
    --hosts 20  # 10 flows instead of 20
```

### 3. Longer Tests

```bash
# 2-minute test
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 2 \
    --duration 120
```

### 4. Custom Queue Size

```python
# In dumbbell.py, line 19:
self.addLink(s1, s2, bw=bw, delay=delay, loss=loss, max_queue_size=500)
# Change from 100 to 500 packets
```

### 5. Save Server Logs

```python
# In helper_quic.py, modify server startup (~line 194):
server_log = os.path.join(output_dir, f"{h.name}_server.log")
h.cmd(
    f"python3 {quic_server_script} "
    f"--host {h.IP()} --port 4433 "
    f"--cert /tmp/certs/cert.pem --key /tmp/certs/key.pem "
    f"--log-level INFO "  # Change to INFO
    f"> {server_log} 2>&1 &"  # Save to output_dir
)
```

### 6. Parallel Experiments (Use with Caution)

```bash
# Run experiments in parallel (advanced users only)
for bw in 10 15 20; do
    sudo python3 experiment_runner_quic.py \
        --topo dumbbell \
        --bw $bw \
        --delay 2ms \
        --loss 2 \
        --duration 60 &
done
wait  # Wait for all to complete
```

**⚠️ Warning**: Can cause interference between experiments!

---

## Expected Results

### Dumbbell Topology

| BW (Mbps) | Expected Throughput | Expected RTT |
|-----------|--------------------|--------------| 
| 10        | ~10 Mbps           | 70-90 ms     |
| 15        | ~15 Mbps           | 60-70 ms     |
| 20        | ~20 Mbps           | 90-100 ms    |
| 35        | ~20 Mbps (capped)  | 90-100 ms    |

**Note**: Throughput capped at 20 Mbps due to 1 Mbps × 20 host links.

### Delay Variation (BW=15, Loss=2%)

| Delay | Expected RTT |
|-------|--------------|
| 1ms   | ~65-70 ms    |
| 2ms   | ~68-72 ms    |
| 5ms   | ~72-78 ms    |
| 10ms  | ~76-82 ms    |

### Loss Variation (BW=15, Delay=2ms)

| Loss (%) | Expected Throughput | Expected RTT |
|----------|--------------------|--------------| 
| 0        | ~15 Mbps           | ~69 ms       |
| 2        | ~15 Mbps           | ~68 ms       |
| 5        | ~15 Mbps           | ~63 ms       |
| 10       | ~15 Mbps           | ~41 ms       |

**Interesting finding**: RTT decreases with loss! (Prevents bufferbloat)

---

## Tips for COL724 Project

### Recommended Experiment Sets

1. **Bandwidth Variation** (Most Important):
   - Test: 10, 15, 20, 35 Mbps
   - Shows: Throughput scaling, saturation point
   - Duration: 60 seconds each

2. **Delay Variation**:
   - Test: 1ms, 2ms, 5ms, 10ms
   - Shows: RTT sensitivity, delay independence
   - Duration: 60 seconds each

3. **Loss Variation**:
   - Test: 0%, 2%, 5%, 10%
   - Shows: Loss resilience, bufferbloat prevention
   - Duration: 60 seconds each

4. **Topology Comparison**:
   - Run same tests on dumbbell vs parking lot
   - Shows: Multi-hop effects, compound loss


3. **Clean Mininet**: Run `sudo mn -c` if experiments behave oddly
3. Test with simple configuration first
4. Check log files in `/tmp/` or output directory
