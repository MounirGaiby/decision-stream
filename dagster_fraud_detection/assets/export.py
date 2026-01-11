from dagster import asset, AssetExecutionContext, Output, MetadataValue
import subprocess
# Removed dependency import
# from .validation import validate_data_asset

@asset(
    description="Export data to Excel files for Tableau analysis",
    group_name="export",
    # deps=[validate_data_asset], # REMOVED: Manual execution only
)
def mongo_export_asset(
    context: AssetExecutionContext,
) -> Output[dict]:
    """Export MongoDB data to Excel files"""

    context.log.info("Exporting data to Excel...")

    try:
        # Run the export script
        result = subprocess.run(
            ["python", "src/export_to_excel.py"],
            capture_output=True,
            text=True,
            timeout=120
        )

        context.log.info(result.stdout)

        if result.returncode != 0:
            raise Exception(f"Export failed: {result.stderr}")

        context.log.info("Export complete!")

        return Output(
            {"success": True, "exit_code": result.returncode},
            metadata={"success": True}
        )

    except Exception as e:
        context.log.error(f"Export failed: {e}")
        return Output(
            {"success": False, "error": str(e)},
            metadata={"success": False}
        )
