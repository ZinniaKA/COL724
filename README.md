# QUIC Network Experiments

QUIC throughput testing using **mininet** and **aioquic**.

## Setup
```bash
# Install
sudo apt-get install mininet
pip install aioquic cryptography

# Verify
sudo mn --test pingall
python3 -c "import aioquic; print(aioquic.__version__)"
```

## Quick Start
```bash
# Single experiment
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 2 \
    --duration 30

# Batch experiments
python3 exp_dumbbell.py
python3 exp_parkinglot.py
```

### Basic Usage

```bash
sudo python3 experiment_runner_quic.py \
    --topo <topology> \
    --bw <bandwidth> \
    --delay <delay> \
    --loss <loss_percentage> \
    --duration <seconds>
```
Example 

```bash
sudo python3 experiment_runner_quic.py \
    --topo dumbbell \
    --bw 15 \
    --delay 2ms \
    --loss 2 \
    --duration 30
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--topo` | Network topology | **Required** |
| `--bw` | Bottleneck bandwidth (Mbps) | 15 |
| `--delay` | Link delay | 2ms |  
| `--loss` | Packet loss (%) | 2 | 
| `--duration` | Test duration (seconds) | 60 | 
| `--hosts` | Total number of hosts | 40 | 
| `--output-dir` | Custom output directory | Auto-generated |

## Advanced Usage

**Modify host bandwidth** (dumbbell.py, line 13):
```python
self.addLink(hosts[i], s1, bw=5, delay="1ms")  # 5 Mbps instead of 1
```

**Change number of flows**:
```bash
--hosts 20  # 10 flows instead of 20
```

**Custom queue size** (dumbbell.py, line 19):
```python
max_queue_size=500  # 500 packets instead of 100
```

## Troubleshooting
```bash
# Clean up
sudo mn -c

# Check logs 
cat /tmp/h20_server.log
```
