import pytest
from pyroute2 import NetlinkError
from pr2modules.netlink.rtnl.ifinfmsg import IFF_NOARP
from pr2test.context_manager import make_test_matrix

test_matrix = make_test_matrix(
    targets=['local', 'netns'],
)


@pytest.mark.parametrize('context', test_matrix, indirect=True)
def test_updown_link(context):
    index, ifname = context.default_interface

    context.ipr.link('set', index=index, state='up')
    assert context.ipr.get_links(ifname=ifname)[0]['flags'] & 1
    context.ipr.link('set', index=index, state='down')
    assert not (context.ipr.get_links(ifname=ifname)[0]['flags'] & 1)


@pytest.mark.parametrize('context', test_matrix, indirect=True)
def test_link_altname(context):
        altname1 = context.new_ifname
        altname2 = context.new_ifname
        weird_name = ("test_with_a_very_long_string"
                      "_and_♄⚕⚚_utf8_symbol")
        index, ifname = context.default_interface

        for name in (altname1, altname2, weird_name):
            with pytest.raises(NetlinkError):
                context.ipr.link("get", altname=name)

        context.ipr.link("property_add",
                     index=index,
                     altname=[altname1, altname2])
        assert len(context.ipr.link("get", altname=altname1)) == 1
        assert len(context.ipr.link("get", altname=altname2)) == 1

        context.ipr.link("property_del",
                     index=index,
                     altname=[altname1, altname2])

        for name in (altname1, altname2):
            with pytest.raises(NetlinkError):
                context.ipr.link("get", altname=name)

        context.ipr.link("property_add", index=index, altname=weird_name)
        assert len(context.ipr.link("get", altname=weird_name)) == 1
        context.ipr.link("property_del", index=index, altname=weird_name)
        assert len(context.ipr.link("dump", altname=weird_name)) == 0
        with pytest.raises(NetlinkError):
            context.ipr.link("get", altname=weird_name)


@pytest.mark.parametrize('context', test_matrix, indirect=True)
def test_link_filter(context):
    links = context.ipr.link('dump', ifname='lo')
    assert len(links) == 1
    assert links[0].get_attr('IFLA_IFNAME') == 'lo'


@pytest.mark.parametrize('context', test_matrix, indirect=True)
def test_link_legacy_nla(context):
    index, ifname = context.default_interface
    new_ifname = context.new_ifname

    context.ipr.link('set', index=index, state='down')
    context.ipr.link('set', index=index, IFLA_IFNAME=new_ifname)
    assert context.ipr.link_lookup(ifname=new_ifname) == [index]

    context.ipr.link('set', index=index, ifname=ifname)
    assert context.ipr.link_lookup(ifname=ifname) == [index]


@pytest.mark.parametrize('context', test_matrix, indirect=True)
def test_link_rename(context):
    index, ifname = context.default_interface
    new_ifname = context.new_ifname

    context.ipr.link('set', index=index, ifname=new_ifname)
    assert context.ipr.link_lookup(ifname=new_ifname) == [index]

    context.ipr.link('set', index=index, ifname=ifname)
    assert context.ipr.link_lookup(ifname=ifname) == [index]


@pytest.mark.parametrize('context', test_matrix, indirect=True)
def test_link_arp_flag(context):
    index, _ = context.default_interface

    # by default dummy interface have NOARP set
    assert context.ipr.get_links(index)[0]['flags'] & IFF_NOARP

    context.ipr.link('set', index=index, arp=True)
    assert not context.ipr.get_links(index)[0]['flags'] & IFF_NOARP

    context.ipr.link('set', index=index, arp=False)
    assert context.ipr.get_links(index)[0]['flags'] & IFF_NOARP

    context.ipr.link('set', index=index, noarp=False)
    assert not context.ipr.get_links(index)[0]['flags'] & IFF_NOARP

    context.ipr.link('set', index=index, noarp=True)
    assert context.ipr.get_links(index)[0]['flags'] & IFF_NOARP


@pytest.mark.parametrize('context', test_matrix, indirect=True)
def test_symbolic_flags_ifinfmsg(context):
    index, _ = context.default_interface

    context.ipr.link('set', index=index, flags=['IFF_UP'])
    iface = context.ipr.get_links(index)[0]
    assert iface['flags'] & 1
    assert 'IFF_UP' in iface.flags2names(iface['flags'])
    context.ipr.link('set', index=index, flags=['!IFF_UP'])
    assert not (context.ipr.get_links(index)[0]['flags'] & 1)


@pytest.mark.parametrize('context', test_matrix, indirect=True)
def test_remove_link(context):
    index, ifname = context.default_interface
    context.ipr.link('del', index=index)
    assert len(context.ipr.link_lookup(ifname=ifname)) == 0
    assert len(context.ipr.link_lookup(index=index)) == 0
