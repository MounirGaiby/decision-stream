"""
Export MongoDB collections to Excel files for Tableau analysis
Exports all collections to separate Excel files in the data/ folder
"""

import os
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

# Configuration MongoDB
# Update: Added authSource=admin to prevent connection errors
MONGO_URI = "mongodb://admin:admin123@localhost:27017/?authSource=admin"
DATABASE = "fraud_detection"

# Collections to export
# Update: Removed 'model_predictions' because our Optimized Spark job 
# merged it into 'ensemble_results' to save speed.
COLLECTIONS = [
    "transactions",
    "ensemble_results",
    "flagged_transactions"
]

def export_collection_to_excel(client, db_name, collection_name, output_dir):
    """
    Export a MongoDB collection to an Excel file
    """
    try:
        db = client[db_name]
        collection = db[collection_name]
        
        # Count documents
        count = collection.count_documents({})
        
        if count == 0:
            print(f"   ⚠️  {collection_name}: No data found, skipping...")
            return False
        
        print(f"   📊 {collection_name}: Found {count} documents")
        
        # Fetch all documents
        cursor = collection.find({})
        
        # Convert to list and then to DataFrame
        documents = list(cursor)
        df = pd.DataFrame(documents)
        
        # Remove MongoDB _id field (ObjectId is not Excel-friendly)
        if '_id' in df.columns:
            df = df.drop('_id', axis=1)
        
        # FIX: Handle Datetime Timezones for Excel
        # Excel does not support timezone-aware datetimes. We must strip them.
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)

        # Convert ObjectId and other non-serializable types to strings
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if column contains ObjectId or other complex types
                sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
                if sample is not None and not isinstance(sample, (str, int, float, bool, datetime)):
                    df[col] = df[col].astype(str)
        
        # Create output file path
        output_file = os.path.join(output_dir, f"{collection_name}.xlsx")
        
        # Export to Excel
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        print(f"   ✅ Exported to: {output_file} ({len(df)} rows, {len(df.columns)} columns)")
        return True
        
    except Exception as e:
        print(f"   ❌ Error exporting {collection_name}: {e}")
        return False

def main():
    """
    Main function to export all collections to Excel
    """
    print("=" * 80)
    print("📤 EXPORTING MONGODB DATA TO EXCEL")
    print("=" * 80)
    print()
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    print()
    
    try:
        # Connect to MongoDB
        print("🔌 Connecting to MongoDB...")
        client = MongoClient(MONGO_URI)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB")
        print()
        
        # Export each collection
        print("📤 Exporting collections...")
        print("-" * 80)
        
        exported_count = 0
        for collection_name in COLLECTIONS:
            success = export_collection_to_excel(client, DATABASE, collection_name, output_dir)
            if success:
                exported_count += 1
            print()
        
        # Summary
        print("=" * 80)
        print(f"✅ Export complete! {exported_count}/{len(COLLECTIONS)} collections exported")
        print()
        print("📂 Files saved in: data/")
        print("💡 You can now import these Excel files into Tableau for analysis")
        print("=" * 80)
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure:")
        print("   1. MongoDB container is running: docker ps | grep mongodb")
        print("   2. MongoDB is accessible at localhost:27017")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())