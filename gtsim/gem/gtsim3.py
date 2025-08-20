import random
import time

# --- Simulation Parameters ---
NUM_NODES = 5000
# NUM_NODES = 500
# NUM_NODES = 50
# NUM_NODES = 10
FANOUT = 5
TOTAL_TIME_STEPS = 50
NUM_SIMULATIONS = 20

# --- Game-Theoretic Parameters ---
INITIAL_REPUTATION = 100
REPUTATION_BOOST_SUCCESS = 10  # Reward for successfully informing a new peer
REPUTATION_PENALTY_REDUNDANCY = 5 # Penalty for sending to an already-informed peer
REPUTATION_DECAY_RATE = 0.99  # A decay factor applied each time step

# ====================================================================
# Conventional Gossip Model
# ====================================================================
class ConventionalNode:
    def __init__(self, node_id, neighbors):
        self.node_id = node_id
        self.neighbors = neighbors
        self.known_messages = set()

    def receive_message(self, message):
        if message not in self.known_messages:
            self.known_messages.add(message)
            return True
        return False

    def gossip(self, message):
        """Randomly selects FANOUT neighbors and forwards the message."""
        neighbors_to_send_to = random.sample(self.neighbors, min(FANOUT, len(self.neighbors)))
        for neighbor in neighbors_to_send_to:
            neighbor.receive_message(message)

def run_conventional_simulation():
    nodes = [ConventionalNode(i, []) for i in range(NUM_NODES)]
    for node in nodes:
        node.neighbors = random.sample([n for n in nodes if n != node], FANOUT)

    message = "block_001"
    start_node = random.choice(nodes)
    start_node.receive_message(message)
    
    infected_nodes_count = 1
    total_messages_sent = 0
    propagation_times = []
    
    start_time = time.time()
    
    for t in range(TOTAL_TIME_STEPS):
        current_infected = [node for node in nodes if message in node.known_messages]
        total_messages_sent += len(current_infected) * FANOUT
        for node in current_infected:
            node.gossip(message)
        
        newly_infected_count = sum(1 for node in nodes if message in node.known_messages)
        if newly_infected_count > infected_nodes_count:
            propagation_times.append(t + 1)
            infected_nodes_count = newly_infected_count
        
        if infected_nodes_count == NUM_NODES:
            break
    
    end_time = time.time()
    
    final_time_step = propagation_times[-1] if propagation_times else TOTAL_TIME_STEPS
    return final_time_step, total_messages_sent, end_time - start_time

# ====================================================================
# Game-Theory Based Gossip Model
# ====================================================================
class GTNode:
    def __init__(self, node_id, neighbors):
        self.node_id = node_id
        self.neighbors = neighbors
        self.known_messages = set()
        self.reputation = INITIAL_REPUTATION

    def receive_message(self, message):
        if message not in self.known_messages:
            self.known_messages.add(message)
            return True
        return False

    def gossip(self, message):
        """Strategically chooses neighbors based on reputation, with a hybrid approach."""
        
        # Sort neighbors by reputation
        sorted_neighbors = sorted(self.neighbors, key=lambda n: n.reputation, reverse=True)
        
        # Select top-reputation neighbors (e.g., top 60%)
        strategic_fanout = int(FANOUT * 0.6)
        strategic_choices = sorted_neighbors[:strategic_fanout]
        
        # Select remaining randomly
        remaining_neighbors = sorted_neighbors[strategic_fanout:]
        random_fanout = FANOUT - strategic_fanout
        random_choices = random.sample(remaining_neighbors, min(random_fanout, len(remaining_neighbors)))
        
        # Combine choices
        neighbors_to_send_to = strategic_choices + random_choices
        
        for neighbor in neighbors_to_send_to:
            if neighbor.receive_message(message):
                neighbor.reputation += REPUTATION_BOOST_SUCCESS
                self.reputation += REPUTATION_BOOST_SUCCESS
            else:
                self.reputation -= REPUTATION_PENALTY_REDUNDANCY

def run_gt_simulation():
    nodes = [GTNode(i, []) for i in range(NUM_NODES)]
    for node in nodes:
        node.neighbors = random.sample([n for n in nodes if n != node], FANOUT)

    message = "block_001"
    start_node = random.choice(nodes)
    start_node.receive_message(message)
    
    infected_nodes_count = 1
    total_messages_sent = 0
    propagation_times = []
    
    start_time = time.time()

    for t in range(TOTAL_TIME_STEPS):
        # Apply reputation decay
        for node in nodes:
            node.reputation = max(INITIAL_REPUTATION, node.reputation * REPUTATION_DECAY_RATE)

        current_infected = [node for node in nodes if message in node.known_messages]
        # Count messages sent only if they are being forwarded
        total_messages_sent += len(current_infected) * FANOUT
        for node in current_infected:
            node.gossip(message)
        
        newly_infected_count = sum(1 for node in nodes if message in node.known_messages)
        if newly_infected_count > infected_nodes_count:
            propagation_times.append(t + 1)
            infected_nodes_count = newly_infected_count
        
        if infected_nodes_count == NUM_NODES:
            break
            
    end_time = time.time()

    final_time_step = propagation_times[-1] if propagation_times else TOTAL_TIME_STEPS
    return final_time_step, total_messages_sent, end_time - start_time

# ====================================================================
# Main Execution and Comparison
# ====================================================================
if __name__ == "__main__":
    
    print("Running simulations...")
    
    conv_times = []
    conv_redundancy = []
    conv_duration = []

    for _ in range(NUM_SIMULATIONS):
        time_steps, messages_sent, duration = run_conventional_simulation()
        conv_times.append(time_steps)
        conv_redundancy.append(messages_sent)
        conv_duration.append(duration)

    gt_times = []
    gt_redundancy = []
    gt_duration = []

    for _ in range(NUM_SIMULATIONS):
        time_steps, messages_sent, duration = run_gt_simulation()
        gt_times.append(time_steps)
        gt_redundancy.append(messages_sent)
        gt_duration.append(duration)

    avg_conv_time = sum(conv_times) / len(conv_times)
    avg_conv_redundancy = sum(conv_redundancy) / len(conv_redundancy)
    avg_conv_duration = sum(conv_duration) / len(conv_duration)

    avg_gt_time = sum(gt_times) / len(gt_times)
    avg_gt_redundancy = sum(gt_redundancy) / len(gt_redundancy)
    avg_gt_duration = sum(gt_duration) / len(gt_duration)
    
    print("\n=======================================================")
    print("              SIMULATION RESULTS")
    print("=======================================================")
    print(f"Simulation Parameters):")
    print(f"  - Number of Nodes: {NUM_NODES}")
    print(f"  - Fanout: {FANOUT}")
    print(f"Conventional Gossip (Avg over {NUM_SIMULATIONS} runs):")
    print(f"  - Propagation Time: {avg_conv_time:.2f} time steps")
    print(f"  - Total Messages Sent: {avg_conv_redundancy:.2f}")
    print(f"  - Simulation Duration: {avg_conv_duration:.4f} seconds")
    print("-" * 50)
    print(f"Game-Theoretic Gossip (Avg over {NUM_SIMULATIONS} runs):")
    print(f"  - Propagation Time: {avg_gt_time:.2f} time steps")
    print(f"  - Total Messages Sent: {avg_gt_redundancy:.2f}")
    print(f"  - Simulation Duration: {avg_gt_duration:.4f} seconds")
    print("=======================================================\n")
    
    print("Interpretation:")
    print(f"The game-theoretic model achieved full network propagation in {avg_gt_time:.2f} time steps compared to the conventional model's {avg_conv_time:.2f} steps.")
    if avg_gt_time < avg_conv_time:
        improvement = ((avg_conv_time - avg_gt_time) / avg_conv_time) * 100
        print(f"This is a {improvement:.2f}% improvement in propagation time.")
    else:
        degradation = ((avg_gt_time - avg_conv_time) / avg_conv_time) * 100
        print(f"This is a degradation of {degradation:.2f}% in propagation time.")
    
    if avg_gt_redundancy < avg_conv_redundancy:
        reduction = ((avg_conv_redundancy - avg_gt_redundancy) / avg_conv_redundancy) * 100
        print(f"Additionally, the game-theoretic model reduced message redundancy by {reduction:.2f}%.")
    else:
        increase = ((avg_gt_redundancy - avg_conv_redundancy) / avg_conv_redundancy) * 100
        print(f"However, the game-theoretic model increased message redundancy by {increase:.2f}%.")
        
    print("This demonstrates how refining the incentive structure can lead to more optimized network behavior.")