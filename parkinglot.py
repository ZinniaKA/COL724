from mininet.topo import Topo


class ParkingLotTopo(Topo):
    def build(self, bw1=10, bw2=8, delay="2ms", loss=0, number_of_hosts=40):
        mid = number_of_hosts//2
        hosts = []

        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")
        s3 = self.addSwitch("s3")
        print(f"mid : {mid}")
        
        # Source hosts connected to s1
        for i in range(mid):
            hosts.append(self.addHost(f"h{i}"))
            self.addLink(hosts[i], s1, bw=1, delay="1ms")
        
        new_mid = mid//2

        # First half of destination hosts connected to s2
        for i in range(mid, mid + new_mid):
            hosts.append(self.addHost(f"h{i}"))
            self.addLink(s2, hosts[i], bw=1, delay="1ms")

        # Second half of destination hosts connected to s3
        for i in range(mid + new_mid, number_of_hosts):
            hosts.append(self.addHost(f"h{i}"))
            self.addLink(s3, hosts[i], bw=1, delay="1ms")
        
        # Switch interconnections
        self.addLink(s1, s2, bw=bw1, delay=delay, loss=loss, max_queue_size=100)
        self.addLink(s2, s3, bw=bw2, delay=delay, loss=loss, max_queue_size=100)
    
    def switch_interface(self, net):
        """Return list of switch interfaces to monitor for throughput"""
        interfaces = ["s1-eth21", "s2-eth12"]
        return interfaces