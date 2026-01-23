"""
اختبار تحمل التطبيق - Load Test
يختبر قدرة التطبيق على تحمل 20+ مستخدم متزامن وبيانات عالية
"""
import asyncio
import aiohttp
import time
import json
import random
import string
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import statistics

# إعدادات الاختبار
BASE_URL = "http://localhost:8001"  # Preview environment
NUM_CONCURRENT_USERS = 25  # عدد المستخدمين المتزامنين
NUM_REQUESTS_PER_USER = 10  # عدد الطلبات لكل مستخدم
TOTAL_DATA_RECORDS = 50  # عدد السجلات للاختبار

# نتائج الاختبار
results = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "response_times": [],
    "errors": []
}


def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_email():
    return f"test_{random_string(6)}@loadtest.com"


async def get_auth_token(session):
    """الحصول على token للمصادقة"""
    try:
        async with session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json={"email": "admin@system.com", "password": "password"},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("access_token")
    except Exception as e:
        results["errors"].append(f"Auth error: {str(e)}")
    return None


async def test_endpoint(session, method, url, token=None, data=None, test_name=""):
    """اختبار endpoint واحد"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    start_time = time.time()
    try:
        if method == "GET":
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response_time = time.time() - start_time
                results["response_times"].append(response_time)
                results["total_requests"] += 1
                
                if response.status in [200, 201]:
                    results["successful_requests"] += 1
                    return True, response_time, response.status
                else:
                    results["failed_requests"] += 1
                    return False, response_time, response.status
                    
        elif method == "POST":
            async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response_time = time.time() - start_time
                results["response_times"].append(response_time)
                results["total_requests"] += 1
                
                if response.status in [200, 201]:
                    results["successful_requests"] += 1
                    return True, response_time, response.status
                else:
                    results["failed_requests"] += 1
                    text = await response.text()
                    return False, response_time, f"{response.status}: {text[:100]}"
                    
    except asyncio.TimeoutError:
        results["total_requests"] += 1
        results["failed_requests"] += 1
        results["errors"].append(f"Timeout: {test_name}")
        return False, 30, "Timeout"
    except Exception as e:
        results["total_requests"] += 1
        results["failed_requests"] += 1
        results["errors"].append(f"{test_name}: {str(e)}")
        return False, 0, str(e)


async def simulate_user(user_id):
    """محاكاة مستخدم واحد"""
    user_results = []
    
    async with aiohttp.ClientSession() as session:
        # 1. تسجيل الدخول
        token = await get_auth_token(session)
        if not token:
            return user_results
        
        for i in range(NUM_REQUESTS_PER_USER):
            # اختيار عملية عشوائية
            operation = random.choice([
                "dashboard",
                "users_list",
                "projects_list",
                "suppliers_list",
                "orders_list",
                "stats"
            ])
            
            if operation == "dashboard":
                success, time_taken, status = await test_endpoint(
                    session, "GET",
                    f"{BASE_URL}/api/v2/reports/dashboard",
                    token, test_name=f"User{user_id}-Dashboard"
                )
            elif operation == "users_list":
                success, time_taken, status = await test_endpoint(
                    session, "GET",
                    f"{BASE_URL}/api/v2/admin/users",
                    token, test_name=f"User{user_id}-Users"
                )
            elif operation == "projects_list":
                success, time_taken, status = await test_endpoint(
                    session, "GET",
                    f"{BASE_URL}/api/v2/projects",
                    token, test_name=f"User{user_id}-Projects"
                )
            elif operation == "suppliers_list":
                success, time_taken, status = await test_endpoint(
                    session, "GET",
                    f"{BASE_URL}/api/v2/catalog/suppliers",
                    token, test_name=f"User{user_id}-Suppliers"
                )
            elif operation == "orders_list":
                success, time_taken, status = await test_endpoint(
                    session, "GET",
                    f"{BASE_URL}/api/v2/orders",
                    token, test_name=f"User{user_id}-Orders"
                )
            elif operation == "stats":
                success, time_taken, status = await test_endpoint(
                    session, "GET",
                    f"{BASE_URL}/api/v2/admin/stats",
                    token, test_name=f"User{user_id}-Stats"
                )
            
            user_results.append({
                "user_id": user_id,
                "operation": operation,
                "success": success,
                "time": time_taken,
                "status": status
            })
            
            # تأخير قصير بين الطلبات
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    return user_results


async def create_test_data(session, token):
    """إنشاء بيانات اختبار"""
    print("\n📊 إنشاء بيانات الاختبار...")
    
    # إنشاء مشاريع
    for i in range(10):
        await test_endpoint(
            session, "POST",
            f"{BASE_URL}/api/v2/projects",
            token,
            data={
                "name": f"مشروع اختبار {i+1}",
                "description": f"وصف المشروع رقم {i+1}",
                "status": "active"
            },
            test_name=f"CreateProject-{i}"
        )
    
    # إنشاء موردين
    for i in range(5):
        await test_endpoint(
            session, "POST",
            f"{BASE_URL}/api/v2/catalog/suppliers",
            token,
            data={
                "name": f"مورد اختبار {i+1}",
                "contact_person": f"جهة اتصال {i+1}",
                "email": f"supplier{i+1}@test.com",
                "phone": f"05000000{i:02d}"
            },
            test_name=f"CreateSupplier-{i}"
        )
    
    print("✅ تم إنشاء بيانات الاختبار")


async def run_load_test():
    """تشغيل اختبار التحمل"""
    print("=" * 60)
    print("🚀 بدء اختبار تحمل التطبيق")
    print("=" * 60)
    print(f"⚙️  عدد المستخدمين المتزامنين: {NUM_CONCURRENT_USERS}")
    print(f"⚙️  عدد الطلبات لكل مستخدم: {NUM_REQUESTS_PER_USER}")
    print(f"⚙️  إجمالي الطلبات المتوقع: {NUM_CONCURRENT_USERS * NUM_REQUESTS_PER_USER}")
    print("=" * 60)
    
    # إنشاء بيانات اختبار أولاً
    async with aiohttp.ClientSession() as session:
        token = await get_auth_token(session)
        if token:
            await create_test_data(session, token)
    
    # بدء الاختبار
    print("\n🏃 تشغيل المستخدمين المتزامنين...")
    start_time = time.time()
    
    # تشغيل جميع المستخدمين بشكل متزامن
    tasks = [simulate_user(i) for i in range(NUM_CONCURRENT_USERS)]
    all_results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    # تحليل النتائج
    print("\n" + "=" * 60)
    print("📈 نتائج اختبار التحمل")
    print("=" * 60)
    
    print(f"\n⏱️  الوقت الإجمالي: {total_time:.2f} ثانية")
    print(f"📊 إجمالي الطلبات: {results['total_requests']}")
    print(f"✅ الطلبات الناجحة: {results['successful_requests']}")
    print(f"❌ الطلبات الفاشلة: {results['failed_requests']}")
    
    if results['response_times']:
        avg_time = statistics.mean(results['response_times'])
        min_time = min(results['response_times'])
        max_time = max(results['response_times'])
        median_time = statistics.median(results['response_times'])
        
        print(f"\n⚡ أوقات الاستجابة:")
        print(f"   - المتوسط: {avg_time*1000:.2f} ms")
        print(f"   - الأدنى: {min_time*1000:.2f} ms")
        print(f"   - الأعلى: {max_time*1000:.2f} ms")
        print(f"   - الوسيط: {median_time*1000:.2f} ms")
        
        if len(results['response_times']) > 1:
            p95 = sorted(results['response_times'])[int(len(results['response_times']) * 0.95)]
            print(f"   - P95: {p95*1000:.2f} ms")
    
    success_rate = (results['successful_requests'] / results['total_requests'] * 100) if results['total_requests'] > 0 else 0
    requests_per_second = results['total_requests'] / total_time if total_time > 0 else 0
    
    print(f"\n📊 معدل النجاح: {success_rate:.1f}%")
    print(f"🚀 الطلبات في الثانية: {requests_per_second:.2f}")
    
    if results['errors']:
        print(f"\n⚠️  الأخطاء ({len(results['errors'])}):")
        for error in results['errors'][:10]:
            print(f"   - {error}")
    
    # تقييم النتائج
    print("\n" + "=" * 60)
    print("🏆 التقييم النهائي")
    print("=" * 60)
    
    if success_rate >= 95 and avg_time < 1:
        print("✅ ممتاز! التطبيق يتحمل الحمل العالي بشكل جيد جداً")
    elif success_rate >= 90 and avg_time < 2:
        print("👍 جيد! التطبيق يتحمل الحمل بشكل مقبول")
    elif success_rate >= 80:
        print("⚠️  مقبول، لكن يحتاج تحسين في الأداء")
    else:
        print("❌ يحتاج تحسين كبير في الأداء")
    
    return {
        "total_time": total_time,
        "total_requests": results['total_requests'],
        "successful_requests": results['successful_requests'],
        "failed_requests": results['failed_requests'],
        "success_rate": success_rate,
        "requests_per_second": requests_per_second,
        "avg_response_time": avg_time if results['response_times'] else 0
    }


if __name__ == "__main__":
    asyncio.run(run_load_test())
