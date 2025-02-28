Pyroute2
========

Pyroute2 is a pure Python **netlink** library. The core requires only Python
stdlib, no 3rd party libraries. The library was started as an RTNL protocol
implementation, so the name is **pyroute2**, but now it supports many netlink
protocols. Some supported netlink families and protocols:

* **rtnl**, network settings --- addresses, routes, traffic controls
* **nfnetlink** --- netfilter API
* **ipq** --- simplest userspace packet filtering, iptables QUEUE target
* **devlink** --- manage and monitor devlink-enabled hardware
* **generic** --- generic netlink families
* **uevent** --- same uevent messages as in udev

Netfilter API:

* **ipset** --- IP sets
* **nftables** --- packet filtering
* **nfct** --- connection tracking

Generic netlink:

* **ethtool** --- low-level network interface setup
* **wireguard** --- VPN setup
* **nl80211** --- wireless functions API (basic support)
* **taskstats** --- extended process statistics
* **acpi_events** --- ACPI events monitoring
* **thermal_events** --- thermal events monitoring
* **VFS_DQUOT** --- disk quota events monitoring

On the low level the library provides socket objects with an
extended API. The additional functionality aims to:

* Help to open/bind netlink sockets
* Discover generic netlink protocols and multicast groups
* Construct, encode and decode netlink and PF_ROUTE messages

Supported systems
-----------------

Pyroute2 runs natively on Linux and emulates some limited subset
of RTNL netlink API on BSD systems on top of PF_ROUTE notifications
and standard system tools.

Other platforms are not supported.

NDB -- high level RTNL API
--------------------------

Key features:

* Data integrity
* Transactions with commit/rollback changes
* State synchronization
* Multiple sources, including netns and remote systems

A "Hello world" example:

.. code-block:: python

    from pyroute2 import NDB

    with NDB() as ndb:
        with ndb.interfaces['eth0'] as eth0
            # set one parameter
            eth0.set(state='down')
            eth0.commit()  # make sure that the interface is down
            # or multiple parameters at once
            eth0.set(ifname='hello_world!', state='up')
            eth0.commit()  # rename, bring up and wait for success
        # --> <-- here you can be sure that the interface is up & renamed

More examples:

.. code-block:: python

    from pyroute2 import NDB

    ndb = NDB(log='debug')

    for record in ndb.interfaces.summary():
        print(record.ifname, record.address, record.state)

    if_dump = ndb.interfaces.dump()
    if_dump.select_records(state='up')
    if_dump.select_fields('index', 'ifname', 'kind')
    for line in if_dump.format('json'):
        print(line)

    addr_summary = ndb.addresses.summary()
    addr_summary.select_records(ifname='eth0')
    for line in addr_summary.format('csv'):
        print(line)

    with ndb.interfaces.create(ifname='br0', kind='bridge') as br0:
        br0.add_port('eth0')
        br0.add_port('eth1')
        br0.add_ip('10.0.0.1/24')
        br0.add_ip('192.168.0.1/24')
        br0.set(
            br_stp_state=1,  # set STP on
            br_group_fwd_mask=0x4000,  # set LLDP forwarding
            state='up',  # bring the interface up
        )
    # --> <-- commit() will be run by the context manager

    # operate on netns:
    ndb.sources.add(netns='testns')  # connect to a namespace

    with (
        ndb.interfaces.create(
            ifname='veth0',  # create veth
            kind='veth',
            peer={
                'ifname': 'eth0',  # setup peer
                'net_ns_fd': 'testns',  # in a namespace
            },
            state='up',
        )
    ) as veth0:
        veth0.add_ip(address='172.16.230.1', prefixlen=24)

    with ndb.interfaces.wait(
        target='testns', ifname='eth0'
    ) as peer:  # wait for the peer
        peer.set(state='up')  # bring it up
        peer.add_ip('172.16.230.2/24')  # add address

IPRoute -- Low level RTNL API
-----------------------------

Low-level **IPRoute** utility --- Linux network configuration.
The **IPRoute** class is a 1-to-1 RTNL mapping. There are no implicit
interface lookups and so on.

Get notifications about network settings changes with IPRoute:

.. code-block:: python

    from pyroute2 import IPRoute
    with IPRoute() as ipr:
        # With IPRoute objects you have to call bind() manually
        ipr.bind()
        for message in ipr.get():
            print(message)

More examples:

.. code-block:: python

    from socket import AF_INET
    from pyroute2 import IPRoute

    # get access to the netlink socket
    ipr = IPRoute()
    # no monitoring here -- thus no bind()

    # print interfaces
    for link in ipr.get_links():
        print(link)

    # create VETH pair and move v0p1 to netns 'test'
    ipr.link('add', ifname='v0p0', peer='v0p1', kind='veth')
    # wait for the devices:
    peer, veth = ipr.poll(
        ipr.link, 'dump', timeout=5, ifname=lambda x: x in ('v0p0', 'v0p1')
    )
    ipr.link('set', index=peer['index'], net_ns_fd='test')

    # bring v0p0 up and add an address
    ipr.link('set', index=veth['index'], state='up')
    ipr.addr('add', index=veth['index'], address='10.0.0.1', prefixlen=24)

    # release Netlink socket
    ip.close()

Network namespace examples
--------------------------

Network namespace manipulation:

.. code-block:: python

    from pyroute2 import netns
    # create netns
    netns.create('test')
    # list
    print(netns.listnetns())
    # remove netns
    netns.remove('test')

Create **veth** interfaces pair and move to **netns**:

.. code-block:: python

    from pyroute2 import IPRoute

    with IPRoute() as ipr:

        # create interface pair
        ipr.link('add', ifname='v0p0', kind='veth',  peer='v0p1')

        # wait for the peer
        (peer,) = ipr.poll(ipr.link, 'dump', timeout=5, ifname='v0p1')

        # move the peer to the 'test' netns:
        ipr.link('set', index=peer['index'], net_ns_fd='test')

List interfaces in some **netns**:

.. code-block:: python

    from pyroute2 import NetNS
    from pprint import pprint

    ns = NetNS('test')
    pprint(ns.get_links())
    ns.close()

More details and samples see in the documentation.

Installation
------------

Using pypi:

.. code-block:: bash

    pip install pyroute2

Using git:

.. code-block:: bash

    pip install git+https://github.com/svinota/pyroute2.git

Using source, requires make and nox

.. code-block:: bash

    git clone https://github.com/svinota/pyroute2.git
    cd pyroute2
    make install

Requirements
------------

Python >= 3.6

Links
-----

* home: https://pyroute2.org/
* source: https://github.com/svinota/pyroute2
* bugs: https://github.com/svinota/pyroute2/issues
* pypi: https://pypi.python.org/pypi/pyroute2
* docs: http://docs.pyroute2.org/
