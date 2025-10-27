import json
import os
from datetime import datetime, timedelta
from typing import Annotated, Optional, Dict, Any, List
from semantic_kernel.functions import kernel_function


class DeliveryManagementPlugin:
    """Plugin for managing delivery operations and scheduling."""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.deliveries_file = os.path.join(self.data_dir, "deliveries.json")
        self.inventory_file = os.path.join(self.data_dir, "inventory.json")
    
    def _load_deliveries_data(self) -> Dict[str, Any]:
        """Load deliveries data from JSON file."""
        try:
            with open(self.deliveries_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"deliveries": [], "delivery_statuses": {}}
    
    def _load_inventory_data(self) -> Dict[str, Any]:
        """Load inventory data from JSON file."""
        try:
            with open(self.inventory_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"stores": {}}
    
    def _save_deliveries_data(self, data: Dict[str, Any]) -> None:
        """Save deliveries data to JSON file."""
        with open(self.deliveries_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_delivery_id(self) -> str:
        """Generate a new delivery ID."""
        data = self._load_deliveries_data()
        existing_ids = [d["delivery_id"] for d in data["deliveries"]]
        counter = len(existing_ids) + 1
        return f"DEL-{counter:03d}"
    
    def _generate_tracking_number(self, supplier: str) -> str:
        """Generate a tracking number based on supplier."""
        supplier_codes = {
            "Coffee Co.": "CC",
            "Tea Masters": "TM", 
            "Sweet Treats Inc.": "STI",
            "Healthy Snacks Co.": "HSC",
            "Dairy Fresh": "DF"
        }
        code = supplier_codes.get(supplier, "GEN")
        timestamp = datetime.now().strftime("%m%d%H%M")
        return f"{code}{timestamp}"

    @kernel_function(
        description="Check scheduled deliveries for a store or all stores",
        name="check_deliveries"
    )
    def check_deliveries(
        self,
        store_id: Annotated[Optional[str], "Store ID to check deliveries for. If not provided, shows all deliveries"] = None,
        status: Annotated[Optional[str], "Filter by delivery status (pending, scheduled, in_transit, delivered, cancelled, delayed)"] = None
    ) -> str:
        """Check scheduled deliveries with optional filtering."""
        data = self._load_deliveries_data()
        inventory_data = self._load_inventory_data()
        
        deliveries = data["deliveries"]
        
        # Filter by store_id if provided
        if store_id:
            deliveries = [d for d in deliveries if d["store_id"] == store_id]
            if not deliveries:
                return f"No deliveries found for store {store_id}."
        
        # Filter by status if provided
        if status:
            deliveries = [d for d in deliveries if d["status"].lower() == status.lower()]
            if not deliveries:
                filter_msg = f" for store {store_id}" if store_id else ""
                return f"No deliveries found with status '{status}'{filter_msg}."
        
        if not deliveries:
            return "No deliveries found."
        
        result = "📦 DELIVERY SCHEDULE:\\n\\n"
        
        for delivery in sorted(deliveries, key=lambda x: x["scheduled_delivery_date"]):
            store_name = "Unknown Store"
            if delivery["store_id"] in inventory_data["stores"]:
                store_name = inventory_data["stores"][delivery["store_id"]]["name"]
            
            # Get item name from inventory
            item_name = "Unknown Item"
            if (delivery["store_id"] in inventory_data["stores"] and 
                delivery["sku"] in inventory_data["stores"][delivery["store_id"]]["inventory"]):
                item_name = inventory_data["stores"][delivery["store_id"]]["inventory"][delivery["sku"]]["name"]
            
            scheduled_date = datetime.fromisoformat(delivery["scheduled_delivery_date"].replace('Z', '+00:00'))
            
            result += f"""Delivery ID: {delivery['delivery_id']}
Store: {store_name} (ID: {delivery['store_id']})
Item: {item_name} (SKU: {delivery['sku']})
Quantity: {delivery['quantity']} units
Status: {delivery['status'].upper()}
Scheduled: {scheduled_date.strftime('%Y-%m-%d %H:%M')}
Supplier: {delivery['supplier']}
Total Cost: ${delivery['total_cost']:.2f}
Tracking: {delivery['tracking_number']}

"""
        
        return result

    @kernel_function(
        description="Place a new delivery order for inventory restocking",
        name="place_delivery_order"
    )
    def place_delivery_order(
        self,
        store_id: Annotated[str, "The store ID where items will be delivered"],
        sku: Annotated[str, "The SKU of the item to order"],
        quantity: Annotated[int, "Quantity to order"],
        urgent: Annotated[bool, "Whether this is an urgent order (affects delivery date)"] = False
    ) -> str:
        """Place a new delivery order for restocking."""
        inventory_data = self._load_inventory_data()
        deliveries_data = self._load_deliveries_data()
        
        # Validate store exists
        if store_id not in inventory_data["stores"]:
            return f"Error: Store {store_id} not found."
        
        # Validate SKU exists in store
        store = inventory_data["stores"][store_id]
        if sku not in store["inventory"]:
            return f"Error: SKU {sku} not found in store {store_id}."
        
        item = store["inventory"][sku]
        
        # Check if quantity would exceed maximum capacity
        new_total = item["current_stock"] + quantity
        if new_total > item["maximum_capacity"]:
            return f"Error: Order quantity would exceed maximum capacity. Current: {item['current_stock']}, Max: {item['maximum_capacity']}, Requested: {quantity}"
        
        # Calculate delivery date (urgent orders get next day, regular orders get 3-5 days)
        order_date = datetime.now()
        if urgent:
            delivery_date = order_date + timedelta(days=1)
        else:
            delivery_date = order_date + timedelta(days=3)  # Standard 3-day delivery
        
        # Create new delivery
        delivery_id = self._generate_delivery_id()
        tracking_number = self._generate_tracking_number(item["supplier"])
        total_cost = quantity * item["cost_per_unit"]
        
        new_delivery = {
            "delivery_id": delivery_id,
            "store_id": store_id,
            "sku": sku,
            "quantity": quantity,
            "status": "pending",
            "order_date": order_date.isoformat() + "Z",
            "scheduled_delivery_date": delivery_date.isoformat() + "Z",
            "supplier": item["supplier"],
            "cost_per_unit": item["cost_per_unit"],
            "total_cost": total_cost,
            "tracking_number": tracking_number
        }
        
        deliveries_data["deliveries"].append(new_delivery)
        self._save_deliveries_data(deliveries_data)
        
        priority = "URGENT" if urgent else "STANDARD"
        capacity_utilization = (new_total/item['maximum_capacity']*100)
        
        # Return adaptive card JSON format
        adaptive_card = {
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Delivery Order Placed Successfully!",
                    "size": "Large",
                    "weight": "Bolder",
                    "color": "Good",
                    "spacing": "Medium"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {
                            "title": "Delivery ID:",
                            "value": delivery_id
                        },
                        {
                            "title": "Store:",
                            "value": f"{store['name']} (ID: {store_id})"
                        },
                        {
                            "title": "Item:",
                            "value": f"{item['name']} (SKU: {sku})"
                        },
                        {
                            "title": "Quantity:",
                            "value": f"{quantity} {item['unit']}"
                        },
                        {
                            "title": "Priority:",
                            "value": priority
                        },
                        {
                            "title": "Supplier:",
                            "value": item['supplier']
                        },
                        {
                            "title": "Unit Cost:",
                            "value": f"${item['cost_per_unit']:.2f}"
                        },
                        {
                            "title": "Total Cost:",
                            "value": f"${total_cost:.2f}"
                        },
                        {
                            "title": "Tracking Number:",
                            "value": tracking_number
                        },
                        {
                            "title": "Scheduled Delivery:",
                            "value": delivery_date.strftime('%Y-%m-%d %H:%M')
                        }
                    ],
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": "Inventory Update:",
                    "weight": "Bolder",
                    "size": "Medium",
                    "spacing": "Large"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {
                            "title": "Current Inventory:",
                            "value": f"{item['current_stock']} {item['unit']}"
                        },
                        {
                            "title": "After Delivery:",
                            "value": f"{new_total} {item['unit']}"
                        },
                        {
                            "title": "Capacity Utilization:",
                            "value": f"{capacity_utilization:.1f}%"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "Track Delivery",
                    "url": f"https://tracking.example.com/{tracking_number}"
                }
            ]
        }
        
        return json.dumps({
            "contentType": "AdaptiveCard",
            "content": adaptive_card
        })

    @kernel_function(
        description="Update the status of an existing delivery",
        name="update_delivery_status"
    )
    def update_delivery_status(
        self,
        delivery_id: Annotated[str, "The delivery ID to update"],
        new_status: Annotated[str, "New status (pending, scheduled, in_transit, delivered, cancelled, delayed)"]
    ) -> str:
        """Update the status of a delivery."""
        data = self._load_deliveries_data()
        
        # Find the delivery
        delivery = None
        for d in data["deliveries"]:
            if d["delivery_id"] == delivery_id:
                delivery = d
                break
        
        if not delivery:
            return f"Delivery {delivery_id} not found."
        
        valid_statuses = list(data["delivery_statuses"].keys())
        if new_status.lower() not in valid_statuses:
            return f"Invalid status '{new_status}'. Valid statuses: {', '.join(valid_statuses)}"
        
        old_status = delivery["status"]
        delivery["status"] = new_status.lower()
        
        # If marked as delivered, add actual delivery date
        if new_status.lower() == "delivered":
            delivery["actual_delivery_date"] = datetime.now().isoformat() + "Z"
        
        self._save_deliveries_data(data)
        
        return f"""Delivery status updated:
Delivery ID: {delivery_id}
Previous Status: {old_status.upper()}
New Status: {new_status.upper()}
Description: {data['delivery_statuses'][new_status.lower()]}"""

    @kernel_function(
        description="Get delivery recommendations based on low stock levels",
        name="get_delivery_recommendations"
    )
    def get_delivery_recommendations(self) -> str:
        """Analyze inventory and recommend deliveries for low stock items."""
        inventory_data = self._load_inventory_data()
        deliveries_data = self._load_deliveries_data()
        
        recommendations = []
        
        # Get pending/scheduled deliveries to avoid duplicates
        pending_deliveries = {}
        for delivery in deliveries_data["deliveries"]:
            if delivery["status"] in ["pending", "scheduled", "in_transit"]:
                key = f"{delivery['store_id']}-{delivery['sku']}"
                pending_deliveries[key] = delivery["quantity"]
        
        for store_id, store in inventory_data["stores"].items():
            for sku, item in store["inventory"].items():
                if item["current_stock"] <= item["minimum_threshold"]:
                    # Check if there's already a pending delivery
                    key = f"{store_id}-{sku}"
                    pending_qty = pending_deliveries.get(key, 0)
                    
                    # Calculate recommended order quantity
                    shortage = item["minimum_threshold"] - item["current_stock"]
                    buffer = int(item["minimum_threshold"] * 0.5)  # 50% buffer
                    recommended_qty = shortage + buffer - pending_qty
                    
                    if recommended_qty > 0:  # Only recommend if we still need more
                        recommendations.append({
                            "store_id": store_id,
                            "store_name": store["name"],
                            "sku": sku,
                            "item_name": item["name"],
                            "current_stock": item["current_stock"],
                            "minimum_threshold": item["minimum_threshold"],
                            "recommended_qty": min(recommended_qty, item["maximum_capacity"] - item["current_stock"]),
                            "unit": item["unit"],
                            "supplier": item["supplier"],
                            "estimated_cost": recommended_qty * item["cost_per_unit"],
                            "pending_delivery": pending_qty
                        })
        
        if not recommendations:
            return "🎉 No delivery recommendations needed. All items are adequately stocked or have pending deliveries."
        
        result = "📋 DELIVERY RECOMMENDATIONS:\\n\\n"
        total_cost = 0
        
        for rec in recommendations:
            result += f"""Store {rec['store_id']} - {rec['store_name']}:
SKU {rec['sku']}: {rec['item_name']}
Current Stock: {rec['current_stock']} {rec['unit']}
Minimum Threshold: {rec['minimum_threshold']} {rec['unit']}
Recommended Order: {rec['recommended_qty']} {rec['unit']}
Supplier: {rec['supplier']}
Estimated Cost: ${rec['estimated_cost']:.2f}
{'⚠️ Pending Delivery: ' + str(rec['pending_delivery']) + ' ' + rec['unit'] if rec['pending_delivery'] > 0 else ''}

"""
            total_cost += rec['estimated_cost']
        
        result += f"💰 Total Estimated Cost: ${total_cost:.2f}"
        
        return result