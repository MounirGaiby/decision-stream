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
# This now defaults to the folder we mounted
DB_FILE = os.getenv('STATE_FILE', "state/producer_state.db") 

# Download Dataset
print("Checking dataset...")
dataset_path = kagglehub.dataset_download("mlg-ulb/creditcardfraud")
CSV_FILE_PATH = os.path.join(dataset_path, "creditcard.csv")

# --- 1. SQLite State Management ---
def init_db():
    # Ensure the directory exists (in case we run locally without Docker)
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
    # Only try to create topic if we are connecting to a real server (not testing)
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
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

    print(f"Loading data from {CSV_FILE_PATH}...")
    df = pd.read_csv(CSV_FILE_PATH)
    
    last_index = get_last_index()
    start_index = last_index + 1
    total_rows = len(df)
    
    if start_index >= total_rows:
        print("Dataset already fully processed! Delete 'state/producer_state.db' to restart.")
        return

    print(f"Resuming stream from index {start_index}...")

    try:
        # Use iloc to skip already processed rows
        for relative_index, row in df.iloc[start_index:].iterrows():
            
            # The 'relative_index' in iloc is 0, 1, 2... of the SLICE. 
            # We need the ACTUAL index from the dataframe
            actual_index = start_index + relative_index
            
            message = row.to_dict()
            producer.send(KAFKA_TOPIC, value=message)
            
            print(f"[{actual_index}/{total_rows}] Sent: Time={message['Time']}, Class={message['Class']}")
            
            update_last_index(actual_index)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStream paused. Progress saved.")
    finally:
        producer.close()

if __name__ == "__main__":
    simulate_stream()