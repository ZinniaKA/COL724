from mininet.topo import Topo

class DumbbellTopo(Topo):
    def build(self, bw=10, delay="1ms", loss=0, number_of_hosts=40):
        mid = number_of_hosts // 2
        hosts = []

        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")

        for i in range(mid):
            hosts.append(self.addHost(f"h{i}", cpu=0.1))  # Limited to 10%, fair sharing
            self.addLink(hosts[i], s1, bw=1, delay="1ms")  
        
        for i in range(mid, number_of_hosts):
            hosts.append(self.addHost(f"h{i}"))
            self.addLink(hosts[i], s2, bw=1, delay="1ms")
        
        self.addLink(s1, s2, bw=bw, delay=delay, loss=loss, max_queue_size=100)
    
    def switch_interface(self, net):
        """Return list of switch interfaces to monitor for throughput"""
        interfaces = ["s1-eth21"]
        return interfaces
