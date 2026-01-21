"""
Reports Service - Business logic for reports and analytics
خدمة التقارير - منطق العمل

Architecture: Route -> Service -> Repository
"""
from typing import Optional, List, Dict
from datetime import datetime
from app.repositories.reports_repository import ReportsRepository


class ReportsService:
    """Service layer for reports operations"""
    
    def __init__(self, repository: ReportsRepository):
        self.repository = repository
    
    # ==================== Dashboard Stats ====================
    
    async def get_dashboard_stats(self) -> Dict:
        """Get main dashboard statistics"""
        total_projects = await self.repository.count_projects()
        active_projects = await self.repository.count_active_projects()
        total_orders = await self.repository.count_orders()
        pending_orders = await self.repository.count_orders_by_status(
            ["pending", "pending_approval", "pending_gm_approval"]
        )
        approved_orders = await self.repository.count_orders_by_status(["approved"])
        total_amount = await self.repository.get_approved_orders_total()
        total_requests = await self.repository.count_requests()
        pending_requests = await self.repository.count_pending_requests()
        total_suppliers = await self.repository.count_suppliers()
        recent_orders = await self.repository.count_recent_orders(7)
        
        return {
            "projects": {
                "total": total_projects,
                "active": active_projects
            },
            "orders": {
                "total": total_orders,
                "pending": pending_orders,
                "approved": approved_orders,
                "recent_7d": recent_orders
            },
            "requests": {
                "total": total_requests,
                "pending": pending_requests
            },
            "suppliers": {
                "total": total_suppliers
            },
            "financials": {
                "total_approved_amount": float(total_amount)
            }
        }
    
    # ==================== Budget Reports ====================
    
    async def get_budget_report(
        self, 
        project_id: Optional[str] = None
    ) -> Dict:
        """Get budget report"""
        categories = await self.repository.get_budget_categories(project_id)
        
        report = []
        total_estimated = 0
        total_spent = 0
        
        for cat in categories:
            spent = await self.repository.get_spent_by_category(cat.id)
            estimated = cat.estimated_budget or 0
            remaining = estimated - spent
            
            total_estimated += estimated
            total_spent += spent
            
            report.append({
                "id": cat.id,
                "code": cat.code,
                "name": cat.name,
                "project_id": cat.project_id,
                "estimated_budget": estimated,
                "spent_amount": float(spent),
                "remaining_amount": float(remaining),
                "percentage_used": round((spent / estimated * 100), 2) if estimated > 0 else 0
            })
        
        return {
            "categories": report,
            "summary": {
                "total_estimated": total_estimated,
                "total_spent": float(total_spent),
                "total_remaining": float(total_estimated - total_spent),
                "overall_percentage": round((total_spent / total_estimated * 100), 2) if total_estimated > 0 else 0
            }
        }
    
    async def get_budget_export_data(
        self, 
        project_id: Optional[str] = None
    ) -> List[Dict]:
        """Get budget data for export"""
        categories = await self.repository.get_budget_categories(project_id)
        
        result = []
        for cat in categories:
            spent = await self.repository.get_spent_by_category(cat.id)
            estimated = cat.estimated_budget or 0
            remaining = estimated - spent
            percentage = round((spent / estimated * 100), 2) if estimated > 0 else 0
            
            result.append({
                "code": cat.code,
                "name": cat.name,
                "estimated": estimated,
                "spent": spent,
                "remaining": remaining,
                "percentage": percentage
            })
        
        return result
    
    # ==================== Cost Savings ====================
    
    async def get_cost_savings_report(self) -> Dict:
        """Get cost savings report comparing prices"""
        orders = await self.repository.get_approved_orders_with_limit(100)
        
        total_savings = 0
        savings_items = []
        
        for order in orders:
            items = await self.repository.get_order_items(order.id)
            
            for item in items:
                if item.catalog_item_id:
                    catalog_item = await self.repository.get_catalog_item(
                        item.catalog_item_id
                    )
                    
                    if catalog_item and item.unit_price and catalog_item.price:
                        price_diff = catalog_item.price - item.unit_price
                        if price_diff > 0:
                            saving = price_diff * item.quantity
                            total_savings += saving
                            savings_items.append({
                                "item_name": item.name,
                                "catalog_price": catalog_item.price,
                                "order_price": item.unit_price,
                                "quantity": item.quantity,
                                "saving": saving
                            })
        
        return {
            "total_savings": total_savings,
            "items_with_savings": len(savings_items),
            "savings_details": savings_items[:20]  # Top 20
        }
    
    # ==================== Project Report ====================
    
    async def get_project_report(self, project_id: str) -> Optional[Dict]:
        """Get detailed project report"""
        project = await self.repository.get_project_by_id(project_id)
        if not project:
            return None
        
        orders = await self.repository.get_orders_by_project(project_id)
        categories = await self.repository.get_budget_categories_by_project(project_id)
        requests = await self.repository.get_requests_by_project(project_id)
        
        # Calculate totals
        total_approved = sum(
            o.total_amount or 0 
            for o in orders 
            if o.status == "approved"
        )
        total_pending = sum(
            o.total_amount or 0 
            for o in orders 
            if o.status in ["pending", "pending_approval"]
        )
        total_budget = sum(c.estimated_budget or 0 for c in categories)
        
        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "code": project.code,
                "status": project.status
            },
            "statistics": {
                "total_orders": len(orders),
                "approved_orders": len([o for o in orders if o.status == "approved"]),
                "pending_orders": len([o for o in orders if o.status in ["pending", "pending_approval"]]),
                "total_requests": len(requests),
                "total_categories": len(categories)
            },
            "financials": {
                "total_budget": total_budget,
                "total_approved_amount": total_approved,
                "total_pending_amount": total_pending,
                "remaining_budget": total_budget - total_approved,
                "budget_utilization": round((total_approved / total_budget * 100), 2) if total_budget > 0 else 0
            }
        }
    
    # ==================== Advanced Reports ====================
    
    async def get_advanced_summary(
        self,
        project_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Get advanced summary report with filters"""
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        orders = await self.repository.get_orders_with_filters(
            project_id, supplier_id, start_dt, end_dt
        )
        requests = await self.repository.get_requests_with_filters(
            project_id, start_dt, end_dt
        )
        
        # Calculate stats
        total_spending = sum(o.total_amount or 0 for o in orders)
        approved_orders = len([
            o for o in orders 
            if o.status in ["approved", "delivered", "completed"]
        ])
        
        # Top projects by spending
        project_spending = {}
        for order in orders:
            pname = order.project_name or "غير محدد"
            project_spending[pname] = project_spending.get(pname, 0) + (order.total_amount or 0)
        
        top_projects = [
            {"name": k, "amount": v} 
            for k, v in sorted(
                project_spending.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        ]
        
        # Top suppliers
        supplier_stats = {}
        for order in orders:
            sname = order.supplier_name or "غير محدد"
            if sname not in supplier_stats:
                supplier_stats[sname] = {"orders": 0, "amount": 0}
            supplier_stats[sname]["orders"] += 1
            supplier_stats[sname]["amount"] += order.total_amount or 0
        
        top_suppliers = [
            {"name": k, "orders": v["orders"], "amount": v["amount"]} 
            for k, v in sorted(
                supplier_stats.items(), 
                key=lambda x: x[1]["amount"], 
                reverse=True
            )[:5]
        ]
        
        return {
            "summary": {
                "total_requests": len(requests),
                "total_orders": len(orders),
                "total_spending": total_spending,
                "approved_orders": approved_orders,
                "pending_orders": len([
                    o for o in orders 
                    if o.status in ["pending", "pending_approval"]
                ]),
                "average_order_value": total_spending / len(orders) if orders else 0
            },
            "top_projects": top_projects,
            "top_suppliers": top_suppliers,
            "spending_by_category": [],
            "period": {
                "start": start_date,
                "end": end_date
            }
        }
    
    async def get_approval_analytics(
        self,
        project_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Get approval analytics report"""
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        requests = await self.repository.get_requests_with_filters(
            project_id, start_dt, end_dt
        )
        
        total = len(requests)
        approved = len([
            r for r in requests 
            if r.status in ["approved_by_engineer", "approved", "issued"]
        ])
        rejected = len([r for r in requests if r.status == "rejected"])
        pending = len([
            r for r in requests 
            if r.status in ["pending", "pending_approval"]
        ])
        
        return {
            "total_requests": total,
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "approval_rate": round((approved / total * 100), 2) if total > 0 else 0,
            "rejection_rate": round((rejected / total * 100), 2) if total > 0 else 0,
            "by_status": {
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
                "issued": len([r for r in requests if r.status == "issued"])
            }
        }
    
    async def get_supplier_performance(
        self,
        supplier_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Get supplier performance report"""
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        orders = await self.repository.get_orders_with_filters(
            supplier_id=supplier_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Group by supplier
        supplier_stats = {}
        for order in orders:
            supplier_name = order.supplier_name or "غير محدد"
            if supplier_name not in supplier_stats:
                supplier_stats[supplier_name] = {
                    "name": supplier_name,
                    "total_orders": 0,
                    "total_amount": 0,
                    "delivered": 0,
                    "pending": 0
                }
            
            supplier_stats[supplier_name]["total_orders"] += 1
            supplier_stats[supplier_name]["total_amount"] += order.total_amount or 0
            
            if order.status in ["delivered", "completed"]:
                supplier_stats[supplier_name]["delivered"] += 1
            elif order.status in ["pending", "pending_approval", "approved"]:
                supplier_stats[supplier_name]["pending"] += 1
        
        suppliers_list = sorted(
            supplier_stats.values(), 
            key=lambda x: x["total_amount"], 
            reverse=True
        )
        
        return {
            "suppliers": suppliers_list[:10],
            "total_suppliers": len(supplier_stats),
            "total_orders": len(orders),
            "total_amount": sum(o.total_amount or 0 for o in orders)
        }
    
    async def get_price_variance(
        self,
        item_name: Optional[str] = None
    ) -> Dict:
        """Get price variance report"""
        items = await self.repository.get_price_variance_items(item_name)
        
        # Group by item name and calculate variance
        item_prices = {}
        for item in items:
            name = item.name
            if name not in item_prices:
                item_prices[name] = {"prices": [], "quantities": []}
            item_prices[name]["prices"].append(item.unit_price or 0)
            item_prices[name]["quantities"].append(item.quantity or 0)
        
        # Calculate variance
        variance_report = []
        for name, data in item_prices.items():
            prices = [p for p in data["prices"] if p > 0]
            if len(prices) >= 2:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                variance = max_price - min_price
                variance_pct = (variance / avg_price * 100) if avg_price > 0 else 0
                
                variance_report.append({
                    "item_name": name,
                    "avg_price": round(avg_price, 2),
                    "min_price": round(min_price, 2),
                    "max_price": round(max_price, 2),
                    "variance": round(variance, 2),
                    "variance_percentage": round(variance_pct, 2),
                    "order_count": len(prices)
                })
        
        # Sort by variance percentage
        variance_report.sort(key=lambda x: x["variance_percentage"], reverse=True)
        
        return {
            "items": variance_report[:20],
            "total_items_analyzed": len(item_prices),
            "high_variance_items": len([
                i for i in variance_report 
                if i["variance_percentage"] > 20
            ])
        }
