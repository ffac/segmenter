class Gateway:
    def __init__(self, gateway, tq, nexthop, interface):
        self.gateway = gateway
        self.tq = tq
        self.nexthop = nexthop
        self.interface = interface

    def __repr__(self):
        return 'Gateway("{0}", "{1}", "{2}", "{3}")'.format(self.gateway, self.tq, self.nexthop, self.interface)

    def __str__(self):
        return "{0} ({1}) {2} [{3}]".format(self.gateway, self.tq, self.nexthop, self.interface)

class BatmanParser:
    """ parser for batman-adv status files """

    def __init__(self, basepath = "/sys/kernel/debug/batman_adv/"):
        self.basepath = basepath

    def gateways(self, device):
        filename = self.basepath + "/" + device + "/gateways"
        ret = []
        with open(filename, 'r') as file:
            file.readline() # discard header
            for line in file.readlines():
                g,t,n,i,r = line.split(None, 4)
                ret.append(Gateway(g,t[1:-1],n,i[1:-2]))
        return ret

