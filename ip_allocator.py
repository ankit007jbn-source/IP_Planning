import ipaddress


def generate_sb_pool(subnet):
    network = ipaddress.ip_network(subnet)

    hosts = list(network.hosts())

    if not hosts:
        raise Exception("Subnet has no usable IPs!")

    gateway_ip = str(hosts[0])
    vm_ips = hosts[1:]
    broadcast_ip = str(network.broadcast_address)

    return gateway_ip, vm_ips, broadcast_ip


def generate_ip_pool(subnet):
    network = ipaddress.ip_network(subnet)
    return list(network.hosts())