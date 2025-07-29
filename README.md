# Agglomerative Clustering
Agglomerative Clustering with BNSF

### Step 1 - Create a network topology (based on ER or BA)
Below is the example on how to create a network overlay of BA/ER network.

```shell
# Create overlay networkDeployments. Change the values accordingly
$ python network_constructor.py --nodes 10 --model BA --minlat 10 --maxlat 98 --others 5
minlat: 10
maxlat: 98
Initial status from the input .....
Number of nodes in the network: 10
Average neighbor (degree): 5
Creating BARABASI ALBERT (BA) network model .....
Average degree: 5.0
Target degree:5
nx.is_connected(network): True
Graph Before: Graph with 10 nodes and 25 edges
BA network model is SUCCESSFUL ! ....
Graph After: Graph with 10 nodes and 25 edges
Do you want to save the graph? (y/n): y 
Topology saved to nodes10_Jul262025125801_BA5.json

```

### Step 2 - Apply Agglomerative Clustering (AC)
The input are BA topology (json) and M total clusters. Once AC processed completed, a new overlay network
is generated in json file. This new file name is formatted by combining its original filename plus "AC"
in the end.
```shell
(venv) $ python AC.py --json_file_path nodes10_Jul262025125801_BA5.json --num_clusters 3
Loading network from : topology/nodes10_Jul262025125801_BA5.json
Total cluster(s), M : 3

--- Loaded Distance Matrix ---
[[0 96 45 92 14 95 73 10 inf 36]
 [96 0 inf inf inf inf 19 38 35 inf]
 [45 inf 0 inf inf inf 71 inf inf 48]
 [92 inf inf 0 inf inf 84 90 59 80]
 [14 inf inf inf 0 inf inf inf 60 inf]
 [95 inf inf inf inf 0 60 23 inf 66]
 [73 19 71 84 inf 60 0 34 59 35]
 [10 38 inf 90 inf 23 34 0 52 inf]
 [inf 35 inf 59 60 inf 59 52 0 inf]
 [36 inf 48 80 inf 66 35 inf inf 0]]


--- BNSF Process Completed ---

--- Final Clusters (M = 3) ---
Cluster 1: ['gossip-2', 'gossip-4', 'gossip-0', 'gossip-7']
Cluster 2: ['gossip-3', 'gossip-8']
Cluster 3: ['gossip-5', 'gossip-9', 'gossip-1', 'gossip-6']

--- Leader Selection & Announcement ---
Cluster 1 Leader: gossip-7
Cluster 2 Leader: gossip-8
Cluster 3 Leader: gossip-9

--- Phase 3: MST Construction (Parallel Logic) ---
  Cluster 1 MST Edges (Root: 2):
    Edge: 0 -> 4, Weight: 14.0
    Edge: 2 -> 0, Weight: 45.0
    Edge: 0 -> 7, Weight: 10.0
  Cluster 2 MST Edges (Root: 3):
    Edge: 3 -> 8, Weight: 59.0
  Cluster 3 MST Edges (Root: 5):
    Edge: 6 -> 9, Weight: 35.0
    Edge: 6 -> 1, Weight: 19.0
    Edge: 5 -> 6, Weight: 60.0

--- Connecting MST Root Nodes ---
  Inter-cluster connecting edges:
    Edge: 5 -> 3, Weight: 35.0
    Edge: 2 -> 5, Weight: 23.0

--- Comprehensive MST for the Entire Network ---
  Edge 1: gossip-5 -> gossip-3, Weight: 35.0
  Edge 2: gossip-2 -> gossip-5, Weight: 23.0
  Edge 3: gossip-0 -> gossip-4, Weight: 14.0
  Edge 4: gossip-2 -> gossip-0, Weight: 45.0
  Edge 5: gossip-0 -> gossip-7, Weight: 10.0
  Edge 6: gossip-3 -> gossip-8, Weight: 59.0
  Edge 7: gossip-6 -> gossip-9, Weight: 35.0
  Edge 8: gossip-6 -> gossip-1, Weight: 19.0
  Edge 9: gossip-5 -> gossip-6, Weight: 60.0

--- Phase 4: Neighbor Selection (MON) ---
  Node gossip-0's Optimal Neighbors:
    - gossip-4 (Weight: 14.0)
    - gossip-2 (Weight: 45.0)
    - gossip-7 (Weight: 10.0)
  Node gossip-1's Optimal Neighbors:
    - gossip-6 (Weight: 19.0)
  Node gossip-2's Optimal Neighbors:
    - gossip-5 (Weight: 23.0)
    - gossip-0 (Weight: 45.0)
  Node gossip-3's Optimal Neighbors:
    - gossip-5 (Weight: 35.0)
    - gossip-8 (Weight: 59.0)
  Node gossip-4's Optimal Neighbors:
    - gossip-0 (Weight: 14.0)
  Node gossip-5's Optimal Neighbors:
    - gossip-3 (Weight: 35.0)
    - gossip-2 (Weight: 23.0)
    - gossip-6 (Weight: 60.0)
  Node gossip-6's Optimal Neighbors:
    - gossip-9 (Weight: 35.0)
    - gossip-1 (Weight: 19.0)
    - gossip-5 (Weight: 60.0)
  Node gossip-7's Optimal Neighbors:
    - gossip-0 (Weight: 10.0)
  Node gossip-8's Optimal Neighbors:
    - gossip-3 (Weight: 59.0)
  Node gossip-9's Optimal Neighbors:
    - gossip-6 (Weight: 35.0)

--- Phase 5: Building New Overlay Topology File ---
Successfully created new overlay topology file at: topology/nodes10_Jul262025125801_BA5_AC.json

```

### Step 4 - Prepare Cloud Native Infrastructure (Starting a GKE cluster)
This a must do step. Since we are going to use GKE for our test, a GKE cluster must be ready. 
Here are the specification used for this test.

| Features/Specification | Description          |
|------------------------|----------------------|
| Name	                  | bcgossip-cluster     |	
| Tier 	                 | Standard             |	
| Mode 	                 | Standard             |	
| Location type          | 	Zonal               |	
| Control plane zone     | 	us-central1-a       |	
| Default node zones     | 	us-central1-a       |
| Total size             | 	36                  |	
| Release channel        | 	Regular channel     |	
| Version                | 	1.33.2-gke.1111000  |	
| Current COS version    | 	cos-121-18867-90-62 |
| Total vCPUs            | 	72                  |
| Total Memory           | 	144 GB              |


### Step 5 - Inject Topology info (from Step 1 & 2) to GKE Cluster
Once GKE cluster is ready, prepare the topology based on the output of Step 1 or Step 2. 
The purpose of this step is to mimic BA or Clustering Topology by extracting and copying all the neighbors
info of each pod (using sqlite). The command is shown below.
```shell
$ python prepare.py --filename nodes1000_Jul282025005524_BA5_AC10.json
Deployment number of nodes equal to topology nodes: 1000

Starting update for 1000 pods (timeout: 300s, max retries: 3)...
Progress: 1.0% | Elapsed: 23.2s | Success: 10/1000 | Failed: 0 | Retries pending: 0
Progress: 100.0% | Elapsed: 2298.1s | Success: 1000/1000 | Failed: 0 | Retries pending: 0

Update completed in 2298.1 seconds
Summary - Total: 1000 | Success: 1000 | Failed: 0
Platform is now ready for testing..!
```

### Step 6 - Run a test to update neighbors in the simulator
Next we need to update the neighbor of each pods by running a single propagation test. Here is the command.
In this step, the neighbors info from the sqlite (ned.db) will be updated to pods' memory.
```shell
$ python3 automate.py --num_tests 1
self.num_tests=1
Number of running pods (num_nodes): 1000
Checking for pods in namespace default...
All 1000 pods are up and running in namespace default.
Selected pod: gossip-dpymt-86dfccf48c-449bd
{"event": "gossip_start", "pod_name": "gossip-dpymt-86dfccf48c-449bd", "message": "72ad-cubaan1000-1", "start_time": "2025/07/29 16:53:49", "details": "Gossip propagation started for message: 72ad-cubaan1000-1"}
host_ip=10.40.15.7

target=10.40.15.7:5050

Sending message to self (10.40.15.7): '72ad-cubaan1000-1' with latency=0.0 ms

Received acknowledgment: Done propagate! 10.40.15.7 received: '72ad-cubaan1000-1'

{"event": "gossip_end", "pod_name": "gossip-dpymt-86dfccf48c-449bd", "message": "72ad-cubaan1000-1", "end_time": "2025/07/29 17:00:37", "details": "Gossip propagation completed for message: 72ad-cubaan1000-1"}
Test 1 complete.
```

### Step 7 - Test the BA / Newly Generated Agglomerative Clustering (AC) in the simulator
Next we need to initiate the gossip test in order to get the propagation time of the topology chosen from previous step (Step 5). 
Here is the command. Just specify the total number of tests.
```shell
puluncode@cloudshell:~/bccl (stoked-cosine-415611)$ python3 automate.py --num_tests 10
self.num_tests=10
Number of running pods (num_nodes): 1000
Checking for pods in namespace default...
All 1000 pods are up and running in namespace default.
Selected pod: gossip-dpymt-86dfccf48c-bcdx4
{"event": "gossip_start", "pod_name": "gossip-dpymt-86dfccf48c-bcdx4", "message": "2940-cubaan1000-1", "start_time": "2025/07/29 17:05:50", "details": "Gossip propagation started for message: 2940-cubaan1000-1"}
host_ip=10.40.23.21

target=10.40.23.21:5050

Sending message to self (10.40.23.21): '2940-cubaan1000-1' with latency=0.0 ms

...
...
...


```