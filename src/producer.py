#!/usr/bin/env python3
"""
Simulation Kafka Producer
Streams Credit Card transactions at a realistic human-watchable speed.
Target Duration: ~30 minutes for full dataset (285k records).
"""

import time
import json
import os
import sqlite3
import pandas as pd
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import kagglehub

# --- Configuration ---
# Get config from Docker environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', "fraud-detection-stream")
DB_FILE = os.getenv('STATE_FILE', "state/producer_state.db") 

# --- TUNING FOR REAL-TIME SIMULATION ---
# Slower speed since we now have "train_full_power" for model creation.
# Aim for sustainable demo speed (e.g., 10-20 records/sec)
BATCH_SIZE = 1000          # Fast batch size
SLEEP_PER_BATCH = 0.1      # Fast sleep

# Download Dataset
print("Checking dataset...")
dataset_path = kagglehub.dataset_download("mlg-ulb/creditcardfraud")
CSV_FILE_PATH = os.path.join(dataset_path, "creditcard.csv")

# --- 1. SQLite State Management ---
def init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS state 
                 (topic_name TEXT PRIMARY KEY, last_index INTEGER)''')
    conn.commit()
    conn.close()

def get_last_index():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT last_index FROM state WHERE topic_name=?", (KAFKA_TOPIC,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else -1
    except sqlite3.OperationalError:
        return -1

def update_last_index(index):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO state (topic_name, last_index) VALUES (?, ?)", 
              (KAFKA_TOPIC, index))
    conn.commit()
    conn.close()

# --- 2. Kafka Setup ---
def ensure_topic_exists():
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        existing_topics = admin_client.list_topics()
        
        if KAFKA_TOPIC not in existing_topics:
            print(f"Topic '{KAFKA_TOPIC}' not found. Creating it...")
            topic_list = [NewTopic(name=KAFKA_TOPIC, num_partitions=1, replication_factor=1)]
            try:
                admin_client.create_topics(new_topics=topic_list, validate_only=False)
            except TopicAlreadyExistsError:
                pass
        admin_client.close()
    except Exception as e:
        print(f"Warning: Could not connect to Admin Client ({e}). Skipping topic creation check.")

# --- 3. Main Simulation ---
def simulate_stream():
    init_db()
    ensure_topic_exists()
    
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        linger_ms=10,
        batch_size=16384
    )

    print(f"Loading data from {CSV_FILE_PATH}...")
    df = pd.read_csv(CSV_FILE_PATH)
    total_rows = len(df)
    
    while True: # Infinite Loop for Continuous Demo
        last_index = get_last_index()
        start_index = last_index + 1
        
        if start_index >= total_rows:
            print("🔄 Dataset finished. Restarting stream from beginning...")
            start_index = 0
            update_last_index(-1) # Reset state
            time.sleep(2)
            continue

        print(f"Resuming simulation from index {start_index}...")
        print(f"Speed: ~{int(BATCH_SIZE / SLEEP_PER_BATCH)} records/second")

        try:
            count = 0
            current_batch_end_index = start_index

            subset_df = df.iloc[start_index:]
            
            for row in subset_df.itertuples(index=True):
                message = row._asdict()
                del message['Index'] 
                
                producer.send(KAFKA_TOPIC, value=message)
                
                count += 1
                current_batch_end_index = row.Index

                if count % BATCH_SIZE == 0:
                    producer.flush()
                    update_last_index(current_batch_end_index)
                    
                    # Print every 10 batches (every 500 records) to keep console clean
                    if count % (BATCH_SIZE * 10) == 0:
                        progress = (current_batch_end_index / total_rows) * 100
                        print(f"[{current_batch_end_index}/{total_rows}] Stream Progress: {progress:.1f}%")
                    
                    time.sleep(SLEEP_PER_BATCH)

            producer.flush()
            update_last_index(current_batch_end_index)
            print(f"Batch run finished. Looping...")
            
        except KeyboardInterrupt:
            print("\nStream paused. Progress saved.")
            break
        finally:
            pass # Keep connection open for loop

if __name__ == "__main__":
    simulate_stream()
