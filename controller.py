import collections
import collections.abc
collections.MutableMapping = collections.abc.MutableMapping

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
from ryu.topology import event
from ryu.topology.api import get_switch, get_link
import networkx as nx


class LinkFailureRecovery(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LinkFailureRecovery, self).__init__(*args, **kwargs)
        self.net = nx.DiGraph()
        self.mac_to_port = {}
        self.datapaths = {}

        # 🔥 FIREWALL RULE: block h1 → h3
        self.blocked_pairs = [("00:00:00:00:00:01", "00:00:00:00:00:03")]

    # 🔹 Switch connects
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    # 🔹 Add flow
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst
        )
        datapath.send_msg(mod)

    # 🔹 Packet handling
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        dst = eth.dst
        src = eth.src
        in_port = msg.match['in_port']

        # 🔥 FIREWALL CHECK
        if (src, dst) in self.blocked_pairs:
            self.logger.info("BLOCKED: %s -> %s", src, dst)
            return  # Drop packet

        # Learn MAC
        self.mac_to_port[dpid][src] = in_port

        # Forwarding logic
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install flow rule
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # Send packet
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data
        )
        datapath.send_msg(out)

    # 🔹 Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology(self, ev):
        switch_list = get_switch(self, None)
        switches = [switch.dp.id for switch in switch_list]
        self.net.add_nodes_from(switches)

        links = get_link(self, None)
        for link in links:
            self.net.add_edge(link.src.dpid, link.dst.dpid)

        self.logger.info("Topology: %s", self.net.edges())

    # 🔹 Link failure detection
    @set_ev_cls(event.EventLinkDelete)
    def link_delete_handler(self, ev):
        link = ev.link
        src = link.src.dpid
        dst = link.dst.dpid

        self.logger.info("LINK FAILURE DETECTED: %s -> %s", src, dst)

        if self.net.has_edge(src, dst):
            self.net.remove_edge(src, dst)

        self.recompute_paths()

    # 🔹 Recompute paths
    def recompute_paths(self):
        self.logger.info("Recomputing paths...")

        for src in self.net.nodes():
            for dst in self.net.nodes():
                if src != dst:
                    try:
                        path = nx.shortest_path(self.net, src, dst)
                        self.logger.info("Path %s -> %s : %s", src, dst, path)
                    except nx.NetworkXNoPath:
                        self.logger.info("No path between %s and %s", src, dst)