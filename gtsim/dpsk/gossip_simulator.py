# gossip_simulator.py
import simpy
import networkx as nx
import random
import matplotlib.pyplot as plt
from collections import deque
import numpy as np


class GossipSubNode:
    def __init__(self, node_id, network, is_free_rider=False):
        self.id = node_id
        self.network = network
        self.peers = set()
        self.received_messages = set()
        self.sent_messages = 0
        self.is_free_rider = is_free_rider # New: Flag for free-rider behavior
        network.nodes[node_id] = self

    def add_peer(self, peer_id):
        """Add a peer connection."""
        self.peers.add(peer_id)

    def receive_message(self, msg_id, source_id):
        """This is called when a message arrives at the node."""
        global message_counter

        if msg_id in self.received_messages:
            return  # Already seen, avoid loops

        # Record the time this node received the message
        if msg_id not in propagation_data:
            propagation_data[msg_id] = {}
        propagation_data[msg_id][self.id] = env.now

        self.received_messages.add(msg_id)

        # FREE-RIDER BEHAVIOR: If this node is a free-rider, it does nothing.
        if self.is_free_rider:
            return

        # NORMAL BEHAVIOR: Relay the message to all peers
        for peer_id in self.peers:
            # Don't send back to the source
            if peer_id == source_id:
                continue
            # Schedule the message arrival at the peer with a random delay (simulating network latency)
            delay = random.uniform(0.1, 1.0)
            self.sent_messages += 1
            env.process(self.send_message(peer_id, msg_id, delay))

    def send_message(self, peer_id, msg_id, delay):
        """Simulates sending a message with a delay."""
        yield env.timeout(delay)
        self.network.nodes[peer_id].receive_message(msg_id, self.id)
        
        
class IncentivizedNode(GossipSubNode):
    def __init__(self, node_id, network, is_free_rider=False, initial_stake=100):
        super().__init__(node_id, network, is_free_rider)
        self.stake = initial_stake
        self.relay_proofs = []  # Simulates proofs of relay

    def receive_message(self, msg_id, source_id):
        """Override the receive method to include proof generation."""
        global message_counter

        if msg_id in self.received_messages:
            return

        if msg_id not in propagation_data:
            propagation_data[msg_id] = {}
        propagation_data[msg_id][self.id] = env.now

        self.received_messages.add(msg_id)

        # FREE-RIDER BEHAVIOR remains the same
        if self.is_free_rider:
            return

        # Generate a "proof" that this node is relaying
        proof = (msg_id, len(self.peers))
        self.relay_proofs.append(proof)

        # Relay the message
        for peer_id in self.peers:
            if peer_id == source_id:
                continue
            delay = random.uniform(0.1, 1.0)
            self.sent_messages += 1
            env.process(self.send_message(peer_id, msg_id, delay))

    def submit_proofs(self):
        """Called periodically. Simulates submitting proofs for rewards."""
        if self.relay_proofs and not self.is_free_rider:
            total_relays = sum(relay_count for (_, relay_count) in self.relay_proofs)
            reward = total_relays * 0.1  # Small reward per relay
            self.stake += reward
            self.relay_proofs = [] # Reset proofs

    def audit(self, auditor):
        """Simulate an audit. If a free-rider has no proofs, slash them."""
        if self.is_free_rider and not self.relay_proofs:
            # This free-rider was caught!
            slash_amount = self.stake * 0.2 # Slash 20%
            self.stake -= slash_amount
            # Punishment: Disconnect from the auditor
            if auditor.id in self.peers:
                self.peers.remove(auditor.id)
            if self.id in auditor.peers:
                auditor.peers.remove(self.id)
            # print(f"Node {self.id} was slashed by {auditor.id}! New stake: {self.stake}")
            

# Create a Simpy environment. This is the core of our simulation.
env = simpy.Environment()

# Create a network graph to represent node connections.
network_graph = nx.erdos_renyi_graph(n=100, p=0.1, seed=42)
# This creates a random graph with 100 nodes, each pair having a 10% chance of being connected.

# Global message ID counter
message_counter = 0
# Dictionary to track propagation data for each message: {message_id: {node_id: receive_time}}
propagation_data = {}
# List to store all nodes
all_nodes = {}

class Network:
    """A simple container class to hold our nodes and make them accessible."""
    def __init__(self):
        self.nodes = {}

# Create our network instance
net = Network()

            
def setup_network(use_incentivized=False):
    """Initializes the network with nodes and connections."""
    global net, all_nodes
    net = Network()
    all_nodes = {}

    # Create nodes
    free_rider_ids = random.sample(range(100), 30) # 30% free-riders
    for i in range(100):
        is_free_rider = i in free_rider_ids
        if use_incentivized:
            node = IncentivizedNode(i, net, is_free_rider)
        else:
            node = GossipSubNode(i, net, is_free_rider)
        all_nodes[i] = node

    # Connect nodes based on the pre-made network graph
    for (node1, node2) in network_graph.edges():
        all_nodes[node1].add_peer(node2)
        all_nodes[node2].add_peer(node1)

def run_simulation():
    """Runs the simulation for a single message."""
    global message_counter, propagation_data
    propagation_data = {} # Reset tracking data
    msg_id = message_counter
    message_counter += 1

    # Start the message from node 0
    all_nodes[0].received_messages.add(msg_id)
    propagation_data[msg_id] = {0: env.now}
    for peer_id in all_nodes[0].peers:
        delay = random.uniform(0.1, 1.0)
        all_nodes[0].sent_messages += 1
        env.process(all_nodes[0].send_message(peer_id, msg_id, delay))

    # For Incentivized protocol: Run audits periodically
    if isinstance(all_nodes[0], IncentivizedNode):
        env.process(periodic_audits())
        env.process(periodic_rewards())

    # Run the simulation for a set amount of time
    env.run(until=50) # Run for 50 simulation time units

def periodic_audits():
    """A process that periodically triggers random audits."""
    while True:
        yield env.timeout(5) # Every 5 time units
        auditor = random.choice(list(all_nodes.values()))
        if not auditor.is_free_rider: # Only honest nodes audit
            target_id = random.choice(list(auditor.peers))
            target = all_nodes[target_id]
            target.audit(auditor)

def periodic_rewards():
    """A process that periodically lets nodes submit proofs for rewards."""
    while True:
        yield env.timeout(10) # Every 10 time units
        for node in all_nodes.values():
            if isinstance(node, IncentivizedNode):
                node.submit_proofs()

def analyze_results():
    """Calculates and prints results for the last run simulation."""
    msg_id = message_counter - 1
    data = propagation_data.get(msg_id, {})
    total_nodes = len(all_nodes)
    nodes_reached = len(data)
    time_values = list(data.values())
    max_time = max(time_values) if time_values else 0

    print(f"Message reached {nodes_reached}/{total_nodes} nodes.")
    print(f"Maximum propagation time: {max_time:.2f}")

    # Calculate total messages sent
    total_messages = sum(node.sent_messages for node in all_nodes.values())
    print(f"Total messages sent: {total_messages}")

    # For incentivized nodes, print average stake of free-riders
    if isinstance(all_nodes[0], IncentivizedNode):
        free_rider_stakes = [node.stake for node in all_nodes.values() if node.is_free_rider]
        avg_stake = sum(free_rider_stakes) / len(free_rider_stakes) if free_rider_stakes else 0
        print(f"Average Free-Rider Stake: {avg_stake:.2f}")

    return nodes_reached, max_time, total_messages

# --- MAIN EXECUTION LOOP ---
print("=== RUNNING BASELINE (GossipSub) SIMULATION ===")
setup_network(use_incentivized=False)
run_simulation()
baseline_reached, baseline_time, baseline_msgs = analyze_results()

env = simpy.Environment() # RESET the environment for the next run
print("\n=== RUNNING INCENTIVIZED SIMULATION ===")
setup_network(use_incentivized=True)
run_simulation()
incentivized_reached, incentivized_time, incentivized_msgs = analyze_results()

# --- PLOTTING RESULTS ---
fig, ax = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: Nodes Reached
labels = ['Baseline', 'Incentivized']
nodes_reached_data = [baseline_reached, incentivized_reached]
ax[0].bar(labels, nodes_reached_data, color=['red', 'green'])
ax[0].set_ylabel('Number of Nodes Reached')
ax[0].set_title('Propagation Completeness\n(30% Free-Riders)')
ax[0].set_ylim(0, 100)

# Plot 2: Messages Sent
messages_data = [baseline_msgs, incentivized_msgs]
ax[1].bar(labels, messages_data, color=['red', 'green'])
ax[1].set_ylabel('Total Messages Sent')
ax[1].set_title('Network Bandwidth Cost')

plt.tight_layout()
plt.savefig('gossip_comparison.png')
plt.show()