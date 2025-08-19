import networkx as nx
import random
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
from collections import defaultdict

# --- Configuration ---
NUM_NODES = 30
FREE_RIDER_RATIO = 0.3
NETWORK_CONNECTIVITY = 0.15

class Network:
    def __init__(self):
        self.nodes = {}
        self.propagation_data = {}  # {message_id: {node_id: receive_step}}
        self.current_message_id = 0
        self.step = 0
        self.message_queue = deque()  # Queue of (delay, node_id, msg_id, source_id)

    def broadcast_message(self, source_id):
        """Starts a new message from a source node."""
        self.step = 0
        self.message_queue.clear()
        
        msg_id = self.current_message_id
        self.current_message_id += 1
        self.propagation_data[msg_id] = {}
        
        # Source node gets the message at step 0
        self.propagation_data[msg_id][source_id] = 0
        self.nodes[source_id].received_messages.add(msg_id)
        
        # The source node immediately relays to its peers with a delay
        for peer_id in self.nodes[source_id].peers:
            delay = 1  # Messages take at least 1 step to reach direct peers
            self.schedule_message(delay, peer_id, msg_id, source_id)
        
        # Run the simulation for a fixed number of steps
        for _ in range(15):  # Allow 15 steps for propagation
            self.run_step()
        return msg_id

    def schedule_message(self, delay, node_id, msg_id, source_id):
        """Schedule a message to arrive at a node after a delay."""
        arrival_step = self.step + delay
        self.message_queue.append((arrival_step, node_id, msg_id, source_id))

    def run_step(self):
        """Process all messages that are due to arrive at this step."""
        self.step += 1
        # Process all messages scheduled for this current step
        messages_to_process = []
        while self.message_queue and self.message_queue[0][0] <= self.step:
            messages_to_process.append(self.message_queue.popleft())
        
        for arrival_step, node_id, msg_id, source_id in messages_to_process:
            self.nodes[node_id].receive_message(msg_id, source_id)

    def analyze_propagation(self, msg_id):
        """Analyzes how well a message propagated."""
        if msg_id not in self.propagation_data:
            return 0, 0
        
        receive_times = list(self.propagation_data[msg_id].values())
        nodes_reached = len(receive_times)
        propagation_time = max(receive_times) if receive_times else 0
        
        return nodes_reached, propagation_time

class BaseNode:
    def __init__(self, node_id, network):
        self.id = node_id
        self.network = network
        self.peers = []
        self.received_messages = set()
        self.sent_messages = 0
        self.is_free_rider = False

    def add_peer(self, peer_id):
        if peer_id not in self.peers:
            self.peers.append(peer_id)

    def receive_message(self, msg_id, source_id):
        """Called when a message arrives at this node."""
        # If we've already seen this message, do nothing (prevent loops)
        if msg_id in self.received_messages:
            return
            
        # Record the time we received this message
        self.network.propagation_data[msg_id][self.id] = self.network.step
        self.received_messages.add(msg_id)
        
        # FREE-RIDER BEHAVIOR: If this node is a free-rider, it stops here.
        if self.is_free_rider:
            return
            
        # NORMAL BEHAVIOR: Relay to all peers (except the sender)
        for peer_id in self.peers:
            if peer_id == source_id:
                continue
            self.sent_messages += 1
            # Schedule the message to arrive at the peer with a random delay
            delay = 1 + random.random()  # 1-2 step delay
            self.network.schedule_message(delay, peer_id, msg_id, self.id)

class ConventionalNode(BaseNode):
    """Standard gossip node. Vulnerable to free-riders."""
    pass

class GameTheoryNode(BaseNode):
    """Game-theoretic node with smarter, gradual punishment."""
    def __init__(self, node_id, network, initial_stake=100):
        super().__init__(node_id, network)
        self.stake = initial_stake
        self.suspicion_level = defaultdict(int)  # Tracks suspicion per peer
        self.connection_priority = {}  # Priority for maintaining connections
        self.message_history = []      # Recent messages to analyze

    def add_peer(self, peer_id):
        """Override to include connection priority."""
        if peer_id not in self.peers:
            self.peers.append(peer_id)
            # Ensure connection_priority exists before assigning to it
            if not hasattr(self, 'connection_priority'):
                self.connection_priority = {}
            self.connection_priority[peer_id] = 1.0  # Default priority

    def receive_message(self, msg_id, source_id):
        super().receive_message(msg_id, source_id)
        
        if self.is_free_rider:
            return
            
        # Store message info for later analysis
        self.message_history.append((msg_id, source_id, self.network.step))
        # Keep only recent history
        self.message_history = [m for m in self.message_history if self.network.step - m[2] < 10]
        
        # Occasionally maintain connections (5% chance per message)
        if random.random() < 0.05 and hasattr(self, 'maintain_connections'):
            self.maintain_connections()
            
        # Periodically analyze peer behavior (not on every message)
        if random.random() < 0.2:  # 20% chance to analyze
            self.analyze_peer_behavior()

    def analyze_peer_behavior(self):
        """Analyze which peers are not relaying properly."""
        if not self.message_history:
            return
            
        # Check which peers should have relayed recent messages but didn't
        recent_msgs = set(msg[0] for msg in self.message_history)
        
        for peer_id in self.peers:
            peer = self.network.nodes[peer_id]
            # Count how many recent messages the peer should have but doesn't
            missing_count = sum(1 for msg_id in recent_msgs 
                              if msg_id not in peer.received_messages)
            
            if missing_count > 2:  # Only punish if consistently missing messages
                self.suspicion_level[peer_id] += 1
                
                # Gradual punishment based on suspicion level
                if self.suspicion_level[peer_id] == 1:
                    # First offense: just reduce priority
                    if not hasattr(self, 'connection_priority'):
                        self.connection_priority = {}
                    self.connection_priority[peer_id] = self.connection_priority.get(peer_id, 1) - 0.3
                    #print(f"Node {self.id} reduced priority of {peer_id}")
                    
                elif self.suspicion_level[peer_id] >= 3:
                    # Multiple offenses: consider disconnection
                    if random.random() < 0.7:  # 70% chance to disconnect
                        self.punish_peer(peer_id)
                
                # Occasionally forgive if network is becoming too sparse
                if len(self.peers) < 3 and random.random() < 0.4:
                    self.suspicion_level[peer_id] = max(0, self.suspicion_level[peer_id] - 1)

    def punish_peer(self, peer_id):
        """Punish a free-riding peer strategically."""
        if peer_id not in self.peers:
            return
            
        # Only disconnect if we have enough other connections
        if len(self.peers) > 4:  # Maintain minimum connectivity
            self.peers.remove(peer_id)
            peer = self.network.nodes[peer_id]
            if self.id in peer.peers:
                peer.peers.remove(self.id)
            
            # Slash stake but not too aggressively
            peer.stake = max(50, peer.stake - 10)  # Don't reduce below 50
            #print(f"Node {self.id} punished {peer_id}. New stake: {peer.stake}")
            
            # Reset suspicion after punishment
            self.suspicion_level[peer_id] = 0

    def maintain_connections(self):
        """Ensure we maintain adequate network connectivity."""
        if len(self.peers) < 4:  # If we have too few connections
            # Try to reconnect to some previously punished nodes or find new ones
            all_nodes = list(self.network.nodes.keys())
            potential_peers = [nid for nid in all_nodes 
                              if nid != self.id and nid not in self.peers]
            
            if potential_peers:
                # Prefer nodes with higher stake (likely more reliable)
                potential_peers.sort(key=lambda x: self.network.nodes[x].stake, reverse=True)
                new_peer = potential_peers[0]  # Connect to the node with highest stake
                self.add_peer(new_peer)
                self.network.nodes[new_peer].add_peer(self.id)
                #print(f"Node {self.id} added new peer {new_peer} for connectivity")

# class GameTheoryNode(BaseNode):
    """Game-theoretic node that identifies and isolates free-riders."""
    def __init__(self, node_id, network, initial_stake=100):
        super().__init__(node_id, network)
        self.stake = initial_stake
        self.suspicion_level = {}  # Tracks how suspicious each peer is

    def receive_message(self, msg_id, source_id):
        super().receive_message(msg_id, source_id)
        
        # Only honest nodes enforce rules
        if self.is_free_rider:
            return
            
        # 1. If this message came from a peer, check if that peer is relaying others
        if source_id is not None and source_id in self.peers:
            # For simplicity, we'll just punish a random free-rider occasionally
            # A more sophisticated version would track message history
            if random.random() < 0.3:  # 30% chance to check for punishment each message
                potential_targets = [pid for pid in self.peers if self.network.nodes[pid].is_free_rider]
                if potential_targets:
                    target_id = random.choice(potential_targets)
                    self.punish_peer(target_id)

    def punish_peer(self, peer_id):
        """Punish a free-riding peer by disconnecting and slashing stake."""
        if peer_id in self.peers:
            self.peers.remove(peer_id)
        
        peer = self.network.nodes[peer_id]
        if self.id in peer.peers:
            peer.peers.remove(self.id)
            
        # Slash the free-rider's stake
        peer.stake = max(0, peer.stake - 25)

def create_network(node_type, free_rider_ratio):
    """Creates a network with the specified node type and free-rider ratio."""
    net = Network()
    graph = nx.erdos_renyi_graph(n=NUM_NODES, p=NETWORK_CONNECTIVITY)
    
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
    
    print(f"Created network with {graph.number_of_edges()} connections (avg degree: {sum(d for n, d in graph.degree()) / NUM_NODES:.2f})")
    return net

def run_simulation(net):
    """Runs a simulation on the given network."""
    # Ensure source is honest
    honest_nodes = [node_id for node_id, node in net.nodes.items() if not node.is_free_rider]
    if not honest_nodes:
        return 0, 0
    source_id = random.choice(honest_nodes)
    
    msg_id = net.broadcast_message(source_id)
    nodes_reached, prop_time = net.analyze_propagation(msg_id)
    total_messages = sum(node.sent_messages for node in net.nodes.values())
    
    return nodes_reached, total_messages

def main():
    """Main function to compare both protocols."""
    print("=== Comparing Gossip Protocols ===")
    print(f"Network: {NUM_NODES} nodes, {FREE_RIDER_RATIO*100}% free-riders")
    print(f"Connectivity: p={NETWORK_CONNECTIVITY}")
    print()
    
    # Run multiple trials to get average results
    num_trials = 5
    conv_results = []
    game_results = []
    
    for trial in range(num_trials):
        print(f"\n--- Trial {trial + 1}/{num_trials} ---")
        
        # Run conventional gossip simulation
        conv_net = create_network("conventional", FREE_RIDER_RATIO)
        conv_reached, conv_msgs = run_simulation(conv_net)
        conv_results.append((conv_reached, conv_msgs))
        print(f"Conventional: {conv_reached}/{NUM_NODES} nodes reached")
        
        # Run game-theoretic gossip simulation
        game_net = create_network("game", FREE_RIDER_RATIO)
        game_reached, game_msgs = run_simulation(game_net)
        game_results.append((game_reached, game_msgs))
        print(f"Game-Theoretic: {game_reached}/{NUM_NODES} nodes reached")
    
    # Calculate averages
    avg_conv_reached = sum(r[0] for r in conv_results) / num_trials
    avg_conv_msgs = sum(r[1] for r in conv_results) / num_trials
    
    avg_game_reached = sum(r[0] for r in game_results) / num_trials
    avg_game_msgs = sum(r[1] for r in game_results) / num_trials
    
    # Print results
    print("\n=== FINAL RESULTS (Averages) ===")
    print("CONVENTIONAL GOSSIP:")
    print(f"  Nodes reached: {avg_conv_reached:.1f}/{NUM_NODES} ({avg_conv_reached/NUM_NODES*100:.1f}%)")
    print(f"  Total messages: {avg_conv_msgs:.1f}")
    
    print("\nGAME-THEORETIC GOSSIP:")
    print(f"  Nodes reached: {avg_game_reached:.1f}/{NUM_NODES} ({avg_game_reached/NUM_NODES*100:.1f}%)")
    print(f"  Total messages: {avg_game_msgs:.1f}")
    
    # Calculate improvement
    if avg_conv_reached > 0:
        reach_improvement = ((avg_game_reached - avg_conv_reached) / avg_conv_reached) * 100
        print(f"\nIMPROVEMENT: {reach_improvement:+.1f}% more nodes reached")
    else:
        print(f"\nIMPROVEMENT: Conventional failed completely (+∞%)")
    
    # Plot results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    models = ['Conventional', 'Game-Theoretic']
    reached_data = [avg_conv_reached, avg_game_reached]
    colors = ['red' if avg_conv_reached < NUM_NODES * 0.9 else 'blue', 'green']
    bars1 = ax1.bar(models, reached_data, color=colors)
    ax1.set_ylabel('Nodes Reached')
    ax1.set_title('Propagation Completeness\n(Higher is Better)')
    ax1.set_ylim(0, NUM_NODES)
    for bar, value in zip(bars1, reached_data):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{value:.1f}/{NUM_NODES}', ha='center', va='bottom')
    
    msgs_data = [avg_conv_msgs, avg_game_msgs]
    bars2 = ax2.bar(models, msgs_data, color=['red', 'green'])
    ax2.set_ylabel('Messages Sent')
    ax2.set_title('Network Overhead\n(Lower is Better)')
    for bar, value in zip(bars2, msgs_data):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{value:.1f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('gossip_comparison_final.png', dpi=120, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    main()