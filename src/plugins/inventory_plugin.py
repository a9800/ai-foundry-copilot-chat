import json
import os
from typing import Annotated, Optional, Dict, Any
from semantic_kernel.functions import kernel_function


class InventoryManagementPlugin:
    """Plugin for managing store inventory operations."""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.inventory_file = os.path.join(self.data_dir, "inventory.json")
    
    def _load_inventory_data(self) -> Dict[str, Any]:
        """Load inventory data from JSON file."""
        try:
            with open(self.inventory_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"stores": {}}
    
    def _save_inventory_data(self, data: Dict[str, Any]) -> None:
        """Save inventory data to JSON file."""
        with open(self.inventory_file, 'w') as f:
            json.dump(data, f, indent=2)

    @kernel_function(
        description="Check current inventory levels for a specific SKU and store",
        name="check_inventory"
    )
    def check_inventory(
        self,
        store_id: Annotated[str, "The store ID to check inventory for"],
        sku: Annotated[Optional[str], "The SKU to check. If not provided, returns all inventory for the store"] = None
    ) -> str:
        """Check inventory levels for a store and optionally a specific SKU."""
        data = self._load_inventory_data()
        
        if store_id not in data["stores"]:
            return f"Store {store_id} not found."
        
        store = data["stores"][store_id]
        store_name = store["name"]
        
        if sku:
            if sku not in store["inventory"]:
                return f"SKU {sku} not found in {store_name} (Store {store_id})."
            
            item = store["inventory"][sku]
            status = "LOW STOCK" if item["current_stock"] <= item["minimum_threshold"] else "ADEQUATE"
            
            return f"""Inventory Status for {store_name} (Store {store_id}):
SKU: {item['sku']} - {item['name']}
Current Stock: {item['current_stock']} {item['unit']}
Minimum Threshold: {item['minimum_threshold']} {item['unit']}
Maximum Capacity: {item['maximum_capacity']} {item['unit']}
Status: {status}
Supplier: {item['supplier']}
Cost per Unit: ${item['cost_per_unit']}"""
        else:
            # Return all inventory for the store
            inventory_summary = f"Full Inventory for {store_name} (Store {store_id}):\\n"
            for sku_id, item in store["inventory"].items():
                status = "LOW STOCK" if item["current_stock"] <= item["minimum_threshold"] else "ADEQUATE"
                inventory_summary += f"- {item['sku']}: {item['name']} - {item['current_stock']} {item['unit']} ({status})\\n"
            
            return inventory_summary

    @kernel_function(
        description="Get all stores that have low stock for any items",
        name="check_low_stock_alerts"
    )
    def check_low_stock_alerts(self) -> str:
        """Check all stores for items with low stock levels."""
        data = self._load_inventory_data()
        low_stock_items = []
        
        for store_id, store in data["stores"].items():
            store_name = store["name"]
            for sku, item in store["inventory"].items():
                if item["current_stock"] <= item["minimum_threshold"]:
                    low_stock_items.append({
                        "store_id": store_id,
                        "store_name": store_name,
                        "sku": item["sku"],
                        "name": item["name"],
                        "current_stock": item["current_stock"],
                        "minimum_threshold": item["minimum_threshold"],
                        "unit": item["unit"],
                        "supplier": item["supplier"]
                    })
        
        if not low_stock_items:
            return "No low stock alerts found. All items are adequately stocked."
        
        alert_summary = "🚨 LOW STOCK ALERTS:\\n\\n"
        for item in low_stock_items:
            shortage = item["minimum_threshold"] - item["current_stock"]
            alert_summary += f"""Store {item['store_id']} ({item['store_name']}):
- SKU {item['sku']}: {item['name']}
- Current: {item['current_stock']} {item['unit']}
- Minimum: {item['minimum_threshold']} {item['unit']}
- Shortage: {shortage} {item['unit']}
- Supplier: {item['supplier']}

"""
        
        return alert_summary

    @kernel_function(
        description="Update inventory levels after receiving deliveries or sales",
        name="update_inventory"
    )
    def update_inventory(
        self,
        store_id: Annotated[str, "The store ID"],
        sku: Annotated[str, "The SKU to update"],
        quantity_change: Annotated[int, "Quantity change (positive for deliveries, negative for sales)"],
        reason: Annotated[str, "Reason for the change (e.g., 'delivery', 'sale', 'adjustment')"]
    ) -> str:
        """Update inventory levels for a specific item."""
        data = self._load_inventory_data()
        
        if store_id not in data["stores"]:
            return f"Store {store_id} not found."
        
        if sku not in data["stores"][store_id]["inventory"]:
            return f"SKU {sku} not found in store {store_id}."
        
        item = data["stores"][store_id]["inventory"][sku]
        old_stock = item["current_stock"]
        new_stock = old_stock + quantity_change
        
        if new_stock < 0:
            return f"Cannot update inventory. Would result in negative stock ({new_stock})."
        
        if new_stock > item["maximum_capacity"]:
            return f"Cannot update inventory. Would exceed maximum capacity ({item['maximum_capacity']} {item['unit']})."
        
        item["current_stock"] = new_stock
        self._save_inventory_data(data)
        
        store_name = data["stores"][store_id]["name"]
        return f"""Inventory updated for {store_name} (Store {store_id}):
SKU {sku} - {item['name']}
Previous Stock: {old_stock} {item['unit']}
Change: {quantity_change:+d} {item['unit']} ({reason})
New Stock: {new_stock} {item['unit']}
Status: {'LOW STOCK' if new_stock <= item['minimum_threshold'] else 'ADEQUATE'}"""