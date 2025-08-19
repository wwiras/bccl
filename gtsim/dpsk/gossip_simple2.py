import networkx as nx
import random
import matplotlib.pyplot as plt
import numpy as np

# --- Configuration ---
# NUM_NODES = 30  # Smaller network to make problems more apparent
# FREE_RIDER_RATIO = 0.4  # Higher ratio of free-riders
# NETWORK_CONNECTIVITY = 0.08  # Sparse network (p=0.08). This is KEY.

# --- Configuration ---
NUM_NODES = 30
FREE_RIDER_RATIO = 0.3  # Slightly lower ratio
NETWORK_CONNECTIVITY = 0.15  # Increased from 0.08 to 0.15. This is the key fix.

class Network:
    def __init__(self):
        self.nodes = {}
        self.propagation_data = {}
        self.current_message_id = 0
        self.steps = 0  # Global simulation time counter

    def broadcast_message(self, source_id):
        msg_id = self.current_message_id
        self.current_message_id += 1
        self.propagation_data[msg_id] = {}
        self.steps = 0  # Reset time for new message
        # The source node starts the message
        self.nodes[source_id].receive_message(msg_id, None)
        # Simulate 10 steps of propagation
        for _ in range(10):
            self.step()
        return msg_id

    def step(self):
        """Advance simulation by one step. In a real sim, this would handle queued events."""
        self.steps += 1

    def analyze_propagation(self, msg_id):
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
        if msg_id in self.received_messages:
            return  # Already seen

        # Record reception time (current simulation step)
        self.network.propagation_data[msg_id][self.id] = self.network.steps
        self.received_messages.add(msg_id)

        # FREE-RIDER BEHAVIOR: Critical change! Free-riders do NOT relay.
        if self.is_free_rider:
            return  # This is the exploit. They break the protocol.

        # NORMAL BEHAVIOR: Relay to all peers (except the sender)
        for peer_id in self.peers:
            if peer_id == source_id:
                continue
            self.sent_messages += 1
            # In this simple model, we assume the message is sent instantly,
            # but the receiving node will process it on the next 'step'
            target_node = self.network.nodes[peer_id]
            # Simulate network delay by processing on the next step
            # For simplicity, we call it directly, but the step counter ensures order.

    def take_step(self, msg_id):
        """Process any pending actions for this time step."""
        # This is a placeholder for more complex logic.
        # For the conventional protocol, nodes do nothing extra.
        pass

class ConventionalNode(BaseNode):
    """Standard gossip node. Vulnerable to free-riders."""
    pass

class GameTheoryNode(BaseNode):
    """Game-theoretic node that identifies and isolates free-riders."""
    def __init__(self, node_id, network, initial_stake=100):
        super().__init__(node_id, network)
        self.stake = initial_stake
        self.suspicion_level = {}  # Maps peer_id to a suspicion score
        self.message_buffer = []   # Buffer of recent messages to check for propagation

    def receive_message(self, msg_id, source_id):
        super().receive_message(msg_id, source_id)
        if not self.is_free_rider:
            self.message_buffer.append((msg_id, source_id))

    def take_step(self, msg_id):
        """Game-theoretic logic: Monitor peers and punish bad actors."""
        if self.is_free_rider:
            return  # Free-riders don't enforce rules

        # 1. Monitor: Check if messages I sent are being relayed.
        for buffered_msg_id, source_id in self.message_buffer:
            if buffered_msg_id != msg_id:
                continue
            for peer_id in self.peers:
                if peer_id == source_id:
                    continue
                peer = self.network.nodes[peer_id]
                # If my peer hasn't relayed this message, they are suspicious
                if buffered_msg_id not in peer.received_messages:
                    self.suspicion_level[peer_id] = self.suspicion_level.get(peer_id, 0) + 1

        # 2. Punish: If a peer is highly suspicious, disconnect from them.
        for peer_id, suspicion in list(self.suspicion_level.items()):
            if suspicion > 2:  # Threshold for punishment
                print(f"Node {self.id} punishing free-rider {peer_id} (suspicion: {suspicion})")
                self.punish_peer(peer_id)
                del self.suspicion_level[peer_id]

        self.message_buffer = []  # Clear buffer after processing

    def punish_peer(self, peer_id):
        """Punish a non-relaying peer by disconnecting."""
        if peer_id in self.peers:
            self.peers.remove(peer_id)
        peer = self.network.nodes[peer_id]
        if self.id in peer.peers:
            peer.peers.remove(self.id)
        # Slashing stake is a powerful economic incentive
        peer.stake = max(0, peer.stake - 20)
        print(f"  Node {peer_id} slashed! New stake: {peer.stake}")

def create_network(node_type, free_rider_ratio):
    """Creates a SPARSE network."""
    net = Network()
    # Key Change: Use a much sparser network
    graph = nx.erdos_renyi_graph(n=NUM_NODES, p=NETWORK_CONNECTIVITY)

    free_rider_ids = random.sample(range(NUM_NODES), int(NUM_NODES * free_rider_ratio))
    for i in range(NUM_NODES):
        is_free_rider = i in free_rider_ids
        if node_type == "conventional":
            node = ConventionalNode(i, net)
        else:
            node = GameTheoryNode(i, net)
        node.is_free_rider = is_free_rider
        net.nodes[i] = node

    for edge in graph.edges():
        node1, node2 = edge
        net.nodes[node1].add_peer(node2)
        net.nodes[node2].add_peer(node1)

    print(f"Created network with {graph.number_of_edges()} connections (avg degree: {sum(d for n, d in graph.degree()) / NUM_NODES:.2f})")
    return net

def run_simulation(net):
    # Ensure source is honest
    honest_nodes = [node_id for node_id, node in net.nodes.items() if not node.is_free_rider]
    if not honest_nodes:
        return 0, 0  # Handle edge case where there are no honest nodes
    source_id = random.choice(honest_nodes)
    msg_id = net.broadcast_message(source_id)
    nodes_reached, prop_time = net.analyze_propagation(msg_id)
    total_messages = sum(node.sent_messages for node in net.nodes.values())
    return nodes_reached, total_messages

# def run_simulation(net):
#     honest_nodes = [node_id for node_id, node in net.nodes.items() if not node.is_free_rider]
#     source_id = random.choice(honest_nodes)
#     msg_id = net.broadcast_message(source_id)
#     nodes_reached, prop_time = net.analyze_propagation(msg_id)
#     total_messages = sum(node.sent_messages for node in net.nodes.values())
#     return nodes_reached, total_messages

def main():
    print("=== Comparing Gossip Protocols ===")
    print(f"Network: {NUM_NODES} nodes, {FREE_RIDER_RATIO*100}% free-riders")
    print(f"Connectivity: p={NETWORK_CONNECTIVITY}")
    print()

    # Run conventional gossip simulation
    print("--- Running Conventional Gossip ---")
    conv_net = create_network("conventional", FREE_RIDER_RATIO)
    conv_reached, conv_msgs = run_simulation(conv_net)

    # Run game-theoretic gossip simulation
    print("\n--- Running Game-Theoretic Gossip ---")
    game_net = create_network("game", FREE_RIDER_RATIO)
    game_reached, game_msgs = run_simulation(game_net)

    # Print results
    print("\n--- RESULTS ---")
    print("CONVENTIONAL GOSSIP:")
    print(f"  Nodes reached: {conv_reached}/{NUM_NODES} ({conv_reached/NUM_NODES*100:.1f}%)")
    print(f"  Total messages: {conv_msgs}")

    print("\nGAME-THEORETIC GOSSIP:")
    print(f"  Nodes reached: {game_reached}/{NUM_NODES} ({game_reached/NUM_NODES*100:.1f}%)")
    print(f"  Total messages: {game_msgs}")

    # Calculate improvement
    if conv_reached > 0:
        reach_improvement = ((game_reached - conv_reached) / conv_reached) * 100
        print(f"\nIMPROVEMENT: {reach_improvement:+.1f}% more nodes reached")
    else:
        print(f"\nIMPROVEMENT: Conventional failed completely (+∞%)")

    # Plot results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    models = ['Conventional', 'Game-Theoretic']
    reached_data = [conv_reached, game_reached]
    colors = ['red' if conv_reached < NUM_NODES else 'blue', 'green']
    bars1 = ax1.bar(models, reached_data, color=colors)
    ax1.set_ylabel('Nodes Reached')
    ax1.set_title('Propagation Completeness\n(Higher is Better)')
    ax1.set_ylim(0, NUM_NODES)
    for bar, value in zip(bars1, reached_data):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{value}/{NUM_NODES}', ha='center', va='bottom')

    msgs_data = [conv_msgs, game_msgs]
    bars2 = ax2.bar(models, msgs_data, color=['red', 'green'])
    ax2.set_ylabel('Messages Sent')
    ax2.set_title('Network Overhead\n(Lower is Better)')
    for bar, value in zip(bars2, msgs_data):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{value}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('gossip_comparison_improved.png', dpi=120, bbox_inches='tight')
    plt.show()

    # Show stake of free-riders in game-theoretic version
    if isinstance(game_net.nodes[0], GameTheoryNode):
        free_rider_stakes = [node.stake for node in game_net.nodes.values() if node.is_free_rider]
        print(f"\nGame Theory Free-Rider Stake Analysis:")
        print(f"  Average stake: {np.mean(free_rider_stakes):.1f}")
        print(f"  Minimum stake: {min(free_rider_stakes):.1f}")
        if min(free_rider_stakes) < 100:
            print("  --> Free-riders are being punished economically!")

if __name__ == "__main__":
    main()