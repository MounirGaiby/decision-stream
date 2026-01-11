from dagster import asset, AssetExecutionContext, Output, MetadataValue
import subprocess
import os
from ..resources import MongoDBResource

@asset(
    description="Reset the environment: Clear DB, Producer state, and Checkpoints",
    group_name="infrastructure",
)
def reset_environment_asset(
    context: AssetExecutionContext,
    mongodb: MongoDBResource
) -> Output[dict]:
    """Clean up all data to start fresh."""
    
    context.log.info("Resetting environment...")

    # 1. Clear Producer State
    db_path = "state/producer_state.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        context.log.info("Deleted producer_state.db")
    else:
        context.log.info("Producer state not found (clean)")

    # 2. Clear Spark Checkpoints
    try:
        subprocess.run(
            ["docker", "exec", "spark", "rm", "-rf", "/tmp/spark-checkpoint", "/tmp/spark-checkpoint-fast"],
            check=False, capture_output=True
        )
        context.log.info("Cleared Spark checkpoints")
    except Exception as e:
        context.log.warning(f"Could not clear checkpoints: {e}")

    # 3. Clear MongoDB Collections
    try:
        client = mongodb.get_client()
        db = client[mongodb.database]
        
        col_list = db.list_collection_names()
        for col_name in col_list:
            if col_name != "system.indexes":
                db[col_name].drop()
                context.log.info(f"Dropped MongoDB collection: {col_name}")
        
        client.close()
    except Exception as e:
        context.log.error(f"MongoDB cleanup failed: {e}")
        raise

    return Output(
        {"status": "reset_complete"},
        metadata={"status": "clean"}
    )
