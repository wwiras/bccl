import networkx as nx
import random
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

# --- Configuration ---
NUM_NODES = 50
FREE_RIDER_RATIO = 0.3  # 30% of nodes will be free-riders
SIMULATION_TIME = 10

class Network:
    """A simple network to hold all nodes and global state."""
    def __init__(self):
        self.nodes = {}
        self.propagation_data = {}  # Tracks when each node received each message
        self.current_message_id = 0

    def broadcast_message(self, source_id):
        """Starts a new message from a source node."""
        msg_id = self.current_message_id
        self.current_message_id += 1
        self.propagation_data[msg_id] = {}
        # The source node instantly "receives" the message
        self.nodes[source_id].receive_message(msg_id, None)
        return msg_id

    def analyze_propagation(self, msg_id):
        """Analyzes how well a message propagated."""
        if msg_id not in self.propagation_data:
            return 0, 0
        
        receive_times = list(self.propagation_data[msg_id].values())
        nodes_reached = len(receive_times)
        propagation_time = max(receive_times) if receive_times else 0
        
        return nodes_reached, propagation_time

class BaseNode:
    """Base class for all node types."""
    def __init__(self, node_id, network):
        self.id = node_id
        self.network = network
        self.peers = []
        self.received_messages = set()
        self.sent_messages = 0
        self.is_free_rider = False

    def add_peer(self, peer_id):
        self.peers.append(peer_id)

    def receive_message(self, msg_id, source_id):
        """Called when a message arrives at this node."""
        # If we've already seen this message, do nothing (prevent loops)
        if msg_id in self.received_messages:
            return
            
        # Record the time we received this message
        current_time = len(self.received_messages)  # Simple模拟时间
        self.network.propagation_data[msg_id][self.id] = current_time
        self.received_messages.add(msg_id)
        
        # FREE-RIDER BEHAVIOR: If this node is a free-rider, it stops here.
        if self.is_free_rider:
            return
            
        # NORMAL BEHAVIOR: Relay to all peers (except the sender)
        for peer_id in self.peers:
            if peer_id == source_id:
                continue
            self.sent_messages += 1
            # Simulate network delay by adding a small random time
            delay = random.random()
            # In a real sim, we'd schedule this. Here we just call directly.
            self.network.nodes[peer_id].receive_message(msg_id, self.id)

class ConventionalNode(BaseNode):
    """Standard gossip node with no incentives. Free-riders can exploit this."""
    pass

class GameTheoryNode(BaseNode):
    """Game-theoretic node that punishes free-riders."""
    def __init__(self, node_id, network, initial_stake=100):
        super().__init__(node_id, network)
        self.stake = initial_stake
        self.relay_count = 0
        
    def receive_message(self, msg_id, source_id):
        if msg_id in self.received_messages:
            return
            
        current_time = len(self.received_messages)
        self.network.propagation_data[msg_id][self.id] = current_time
        self.received_messages.add(msg_id)
        
        if self.is_free_rider:
            return  # Free-riders still don't relay
            
        # Honest nodes relay and earn rewards
        for peer_id in self.peers:
            if peer_id == source_id:
                continue
            self.sent_messages += 1
            self.relay_count += 1
            self.network.nodes[peer_id].receive_message(msg_id, self.id)
        
        # Periodically reward honest behavior
        if self.relay_count >= 5:
            self.stake += self.relay_count * 0.1
            self.relay_count = 0
            
    def punish_free_rider(self, target_id):
        """Punish a free-riding node by disconnecting and slashing stake."""
        target = self.network.nodes[target_id]
        if target.is_free_rider and target_id in self.peers:
            # Disconnect from the free-rider
            self.peers.remove(target_id)
            if self.id in target.peers:
                target.peers.remove(self.id)
            # Slash the free-rider's stake
            target.stake -= target.stake * 0.2

def create_network(node_type, free_rider_ratio):
    """Creates a network with the specified node type and free-rider ratio."""
    net = Network()
    graph = nx.erdos_renyi_graph(n=NUM_NODES, p=0.15)
    
    # Create nodes
    free_rider_ids = random.sample(range(NUM_NODES), int(NUM_NODES * free_rider_ratio))
    for i in range(NUM_NODES):
        is_free_rider = i in free_rider_ids
        if node_type == "conventional":
            node = ConventionalNode(i, net)
        else:
            node = GameTheoryNode(i, net)
        node.is_free_rider = is_free_rider
        net.nodes[i] = node
    
    # Connect nodes based on the graph
    for edge in graph.edges():
        node1, node2 = edge
        net.nodes[node1].add_peer(node2)
        net.nodes[node2].add_peer(node1)
    
    return net

def run_simulation(net):
    """Runs a simulation on the given network."""
    # Start a message from a random honest node
    honest_nodes = [node_id for node_id, node in net.nodes.items() if not node.is_free_rider]
    source_id = random.choice(honest_nodes)
    
    msg_id = net.broadcast_message(source_id)
    
    # For game theory network, occasionally punish free-riders
    if isinstance(net.nodes[0], GameTheoryNode):
        for _ in range(5):  # 5 punishment attempts
            punisher_id = random.choice(honest_nodes)
            target_id = random.choice(list(net.nodes.keys()))
            if target_id != punisher_id:
                net.nodes[punisher_id].punish_free_rider(target_id)
    
    # Analyze results
    nodes_reached, prop_time = net.analyze_propagation(msg_id)
    total_messages = sum(node.sent_messages for node in net.nodes.values())
    
    return nodes_reached, total_messages

def main():
    """Main function to compare both protocols."""
    print("=== Comparing Gossip Protocols ===")
    print(f"Network: {NUM_NODES} nodes, {FREE_RIDER_RATIO*100}% free-riders")
    print()
    
    # Run conventional gossip simulation
    conv_net = create_network("conventional", FREE_RIDER_RATIO)
    conv_reached, conv_msgs = run_simulation(conv_net)
    
    # Run game-theoretic gossip simulation
    game_net = create_network("game", FREE_RIDER_RATIO)
    game_reached, game_msgs = run_simulation(game_net)
    
    # Print results
    print("CONVENTIONAL GOSSIP:")
    print(f"  Nodes reached: {conv_reached}/{NUM_NODES} ({conv_reached/NUM_NODES*100:.1f}%)")
    print(f"  Total messages: {conv_msgs}")
    print()
    
    print("GAME-THEORETIC GOSSIP:")
    print(f"  Nodes reached: {game_reached}/{NUM_NODES} ({game_reached/NUM_NODES*100:.1f}%)")
    print(f"  Total messages: {game_msgs}")
    print()
    
    # Calculate and show improvement
    reach_improvement = ((game_reached - conv_reached) / conv_reached) * 100
    print(f"IMPROVEMENT: {reach_improvement:+.1f}% more nodes reached")
    
    # Plot results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Nodes Reached
    models = ['Conventional', 'Game-Theoretic']
    reached_data = [conv_reached, game_reached]
    bars = ax1.bar(models, reached_data, color=['red', 'green'])
    ax1.set_ylabel('Nodes Reached')
    ax1.set_title('Propagation Completeness')
    ax1.set_ylim(0, NUM_NODES)
    for bar, value in zip(bars, reached_data):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{value}/{NUM_NODES}', ha='center')
    
    # Plot 2: Messages Sent
    msgs_data = [conv_msgs, game_msgs]
    bars = ax2.bar(models, msgs_data, color=['red', 'green'])
    ax2.set_ylabel('Messages Sent')
    ax2.set_title('Network Overhead')
    for bar, value in zip(bars, msgs_data):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                f'{value}', ha='center')
    
    plt.tight_layout()
    plt.savefig('gossip_comparison_simple.png', dpi=100, bbox_inches='tight')
    plt.show()
    
    # Show stake of free-riders in game-theoretic version
    if isinstance(game_net.nodes[0], GameTheoryNode):
        free_rider_stakes = [node.stake for node in game_net.nodes.values() if node.is_free_rider]
        print(f"\nGame Theory Free-Rider Stake Analysis:")
        print(f"  Average stake: {np.mean(free_rider_stakes):.1f}")
        print(f"  Minimum stake: {min(free_rider_stakes):.1f}")
        print("  (Free-riders are being punished economically)")

if __name__ == "__main__":
    main()