"""
اختبار تحمل محسّن - يفحص الأخطاء بالتفصيل
"""
import asyncio
import aiohttp
import time
import json
import statistics
from collections import defaultdict

BASE_URL = "http://localhost:8001"
NUM_USERS = 20
REQUESTS_PER_USER = 5

results = {
    "by_endpoint": defaultdict(lambda: {"success": 0, "fail": 0, "times": [], "errors": []}),
    "total": {"success": 0, "fail": 0}
}


async def get_token(session):
    try:
        async with session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json={"email": "admin@system.com", "password": "password"},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("access_token")
    except Exception as e:
        print(f"Auth Error: {e}")
    return None


async def test_endpoint(session, url, token, name):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    start = time.time()
    
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            elapsed = time.time() - start
            results["by_endpoint"][name]["times"].append(elapsed)
            
            if resp.status == 200:
                results["by_endpoint"][name]["success"] += 1
                results["total"]["success"] += 1
                return True
            else:
                text = await resp.text()
                results["by_endpoint"][name]["fail"] += 1
                results["by_endpoint"][name]["errors"].append(f"{resp.status}: {text[:100]}")
                results["total"]["fail"] += 1
                return False
                
    except Exception as e:
        results["by_endpoint"][name]["fail"] += 1
        results["by_endpoint"][name]["errors"].append(str(e))
        results["total"]["fail"] += 1
        return False


async def user_simulation(user_id):
    async with aiohttp.ClientSession() as session:
        token = await get_token(session)
        if not token:
            print(f"User {user_id}: Failed to get token")
            return
        
        endpoints = [
            (f"{BASE_URL}/api/v2/reports/dashboard", "Dashboard"),
            (f"{BASE_URL}/api/v2/admin/stats", "Stats"),
            (f"{BASE_URL}/api/v2/admin/users", "Users"),
            (f"{BASE_URL}/api/v2/projects", "Projects"),
            (f"{BASE_URL}/api/v2/suppliers", "Suppliers"),
        ]
        
        for _ in range(REQUESTS_PER_USER):
            for url, name in endpoints:
                await test_endpoint(session, url, token, name)
                await asyncio.sleep(0.05)


async def main():
    print("=" * 60)
    print(f"🧪 اختبار تحمل: {NUM_USERS} مستخدم × {REQUESTS_PER_USER} جولات")
    print("=" * 60)
    
    start = time.time()
    
    # تشغيل المستخدمين
    await asyncio.gather(*[user_simulation(i) for i in range(NUM_USERS)])
    
    total_time = time.time() - start
    
    # النتائج
    print(f"\n⏱️  الوقت الإجمالي: {total_time:.2f}s")
    print(f"✅ نجاح: {results['total']['success']}")
    print(f"❌ فشل: {results['total']['fail']}")
    
    total = results['total']['success'] + results['total']['fail']
    rate = results['total']['success'] / total * 100 if total > 0 else 0
    print(f"📊 معدل النجاح: {rate:.1f}%")
    print(f"🚀 طلبات/ثانية: {total/total_time:.1f}")
    
    print("\n📋 النتائج حسب الـ Endpoint:")
    print("-" * 60)
    
    for name, data in sorted(results["by_endpoint"].items()):
        total_ep = data["success"] + data["fail"]
        rate_ep = data["success"] / total_ep * 100 if total_ep > 0 else 0
        avg_time = statistics.mean(data["times"]) * 1000 if data["times"] else 0
        
        status = "✅" if rate_ep >= 95 else "⚠️" if rate_ep >= 80 else "❌"
        print(f"{status} {name:15} | نجاح: {data['success']:3} | فشل: {data['fail']:3} | {rate_ep:5.1f}% | {avg_time:6.1f}ms")
        
        if data["errors"]:
            unique_errors = list(set(data["errors"]))[:3]
            for err in unique_errors:
                print(f"   ⚠️  {err[:80]}")
    
    print("\n" + "=" * 60)
    if rate >= 95:
        print("🏆 ممتاز! التطبيق يتحمل الحمل العالي")
    elif rate >= 85:
        print("👍 جيد! أداء مقبول")
    elif rate >= 70:
        print("⚠️  مقبول مع بعض المشاكل")
    else:
        print("❌ يحتاج تحسين")


if __name__ == "__main__":
    asyncio.run(main())
