from mininet.topo import Topo


class MultiBottleneckTopo(Topo):
    def build(self, bw1=10, bw2=8, bw3=6, delay="2ms", loss=0, number_of_hosts=40):
        mid = number_of_hosts//2
        hosts = []

        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")
        s3 = self.addSwitch("s3")
        s4 = self.addSwitch("s4")
        s5 = self.addSwitch("s5")
        s6 = self.addSwitch("s6")

        # Source hosts connected to s1
        for i in range(mid):
            hosts.append(self.addHost(f"h{i}"))
            self.addLink(hosts[i], s1, bw=1, delay="1ms")
        
        new_mid = mid//2

        # First half of destination hosts connected to s5
        for i in range(mid, mid + new_mid):
            hosts.append(self.addHost(f"h{i}"))
            self.addLink(s5, hosts[i], bw=1, delay="1ms")

        # Second half of destination hosts connected to s6
        for i in range(mid + new_mid, number_of_hosts):
            hosts.append(self.addHost(f"h{i}"))
            self.addLink(s6, hosts[i], bw=1, delay="1ms")
        
        # Switch interconnections
        self.addLink(s1, s2, bw=bw1, delay=delay, loss=loss, max_queue_size=100)
        self.addLink(s1, s3, bw=bw2, delay=delay, loss=loss, max_queue_size=100)
        self.addLink(s2, s4, bw=bw2, delay=delay, loss=loss, max_queue_size=100)
        self.addLink(s3, s4, bw=bw2, delay=delay, loss=loss, max_queue_size=100)
        self.addLink(s4, s5, bw=bw3, delay=delay, loss=loss, max_queue_size=100)
        self.addLink(s4, s6, bw=bw3, delay=delay, loss=loss, max_queue_size=100)
    
    def switch_interface(self, net):
        """Return list of switch interfaces to monitor for TX throughput"""
        interfaces = ["s1-eth21", "s2-eth2", "s3-eth2", "s4-eth2", "s4-eth3"]
        return interfaces
    
    def other_interfaces(self, net):
        """Return additional interfaces to monitor for RX throughput"""
        interfaces = ["s2-eth1"]
        return interfaces