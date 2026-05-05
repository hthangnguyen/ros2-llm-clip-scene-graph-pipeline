#!/usr/bin/env bash
# Full Pipeline Launch Script - Robust Version
echo "Initializing environment..."

# 1. Environment Setup
source /opt/ros/humble/setup.bash
eval "$(/home/aidev1/miniconda3/bin/conda shell.bash hook)"
export PYTHONPATH=/home/aidev1/miniconda3/envs/auto-robot/lib/python3.10/site-packages:$PYTHONPATH
export PATH=/home/aidev1/miniconda3/envs/auto-robot/bin:$PATH

cd /home/aidev1/research/ros2-robot/ros2_scene_graph_ws
source install/setup.bash
mkdir -p eval logs

echo "Starting Full Pipeline..."

# Cleanup function
cleanup() {
    echo "Shutting down nodes..."
    pkill -P $$ 2>/dev/null
    # Safety pkill for any leftover nodes in this workspace
    pkill -f synthetic_scene 2>/dev/null
    pkill -f perception_oracle 2>/dev/null
    pkill -f scene_graph_builder 2>/dev/null
    pkill -f trajectory_predictor 2>/dev/null
    pkill -f agent_sim 2>/dev/null
    echo "Cleanup complete."
}
trap cleanup EXIT INT TERM

# 2. Launch Nodes (with logging)
echo "Launching nodes (logs in ros2_scene_graph_ws/logs/)..."

xvfb-run -a ros2 run synthetic_scene synthetic_scene_node > logs/sim.log 2>&1 &
ros2 run agent_sim agent_sim_node --ros-args -p sim_duration_sec:=120.0 > logs/agent.log 2>&1 &
ros2 run perception_oracle perception_oracle_node > logs/perc.log 2>&1 &
ros2 run scene_graph_builder scene_graph_builder_node > logs/builder.log 2>&1 &
ros2 run trajectory_predictor trajectory_predictor_node > logs/pred.log 2>&1 &

echo "Nodes started. Waiting for warmup (40s)..."
for i in {40..1}; do
    echo -ne "Warmup: $i \r"
    sleep 1
done
echo -e "\nWarmup complete. Starting prediction capture..."

# 3. Capture
ros2 topic echo /agent_primary/prediction --full-length > eval/prediction_log.txt &
ECHO_PID=$!

echo "Running for 150 seconds. Watch logs/pred.log for live updates."
sleep 150

echo "Done. Triggering final cleanup."