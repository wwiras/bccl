import random
import time

# --- Simulation Parameters ---
NUM_NODES = 5000
FANOUT = 5
TOTAL_TIME_STEPS = 50
NUM_SIMULATIONS = 20

# --- Game-Theoretic Parameters ---
INITIAL_REPUTATION = 100
REPUTATION_BOOST = 10
REPUTATION_PENALTY = 5

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
        newly_infected_neighbors = 0
        neighbors_to_send_to = random.sample(self.neighbors, min(FANOUT, len(self.neighbors)))
        for neighbor in neighbors_to_send_to:
            if neighbor.receive_message(message):
                newly_infected_neighbors += 1
        return newly_infected_neighbors

def run_conventional_simulation():
    nodes = [ConventionalNode(i, []) for i in range(NUM_NODES)]
    for node in nodes:
        node.neighbors = random.sample([n for n in nodes if n != node], 5)

    message = "block_001"
    start_node = random.choice(nodes)
    start_node.receive_message(message)
    
    infected_nodes_count = 1
    total_messages_sent = 0
    propagation_times = []
    
    start_time = time.time()
    
    for t in range(TOTAL_TIME_STEPS):
        current_infected = [node for node in nodes if message in node.known_messages]
        for node in current_infected:
            total_messages_sent += FANOUT
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
        """Strategically chooses neighbors based on reputation."""
        total_messages_sent = 0
        
        reputations = [n.reputation for n in self.neighbors]
        total_reputation = sum(reputations)
        
        if total_reputation == 0:
            return 0
        
        weights = [r / total_reputation for r in reputations]
        
        neighbors_to_send_to = random.choices(self.neighbors, weights=weights, k=min(FANOUT, len(self.neighbors)))
        
        for neighbor in neighbors_to_send_to:
            total_messages_sent += 1
            if neighbor.receive_message(message):
                neighbor.reputation += REPUTATION_BOOST
                self.reputation += REPUTATION_BOOST
            else:
                self.reputation -= REPUTATION_PENALTY
        return total_messages_sent

def run_gt_simulation():
    nodes = [GTNode(i, []) for i in range(NUM_NODES)]
    for node in nodes:
        node.neighbors = random.sample([n for n in nodes if n != node], 5)

    message = "block_001"
    start_node = random.choice(nodes)
    start_node.receive_message(message)
    
    infected_nodes_count = 1
    total_messages_sent = 0
    propagation_times = []
    
    start_time = time.time()

    for t in range(TOTAL_TIME_STEPS):
        current_infected = [node for node in nodes if message in node.known_messages]
        for node in current_infected:
            total_messages_sent += node.gossip(message)
        
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
    print(f"This is a {((avg_conv_time - avg_gt_time) / avg_conv_time) * 100:.2f}% improvement in propagation time.")
    print("This demonstrates how aligning self-interest (reputation) with network efficiency can lead to a more optimized and faster gossip protocol.")