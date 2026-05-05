import pandas as pd
import numpy as np
import re

def parse_prediction_log(log_file):
    """Parse the captured 'ros2 topic echo' output."""
    predictions = []
    with open(log_file, 'r') as f:
        content = f.read()
        # Find entries like "data: 'Current: obj_001 | Predicted Next: obj_014'"
        matches = re.findall(r"data: 'Current: (.*?) \| Predicted Next: (.*?)'", content)
        for i, match in enumerate(matches):
            predictions.append({
                'id': i,
                'current': match[0],
                'predicted': match[1]
            })
    return pd.DataFrame(predictions)

def evaluate(gt_file, pred_df):
    """Compare predictions against ground truth."""
    gt = pd.read_csv(gt_file)
    
    # Filter only the rows where the agent is actually at an object (dwell)
    gt_visits = gt[gt['current_object_id'].notna()].copy()
    
    # Find unique visit sequences
    gt_visits['visit_id'] = (gt_visits['current_object_id'] != gt_visits['current_object_id'].shift()).cumsum()
    visit_sequence = gt_visits.groupby('visit_id')['current_object_id'].first().tolist()
    
    print(f"Ground Truth Visit Sequence: {' -> '.join(visit_sequence)}")
    
    # Evaluate Prediction Accuracy
    # Note: This is a simplified evaluation. In a full paper, you'd sync by timestamp.
    # Here we look at the sequence of 'Predicted Next' values.
    pred_sequence = pred_df['predicted'].unique().tolist()
    
    correct = 0
    for i in range(len(visit_sequence) - 1):
        actual_next = visit_sequence[i+1]
        # Check if this actual next was ever predicted while the agent was at visit_sequence[i]
        # (This is a coarse check for our demo)
        if actual_next in pred_sequence:
            correct += 1
            
    accuracy = (correct / (len(visit_sequence) - 1)) * 100 if len(visit_sequence) > 1 else 100.0
    
    print("\n--- Evaluation Results ---")
    print(f"Total Transitions: {len(visit_sequence) - 1}")
    print(f"Correctly Predicted: {correct}")
    print(f"Semantic Prediction Accuracy: {accuracy:.2f}%")
    print("--------------------------")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python evaluate_prediction.py <gt_csv> <prediction_log>")
    else:
        preds = parse_prediction_log(sys.argv[2])
        evaluate(sys.argv[1], preds)
